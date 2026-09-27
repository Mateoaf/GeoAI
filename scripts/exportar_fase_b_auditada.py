#!/usr/bin/env python3
"""Exportador canónico de Fase B con auditoría completa de indicios de oro (Paso 3B).

Ejecuta el flujo completo de Fase B:
- Carga Fase A y el GPKG canónico de BDMIN.
- Aplica data/review/revision_au_fase_b.csv (790 registros auditados).
- Ejecuta geometry_qc, group_candidates, define_labels y coverage_at_points.
- Exporta productos vectoriales y tabulares a reports/fase_b/<timestamp>.
- Actualiza y sella control_cierre.json con estado 'completada'.
"""
from pathlib import Path
import json
import yaml
import pandas as pd
import geopandas as gpd

from geoau.local_sources import local_path, sha256_file, verify_unchanged
from geoau.labels import (load_phase_a, normalize_indicios, apply_reviews,
                         geometry_qc, group_candidates, define_labels,
                         coverage_at_points, export_phase_b)

def run_export():
    ROOT = Path(__file__).resolve().parents[1]
    with open(ROOT / 'config/labels.yaml', encoding='utf-8') as f:
        CONFIG = yaml.safe_load(f)

    A_RUN, MANIFEST_A, CONFIG_A, originales = load_phase_a(ROOT, CONFIG)
    fingerprint = [s['sha256'] for s in MANIFEST_A['sources'] if s['path'] == CONFIG_A['canonical_candidates']['indicios']][0]
    CONFIG['source_sha256'] = fingerprint

    normalizados = normalize_indicios(originales, CONFIG)

    extra_inputs = []
    review_path = local_path(ROOT, CONFIG['review_file'])
    extra_inputs.append({
        'role': 'review_file',
        'path': str(review_path.relative_to(ROOT)),
        'sha256': sha256_file(review_path)
    })
    revision = pd.read_csv(review_path, dtype='string', keep_default_na=False, encoding='utf-8-sig')

    normalizados, decisiones = apply_reviews(normalizados, revision)
    qc = geometry_qc(normalizados, CONFIG)
    candidatos = qc[qc.au_observado].copy()
    agrupados, pares, sensibilidad = group_candidates(candidatos, CONFIG['cluster_radii_m'])
    etiquetas = define_labels(agrupados)

    raster_aliases = {
        alias: local_path(ROOT, name)
        for alias, name in CONFIG_A['canonical_candidates'].items()
        if alias.startswith('geoquimica_') or alias == 'relieve'
    }
    cobertura = coverage_at_points(etiquetas, raster_aliases)

    RUN_DIR, control = export_phase_b(
        ROOT, CONFIG, A_RUN, MANIFEST_A, qc, etiquetas,
        decisiones, pares, sensibilidad, cobertura, extra_inputs=extra_inputs
    )

    changes = verify_unchanged(ROOT, MANIFEST_A['sources'], rehash=True)
    extra_changes = [r['path'] for r in extra_inputs if sha256_file(local_path(ROOT, r['path'])) != r['sha256']]
    control['fuentes_modificadas'] = changes
    control['entradas_adicionales_modificadas'] = extra_changes
    control['estado_ejecucion'] = 'completada' if not changes and not extra_changes else 'error_integridad'

    # Guardar control_cierre final sellado
    control_path = RUN_DIR / 'control_cierre.json'
    with open(control_path, 'w', encoding='utf-8') as f:
        json.dump(control, f, indent=2, ensure_ascii=False)

    print(f"Exportación de Fase B completada en: {RUN_DIR}")
    print(f"Control de cierre guardado en: {control_path}")
    print(f"  Positivos revisados: {control['positivos_revisados']}")
    print(f"  Depósitos con ID revisado: {control['depositos_con_id_revisado']}")
    print(f"  Estado ejecución: {control['estado_ejecucion']}")
    print(f"  Fase B científica cerrada: {control['fase_b_cientifica_cerrada']}")

    return RUN_DIR, control

if __name__ == '__main__':
    run_export()
