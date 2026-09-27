"""
scripts/verify_dashboard_sources.py
Verificación rigurosa de integridad criptográfica y procedencia de fuentes científicas para GeoAI-Au Explorer.
Comprueba que los run IDs canónicos y los hashes SHA-256 de los artefactos científicos coinciden exactamente
con los manifiestos sellados del experimento GeoAI-Au v1.0.
"""

import sys
import os
import json
import hashlib
from pathlib import Path

# Raíz del repositorio
REPO_ROOT = Path(__file__).resolve().parent.parent

# 1. Definición de ejecuciones canónicas esperadas
CANONICAL_RUNS = {
    "fase_d": "reports/fase_d/20260927T135413_959884Z",
    "fase_e": "reports/fase_e/20260927T135620_576911Z",
    "fase_f": "reports/fase_f/20260927T135750_819061Z",
    "fase_g": "reports/fase_g/20260927T141408_460613Z",
    "fase_h": "reports/fase_h/20260927T142549_961719Z",
}

# 2. Artefactos científicos críticos y sus firmas SHA-256 canónicas selladas
SEALED_HASHES = {
    # Fase D (Soporte territorial y diccionario de predictores)
    "reports/fase_d/20260927T135413_959884Z/feature_allowlist.json": "abd445b251af9553e3f9b2235976d68ab40c7f39be88061ac0e63ec4970f1b4a",
    "reports/fase_d/20260927T135413_959884Z/feature_dictionary.csv": "5a2fa0d98dec301302f9591103abf5b2060e295fd14fec4485d384e36440e142",
    "reports/fase_d/20260927T135413_959884Z/grid_spec.json": "f6cf5258049d5a9b50a859d071db4963deefd93d48aa6fb0b29e277e9164197d",
    "reports/fase_d/20260927T135413_959884Z/calidad_y_soporte.parquet": "c32def065d170aa308cf6f3bb7c20d3f265b9478b2a7589956cd0a8f29fc7a0e",
    "reports/fase_d/20260927T135413_959884Z/relacion_deposit_id_celda.parquet": "65c7ef4c80d2d41bb4710b4c712bc5f91e374ae400efcd01c019d630ab15b7fd",
    "reports/fase_d/20260927T135413_959884Z/relacion_district_id_celda.parquet": "d5e4c626abdc1a7f39b5e174a51bc6d8c08ffa69d3a2e4a267052b4044a79c38",
    "reports/fase_d/20260927T135413_959884Z/relacion_indicios_celda.parquet": "45192ef076ab1f2ac38b27482a61eef58e5c9d236e3a97c524c37939b77c4819",

    # Fase F (Modelo serializado final)
    "reports/fase_f/20260927T135750_819061Z/final_model/final_validated_model.joblib": "b65c3574c3992210bff99888a3c3c4206e41e25e0d9340c952119f7b31491723",
    "reports/fase_f/20260927T135750_819061Z/final_model/final_validated_model.json": "331fc21fdebcd9662d8ec313a685a5c86484159f09bf348a1e7b7f320a6a4cee",

    # Fase G (Métricas del holdout ciego)
    "reports/fase_g/20260927T141408_460613Z/metrics/holdout_overall_metrics.json": "c14a8c2903039ecff7e61328f4e6fd353d753b74a8459a91a7969620b690507e",
    "reports/fase_g/20260927T141408_460613Z/metrics/holdout_by_deposit.csv": "94e6b582eb52b8b049ea9c12749c1384515283f62e70c4b74da7a242594aacca",
    "reports/fase_g/20260927T141408_460613Z/metrics/holdout_by_district.csv": "746724bad9642dd40753cbb54dd1634a7991221cab84dd96c807ed0686a204f5",
    "reports/fase_g/20260927T141408_460613Z/metrics/development_vs_holdout_comparison.csv": "b7a2910ffe7728bac8e78314bddb8676b0968809ac49ba9ffd58467afc2b4d89",
    "reports/fase_g/20260927T141408_460613Z/metrics/bootstrap_deposit_uncertainty.json": "5718bcfadc252ca41b50da3eb4e3ae284ea418fa7f713d5ea6b93c086f688c75",

    # Fase H (Cartografía nacional, targets e interpretabilidad)
    "reports/fase_h/20260927T142549_961719Z/control_cierre.json": "2add5133bfff556886563ba7b00b9a806df0648c8b4470e0658bdcc249345eed",
    "reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_favorabilidad_score.tif": "bf5d9f77b63ef728901513967e52bcaa5f3c2d3a18ca4aa46fad7c298bd51a22",
    "reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_favorabilidad_percentil.tif": "8ca249fd628d5803b15a8a71a6a460b535aa5aa24b0b7ed360fee1ee8231c4fe",
    "reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_bandas_prioritarias.tif": "5421652eec4071918c3f0eb352f1c781fec8d9fdd1f280bbfac7ffcc4f914c3d",
    "reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_prospectividad.geoparquet": "cee41a38004bfb44db72ef42d1479fe5fe7268cba0b42c9d6a38e8845271b984",
    "reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_prospectividad.gpkg": "443427a953a135dbfe2ff1c0d4522625c11ca676104f6161fe4b84b88237f8e9",
    "reports/fase_h/20260927T142549_961719Z/targets/zonas_prospectividad_ranking.csv": "a20970fd8e34c7ab828991611a31c5e5f8ab00834f314a1cee17ba9c350b3efc",
    "reports/fase_h/20260927T142549_961719Z/interpretability/coeficientes_estandarizados.csv": "3b96632f4055065173db972d03024bd6b350743b55a1ca0375d6242ac5bacbf9",
    "reports/fase_h/20260927T142549_961719Z/interpretability/contribuciones_locales_casos_estudio.csv": "393ec6cecb568e7e67ee0182fd65e6a8aa3b0614e1a5fad97c6d843b7d0065dd",

    # Inventarios de depósitos y distritos auditados
    "data/review/revision_au_fase_b.csv": "fd8b7826cec0b853b217e988b58a9c321cdfcb63750929c766906bb115f6a4f5",
    "data/review/inventario_distritos_metalogeneticos.csv": "942333173f54f6db836c35af5b3343822ec3183cba0b0ee55a548ea52d9896ff",
}


def compute_sha256(file_path: Path) -> str:
    """Calcula el hash SHA-256 de un fichero binario en streaming."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_canonical_runs() -> bool:
    """Verifica que current_run.json en cada fase apunte a la ejecución canónica esperada."""
    print("=" * 70)
    print("1. VERIFICACIÓN DE RUN IDs CANÓNICOS")
    print("=" * 70)
    all_ok = True
    for phase, expected_rel_path in CANONICAL_RUNS.items():
        current_run_file = REPO_ROOT / "reports" / phase / "current_run.json"
        if not current_run_file.exists():
            print(f"[ERROR] Falta archivo current_run.json para {phase}: {current_run_file}")
            all_ok = False
            continue
        try:
            with open(current_run_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            actual_run = data.get("run", "")
            # Normalizar separadores
            actual_run_norm = actual_run.replace("\\", "/")
            expected_norm = expected_rel_path.replace("\\", "/")
            if actual_run_norm == expected_norm:
                print(f"[OK] {phase.upper()}: {actual_run_norm}")
            else:
                print(f"[ERROR] {phase.upper()} run canónico discrepante:")
                print(f"       Esperado: {expected_norm}")
                print(f"       Actual:   {actual_run_norm}")
                all_ok = False
        except Exception as e:
            print(f"[ERROR] No se pudo leer {current_run_file}: {e}")
            all_ok = False
    return all_ok


def verify_sealed_hashes() -> bool:
    """Verifica la existencia y firma SHA-256 de todos los artefactos científicos."""
    print("\n" + "=" * 70)
    print("2. VERIFICACIÓN CRIPTOGRÁFICA DE ARTEFACTOS SELLADOS (SHA-256)")
    print("=" * 70)
    all_ok = True
    for rel_path, expected_hash in SEALED_HASHES.items():
        abs_path = REPO_ROOT / rel_path
        if not abs_path.exists():
            print(f"[ERROR] Artefacto ausente: {rel_path}")
            all_ok = False
            continue
        actual_hash = compute_sha256(abs_path)
        if actual_hash == expected_hash:
            print(f"[OK] {rel_path}\n     SHA-256: {actual_hash[:16]}...")
        else:
            print(f"[ERROR] Hash alterado en {rel_path}!")
            print(f"        Esperado: {expected_hash}")
            print(f"        Actual:   {actual_hash}")
            all_ok = False
    return all_ok


def main():
    print("Iniciando auditoría estricta de fuentes de datos para GeoAI-Au Explorer...\n")
    runs_ok = verify_canonical_runs()
    hashes_ok = verify_sealed_hashes()

    print("\n" + "=" * 70)
    print("RESUMEN DE AUDITORÍA")
    print("=" * 70)
    if runs_ok and hashes_ok:
        print("[ÉXITO] Todos los run IDs canónicos y artefactos científicos sellados están intactos.")
        print("        GeoAI-Au v1.0 es inmutable y seguro para ser consumido en el dashboard web.")
        sys.exit(0)
    else:
        print("[FALLO CRÍTICO] Se detectaron discrepancias en las fuentes científicas.")
        print("                Revise los errores indicados arriba antes de continuar.")
        sys.exit(1)


if __name__ == "__main__":
    main()
