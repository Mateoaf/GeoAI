"""
apps/api/routers/summary.py
Rutas de resumen del proyecto, configuración de capas y metadatos de release.
"""

from fastapi import APIRouter

from ..data_loader import get_data_loader
from ..schemas.summary import ProjectSummary, ProjectSummaryResponse, ThresholdsSummary

router = APIRouter(tags=["Project Summary"])

@router.get("/api/project/summary", response_model=ProjectSummaryResponse)
def get_project_summary():
    loader = get_data_loader()
    ctrl = loader.control_cierre

    summary = ProjectSummary(
        project_name="GeoAI-Au",
        tagline="Mineral Prospectivity Intelligence — España Peninsular",
        release_version="v1.0",
        is_scientific_release=True,
        model_name="logistic_01",
        model_family="Logistic Regression (L2 regularization, C=0.1, solver=lbfgs)",
        resolution="1 km x 1 km (100 hectáreas por celda)",
        crs="EPSG:25830 (ETRS89 / UTM huso 30N)",
        region="España peninsular",
        eligible_cells_count=int(ctrl.get("national_cells_inferred", len(loader.cell_lookup))),
        features_count=len(loader.approved_columns),
        prioritized_zones_count=int(ctrl.get("zones_prioritized_count", 1529)),
        thresholds=ThresholdsSummary(
            top_01=float(ctrl.get("threshold_score_top01", 0.833276)),
            top_05=float(ctrl.get("threshold_score_top05", 0.652645)),
            top_10=float(ctrl.get("threshold_score_top10", 0.517859)),
        ),
        run_ids={
            "fase_d": "reports/fase_d/20260927T135413_959884Z",
            "fase_e": "reports/fase_e/20260927T135620_576911Z",
            "fase_f": "reports/fase_f/20260927T135750_819061Z",
            "fase_g": "reports/fase_g/20260927T141408_460613Z",
            "fase_h": "reports/fase_h/20260927T142549_961719Z",
        }
    )
    return ProjectSummaryResponse(summary=summary)


@router.get("/api/layers")
def get_layers_catalog():
    loader = get_data_loader()
    ctrl = loader.control_cierre

    return {
        "layers": [
            {
                "id": "score",
                "name": "Prospectivity Score",
                "type": "raster",
                "tile_url": "/api/tiles/score/{z}/{x}/{y}.png",
                "description": "Score continuo relativo de favorabilidad geológica en (0, 1)",
                "default_visible": True,
                "default_opacity": 0.85,
                "colormap": "viridis",
                "range": [0.0, 1.0],
                "units": "Índice continuo (0-1)"
            },
            {
                "id": "percentile",
                "name": "Percentil Territorial Nacional",
                "type": "raster",
                "tile_url": "/api/tiles/percentile/{z}/{x}/{y}.png",
                "description": "Rango percentil territorial respecto a las 478.443 celdas modelables",
                "default_visible": False,
                "default_opacity": 0.85,
                "colormap": "plasma",
                "range": [0.0, 100.0],
                "units": "Percentil (0-100)"
            },
            {
                "id": "priority",
                "name": "Bandas de Prioridad de Exploración",
                "type": "raster",
                "tile_url": "/api/tiles/priority/{z}/{x}/{y}.png",
                "description": "Categorías operativas de priorización: Top 1%, Top 1-5%, Top 5-10%",
                "default_visible": False,
                "default_opacity": 0.90,
                "classes": [
                    {"label": "Top 1% (Muy Alta)", "threshold": f">= {ctrl.get('threshold_score_top01', 0.8333):.4f}", "color": "#E63946"},
                    {"label": "Top 1-5% (Alta)", "threshold": f">= {ctrl.get('threshold_score_top05', 0.6526):.4f}", "color": "#F4A261"},
                    {"label": "Top 5-10% (Moderada)", "threshold": f">= {ctrl.get('threshold_score_top10', 0.5179):.4f}", "color": "#2A9D8F"},
                    {"label": "Fondo / Resto", "threshold": "< 0.5179", "color": "#4A5568"}
                ]
            },
            {
                "id": "zones",
                "name": "Zonas de Prospectividad (Polígonos)",
                "type": "vector",
                "data_url": "/api/targets/geojson",
                "description": "1.529 clusters espaciales delimitados en Top 1% y Top 5%",
                "default_visible": True,
                "default_opacity": 0.75,
                "outline_color": "#F39C12"
            },
            {
                "id": "deposits",
                "name": "Depósitos Históricos Auditados (Fase B)",
                "type": "vector_points",
                "data_url": "/api/deposits",
                "description": "46 depósitos auríferos independientes confirmados (190 indicios BDMIN)",
                "default_visible": True,
                "default_opacity": 1.0,
                "marker_color": "#FFD700"
            }
        ]
    }
