"""
apps/api/test_api.py
Tests unitarios y de contrato para la API de GeoAI-Au Explorer.
"""

import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Asegurar importación
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "apps"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from apps.api.main import app
from apps.api.data_loader import get_data_loader

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["cells_indexed"] == 478443
    assert data["zones_count"] == 1529
    assert data["features_loaded"] == 56


def test_project_summary_contract():
    response = client.get("/api/project/summary")
    assert response.status_code == 200
    data = response.json()["summary"]
    assert data["model_name"] == "logistic_01"
    assert data["eligible_cells_count"] == 478443
    assert data["features_count"] == 56
    assert data["prioritized_zones_count"] == 1529
    assert round(data["thresholds"]["top_01"], 4) == 0.8333
    assert round(data["thresholds"]["top_05"], 4) == 0.6526
    assert round(data["thresholds"]["top_10"], 4) == 0.5179


def test_layers_catalog():
    response = client.get("/api/layers")
    assert response.status_code == 200
    data = response.json()
    assert len(data["layers"]) >= 5
    layer_ids = [l["id"] for l in data["layers"]]
    assert "score" in layer_ids
    assert "percentile" in layer_ids
    assert "priority" in layer_ids
    assert "zones" in layer_ids
    assert "deposits" in layer_ids


def test_cell_inspection_and_nodata_boundary():
    # 1. Celda elegible conocida (Top 1): es_pen_utm30_1km_v1_r0653_c0387
    resp_top = client.get("/api/cell/es_pen_utm30_1km_v1_r0653_c0387")
    assert resp_top.status_code == 200
    data_top = resp_top.json()
    assert data_top["eligible"] is True
    assert data_top["cell"]["score"] > 0.989
    assert data_top["cell"]["prioridad_banda"] == "top_01"

    # 2. Celda por coordenadas
    lat = data_top["cell"]["lat_wgs84"]
    lon = data_top["cell"]["lon_wgs84"]
    resp_coord = client.get(f"/api/cell/by-coordinate?lat={lat}&lon={lon}")
    assert resp_coord.status_code == 200
    data_coord = resp_coord.json()
    assert data_coord["eligible"] is True
    assert data_coord["cell"]["cell_id"] == "es_pen_utm30_1km_v1_r0653_c0387"

    # 3. Coordenada en mar abierto (NoData, no elegible)
    resp_sea = client.get("/api/cell/by-coordinate?lat=43.9&lon=-4.0") # Mar Cantábrico
    assert resp_sea.status_code == 200
    data_sea = resp_sea.json()
    assert data_sea["eligible"] is False
    assert data_sea["cell"] is None


def test_explain_additive_consistency():
    # Celda elegible
    resp = client.get("/api/cell/es_pen_utm30_1km_v1_r0653_c0387/explain")
    assert resp.status_code == 200
    data = resp.json()["explanation"]

    assert data["consistency_test_passed"] is True
    assert data["consistency_error"] < 1e-6
    assert abs(data["logit_calculated"] - data["logit_decision_function"]) < 1e-6
    assert abs(data["prospectivity_score"] - data["sigmoid_score"]) < 1e-4
    assert len(data["top_positive_contributions"]) > 0
    assert len(data["all_contributions"]) == 56


def test_targets_ranking_and_contract():
    resp = client.get("/api/targets?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 1529
    assert len(data["zones"]) == 10
    top1_zone = data["zones"][0]
    assert top1_zone["ranking_nacional"] == 1
    assert "zona_priorizacion_1425" in top1_zone["zona_id"]
    assert top1_zone["categoria_prioridad"] == "prioridad_muy_alta_top01"
    assert top1_zone["anotacion_post_hoc"] != ""

    # Ficha monográfica
    resp_single = client.get("/api/targets/zona_priorizacion_1425")
    assert resp_single.status_code == 200
    assert resp_single.json()["zona_id"] == "zona_priorizacion_1425"


def test_validation_holdout_contract():
    resp = client.get("/api/validation/summary")
    assert resp.status_code == 200
    summary = resp.json()["summary"]
    assert summary["holdout_cells"] == 13541
    assert summary["observed_P_cells"] == 19
    assert summary["observed_deposits"] == 8
    assert summary["districts_count"] == 5
    assert summary["deposit_recovery_at_01"] == 0.125
    assert summary["deposit_recovery_at_05"] == 0.125
    assert summary["deposit_recovery_at_10"] == 0.250
    assert round(summary["roc_auc_PU"], 4) == 0.5807

    # 8 depósitos
    resp_deps = client.get("/api/validation/deposits")
    assert resp_deps.status_code == 200
    assert len(resp_deps.json()["deposits"]) == 8

    # 5 distritos
    resp_dists = client.get("/api/validation/districts")
    assert resp_dists.status_code == 200
    assert len(resp_dists.json()["districts"]) == 5


def test_model_coefficients():
    resp = client.get("/api/model/coefficients")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_id"] == "logistic_01"
    assert data["total_variables"] == 56
    assert len(data["coefficients"]) == 56
    # Mayor coeficiente positivo: edades_u023
    top_var = data["coefficients"][0]
    assert "edades_u023" in top_var["variable"]
    assert round(top_var["coeficiente_estandarizado"], 4) == 0.5962


def test_tiles_endpoint():
    for layer in ["score", "percentile", "priority"]:
        resp = client.get(f"/api/tiles/{layer}/6/31/24.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert len(resp.content) > 500


def test_deposits_geojson():
    resp = client.get("/api/deposits")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 46


def test_copilot_deterministic():
    # Consulta 1: Por qué score alto
    resp1 = client.post(
        "/api/copilot/query",
        json={"query": "¿Por qué esta celda tiene score alto?", "context": {"cell_id": "es_pen_utm30_1km_v1_r0653_c0387"}}
    )
    assert resp1.status_code == 200
    assert "Explicación Aditiva" in resp1.json()["answer_markdown"]

    # Consulta 2: Holdout
    resp2 = client.post("/api/copilot/query", json={"query": "¿Qué ocurrió en el holdout?"})
    assert resp2.status_code == 200
    assert "Brecha de Transferencia" in resp2.json()["answer_markdown"]


def test_absence_of_forbidden_words_in_schemas():
    """Garantiza que ningún endpoint devuelve campos prohibidos (probability_of_gold, etc.)."""
    openapi = client.get("/api/openapi.json").json()
    openapi_str = str(openapi).lower()
    assert "probability_of_gold" not in openapi_str
    assert "probabilidad_de_oro" not in openapi_str
    assert "probabilidad_deposito" not in openapi_str
