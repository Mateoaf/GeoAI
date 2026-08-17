"""
Módulo GIS de Análisis Estructural y Tectónico.
Calcula distancias geométricas euclidianas exactas a trazas de fallas y contactos lineales reales del IGME,
así como densidad de longitud de fracturación (km de falla / km2) mediante Shapely STRtree.
"""
import math
import logging
from pathlib import Path
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from shapely.strtree import STRtree

logger = logging.getLogger(__name__)

_FAULT_TREE = None
_FAULT_GEOMS = None
_CONTACT_TREE = None
_CONTACT_GEOMS = None
_FAULT_LINES_GDF = None

def load_spatial_structures(cache_path: Path):
    """
    Carga y construye el índice espacial R-Tree (STRtree) a partir de geometrías vectoriales lineales reales del IGME.
    Garantiza que la fuente de datos es exclusivamente la cartografía geológica oficial.
    """
    global _FAULT_TREE, _FAULT_GEOMS, _CONTACT_TREE, _CONTACT_GEOMS, _FAULT_LINES_GDF
    
    if _FAULT_TREE is not None and _FAULT_GEOMS is not None:
        return _FAULT_TREE, _FAULT_GEOMS, _CONTACT_TREE, _CONTACT_GEOMS
        
    if not cache_path.exists():
        from ..data_sources.igme_client import fetch_and_cache_igme_fault_lines
        _FAULT_LINES_GDF = fetch_and_cache_igme_fault_lines(cache_path)
    else:
        _FAULT_LINES_GDF = gpd.read_file(cache_path)
        
    if _FAULT_LINES_GDF.crs is None or _FAULT_LINES_GDF.crs.to_epsg() != 25830:
        _FAULT_LINES_GDF = _FAULT_LINES_GDF.to_crs("EPSG:25830")
        
    fault_mask = _FAULT_LINES_GDF["is_fault"] == 1
    contact_mask = _FAULT_LINES_GDF["is_fault"] == 0
    
    fault_subset = _FAULT_LINES_GDF[fault_mask]
    contact_subset = _FAULT_LINES_GDF[contact_mask]
    
    if len(fault_subset) == 0:
        fault_subset = _FAULT_LINES_GDF
        
    if len(contact_subset) == 0:
        contact_subset = _FAULT_LINES_GDF
        
    _FAULT_GEOMS = list(fault_subset.geometry.values)
    _CONTACT_GEOMS = list(contact_subset.geometry.values)
    
    _FAULT_TREE = STRtree(_FAULT_GEOMS)
    _CONTACT_TREE = STRtree(_CONTACT_GEOMS)
    
    logger.info(f"Índices espaciales STRtree listos: {len(_FAULT_GEOMS)} fallas, {len(_CONTACT_GEOMS)} contactos.")
    return _FAULT_TREE, _FAULT_GEOMS, _CONTACT_TREE, _CONTACT_GEOMS

def compute_structural_features(x_utm: float, y_utm: float, cache_path: Path) -> dict:
    """
    Calcula las variables estructurales observadas/derivadas para una coordenada proyectada en EPSG:25830:
    1. Real_IGME_Dist_Fault_m: Distancia euclidiana mínima exacta en metros a la traza de falla más cercana.
    2. Real_IGME_Dist_Contact_m: Distancia euclidiana mínima exacta en metros al contacto litológico más cercano.
    3. Real_IGME_Fault_Length_Density_5km: Densidad lineal de fallas en radio de 5 km (km de falla / km2).
       Fórmula: Longitud total de fallas intersectadas en buffer 5 km (en km) / (pi * 5^2 km2).
    """
    fault_tree, fault_geoms, contact_tree, contact_geoms = load_spatial_structures(cache_path)
    
    pt = Point(x_utm, y_utm)
    
    # 1. Distancia geométrica exacta a la falla más cercana
    nearest_fault_idx = fault_tree.nearest(pt)
    nearest_fault_geom = fault_geoms[nearest_fault_idx]
    dist_fault_m = float(nearest_fault_geom.distance(pt))
    
    # 2. Distancia geométrica exacta al contacto más cercano
    nearest_contact_idx = contact_tree.nearest(pt)
    nearest_contact_geom = contact_geoms[nearest_contact_idx]
    dist_contact_m = float(nearest_contact_geom.distance(pt))
    
    # 3. Densidad de longitud de fallas en buffer r=5000 m (área = pi * 25 km2 = 78.5398 km2)
    buffer_5km = pt.buffer(5000.0)
    candidate_indices = fault_tree.query(buffer_5km)
    
    total_length_m = 0.0
    for idx in candidate_indices:
        line = fault_geoms[idx]
        if buffer_5km.contains(line):
            total_length_m += line.length
        elif buffer_5km.intersects(line):
            inter = line.intersection(buffer_5km)
            if not inter.is_empty:
                total_length_m += inter.length
            
    buffer_area_km2 = math.pi * (5.0 ** 2)  # 78.54 km2
    fault_length_km = total_length_m / 1000.0
    fault_density_km_per_km2 = fault_length_km / buffer_area_km2
    
    return {
        "dist_fault_m": round(dist_fault_m, 1),
        "dist_contact_m": round(dist_contact_m, 1),
        "fault_length_density_5km": round(float(fault_density_km_per_km2), 4)
    }
