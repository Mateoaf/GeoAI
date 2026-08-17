"""
Generador del Dataset Maestro ML v2 Oficial de GeoAI.
Implementa muestreo de background sobre el dominio continental de la Península Ibérica,
buffer espacial de exclusión de 5 km respecto a positivos, métricas completas de QA,
extracción geométrica real de fallas IGME mediante STRtree y topografía observada Copernicus DEM.
"""
import os
import sys
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from scipy.spatial import cKDTree

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_dataset_v2")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
INTERIM_DIR = DATA_DIR / "interim"
REPORTS_DIR = PROJECT_ROOT / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
INTERIM_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

FAULT_CACHE_FILE = INTERIM_DIR / "igme_faults_lines.gpkg"

from geoai_roman_spain.data_sources.igme_client import fetch_and_cache_igme_fault_lines, query_igme_lithology_at_point
from geoai_roman_spain.data_sources.dem_client import derive_terrain_morphometry_batch
from geoai_roman_spain.gis.fault_analysis import load_spatial_structures, compute_structural_features

# ==============================================================================
# 1. DEFINICIÓN EXPLÍCITA DEL DOMINIO DE ESTUDIO (Península Ibérica Continental)
# ==============================================================================
IBERIAN_PENINSULA_COORDS = [
    (-1.80, 43.35), (-3.80, 43.48), (-5.80, 43.62), (-7.70, 43.78), (-8.40, 43.65),
    (-9.30, 43.00), (-8.90, 42.15), (-8.70, 41.15), (-9.55, 39.35), (-8.90, 38.40),
    (-9.00, 37.00), (-7.40, 37.10), (-6.45, 36.75), (-5.60, 36.00), (-4.40, 36.70),
    (-2.15, 36.70), (-0.70, 37.60), (0.20, 38.75), (0.15, 40.00), (0.90, 40.70),
    (2.20, 41.40), (3.30, 42.35), (3.10, 42.45), (0.80, 42.60), (-0.70, 42.85),
    (-1.80, 43.35)
]
IBERIA_DOMAIN_POLY_WGS84 = Polygon(IBERIAN_PENINSULA_COORDS)
gdf_domain_utm = gpd.GeoDataFrame(geometry=[IBERIA_DOMAIN_POLY_WGS84], crs="EPSG:4326").to_crs("EPSG:25830")
IBERIA_DOMAIN_POLY_UTM = gdf_domain_utm.geometry.iloc[0]

print("=" * 80, flush=True)
print("🚀 INICIANDO GENERACIÓN DEL DATASET MAESTRO ML v2 (GEODATOS 100% OBSERVADOS)", flush=True)
print(f"🌍 Dominio Territorial: Península Ibérica Continental (Hispania / España + Portugal)", flush=True)
print(f"📁 Directorio de salida: {PROCESSED_DIR}", flush=True)
print("=" * 80, flush=True)

# 2. Asegurar y precargar geometrías lineales reales de fallas IGME
print("\n📡 1/5. Verificando cartografía estructural oficial del IGME...", flush=True)
faults_gdf = fetch_and_cache_igme_fault_lines(FAULT_CACHE_FILE)
load_spatial_structures(FAULT_CACHE_FILE)
print(f"✅ Capa vectorial de fallas y contactos lista: {len(faults_gdf):,} entidades geométricas.", flush=True)

# 3. Cargar minas reales de OxREP (Evidencias de Minería Romana)
mines_csv = PROCESSED_DIR / "OxREP_Hispania_Enriched.csv"
if not mines_csv.exists():
    mines_csv = PROCESSED_DIR / "oxrep_roman_mines_spain_clean.csv"
    
df_mines = pd.read_csv(mines_csv)
print(f"📊 Minas históricas de OxREP cargadas: {len(df_mines)}", flush=True)

def parse_commodity_flags(row):
    def check_col(col_names):
        for c in col_names:
            val = row.get(c)
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str in ['1', '1.0', 'true', 'confirmado', 'hipotetico'] or 'confirmado' in val_str:
                    return 1
        return 0
    return {
        'flag_Au': check_col(['Flag_Au_Oro', 'metalMinedGold', 'Status_Au_Oro']),
        'flag_Cu': check_col(['Flag_Cu_Cobre', 'metalMinedCopper', 'Status_Cu_Cobre']),
        'flag_Ag': check_col(['Flag_Ag_Plata', 'metalMinedSilver', 'Status_Ag_Plata']),
        'flag_Pb': check_col(['Flag_Pb_Plomo', 'metalMinedLead', 'Status_Pb_Plomo'])
    }

# 4. Preparar Coordenadas y Muestreo de Fondo con QA
print("\n🌍 2/5. Muestreando 800 puntos de background estratificado sobre tierra continental...", flush=True)
np.random.seed(42)

pos_coords_wgs84 = [(float(row['latitude']), float(row['longitude'])) for _, row in df_mines.iterrows()]
gdf_pos_wgs84 = gpd.GeoDataFrame(geometry=[Point(xy[1], xy[0]) for xy in pos_coords_wgs84], crs="EPSG:4326")
gdf_pos_utm = gdf_pos_wgs84.to_crs("EPSG:25830")
pos_coords_utm = np.column_stack([gdf_pos_utm.geometry.x.values, gdf_pos_utm.geometry.y.values])

mine_tree = cKDTree(pos_coords_utm)

qa_candidates_total = 0
qa_rejected_outside_domain = 0
qa_rejected_distance_buffer = 0
bg_coords_wgs84 = []
bg_coords_utm = []

while len(bg_coords_wgs84) < 800:
    qa_candidates_total += 1
    x_rand = np.random.uniform(100000, 950000)
    y_rand = np.random.uniform(4000000, 4850000)
    pt_cand = Point(x_rand, y_rand)
    
    if not IBERIA_DOMAIN_POLY_UTM.contains(pt_cand):
        qa_rejected_outside_domain += 1
        continue
        
    dist_min, _ = mine_tree.query([x_rand, y_rand])
    if dist_min < 5000.0:
        qa_rejected_distance_buffer += 1
        continue
        
    gdf_pt = gpd.GeoDataFrame(geometry=[pt_cand], crs="EPSG:25830").to_crs("EPSG:4326")
    lat_bg = float(gdf_pt.geometry.iloc[0].y)
    lng_bg = float(gdf_pt.geometry.iloc[0].x)
    bg_coords_wgs84.append((lat_bg, lng_bg))
    bg_coords_utm.append((x_rand, y_rand))

print(f"   • QA Muestreo de Fondo:", flush=True)
print(f"     - Candidatos generados:       {qa_candidates_total:,}", flush=True)
print(f"     - Rechazados fuera de tierra: {qa_rejected_outside_domain:,}", flush=True)
print(f"     - Rechazados por buffer <5km: {qa_rejected_distance_buffer:,}", flush=True)
print(f"     - Aceptados para extracción:  {len(bg_coords_wgs84):,}", flush=True)

all_coords_wgs84 = pos_coords_wgs84 + bg_coords_wgs84
all_coords_utm = list(pos_coords_utm) + bg_coords_utm

# 5. Extracción de Morfometría DEM en Bloques de Alta Velocidad
print("\n🏔️ 3/5. Extrayendo elevación, pendiente, TPI y TRI desde Copernicus DEM...", flush=True)
dem_results = derive_terrain_morphometry_batch(all_coords_wgs84)
print(f"   • Morfometría DEM procesada: {len(dem_results)} puntos.", flush=True)

# 6. Extracción de Distancias y Densidades de Fallas IGME
print("\n📐 4/5. Calculando distancias geométricas y densidad de longitud de fallas IGME...", flush=True)
struct_results = []
for idx, (x, y) in enumerate(all_coords_utm):
    s = compute_structural_features(x, y, FAULT_CACHE_FILE)
    struct_results.append(s)
    if (idx + 1) % 500 == 0 or (idx + 1) == len(all_coords_utm):
        print(f"   • Fallas procesadas: {idx + 1}/{len(all_coords_utm)} puntos...", flush=True)

# 7. Extracción de Litología IGME en Paralelo con Caché
print("\n🏛️ 5/5. Consultando polígonos del Mapa Geológico 1M del IGME...", flush=True)
litho_cache = {}
litho_results = [None] * len(all_coords_wgs84)

def fetch_litho(idx, lat, lng):
    key = (round(lat, 4), round(lng, 4))
    if key in litho_cache:
        return idx, litho_cache[key]
    res = query_igme_lithology_at_point(lat, lng)
    litho_cache[key] = res
    return idx, res

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(fetch_litho, i, lat, lng): i for i, (lat, lng) in enumerate(all_coords_wgs84)}
    done = 0
    for future in as_completed(futures):
        i, res = future.result()
        litho_results[i] = res
        done += 1
        if done % 300 == 0 or done == len(all_coords_wgs84):
            print(f"   • Litología consultada {done}/{len(all_coords_wgs84)} puntos...", flush=True)

# 8. Ensamblar Registros Finales
records = []
n_pos = len(df_mines)

for i, (lat, lng) in enumerate(all_coords_wgs84):
    is_pos = (i < n_pos)
    x_utm, y_utm = all_coords_utm[i]
    dem = dem_results[i]
    struct = struct_results[i]
    litho = litho_results[i]
    
    if is_pos:
        row_m = df_mines.iloc[i]
        rec_id = f"MINE_{i:04d}"
        site_name = str(row_m.get('site', row_m.get('name', f'Mina_{i}')))
        target_class = 1
        target_source = "OxREP_v3_Roman_Exploitation"
        flags = parse_commodity_flags(row_m)
    else:
        bg_idx = i - n_pos
        rec_id = f"BG_{bg_idx:04d}"
        site_name = f"Background_Point_{bg_idx}"
        target_class = 0
        target_source = "Spatial_Background_Buffered"
        flags = {'flag_Au': 0, 'flag_Cu': 0, 'flag_Ag': 0, 'flag_Pb': 0}
        
    records.append({
        'id': rec_id,
        'site_name': site_name,
        'latitude': lat,
        'longitude': lng,
        'target_class': target_class,
        'target_source': target_source,
        **flags,
        'Real_Elevation_MDT_m': dem['elevation_m'],
        'Real_Slope_Deg': dem['slope_deg'],
        'Real_TPI_1km': dem['tpi_1km'],
        'Real_TRI_Roughness': dem['tri_roughness'],
        'Real_IGME_Dist_Fault_m': struct['dist_fault_m'],
        'Real_IGME_Dist_Contact_m': struct['dist_contact_m'],
        'Real_IGME_Fault_Length_Density_5km': struct['fault_length_density_5km'],
        'Coord_X': x_utm,
        'Coord_Y': y_utm,
        'Real_IGME_Lithology_General': litho['lithology'],
        'Real_IGME_Era': litho['era'],
        'Real_IGME_Dominio': litho['domain'],
        'dem_qa_status': dem['dem_qa_status'],
        'igme_qa_status': litho['igme_qa_status']
    })

df_master_v2 = pd.DataFrame(records)

# Chequeo y tratamiento documentado de NaNs
print(f"\n📊 Diagnóstico de nulos:", flush=True)
for col in df_master_v2.columns:
    n_null = df_master_v2[col].isnull().sum()
    if n_null > 0:
        print(f"   • {col}: {n_null} valores nulos detectados.", flush=True)

# Preservar NaNs en el dataset maestro oficial (sin fallbacks sintéticos en datos brutos)
# Las ausencias de datos se registran explícitamente y se dejan como NaN con su estado QA.
# Para columnas categóricas no mapeadas por el IGME se asigna 'UNMAPPED_OR_NODATA'
df_master_v2['Real_IGME_Lithology_General'] = df_master_v2['Real_IGME_Lithology_General'].fillna('UNMAPPED_OR_NODATA')
df_master_v2['Real_IGME_Era'] = df_master_v2['Real_IGME_Era'].fillna('UNMAPPED_OR_NODATA')
df_master_v2['Real_IGME_Dominio'] = df_master_v2['Real_IGME_Dominio'].fillna('UNMAPPED_OR_NODATA')

# Guardar CSV y GeoPackage
out_csv = PROCESSED_DIR / "ml_dataset_real_v2.csv"
df_master_v2.to_csv(out_csv, index=False, encoding='utf-8-sig')

gdf_master_v2 = gpd.GeoDataFrame(
    df_master_v2,
    geometry=[Point(xy) for xy in zip(df_master_v2['Coord_X'], df_master_v2['Coord_Y'])],
    crs="EPSG:25830"
)
out_gpkg = PROCESSED_DIR / "ml_dataset_real_v2.gpkg"
gdf_master_v2.to_file(out_gpkg, layer="ml_dataset_real_v2", driver="GPKG")

# Guardar Informe QA
qa_report = {
    "total_samples": len(df_master_v2),
    "positive_mines": n_pos,
    "background_samples": len(bg_coords_wgs84),
    "commodities_positives": {
        "Au_Oro": int(df_master_v2['flag_Au'].sum()),
        "Cu_Cobre": int(df_master_v2['flag_Cu'].sum()),
        "Ag_Plata": int(df_master_v2['flag_Ag'].sum()),
        "Pb_Plomo": int(df_master_v2['flag_Pb'].sum())
    },
    "sampling_qa": {
        "candidates_generated": qa_candidates_total,
        "rejected_outside_land_domain": qa_rejected_outside_domain,
        "rejected_distance_buffer_5km": qa_rejected_distance_buffer,
        "accepted_final": len(bg_coords_wgs84)
    }
}

with open(REPORTS_DIR / "dataset_v2_qa_report.json", "w", encoding="utf-8") as f:
    json.dump(qa_report, f, indent=2)

print("\n" + "=" * 80, flush=True)
print(f"🎉 ¡DATASET ML v2 GENERADO Y VERIFICADO CON ÉXITO!", flush=True)
print(f"📊 Registros totales: {len(df_master_v2)} ({n_pos} Positivos | {len(bg_coords_wgs84)} Fondo)", flush=True)
print(f"📁 CSV:  {out_csv}", flush=True)
print(f"📁 GPKG: {out_gpkg}", flush=True)
print(f"📄 QA Report: {REPORTS_DIR / 'dataset_v2_qa_report.json'}", flush=True)
print("=" * 80, flush=True)
