"""
Cliente oficial de altimetría y morfometría del terreno (Copernicus DEM / Open-Meteo Elevation API).
Extrae elevación observada y calcula pendiente, TPI y rugosidad TRI sin fallbacks sintéticos.
Implementa caché persistente en disco (copernicus_dem_cache.json) y manejo de cuotas/límites de API.
"""
import os
import json
import math
import time
import requests
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ELEVATION_API_URL = "https://api.open-meteo.com/v1/elevation"
DEFAULT_HEADERS = {"User-Agent": "GeoAI-Geoscience-Research/2.0"}
CACHE_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "interim" / "copernicus_dem_cache.json"

_DEM_CACHE = {}
_CACHE_LOADED = False

def _load_cache():
    global _DEM_CACHE, _CACHE_LOADED
    if not _CACHE_LOADED:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    _DEM_CACHE = json.load(f)
                logger.info(f"Caché DEM cargada: {len(_DEM_CACHE)} puntos previos.")
            except Exception as e:
                logger.warning(f"Error al leer caché DEM en {CACHE_FILE}: {e}")
        _CACHE_LOADED = True

def _save_cache():
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_DEM_CACHE, f)
    except Exception as e:
        logger.warning(f"Error al guardar caché DEM: {e}")

def query_elevation_batch(coords: list, timeout: int = 10, max_retries: int = 2) -> list:
    """
    Consulta elevaciones para una lista de tuplas [(lat, lng), ...].
    Utiliza caché local persistente y realiza peticiones REST en bloques.
    Si la API remota agota su cuota o devuelve 429 diario, retorna np.nan de forma controlada.
    """
    if not coords:
        return []
        
    _load_cache()
    
    results = [None] * len(coords)
    missing_indices = []
    missing_coords = []
    
    for i, (lat, lng) in enumerate(coords):
        key = f"{lat:.5f},{lng:.5f}"
        if key in _DEM_CACHE:
            results[i] = _DEM_CACHE[key]
        else:
            missing_indices.append(i)
            missing_coords.append((lat, lng))
            
    if not missing_coords:
        return results
        
    chunk_size = 90
    newly_cached = False
    daily_quota_exceeded = False
    
    for c_idx in range(0, len(missing_coords), chunk_size):
        if daily_quota_exceeded:
            for orig_i in missing_indices[c_idx:c_idx + chunk_size]:
                results[orig_i] = np.nan
            continue
            
        chunk_coords = missing_coords[c_idx:c_idx + chunk_size]
        chunk_orig_indices = missing_indices[c_idx:c_idx + chunk_size]
        
        lats_str = ",".join(f"{c[0]:.5f}" for c in chunk_coords)
        lngs_str = ",".join(f"{c[1]:.5f}" for c in chunk_coords)
        url = f"{ELEVATION_API_URL}?latitude={lats_str}&longitude={lngs_str}"
        
        elevs_chunk = [np.nan] * len(chunk_coords)
        
        for attempt in range(max_retries):
            try:
                r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
                if r.status_code == 200:
                    data = r.json()
                    raw_elevs = data.get('elevation', [])
                    if len(raw_elevs) == len(chunk_coords):
                        elevs_chunk = [float(v) if v is not None else np.nan for v in raw_elevs]
                        break
                elif r.status_code == 429:
                    err_msg = str(r.json().get('reason', ''))
                    if "Daily" in err_msg or "daily" in err_msg:
                        logger.warning(f"Límite diario de Open-Meteo alcanzado: {err_msg}. Registrando NODATA controlado.")
                        daily_quota_exceeded = True
                        break
                    else:
                        time.sleep(2.0)
                else:
                    time.sleep(1.0)
            except Exception as e:
                time.sleep(1.0)
                
        for orig_i, (lat, lng), val in zip(chunk_orig_indices, chunk_coords, elevs_chunk):
            results[orig_i] = val
            key = f"{lat:.5f},{lng:.5f}"
            if not np.isnan(val):
                _DEM_CACHE[key] = val
                newly_cached = True
                
        time.sleep(0.1)
        
    if newly_cached:
        _save_cache()
        
    return results

def derive_terrain_morphometry_batch(coords: list) -> list:
    """
    Calcula la morfometría del terreno observada (elevación, pendiente, TPI 1km, TRI) para una lista de coordenadas.
    Para cada coordenada consulta una cruz de 5 puntos (centro, norte, sur, este, oeste).
    """
    if not coords:
        return []
        
    d_lat = 0.005  # ~550 m
    d_lng = 0.006  # ~500 m
    
    query_points = []
    for lat, lng in coords:
        query_points.extend([
            (lat, lng),              # 0: centro
            (lat + d_lat, lng),      # 1: norte
            (lat - d_lat, lng),      # 2: sur
            (lat, lng + d_lng),      # 3: este
            (lat, lng - d_lng)       # 4: oeste
        ])
        
    all_elevations = query_elevation_batch(query_points)
    
    morphometry_results = []
    for i in range(len(coords)):
        sub_elevs = all_elevations[i * 5:(i + 1) * 5]
        
        if len(sub_elevs) == 5 and all(v is not None and not np.isnan(v) for v in sub_elevs):
            z_center, z_north, z_south, z_east, z_west = sub_elevs
            
            dz_dx = (z_east - z_west) / 1000.0
            dz_dy = (z_north - z_south) / 1100.0
            slope_deg = math.degrees(math.atan(math.hypot(dz_dx, dz_dy)))
            mean_neighbors = (z_north + z_south + z_east + z_west) / 4.0
            tpi_1km = z_center - mean_neighbors
            tri_roughness = float(np.std([z_center, z_north, z_south, z_east, z_west]))
            
            morphometry_results.append({
                "elevation_m": round(z_center, 1),
                "slope_deg": round(slope_deg, 2),
                "tpi_1km": round(tpi_1km, 2),
                "tri_roughness": round(tri_roughness, 2),
                "dem_qa_status": "OBSERVED_COPERNICUS_DEM"
            })
        else:
            z_center = sub_elevs[0] if (sub_elevs and sub_elevs[0] is not None and not np.isnan(sub_elevs[0])) else np.nan
            morphometry_results.append({
                "elevation_m": z_center,
                "slope_deg": np.nan,
                "tpi_1km": np.nan,
                "tri_roughness": np.nan,
                "dem_qa_status": "NODATA_API_LIMIT" if np.isnan(z_center) else "OBSERVED_POINT_ONLY"
            })
            
    return morphometry_results

def query_elevation_at_point(lat: float, lng: float, timeout: int = 8) -> float:
    """Consulta puntual simple."""
    res = query_elevation_batch([(lat, lng)], timeout=timeout)
    return res[0] if res else np.nan

def derive_terrain_morphometry(lat: float, lng: float, base_elev: float = None) -> dict:
    """Derivada puntual simple."""
    res = derive_terrain_morphometry_batch([(lat, lng)])
    return res[0] if res else {
        "elevation_m": np.nan, "slope_deg": np.nan, "tpi_1km": np.nan,
        "tri_roughness": np.nan, "dem_qa_status": "NODATA_ERROR"
    }
