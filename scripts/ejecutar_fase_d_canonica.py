#!/usr/bin/env python3
"""Ejecución canónica de Fase D vinculando la nueva Fase C y Fase B auditadas.

Flujo de ejecución:
- Carga config/features.yaml con phase_c_run = reports/fase_c/20260927T112017_665153Z.
- Inicia la ejecución D con start_run().
- Copia y verifica los bloques predictivos precalculados (geología, terreno,
  geoquímica, estructuras, hidrología) desde la ejecución base.
- Ejecuta assemble() que procesa las etiquetas de la nueva Fase C, generando:
    - relacion_indicios_celda.parquet (190 positivos revisados)
    - relacion_deposit_id_celda.parquet (46 depósitos)
    - relacion_district_id_celda.parquet (32 distritos)
    - etiquetas_por_celda.parquet
    - Grid_Master_Au.parquet
- Sella la ejecución con outputs_manifest.json y control_cierre.json.
"""
from pathlib import Path
import shutil
import yaml
import pandas as pd
from geoau.features import start_run, assemble, read_json, sha256_file, verify_records

def run_phase_d():
    ROOT = Path(__file__).resolve().parents[1]
    cfg_path = ROOT / 'config/features.yaml'
    cfg = yaml.safe_load(cfg_path.read_text(encoding='utf-8'))
    print(f"Iniciando Fase D con phase_c_run = {cfg['phase_c_run']}...")

    # 1. Iniciar ejecución D
    out = start_run(ROOT, verify_phase_c_sha256=False)
    print(f"Directorio de ejecución D creado: {out.relative_to(ROOT)}")

    # 2. Reutilizar bloques predictivos verificados desde la ejecución anterior
    previous = ROOT / 'reports/fase_d/20260926T212039_928615Z'
    blocks = ['geology', 'terrain', 'geochemistry', 'structural', 'hydrology']
    print(f"Copiando y verificando bloques predictivos desde {previous.name}...")
    for b in blocks:
        manifest_p = previous / 'blocks' / f'{b}_manifest.json'
        entries = read_json(manifest_p)
        # Verificar entradas en el origen
        verify_records(previous, entries)
        for item in entries:
            dst = out / item['path']
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(previous / item['path'], dst)
        shutil.copy2(manifest_p, out / 'blocks' / manifest_p.name)
        # Verificar integridad en el destino
        verify_records(out, entries)
        print(f"  Bloque {b}: verificado y transferido con éxito.")

    # 3. Ensamblar matriz, integrar etiquetas revisadas de C y sellar
    print("Ejecutando assemble() para integrar etiquetas revisadas y construir Grid_Master_Au...")
    x, q, y = assemble(ROOT, out)

    # 4. Verificaciones de integridad sobre los productos de D
    print("\n--- Verificaciones de Integridad de Fase D ---")
    rel_indicios = pd.read_parquet(out / 'relacion_indicios_celda.parquet')
    n_rev = int(rel_indicios['elegible_general_revisada'].sum())
    print(f"Positivos revisados en relacion_indicios_celda: {n_rev} (esperado: 190)")
    assert n_rev == 190, f"Error: esperados 190 positivos revisados, encontrados {n_rev}"

    rel_dep = pd.read_parquet(out / 'relacion_deposit_id_celda.parquet')
    n_dep = rel_dep['deposit_id'].nunique()
    print(f"Depósitos únicos en relacion_deposit_id_celda: {n_dep} (esperado: 46)")
    assert n_dep == 46, f"Error: esperados 46 depósitos, encontrados {n_dep}"

    rel_dist = pd.read_parquet(out / 'relacion_district_id_celda.parquet')
    n_dist = rel_dist['district_id'].nunique()
    print(f"Distritos únicos en relacion_district_id_celda: {n_dist} (esperado: 32)")
    assert n_dist == 32, f"Error: esperados 32 distritos, encontrados {n_dist}"

    etiquetas = pd.read_parquet(out / 'etiquetas_por_celda.parquet')
    n_p_celdas = int((etiquetas['n_positivos_revisados'] > 0).sum())
    print(f"Celdas con positivos revisados en etiquetas_por_celda: {n_p_celdas} (esperado: 137)")
    assert n_p_celdas == 137, f"Error: esperadas 137 celdas con positivos, encontradas {n_p_celdas}"

    control = read_json(out / 'control_cierre.json')
    print(f"Estado de control_cierre Fase D: {control['estado_ejecucion']}")
    print(f"outputs_manifest.json sellado con {len(read_json(out / 'outputs_manifest.json'))} archivos.")

    return out, control

if __name__ == '__main__':
    run_phase_d()
