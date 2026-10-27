"""
Descarga y procesamiento de reflectancia de superficie satelital (MCD43A4 NBAR 500m)
para derivar indices de alteracion hidrotermal (Al-OH sericita/arcillas y Gossan oxidos de hierro)
alineados celda a celda con el cubo nacional en EPSG:25830.
"""

import os
import json
import time
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from scipy.ndimage import gaussian_filter

ROOT = Path(".")
RAW_DIR = ROOT / "data/raw/satelite_mcd43a4"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Configuracion de rejilla nacional canónica
ORIGIN_X = -50000
ORIGIN_Y = 4860000
RES = 1000
WIDTH = 1100
HEIGHT = 910
CRS = "EPSG:25830"
TARGET_TRANSFORM = from_origin(ORIGIN_X, ORIGIN_Y, RES, RES)

BANDS = {
    "Band1": "Nadir_Reflectance_Band1", # Red (645 nm)
    "Band2": "Nadir_Reflectance_Band2", # NIR (858 nm)
    "Band3": "Nadir_Reflectance_Band3", # Blue (470 nm)
    "Band6": "Nadir_Reflectance_Band6", # SWIR-1 (1640 nm)
    "Band7": "Nadir_Reflectance_Band7"  # SWIR-2 (2130 nm)
}

TILES = ["h17v04", "h17v05", "h18v04", "h18v05"]

def fetch_stac_items():
    print("Buscando teselas en Microsoft Planetary Computer STAC...")
    post_data = json.dumps({
        "collections": ["modis-43A4-061"],
        "bbox": [-9.5, 36.0, 3.3, 43.8],
        "datetime": "2023-08-08T00:00:00Z/2023-08-08T23:59:59Z",
        "limit": 10
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "https://planetarycomputer.microsoft.com/api/stac/v1/search",
        data=post_data,
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        data = json.loads(res.read())
    
    items_by_tile = {}
    for feat in data["features"]:
        tile = feat["id"].split(".")[2]
        if tile in TILES:
            items_by_tile[tile] = feat
    print(f"Teselas identificadas para Espana: {list(items_by_tile.keys())}")
    return items_by_tile

def sign_url(href):
    sign_api = f"https://planetarycomputer.microsoft.com/api/sas/v1/sign?href={href}"
    for attempt in range(5):
        try:
            time.sleep(1.2) # Respetar rate limits
            req = urllib.request.Request(sign_api, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as res:
                return json.loads(res.read())["href"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = (attempt + 1) * 3
                print(f"    [Rate limit 429] Esperando {wait_time}s antes de reintentar...")
                time.sleep(wait_time)
            else:
                raise
    raise RuntimeError(f"No se pudo firmar URL tras reintentos: {href}")

def download_tiles(items_by_tile):
    downloaded_paths = {band_key: {} for band_key in BANDS}
    for tile in TILES:
        feat = items_by_tile.get(tile)
        if not feat:
            raise RuntimeError(f"Falta tesela {tile}")
        for band_key, asset_name in BANDS.items():
            out_file = RAW_DIR / f"{tile}_{band_key}.tif"
            downloaded_paths[band_key][tile] = out_file
            if out_file.exists() and out_file.stat().st_size > 1000000:
                print(f"  [Cache] {out_file.name} ya existe ({out_file.stat().st_size/(1024*1024):.1f} MB)")
                continue
            
            href = feat["assets"][asset_name]["href"]
            signed = sign_url(href)
            print(f"  Descargando {tile} {band_key} ({asset_name})...")
            t0 = time.time()
            with urllib.request.urlopen(signed, timeout=30) as resp, open(out_file, "wb") as f:
                f.write(resp.read())
            print(f"    Listo en {time.time()-t0:.1f}s ({out_file.stat().st_size/(1024*1024):.1f} MB)")
    return downloaded_paths

def mosaic_and_reproject_band(tile_paths):
    """Reproyecta cada tesela y combina en la rejilla peninsular EPSG:25830."""
    destination = np.full((HEIGHT, WIDTH), np.nan, dtype=np.float32)
    weights = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    
    for tile, path in tile_paths.items():
        with rasterio.open(path) as src:
            src_data = src.read(1).astype(np.float32)
            # Escala MODIS MCD43A4: 0.0001; NoData = 32767
            nodata = src.nodata if src.nodata is not None else 32767
            src_data[src_data >= 32760] = np.nan
            src_data[src_data < 0] = np.nan
            src_data = src_data * 0.0001
            
            temp_dest = np.full((HEIGHT, WIDTH), np.nan, dtype=np.float32)
            reproject(
                source=src_data,
                destination=temp_dest,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=TARGET_TRANSFORM,
                dst_crs=CRS,
                resampling=Resampling.bilinear,
                src_nodata=np.nan,
                dst_nodata=np.nan
            )
            valid = ~np.isnan(temp_dest)
            # Donde ya hay datos y el nuevo es válido, promediamos
            overlap = valid & ~np.isnan(destination)
            only_new = valid & np.isnan(destination)
            destination[overlap] = (destination[overlap] * weights[overlap] + temp_dest[overlap]) / (weights[overlap] + 1)
            weights[overlap] += 1
            destination[only_new] = temp_dest[only_new]
            weights[only_new] = 1
            
    return destination

def main():
    items = fetch_stac_items()
    paths = download_tiles(items)
    
    print("\nReproyectando bandas a la rejilla nacional EPSG:25830 (1 km)...")
    mosaic_bands = {}
    for band_key, tile_dict in paths.items():
        t0 = time.time()
        print(f"  Mosaico de {band_key}...")
        mosaic_bands[band_key] = mosaic_and_reproject_band(tile_dict)
        print(f"    Completado en {time.time()-t0:.1f}s. Cobertura valida: {(~np.isnan(mosaic_bands[band_key])).mean()*100:.1f}%")
        
    b1 = mosaic_bands["Band1"] # Red
    b2 = mosaic_bands["Band2"] # NIR
    b3 = mosaic_bands["Band3"] # Blue
    b6 = mosaic_bands["Band6"] # SWIR-1
    b7 = mosaic_bands["Band7"] # SWIR-2
    
    print("\nCalculando indices espectrales de alteracion hidrotermal...")
    # 1. Ratio Al-OH / Arcillas / Sericita: SWIR-1 / SWIR-2
    ratio_swir = np.where((b6 > 0.01) & (b7 > 0.01), b6 / b7, np.nan)
    
    # 2. Ratio Gossan / Oxidos de Hierro: Red / Blue
    ratio_gossan = np.where((b1 > 0.01) & (b3 > 0.01), b1 / b3, np.nan)
    
    # 3. NDVI de cobertura vegetal
    ndvi = np.where((b2 + b1) > 0.02, (b2 - b1) / (b2 + b1), np.nan)
    
    # 4. Normalizacion local (invarianza climatica) mediante Z-score residual sobre ventana 25 km
    def local_zscore(arr, sigma_cells=25):
        valid = ~np.isnan(arr)
        clean = np.where(valid, arr, 0.0)
        norm = np.where(valid, 1.0, 0.0)
        
        smooth = gaussian_filter(clean, sigma=sigma_cells)
        weights = gaussian_filter(norm, sigma=sigma_cells)
        local_mean = np.where(weights > 0.01, smooth / weights, np.nan)
        
        diff = np.where(valid, arr - local_mean, 0.0)
        smooth_sq = gaussian_filter(diff**2, sigma=sigma_cells)
        local_std = np.where(weights > 0.01, np.sqrt(np.maximum(smooth_sq / weights, 1e-4)), np.nan)
        
        z = np.where(valid & (local_std > 1e-4), (arr - local_mean) / local_std, 0.0)
        return np.clip(z, -4.0, 4.0)

    z_swir = local_zscore(ratio_swir)
    z_gossan = local_zscore(ratio_gossan)
    z_ndvi = local_zscore(ndvi)
    
    # Indice combinado de anomalia hidrotermal espectral
    anomalia_hidrotermal = z_swir + z_gossan - 0.5 * z_ndvi
    
    # Mapeo a celdas canónicas del proyecto
    print("\nMapeando a celdas canónicas del proyecto...")
    X_raw = pd.read_parquet("reports/fase_d/20260923T211448_267684Z/X_features.parquet", columns=["cell_id"])
    cell_ids = X_raw["cell_id"].values
    
    # Parsear r y c de cell_id
    rows = np.array([int(c.split("_r")[1].split("_c")[0]) for c in cell_ids])
    cols = np.array([int(c.split("_c")[1]) for c in cell_ids])
    
    df_sat = pd.DataFrame({
        "cell_id": cell_ids,
        "ratio_alteracion_filica_swir": ratio_swir[rows, cols],
        "ratio_gossan_oxidos_hierro": ratio_gossan[rows, cols],
        "ndvi_cobertura_vegetal": ndvi[rows, cols],
        "anomalia_hidrotermal_multiespectral_zscore": anomalia_hidrotermal[rows, cols]
    })
    
    # Imputacion de celdas costeras residuales con media local si quedase algun NaN
    for col in ["ratio_alteracion_filica_swir", "ratio_gossan_oxidos_hierro", "ndvi_cobertura_vegetal"]:
        med = df_sat[col].median()
        df_sat[col] = df_sat[col].fillna(med)
    
    out_parquet = RAW_DIR / "variables_alteracion_hidrotermal.parquet"
    df_sat.to_parquet(out_parquet, index=False)
    print(f"\nVariables guardadas con exito en {out_parquet} ({len(df_sat)} celdas)")
    
    # Auditoría sobre depósitos de oro
    rot = pd.read_csv("reports/evaluacion_configuracion_nacional_20261021/rotation_deposit_predictions.csv")
    p_cells = rot["cell_id"].unique()
    
    print("\nAuditoria de contraste espectral en yacimientos de oro (P) vs Fondo Nacional:")
    is_p = df_sat["cell_id"].isin(p_cells)
    for col in ["ratio_alteracion_filica_swir", "ratio_gossan_oxidos_hierro", "ndvi_cobertura_vegetal", "anomalia_hidrotermal_multiespectral_zscore"]:
        f_med = df_sat.loc[~is_p, col].median()
        p_med = df_sat.loc[is_p, col].median()
        print(f"  {col:<42}: Fondo Median={f_med:.3f} | P Median={p_med:.3f} | Delta={p_med-f_med:+.3f}")

if __name__ == "__main__":
    main()
