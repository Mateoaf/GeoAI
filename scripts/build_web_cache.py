"""
scripts/build_web_cache.py
Generación de artefactos optimizados para web en apps/api/data_cache/.
IMPORTANTE: Estos ficheros son DERIVADOS estrictamente de solo lectura y alto rendimiento web.
No son artefactos científicos canónicos; se generan de forma reproducible a partir de B, D y H.
"""

import os
import json
import time
from pathlib import Path
import pandas as pd
import geopandas as gpd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "apps" / "api" / "data_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def build_features_cache():
    print("1. Generando caché de 56 características aprobadas...")
    t0 = time.time()
    
    # 1. Cargar allowlist de 56 predictores
    allowlist_path = REPO_ROOT / "reports/fase_d/20260927T135413_959884Z/feature_allowlist.json"
    with open(allowlist_path, "r", encoding="utf-8") as f:
        approved_cols = json.load(f)["approved_training_columns"]
        
    # 2. Cargar celdas elegibles
    soporte_path = REPO_ROOT / "reports/fase_d/20260927T135413_959884Z/calidad_y_soporte.parquet"
    df_soporte = pq.read_table(soporte_path, columns=["cell_id", "eligible_approved_features"]).to_pandas()
    eligible_cell_ids = set(df_soporte.loc[df_soporte["eligible_approved_features"], "cell_id"])
    assert len(eligible_cell_ids) == 478443, f"Esperadas 478.443 celdas elegibles, obtenidas {len(eligible_cell_ids)}"
    
    # 3. Leer X_features solo con las 56 columnas
    features_path = REPO_ROOT / "reports/fase_d/20260927T135413_959884Z/X_features.parquet"
    table_features = pq.read_table(features_path, columns=["cell_id"] + approved_cols)
    df_features = table_features.to_pandas()
    
    # Filtrar solo celdas elegibles
    df_features_eligible = df_features[df_features["cell_id"].isin(eligible_cell_ids)].copy()
    assert len(df_features_eligible) == 478443
    
    # Guardar en data_cache
    out_parquet = CACHE_DIR / "features_approved_56.parquet"
    df_features_eligible.to_parquet(out_parquet, index=False, compression="snappy")
    t1 = time.time()
    print(f"   -> {out_parquet.name} ({out_parquet.stat().st_size / 1e6:.1f} MB) generado en {t1 - t0:.2f} s.")


def build_zonas_geojson():
    print("2. Generando GeoJSON WGS84 de las 1.529 zonas de prospectividad...")
    t0 = time.time()
    gpkg_path = REPO_ROOT / "reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_prospectividad.gpkg"
    gdf_zonas = gpd.read_file(gpkg_path, layer="zonas_prospectividad")
    assert len(gdf_zonas) == 1529, f"Esperadas 1.529 zonas, obtenidas {len(gdf_zonas)}"
    
    # Reproyectar a EPSG:4326 (WGS84) para MapLibre
    gdf_zonas_4326 = gdf_zonas.to_crs(epsg=4326)
    
    out_geojson = CACHE_DIR / "zonas_prospectividad_4326.geojson"
    gdf_zonas_4326.to_file(out_geojson, driver="GeoJSON")
    t1 = time.time()
    print(f"   -> {out_geojson.name} ({out_geojson.stat().st_size / 1e6:.1f} MB) generado en {t1 - t0:.2f} s.")


def build_depositos_geojson():
    print("3. Generando GeoJSON WGS84 de los 46 depósitos minerales confirmados...")
    t0 = time.time()
    fase_b_path = REPO_ROOT / "data/review/revision_au_fase_b.csv"
    df_b = pd.read_csv(fase_b_path)
    
    # Filtrar ocurrencias confirmadas (190)
    confirmed = df_b[df_b["estado_presencia"] == "confirmada"].copy()
    confirmed["final_lon"] = confirmed["lon_corregida"].fillna(confirmed["lon"])
    confirmed["final_lat"] = confirmed["lat_corregida"].fillna(confirmed["lat"])
    
    # Agrupar a nivel de depósito
    dep_summary = confirmed.groupby(["deposit_id", "district_id"]).agg(
        nombre_mina=("Nombre_mina", lambda s: ", ".join(sorted(set(str(x) for x in s if pd.notna(x)))[:3])),
        provincia=("Provincia", lambda s: list(s)[0] if len(s)>0 else ""),
        municipio=("Municipio", lambda s: list(s)[0] if len(s)>0 else ""),
        records_count=("record_id", "count"),
        lon=("final_lon", "mean"),
        lat=("final_lat", "mean"),
        tipo_au=("tipo_au_revisado", lambda s: list(set(s))[0] if len(set(s)) == 1 else "mixto")
    ).reset_index()
    
    assert len(dep_summary) == 46, f"Esperados 46 depósitos, obtenidos {len(dep_summary)}"
    
    gdf_deps = gpd.GeoDataFrame(
        dep_summary,
        geometry=gpd.points_from_xy(dep_summary["lon"], dep_summary["lat"]),
        crs="EPSG:4326"
    )
    
    out_geojson = CACHE_DIR / "depositos_confirmados_4326.geojson"
    gdf_deps.to_file(out_geojson, driver="GeoJSON")
    t1 = time.time()
    print(f"   -> {out_geojson.name} ({out_geojson.stat().st_size / 1e3:.1f} KB) generado en {t1 - t0:.2f} s.")


def build_manifest_cache():
    print("4. Guardando manifiesto de artefactos de caché web...")
    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "Web performance optimization for GeoAI-Au Explorer (FastAPI + MapLibre)",
        "canonical_sources": {
            "fase_d": "reports/fase_d/20260927T135413_959884Z",
            "fase_h": "reports/fase_h/20260927T142549_961719Z",
            "fase_b": "data/review/revision_au_fase_b.csv"
        },
        "artifacts": [
            "features_approved_56.parquet",
            "zonas_prospectividad_4326.geojson",
            "depositos_confirmados_4326.geojson"
        ]
    }
    with open(CACHE_DIR / "cache_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("   -> cache_manifest.json generado.")


def main():
    print("=" * 60)
    print("INICIANDO GENERACIÓN DE ARTEFACTOS WEB DERIVADOS")
    print("=" * 60)
    build_features_cache()
    build_zonas_geojson()
    build_depositos_geojson()
    build_manifest_cache()
    print("=" * 60)
    print("GENERACIÓN DE CACHÉ WEB COMPLETADA EXITOSAMENTE")
    print("=" * 60)

build_all_cache = main

if __name__ == "__main__":
    main()
