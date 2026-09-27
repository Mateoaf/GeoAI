#!/usr/bin/env python3
"""Ejecución canónica de Fase C vinculando la Fase B auditada.

Ejecuta el pipeline completo de Fase C:
- Carga config/grid.yaml apuntando a reports/fase_b/20260927T105348_425399Z.
- Inicia la ejecución C con start_run().
- Carga la máscara peninsular (load_mask) y calcula áreas terrestres (land_areas).
- Crea la rejilla peninsular de 1 km (make_grid).
- Genera el diccionario de extracción (feature_dictionary).
- Alinea y agrega los rásteres geoquímicos y MDT (align_rasters).
- Armoniza vectores usando la caché verificada (harmonize_vectors).
- Deriva productos de cobertura y relaciona indicios con celdas (coverage_products).
- Sella la ejecución con finish_run().
"""
from pathlib import Path
import yaml
import pandas as pd
from geoau.territory import (
    start_run, grid_spec, load_mask, land_areas, make_grid,
    feature_dictionary, align_rasters, harmonize_vectors,
    coverage_products, finish_run
)

def run_phase_c():
    ROOT = Path(__file__).resolve().parents[1]
    cfg_path = ROOT / 'config/grid.yaml'
    config = yaml.safe_load(cfg_path.read_text(encoding='utf-8'))
    print(f"Iniciando Fase C con phase_b_run = {config['phase_b_run']}...")
    spec = grid_spec(config)

    # 1. Iniciar ejecución
    run_dir, fuentes, manifest_a, entradas_c, indicios = start_run(ROOT, config)
    print(f"Directorio de ejecución C creado: {run_dir.relative_to(ROOT)}")
    print(f"Indicios candidatos leídos de B: {len(indicios)}")

    # 2. Máscara y áreas
    print("Cargando máscara territorial...")
    mascara = load_mask(ROOT, config, run_dir)
    print("Calculando áreas terrestres a 500 m...")
    area_terrestre_500m = land_areas(mascara, spec['native_shape'], spec['native_transform'])

    # 3. Rejilla
    print("Generando rejilla de 1 km...")
    grid = make_grid(area_terrestre_500m, spec, run_dir)
    print(f"Rejilla generada con {len(grid)} celdas.")

    # 4. Diccionario de variables
    diccionario = feature_dictionary(run_dir)

    # 5. Rásteres
    print("Alineando rásteres geoquímicos y MDT...")
    fracciones_raster = align_rasters(ROOT, fuentes, area_terrestre_500m, spec, run_dir)

    # 6. Vectores (con caché verificada)
    print("Armonizando vectores...")
    fracciones_vector, control_vectores = harmonize_vectors(
        ROOT, fuentes, mascara, area_terrestre_500m, spec, run_dir
    )

    # 7. Productos de cobertura
    print("Generando productos de cobertura y relación con indicios...")
    all_fractions = {**fracciones_raster, **fracciones_vector}
    grid_cobertura, cobertura_ambitos, decisiones, indicios_celda, estados = coverage_products(
        ROOT, grid, all_fractions, indicios, mascara, spec, run_dir
    )

    # 8. Cierre y sellado
    print("Sellando ejecución de Fase C...")
    control = finish_run(ROOT, run_dir, manifest_a, entradas_c, grid_cobertura, indicios_celda, control_vectores)
    print(f"Control de cierre Fase C: {control['estado_ejecucion']}")
    print(f"Positivos revisados asignados: {control['positivos_revisados_asignados']}")
    print(f"Candidatos asignados: {control['candidatos_asignados']}")
    return run_dir, control

if __name__ == '__main__':
    run_phase_c()
