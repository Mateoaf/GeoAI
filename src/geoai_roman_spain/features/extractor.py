"""
Extractor Unificado de Características Geocientíficas (Feature Extraction Pipeline v2.0).
Garantiza paridad 100% idéntica entre la creación de datasets de entrenamiento,
validación espacial e inferencia puntual y en malla para toda la Península Ibérica.
"""
from pathlib import Path
import logging
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

from ..data_sources.igme_client import query_igme_lithology_at_point
from ..data_sources.dem_client import derive_terrain_morphometry
from ..gis.fault_analysis import compute_structural_features

logger = logging.getLogger(__name__)

DEFAULT_FAULT_CACHE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "interim" / "igme_faults_lines.gpkg"

# Polígono estricto del dominio continental ibérico (tierra firme)
IBERIA_DOMAIN_POLY_WGS84 = Polygon([
    (-9.40, 43.85), (-8.00, 44.00), (-4.50, 43.60), (-1.80, 43.45),
    (3.35, 42.45), (3.20, 41.80), (0.75, 40.50), (0.20, 38.70),
    (-0.50, 38.00), (-1.80, 37.40), (-2.20, 36.70), (-3.70, 36.65),
    (-5.60, 35.95), (-6.50, 36.60), (-7.50, 37.15), (-8.90, 37.00),
    (-9.50, 38.75), (-9.00, 42.00), (-9.40, 43.85)
])

def is_point_in_iberian_domain(lat: float, lng: float) -> bool:
    """Verifica si una coordenada WGS84 cae estrictamente dentro de la tierra continental ibérica."""
    pt = Point(lng, lat)
    return IBERIA_DOMAIN_POLY_WGS84.contains(pt)

def to_utm30n(lat: float, lng: float) -> tuple:
    """Convierte coordenadas geográficas WGS84 (lat, lng) a métricas proyectadas EPSG:25830 (UTM 30N)."""
    pt_wgs84 = gpd.GeoDataFrame(geometry=[Point(lng, lat)], crs="EPSG:4326")
    pt_utm = pt_wgs84.to_crs("EPSG:25830")
    return float(pt_utm.geometry.iloc[0].x), float(pt_utm.geometry.iloc[0].y)

def extract_geoscientific_features(lat: float, lng: float, fault_cache: Path = None) -> dict:
    """
    Extrae el vector estricto de características observadas y derivadas reales para una coordenada:
    - 4 variables de relieve DEM (elevación, pendiente, TPI 1km, TRI rugosidad).
    - 3 variables estructurales IGME (distancia geométrica a fallas, distancia a contactos, densidad de longitud km/km2).
    - 2 coordenadas métricas EPSG:25830 (Coord_X, Coord_Y) - Solo para indexación espacial.
    - 3 atributos geológicos oficiales IGME (litología, era, dominio).
    - 2 estados QA de disponibilidad de datos.
    - 1 indicador booleano de dominio continental (in_domain).
    """
    if fault_cache is None:
        fault_cache = DEFAULT_FAULT_CACHE
        
    in_domain = is_point_in_iberian_domain(lat, lng)
    coord_x, coord_y = to_utm30n(lat, lng)
    
    # 2. Litología y Estratigrafía Oficial del IGME (ArcGIS REST)
    litho_data = query_igme_lithology_at_point(lat, lng)
    
    # 3. Topografía y Geomorfología Observada (Copernicus DEM)
    dem_data = derive_terrain_morphometry(lat, lng)
    
    # 4. Análisis Estructural y Tectónico Real (Líneas vectoriales IGME vía STRtree)
    struct_data = compute_structural_features(coord_x, coord_y, fault_cache)
    
    return {
        "Real_Elevation_MDT_m": dem_data["elevation_m"],
        "Real_Slope_Deg": dem_data["slope_deg"],
        "Real_TPI_1km": dem_data["tpi_1km"],
        "Real_TRI_Roughness": dem_data["tri_roughness"],
        "Real_IGME_Dist_Fault_m": struct_data["dist_fault_m"],
        "Real_IGME_Dist_Contact_m": struct_data["dist_contact_m"],
        "Real_IGME_Fault_Length_Density_5km": struct_data["fault_length_density_5km"],
        "Coord_X": coord_x,
        "Coord_Y": coord_y,
        "Real_IGME_Lithology_General": litho_data["lithology"],
        "Real_IGME_Era": litho_data["era"],
        "Real_IGME_Dominio": litho_data["domain"],
        "dem_qa_status": dem_data["dem_qa_status"],
        "igme_qa_status": litho_data["igme_qa_status"],
        "in_domain": in_domain
    }

def extract_features_to_dataframe(points: list, fault_cache: Path = None) -> pd.DataFrame:
    """
    Extrae características para una lista de tuplas [(lat, lng), ...] o diccionarios con 'latitude', 'longitude'.
    """
    rows = []
    for pt in points:
        if isinstance(pt, dict):
            lat, lng = pt['latitude'], pt['longitude']
        else:
            lat, lng = pt[0], pt[1]
        feat = extract_geoscientific_features(lat, lng, fault_cache)
        rows.append(feat)
    return pd.DataFrame(rows)
