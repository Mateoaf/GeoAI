"""
apps/api/test_api.py
Tests unitarios y de contrato para la API de GeoAI-Au Explorer.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Asegurar importación
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "apps"))
sys.path.insert(0, str(REPO_ROOT / "src"))

# pyrefly: ignore [missing-import]
from apps.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["cells_indexed"] == 478443
    assert data["zones_count"] == 1529
    assert data["features_loaded"] in (56, 64)


def test_project_summary_contract():
    response = client.get("/api/project/summary")
    assert response.status_code == 200
    data = response.json()["summary"]
    assert data["model_name"] in ("logistic_01", "GeoAI_64_Predictores")
    assert data["eligible_cells_count"] == 478443
    assert data["features_count"] in (56, 64)
    assert data["prioritized_zones_count"] == 1529
    assert data["thresholds"]["top_01"] > 0
    assert data["thresholds"]["top_05"] > 0
    assert data["thresholds"]["top_10"] > 0


def test_layers_catalog():
    response = client.get("/api/layers")
    assert response.status_code == 200
    data = response.json()
    assert len(data["layers"]) >= 5
    layer_ids = [layer["id"] for layer in data["layers"]]
    assert "score" in layer_ids
    assert "percentile" in layer_ids
    assert "priority" in layer_ids
    assert "zones" in layer_ids
    assert "deposits" in layer_ids


def test_cell_inspection_and_nodata_boundary():
    # 1. Celda elegible conocida: es_pen_utm30_1km_v1_r0653_c0387
    resp_top = client.get("/api/cell/es_pen_utm30_1km_v1_r0653_c0387")
    assert resp_top.status_code == 200
    data_top = resp_top.json()
    assert data_top["eligible"] is True
    assert 0.0 <= data_top["cell"]["score"] <= 1.0

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
    assert data["consistency_error"] < 1e-4
    assert abs(data["logit_calculated"] - data["logit_decision_function"]) < 1e-4
    assert 0.0 <= data["prospectivity_score"] <= 1.0
    assert 0.0 <= data["sigmoid_score"] <= 1.0
    assert len(data["top_positive_contributions"]) > 0
    assert len(data["all_contributions"]) in (56, 64)


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
    assert summary["observed_P_cells"] in (19, 664)
    assert summary["observed_deposits"] in (8, 45)
    assert summary["districts_count"] in (5, 32)
    assert summary["roc_auc_PU"] > 0.5

    # 8 depósitos
    resp_deps = client.get("/api/validation/deposits")
    assert resp_deps.status_code == 200
    assert len(resp_deps.json()["deposits"]) == 8

    # 5 distritos
    resp_dists = client.get("/api/validation/districts")
    assert resp_dists.status_code == 200
    assert len(resp_dists.json()["districts"]) == 5

    # Comparación OOF vs Holdout
    resp_comp = client.get("/api/validation/comparison")
    assert resp_comp.status_code == 200
    assert len(resp_comp.json()["comparison"]) == 6


def test_model_coefficients():
    resp = client.get("/api/model/coefficients")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_id"] in ("logistic_01", "GeoAI_64_Predictores")
    assert data["total_variables"] in (56, 64)
    assert len(data["coefficients"]) in (56, 64)
    top_var = data["coefficients"][0]
    assert "variable" in top_var
    assert abs(top_var["coeficiente_estandarizado"]) > 0


def test_tiles_endpoint():
    for layer in ["score", "percentile", "priority", "global_v2_score", "rock_score", "alluvial_score"]:
        resp = client.get(f"/api/tiles/{layer}/6/31/24.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert resp.content.startswith(b"\x89PNG\r\n\x1a\n")
        assert len(resp.content) >= 300


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


def test_calibration_is_monotone_and_bounded():
    import numpy as np

    from apps.api import calibration

    grid = np.linspace(0.0, 1.0, 5001)
    out = calibration.calibrate(grid)
    assert np.all(np.diff(out) >= 0), "La calibración debe preservar el orden"
    assert np.all((out >= 0.0) & (out <= 1.0))
    if calibration.is_active():
        # La calibración corrige la subestimación sistemática del score bruto en validación espacial
        assert calibration.calibrate(0.4) > 0.4


def test_calibrated_scores_preserve_ranking_and_thresholds():
    from apps.api.data_loader import get_data_loader

    loader = get_data_loader()
    cells = list(loader.cell_lookup.values())[::97]  # muestra determinista (~5k celdas)
    by_score = sorted(cells, key=lambda c: c["score"])
    pcts = [c["percentile_favorabilidad"] for c in by_score]
    # El percentil (calculado sobre el score bruto) no puede decrecer al subir el score calibrado
    assert all(b >= a - 0.011 for a, b in zip(pcts, pcts[1:]))
    assert all(0.0 <= c["score"] <= 1.0 for c in cells)
    assert all(c["favorabilidad_pu_media"] == pytest.approx(c["score"], abs=1e-4) for c in cells)

    th = client.get("/api/project/summary").json()["summary"]["thresholds"]
    assert 0 < th["top_10"] < th["top_05"] < th["top_01"] <= 1.0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

