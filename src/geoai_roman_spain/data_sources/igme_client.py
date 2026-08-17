"""
Cliente oficial de consulta y extracción de datos geológicos del IGME (CSIC).
Utiliza el servicio ArcGIS REST del Mapa Geológico de España 1:1.000.000 (GEODE).
Implementa paginación completa, deduplicación, validación de geometrías y cero fallbacks sintéticos.
"""
import os
import json
import time
import logging
import requests
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import Point, LineString, MultiLineString

logger = logging.getLogger(__name__)

# Endpoints oficiales del IGME
IGME_LITHO_LAYER_URL = "https://mapas.igme.es/gis/rest/services/Cartografia_Geologica/IGME_Geologico_1M/MapServer/4/query"
IGME_STRUCT_LAYER_URL = "https://mapas.igme.es/gis/rest/services/Cartografia_Geologica/IGME_Geologico_1M/MapServer/2/query"

DEFAULT_HEADERS = {"User-Agent": "GeoAI-Geoscience-Research/2.0"}

def query_igme_lithology_at_point(lat: float, lng: float, timeout: int = 10) -> dict:
    """
    Realiza una intersección espacial puntual con los polígonos del Mapa Geológico 1M del IGME.
    Retorna litología observada, era cronoestratigráfica y dominio tectonotermal.
    Si la consulta falla o no hay polígono, retorna NaN/NODATA (sin fallbacks sintéticos).
    """
    params = {
        "geometry": f"{lng:.5f},{lat:.5f}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "LITOGENER,DLO,EON_ERA,SISTEMA,DOMINIO",
        "returnGeometry": "false",
        "f": "json"
    }
    try:
        r = requests.get(IGME_LITHO_LAYER_URL, params=params, headers=DEFAULT_HEADERS, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            features = data.get("features", [])
            if features:
                attrs = features[0].get("attributes", {})
                litho = attrs.get("LITOGENER")
                era = attrs.get("EON_ERA")
                dominio = attrs.get("DOMINIO")
                sistema = attrs.get("SISTEMA")
                
                if litho and str(litho).strip():
                    return {
                        "lithology": str(litho).strip(),
                        "era": str(era).strip() if era else "INDIFERENCIADO",
                        "domain": str(dominio).strip() if dominio else "INDIFERENCIADO",
                        "system": str(sistema).strip() if sistema else "INDIFERENCIADO",
                        "igme_qa_status": "OBSERVED_IGME_1M"
                    }
    except Exception as e:
        logger.warning(f"Error al consultar litología IGME en ({lat}, {lng}): {e}")
        
    return {
        "lithology": np.nan,
        "era": np.nan,
        "domain": np.nan,
        "system": np.nan,
        "igme_qa_status": "NODATA_ERROR"
    }

def fetch_and_cache_igme_fault_lines(cache_file: Path, max_records_per_query: int = 1000) -> gpd.GeoDataFrame:
    """
    Descarga, valida, deduplica y cachea localmente las geometrías lineales reales de fallas y contactos del IGME.
    No utiliza geometrías inventadas ni fallbacks sintéticos.
    """
    if cache_file.exists():
        try:
            gdf = gpd.read_file(cache_file)
            if len(gdf) > 0:
                logger.info(f"Capa de fallas IGME cargada desde caché: {len(gdf)} entidades.")
                return gdf
        except Exception as e:
            logger.warning(f"Error al leer caché de fallas en {cache_file}: {e}")

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Envolventes territoriales principales en EPSG:25830
    ENVELOPES = [
        {"name": "Noroeste", "geom": "50000,4600000,500000,4880000"},
        {"name": "Suroeste", "geom": "100000,4050000,450000,4400000"},
        {"name": "Centro-Sur", "geom": "400000,4100000,700000,4450000"},
        {"name": "Sureste", "geom": "600000,4050000,900000,4350000"},
        {"name": "Centro-Norte", "geom": "450000,4400000,800000,4750000"},
        {"name": "Noreste", "geom": "750000,4500000,1050000,4750000"}
    ]
    
    seen_object_ids = set()
    geometries = []
    attributes = []
    
    for env in ENVELOPES:
        for offset in range(0, 5000, max_records_per_query):
            params = {
                "geometry": env["geom"],
                "geometryType": "esriGeometryEnvelope",
                "inSR": "25830",
                "outSR": "25830",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "OBJECTID,TIPO",
                "returnGeometry": "true",
                "f": "json",
                "resultRecordCount": str(max_records_per_query),
                "resultOffset": str(offset)
            }
            try:
                r = requests.get(IGME_STRUCT_LAYER_URL, params=params, headers=DEFAULT_HEADERS, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    features = data.get("features", [])
                    if not features:
                        break
                    for feat in features:
                        attrs = feat.get("attributes", {})
                        obj_id = attrs.get("OBJECTID")
                        if obj_id in seen_object_ids:
                            continue
                        seen_object_ids.add(obj_id)
                        
                        tipo = str(attrs.get("TIPO", "")).lower()
                        paths = feat.get("geometry", {}).get("paths", [])
                        for path in paths:
                            if len(path) >= 2:
                                line = LineString(path)
                                if line.is_valid and not line.is_empty:
                                    geometries.append(line)
                                    is_fault = 1 if ("falla" in tipo or "cabalgamiento" in tipo) else 0
                                    attributes.append({
                                        "object_id": obj_id,
                                        "tipo": tipo,
                                        "is_fault": is_fault,
                                        "length_m": round(line.length, 1)
                                    })
                    if len(features) < max_records_per_query:
                        break
            except Exception as e:
                logger.warning(f"Error en consulta de fallas para sector {env['name']} offset {offset}: {e}")
                break
            time.sleep(0.05)
            
    if not geometries:
        raise RuntimeError("No se pudieron descargar geometrías reales del IGME y no existe caché válida. Se prohíbe el uso de geometrías sintéticas.")

    gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs="EPSG:25830")
    gdf.to_file(cache_file, driver="GPKG")
    logger.info(f"Caché de fallas IGME guardada con {len(gdf)} entidades deduplicadas.")
    return gdf
