"""
Extractor Unificado de Características Geocientíficas (Feature Extraction Pipeline).
Garantiza paridad 100% idéntica entre la creación de datasets de entrenamiento
y la inferencia en tiempo real para cualquier punto de España.
"""
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from ..data_sources.igme_client import query_igme_lithology_at_point
from ..data_sources.dem_client import derive_terrain_morphometry
from ..gis.fault_analysis import compute_structural_features

# Ruta por defecto a la caché de fallas IGME
DEFAULT_FAULT_CACHE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "interim" / "igme_faults_lines.gpkg"

def extract_geoscientific_features(lat: float, lng: float, fault_cache: Path = None) -> dict:
    """
    Extrae el vector completo de 13 características observadas y derivadas reales para una coordenada:
    - 4 variables de relieve DEM (elevación, pendiente, TPI, TRI).
    - 4 variables estructurales IGME (distancia a fallas, distancia a contactos, densidad 5km, densidad 2.5km).
    - 2 coordenadas métricas EPSG:25830 (Coord_X, Coord_Y).
    - 3 atributos geológicos oficiales IGME (litología, era, dominio).
    """
    if fault_cache is None:
        fault_cache = DEFAULT_FAULT_CACHE
        
    # 1. Proyección métrica oficial EPSG:25830
    pt_wgs84 = gpd.GeoDataFrame(geometry=[Point(lng, lat)], crs="EPSG:4326")
    pt_utm = pt_wgs84.to_crs("EPSG:25830")
    coord_x = float(pt_utm.geometry.iloc[0].x)
    coord_y = float(pt_utm.geometry.iloc[0].y)
    
    # 2. Litología y Estratigrafía Oficial del IGME (ArcGIS REST)
    litho_data = query_igme_lithology_at_point(lat, lng)
    
    # 3. Topografía y Geomorfología Real (Copernicus DEM 30m)
    dem_data = derive_terrain_morphometry(lat, lng)
    
    # 4. Análisis Estructural y Tectónico Real (Líneas vectoriales IGME)
    struct_data = compute_structural_features(coord_x, coord_y, fault_cache)
    
    return {
        "Real_Elevation_MDT_m": dem_data["elevation_m"],
        "Real_Slope_Deg": dem_data["slope_deg"],
        "Real_TPI_1km": dem_data["tpi_1km"],
        "Real_TRI_Roughness": dem_data["tri_roughness"],
        "Real_IGME_Dist_Fault_m": struct_data["dist_fault_m"],
        "Real_IGME_Dist_Contact_m": struct_data["dist_contact_m"],
        "Real_IGME_Fault_Density_5km": struct_data["fault_density_5km"],
        "Real_IGME_Fault_Density_2_5km": struct_data["fault_density_2_5km"],
        "Coord_X": coord_x,
        "Coord_Y": coord_y,
        "Real_IGME_Lithology_General": litho_data["lithology"],
        "Real_IGME_Era": litho_data["era"],
        "Real_IGME_Dominio": litho_data["domain"]
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
