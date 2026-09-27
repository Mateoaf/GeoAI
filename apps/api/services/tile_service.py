"""
apps/api/services/tile_service.py
Servicio de generación dinámica de teselas ráster Web Mercator (EPSG:3857) a partir de COGs en EPSG:25830.
"""

import io
from functools import lru_cache
from typing import Optional

import matplotlib
import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

from .. import config

ORIGIN_SHIFT = 20037508.342789244
INITIAL_RESOLUTION = ORIGIN_SHIFT * 2.0 / 256.0


class TileService:
    _instance: Optional["TileService"] = None

    def __init__(self):
        # Fuentes raster abiertas persistentemente en modo lectura
        self.src_score = rasterio.open(config.PATH_COG_SCORE)
        self.src_pct = rasterio.open(config.PATH_COG_PERCENTILE)
        self.src_prio = rasterio.open(config.PATH_COG_PRIORITY)

        # Fuentes ráster especializadas v2 (si existen)
        self.src_global_v2 = rasterio.open(config.PATH_COG_GLOBAL_V2) if config.PATH_COG_GLOBAL_V2.exists() else None
        self.src_roca = rasterio.open(config.PATH_COG_ROCA) if config.PATH_COG_ROCA.exists() else None
        self.src_aluvial = rasterio.open(config.PATH_COG_ALUVIAL) if config.PATH_COG_ALUVIAL.exists() else None

        # Colormaps
        self.cmap_viridis = matplotlib.colormaps["viridis"]
        self.cmap_plasma = matplotlib.colormaps["plasma"]
        self.cmap_magma = matplotlib.colormaps["magma"]
        self.cmap_cividis = matplotlib.colormaps["cividis"]

        # Cache en memoria para teselas vacías o fuera de límites
        empty_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        buf = io.BytesIO()
        empty_img.save(buf, format="PNG")
        self.empty_png = buf.getvalue()

    @classmethod
    def get_instance(cls) -> "TileService":
        if cls._instance is None:
            cls._instance = TileService()
        return cls._instance

    @lru_cache(maxsize=4096)  # noqa: B019 (Singleton instance)
    def render_tile(self, layer: str, z: int, x: int, y: int) -> bytes:
        """Renderiza una tesela PNG de 256x256 en Web Mercator EPSG:3857."""
        if z < 4 or z > 15:
            return self.empty_png

        # Bounding box en EPSG:3857
        res = INITIAL_RESOLUTION / (2 ** z)
        minx = x * 256.0 * res - ORIGIN_SHIFT
        maxx = (x + 1) * 256.0 * res - ORIGIN_SHIFT
        maxy = ORIGIN_SHIFT - y * 256.0 * res
        miny = ORIGIN_SHIFT - (y + 1) * 256.0 * res

        # Seleccionar raster origen
        if layer == "score":
            src = self.src_score
        elif layer == "percentile":
            src = self.src_pct
        elif layer == "priority":
            src = self.src_prio
        elif layer == "global_v2_score" and self.src_global_v2 is not None:
            src = self.src_global_v2
        elif layer == "rock_score" and self.src_roca is not None:
            src = self.src_roca
        elif layer == "alluvial_score" and self.src_aluvial is not None:
            src = self.src_aluvial
        else:
            return self.empty_png

        dst_transform = from_bounds(minx, miny, maxx, maxy, 256, 256)
        dst_array = np.full((256, 256), -9999.0, dtype=np.float32)

        try:
            reproject(
                source=rasterio.band(src, 1),
                destination=dst_array,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs="EPSG:3857",
                resampling=Resampling.nearest,
                src_nodata=src.nodata,
                dst_nodata=-9999.0
            )
        except Exception:  # noqa: BLE001
            return self.empty_png

        valid_mask = (dst_array != -9999.0) & (~np.isnan(dst_array)) & (dst_array > -9000)
        if not np.any(valid_mask):
            return self.empty_png

        rgba = np.zeros((256, 256, 4), dtype=np.uint8)

        if layer in ("score", "global_v2_score"):
            norm_vals = np.clip(dst_array, 0.0, 1.0)
            colored = self.cmap_viridis(norm_vals)
            rgb = (colored[:, :, :3] * 255).astype(np.uint8)
            rgba[valid_mask, :3] = rgb[valid_mask]
            rgba[valid_mask, 3] = 210

        elif layer == "rock_score":
            norm_vals = np.clip(dst_array, 0.0, 1.0)
            colored = self.cmap_magma(norm_vals)
            rgb = (colored[:, :, :3] * 255).astype(np.uint8)
            rgba[valid_mask, :3] = rgb[valid_mask]
            rgba[valid_mask, 3] = 215

        elif layer == "alluvial_score":
            norm_vals = np.clip(dst_array, 0.0, 1.0)
            colored = self.cmap_cividis(norm_vals)
            rgb = (colored[:, :, :3] * 255).astype(np.uint8)
            rgba[valid_mask, :3] = rgb[valid_mask]
            rgba[valid_mask, 3] = 215

        elif layer == "percentile":
            norm_vals = np.clip(dst_array / 100.0, 0.0, 1.0)
            colored = self.cmap_plasma(norm_vals)
            rgb = (colored[:, :, :3] * 255).astype(np.uint8)
            rgba[valid_mask, :3] = rgb[valid_mask]
            rgba[valid_mask, 3] = 210

        elif layer == "priority":
            # 1: Top 1% (Rojo vivo), 2: Top 1-5% (Ámbar), 3: Top 5-10% (Turquesa), 0: Resto (Fondo sutil)
            m1 = valid_mask & (dst_array == 1)
            m2 = valid_mask & (dst_array == 2)
            m3 = valid_mask & (dst_array == 3)
            m0 = valid_mask & (dst_array == 0)

            rgba[m1] = [230, 57, 70, 235]    # Rojo intenso
            rgba[m2] = [244, 162, 97, 215]   # Ámbar
            rgba[m3] = [42, 157, 143, 195]   # Turquesa
            rgba[m0] = [70, 80, 95, 45]      # Gris azulado sutil

        img = Image.fromarray(rgba, "RGBA")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


def get_tile_service() -> TileService:
    return TileService.get_instance()
