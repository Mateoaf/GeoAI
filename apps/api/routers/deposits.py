"""
apps/api/routers/deposits.py
Rutas para servir capas vectoriales de depósitos, indicios BDMIN, distritos metalogénicos
y herramientas de análisis espacial por radio (buffer).
"""

import math
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..data_loader import get_data_loader

router = APIRouter(tags=["Mineral Deposits & Occurrences"])

@router.get("/api/deposits")
def get_deposits_geojson():
    """Retorna los 46 depósitos canónicos confirmados en Fase B."""
    loader = get_data_loader()
    return JSONResponse(content=loader.depositos_geojson)

@router.get("/api/indicios")
def get_indicios_geojson(tipo_au: Optional[str] = Query(None, description="Filtro por tipo: 'roca', 'aluvial' o None para todos")):
    """Retorna los 787 indicios y minas históricas de la BDMIN."""
    loader = get_data_loader()
    raw = loader.indicios_geojson
    if not tipo_au or tipo_au.lower() in ("todos", "all"):
        return JSONResponse(content=raw)

    tipo_filter = tipo_au.lower().strip()
    features = [
        f for f in raw.get("features", [])
        if f.get("properties", {}).get("tipo_au", "").lower() == tipo_filter
    ]
    return JSONResponse(content={"type": "FeatureCollection", "features": features})

@router.get("/api/districts")
def get_districts_geojson():
    """Retorna los 32 distritos metalogénicos peninsulares con centroides y datos geológicos."""
    loader = get_data_loader()
    return JSONResponse(content=loader.distritos_geojson)

@router.get("/api/spatial/buffer-analysis")
def get_buffer_analysis(
    lat: float = Query(..., description="Latitud WGS84"),
    lon: float = Query(..., description="Longitud WGS84"),
    radius_km: float = Query(10.0, ge=1.0, le=50.0, description="Radio de análisis en km (1 a 50)")
):
    """
    Análisis espacial instantáneo en radio de prospección:
    - Indicios BDMIN dentro del radio (con distancias y tipologías)
    - Distrito metalogénico más cercano
    - Estadísticas de favorabilidad del modelo GeoAI (score máx, score medio, celdas)
    """
    loader = get_data_loader()
    x0, y0 = loader.proj_to_25830.transform(lon, lat)
    radius_m = radius_km * 1000.0

    # 1. Indicios dentro del radio
    indicios_in_r = []
    for f in loader.indicios_geojson.get("features", []):
        coords = f.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue
        ix, iy = loader.proj_to_25830.transform(coords[0], coords[1])
        d_m = math.hypot(ix - x0, iy - y0)
        if d_m <= radius_m:
            props = f.get("properties", {})
            indicios_in_r.append({
                "record_id": props.get("record_id"),
                "nombre_mina": props.get("nombre_mina"),
                "provincia": props.get("provincia"),
                "municipio": props.get("municipio"),
                "tipo_au": props.get("tipo_au"),
                "morfologia": props.get("morfologia"),
                "distance_km": round(d_m / 1000.0, 2),
                "lon": coords[0],
                "lat": coords[1]
            })

    indicios_in_r.sort(key=lambda x: x["distance_km"])

    # 2. Distrito más cercano
    nearest_dist = None
    min_dist_distrito = float("inf")
    for f in loader.distritos_geojson.get("features", []):
        coords = f.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue
        dx, dy = loader.proj_to_25830.transform(coords[0], coords[1])
        d_m = math.hypot(dx - x0, dy - y0)
        if d_m < min_dist_distrito:
            min_dist_distrito = d_m
            nearest_dist = {
                "district_id": f.get("properties", {}).get("district_id"),
                "nombre": f.get("properties", {}).get("nombre"),
                "distance_km": round(d_m / 1000.0, 2)
            }

    # 3. Celdas dentro del radio
    scores_in_r = []
    r_cells = int(math.ceil(radius_m / loader.resolution_m))
    center_cell = loader.coordinate_to_cell_id(lat, lon)
    if center_cell and center_cell in loader.cell_lookup:
        c_info = loader.cell_lookup[center_cell]
        c_row, c_col = c_info["row"], c_info["col"]
        for dr in range(-r_cells, r_cells + 1):
            for dc in range(-r_cells, r_cells + 1):
                tgt_cell_id = f"es_pen_utm30_1km_v1_r{c_row + dr:04d}_c{c_col + dc:04d}"
                tgt_info = loader.cell_lookup.get(tgt_cell_id)
                if tgt_info:
                    d_m = math.hypot(tgt_info["x_epsg25830"] - x0, tgt_info["y_epsg25830"] - y0)
                    if d_m <= radius_m:
                        scores_in_r.append(tgt_info["score"])

    max_score = round(max(scores_in_r), 4) if scores_in_r else 0.0
    mean_score = round(sum(scores_in_r) / len(scores_in_r), 4) if scores_in_r else 0.0

    # Clasificación del radio
    if max_score >= 0.833:
        tier = "Muy Alta (Top 1% Nacional)"
    elif max_score >= 0.653:
        tier = "Alta (Top 5% Nacional)"
    elif max_score >= 0.518:
        tier = "Moderada-Alta (Top 10% Nacional)"
    else:
        tier = "Fondo Territorial"

    return JSONResponse(content={
        "center": {
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "x_epsg25830": round(x0, 1),
            "y_epsg25830": round(y0, 1)
        },
        "radius_km": radius_km,
        "indicios_count": len(indicios_in_r),
        "indicios_roca": sum(1 for i in indicios_in_r if i["tipo_au"] == "roca"),
        "indicios_aluvial": sum(1 for i in indicios_in_r if i["tipo_au"] == "aluvial"),
        "indicios": indicios_in_r[:20],
        "nearest_district": nearest_dist,
        "max_score": max_score,
        "mean_score": mean_score,
        "cells_analyzed": len(scores_in_r),
        "prospectivity_tier": tier
    })
