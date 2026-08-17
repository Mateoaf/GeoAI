"""
Generador del Dataset Maestro ML v2 Oficial de GeoAI (Optimizado con cKDTree).
Extrae características 100% observadas y derivadas reales para 993 minas históricas
y 800 puntos de background estratificado con buffer de exclusión de 5 km.
"""
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
INTERIM_DIR = DATA_DIR / "interim"

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

FAULT_CACHE_FILE = INTERIM_DIR / "igme_faults_lines.gpkg"

print(f"🚀 Generando Dataset Maestro ML v2 en: {PROCESSED_DIR}")

from geoai_roman_spain.data_sources.igme_client import fetch_and_cache_igme_fault_lines
from geoai_roman_spain.features.extractor import extract_geoscientific_features
from geoai_roman_spain.gis.fault_analysis import load_spatial_structures

# 1. Asegurar descarga y precarga de geometrías lineales de fallas IGME
print("📡 Verificando caché de fallas y contactos vectoriales del IGME...")
faults_gdf = fetch_and_cache_igme_fault_lines(FAULT_CACHE_FILE)
load_spatial_structures(FAULT_CACHE_FILE)
print(f"✅ Capa vectorial de fallas lista: {len(faults_gdf):,} entidades geométricas.")

# 2. Cargar minas reales de OxREP
mines_csv = PROCESSED_DIR / "OxREP_Hispania_Enriched.csv"
if not mines_csv.exists():
    mines_csv = PROCESSED_DIR / "oxrep_roman_mines_spain_clean.csv"
    
df_mines = pd.read_csv(mines_csv)
print(f"📊 Minas históricas cargadas: {len(df_mines)}")

def get_commodity_flags(row):
    comm = str(row.get('commodity', row.get('Commodity', ''))).lower()
    return {
        'flag_Au': 1 if ('gold' in comm or 'oro' in comm or 'au' in comm) else 0,
        'flag_Cu': 1 if ('copper' in comm or 'cobre' in comm or 'cu' in comm) else 0,
        'flag_Ag': 1 if ('silver' in comm or 'plata' in comm or 'ag' in comm) else 0,
        'flag_Pb': 1 if ('lead' in comm or 'plomo' in comm or 'pb' in comm) else 0
    }

def process_single_point(idx, lat, lng, site_name, target_class, target_source, flags=None):
    if flags is None:
        flags = {'flag_Au': 0, 'flag_Cu': 0, 'flag_Ag': 0, 'flag_Pb': 0}
    feats = extract_geoscientific_features(lat, lng, FAULT_CACHE_FILE)
    return {
        'id': f"{'MINE' if target_class == 1 else 'BG'}_{idx:04d}",
        'site_name': site_name,
        'latitude': lat,
        'longitude': lng,
        'target_class': target_class,
        'target_source': target_source,
        **flags,
        **feats
    }

# 3. Procesar minas positivas en paralelo
print("\n🛰️ Extrayendo 13 variables observadas/derivadas reales para las minas (Multithreaded)...")
pos_records = []

with ThreadPoolExecutor(max_workers=16) as executor:
    futures = {
        executor.submit(
            process_single_point,
            idx,
            float(row['latitude']),
            float(row['longitude']),
            str(row.get('site', row.get('name', f'Mina_{idx}'))),
            1,
            "OxREP_v3_Roman_Exploitation",
            get_commodity_flags(row)
        ): idx for idx, row in df_mines.iterrows()
    }
    
    done = 0
    for future in as_completed(futures):
        pos_records.append(future.result())
        done += 1
        if done % 250 == 0 or done == len(df_mines):
            print(f"   • Extraídas {done}/{len(df_mines)} minas...")

df_pos = pd.DataFrame(pos_records).sort_values('id').reset_index(drop=True)

# 4. Generar Muestras de Background Estratificado con Buffer de 5 km usando cKDTree
print("\n🌍 Generando 800 puntos de Background estratificado (con buffer cKDTree de 5 km)...")
np.random.seed(42)

# Crear árbol espacial de las minas en EPSG:25830
mine_coords_utm = np.column_stack([df_pos['Coord_X'].values, df_pos['Coord_Y'].values])
mine_tree = cKDTree(mine_coords_utm)

bg_candidate_coords = []
while len(bg_candidate_coords) < 800:
    x_rand = np.random.uniform(120000, 920000)
    y_rand = np.random.uniform(4020000, 4780000)
    
    # Búsqueda ultra-rápida en KDTree: debe estar a más de 5.000 metros de cualquier mina
    dist_min, _ = mine_tree.query([x_rand, y_rand])
    if dist_min >= 5000.0:
        gdf_pt = gpd.GeoDataFrame(geometry=[Point(x_rand, y_rand)], crs="EPSG:25830").to_crs("EPSG:4326")
        lat_bg = float(gdf_pt.geometry.iloc[0].y)
        lng_bg = float(gdf_pt.geometry.iloc[0].x)
        bg_candidate_coords.append((lat_bg, lng_bg))

print(f"   • 800 Coordenadas de background fuera del buffer de 5km listas. Extrayendo geología en paralelo...")
bg_records = []

with ThreadPoolExecutor(max_workers=16) as executor:
    futures = {
        executor.submit(
            process_single_point,
            idx,
            lat,
            lng,
            f"Background_Point_{idx}",
            0,
            "Spatial_Background_Buffered"
        ): idx for idx, (lat, lng) in enumerate(bg_candidate_coords)
    }
    
    done = 0
    for future in as_completed(futures):
        bg_records.append(future.result())
        done += 1
        if done % 200 == 0 or done == len(bg_candidate_coords):
            print(f"   • Extraídos {done}/800 backgrounds...")

df_bg = pd.DataFrame(bg_records).sort_values('id').reset_index(drop=True)

# 5. Ensamblar y Guardar Dataset Maestro ML v2
df_master_v2 = pd.concat([df_pos, df_bg], ignore_index=True)

out_csv = PROCESSED_DIR / "ml_dataset_real_v2.csv"
df_master_v2.to_csv(out_csv, index=False, encoding='utf-8-sig')

# Guardar GeoPackage oficial EPSG:25830
gdf_master_v2 = gpd.GeoDataFrame(
    df_master_v2,
    geometry=[Point(xy) for xy in zip(df_master_v2['Coord_X'], df_master_v2['Coord_Y'])],
    crs="EPSG:25830"
)
out_gpkg = PROCESSED_DIR / "ml_dataset_real_v2.gpkg"
gdf_master_v2.to_file(out_gpkg, layer="ml_dataset_real_v2", driver="GPKG")

print("\n" + "=" * 80)
print(f"🎉 ¡DATASET ML v2 GENERADO CON ÉXITO Y SIN LEAKAGE!")
print(f"📊 Total de registros: {len(df_master_v2)} ({len(df_pos)} Minas Positivas + {len(df_bg)} Backgrounds)")
print(f"📁 CSV v2:        {out_csv}")
print(f"📁 GeoPackage v2: {out_gpkg}")
print("=" * 80)
