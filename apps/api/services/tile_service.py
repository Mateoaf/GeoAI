"""
apps/api/services/tile_service.py
Servicio de generación dinámica y concurrente de teselas ráster Web Mercator (EPSG:3857)
a partir de arrays en memoria (EPSG:25830). 100% thread-safe y de ultra baja latencia.
"""

import io
import threading
from functools import lru_cache
from typing import Optional

import matplotlib
import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

# pyrefly: ignore [missing-import]
from .. import config

ORIGIN_SHIFT = 20037508.342789244
INITIAL_RESOLUTION = ORIGIN_SHIFT * 2.0 / 256.0


class TileService:
    _instance: Optional["TileService"] = None

    def __init__(self):
        self._lock = threading.Lock()

        # Cargar los rasters en memoria para evitar contención de handles I/O en GDAL
        with rasterio.open(config.PATH_COG_SCORE) as src:
            self.data_score = src.read(1)
            self.transform = src.transform
            self.crs = src.crs
            self.nodata = src.nodata if src.nodata is not None else -9999.0

        with rasterio.open(config.PATH_COG_PERCENTILE) as src:
            self.data_pct = src.read(1)

        with rasterio.open(config.PATH_COG_PRIORITY) as src:
            self.data_prio = src.read(1)

        # Cargar rasters especializados v2 si existen
        self.data_global_v2 = None
        if config.PATH_COG_GLOBAL_V2.exists():
            with rasterio.open(config.PATH_COG_GLOBAL_V2) as src:
                self.data_global_v2 = src.read(1)

        self.data_roca = None
        if config.PATH_COG_ROCA.exists():
            with rasterio.open(config.PATH_COG_ROCA) as src:
                self.data_roca = src.read(1)

        self.data_aluvial = None
        if config.PATH_COG_ALUVIAL.exists():
            with rasterio.open(config.PATH_COG_ALUVIAL) as src:
                self.data_aluvial = src.read(1)

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

    @lru_cache(maxsize=8192)  # noqa: B019 (Singleton instance)
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

        # Seleccionar raster origen en memoria
        if layer == "score":
            source_arr = self.data_score
        elif layer == "percentile":
            source_arr = self.data_pct
        elif layer == "priority":
            source_arr = self.data_prio
        elif layer == "global_v2_score" and self.data_global_v2 is not None:
            source_arr = self.data_global_v2
        elif layer == "rock_score" and self.data_roca is not None:
            source_arr = self.data_roca
        elif layer == "alluvial_score" and self.data_aluvial is not None:
            source_arr = self.data_aluvial
        else:
            return self.empty_png

        dst_transform = from_bounds(minx, miny, maxx, maxy, 256, 256)
        dst_array = np.full((256, 256), -9999.0, dtype=np.float32)

        try:
            with self._lock:
                reproject(
                    source=source_arr,
                    destination=dst_array,
                    src_transform=self.transform,
                    src_crs=self.crs,
                    dst_transform=dst_transform,
                    dst_crs="EPSG:3857",
                    resampling=Resampling.nearest,
                    src_nodata=self.nodata,
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
            # Solo hacer visibles celdas con señal (>0.08) para no tapar el mapa con un fondo opaco
            show_mask = valid_mask & (dst_array >= 0.08)
            rgba[show_mask, :3] = rgb[show_mask]
            alpha_scaled = np.clip((dst_array[show_mask] - 0.08) / 0.5, 0.0, 1.0)
            rgba[show_mask, 3] = (90 + alpha_scaled * 145).astype(np.uint8)

        elif layer == "rock_score":
            norm_vals = np.clip(dst_array, 0.0, 1.0)
            colored = self.cmap_magma(norm_vals)
            rgb = (colored[:, :, :3] * 255).astype(np.uint8)
            show_mask = valid_mask & (dst_array >= 0.10)
            rgba[show_mask, :3] = rgb[show_mask]
            alpha_scaled = np.clip((dst_array[show_mask] - 0.10) / 0.5, 0.0, 1.0)
            rgba[show_mask, 3] = (100 + alpha_scaled * 140).astype(np.uint8)

        elif layer == "alluvial_score":
            norm_vals = np.clip(dst_array, 0.0, 1.0)
            colored = self.cmap_cividis(norm_vals)
            rgb = (colored[:, :, :3] * 255).astype(np.uint8)
            show_mask = valid_mask & (dst_array >= 0.08)
            rgba[show_mask, :3] = rgb[show_mask]
            alpha_scaled = np.clip((dst_array[show_mask] - 0.08) / 0.45, 0.0, 1.0)
            rgba[show_mask, 3] = (90 + alpha_scaled * 145).astype(np.uint8)

        elif layer == "percentile":
            norm_vals = np.clip(dst_array / 100.0, 0.0, 1.0)
            colored = self.cmap_plasma(norm_vals)
            rgb = (colored[:, :, :3] * 255).astype(np.uint8)
            # Solo mostrar percentiles superiores a la mediana (>50%)
            show_mask = valid_mask & (dst_array >= 50.0)
            rgba[show_mask, :3] = rgb[show_mask]
            alpha_scaled = np.clip((dst_array[show_mask] - 50.0) / 50.0, 0.0, 1.0)
            rgba[show_mask, 3] = (80 + alpha_scaled * 150).astype(np.uint8)

        elif layer == "priority":
            # 1: Top 1% (Rojo carmesí), 2: Top 1-5% (Ámbar dorado), 3: Top 5-10% (Turquesa esmeralda)
            # El fondo (0) es 100% transparente para ver el mapa satelital/topográfico debajo
            m1 = valid_mask & (dst_array == 1)
            m2 = valid_mask & (dst_array == 2)
            m3 = valid_mask & (dst_array == 3)

            rgba[m1] = [239, 68, 68, 245]    # Rojo vivo
            rgba[m2] = [245, 158, 11, 230]   # Ámbar intenso
            rgba[m3] = [16, 185, 129, 210]   # Esmeralda / turquesa

        img = Image.fromarray(rgba, "RGBA")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


def get_tile_service() -> TileService:
    return TileService.get_instance()
