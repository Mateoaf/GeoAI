"""Paso 8: Activar protocolo validado y regenerar Fase E completa desde cero.

Ejecuta el pipeline científico de Fase E bajo mode: validated:
- selected_role == P_reviewed (cero P_candidate_proxy como positivos)
- Exclusivamente las 56 variables aprobadas en Fase D
- 5 distritos pre-registrados como reserva ciega (holdout)
- Bloques de 50 km + gap espacial de 5 km
- Verificación estricta de cuarentena del holdout (sin fit, tuning, imputación ni selección)
- Generación y auditoría de 20 particiones (5 outer, 15 inner) y 180 muestras P/U
"""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from geoau import evaluation as ev
read_json = ev.read_json


def main():
    print("=" * 80)
    print("EJECUTANDO Y AUDITANDO FASE E VALIDADA (PASO 8)")
    print("=" * 80)

    # 1. Obten o inicializa ejecucion E
    try:
        out = ev.current_run(ROOT)
        print(f"\n--- 1. Usando ejecucion E actual: {out} ---")
    except Exception as e:
        print(f"\n--- 1. Inicializando nueva ejecucion E ({e}) ---")
        out = ev.start_run(ROOT)
        print(f"Directorio de ejecucion: {out}")

    # Verificar readiness
    readiness = read_json(out / 'readiness.json')
    print(f"Readiness: ready={readiness['ready_for_scientific_training']}, selected_role={readiness['selected_role']}")
    assert readiness['ready_for_scientific_training'] is True, f"Bloqueos: {readiness['reasons']}"
    assert readiness['selected_role'] == 'P_reviewed', f"Rol erroneo: {readiness['selected_role']}"
    assert readiness['reasons'] == [], f"Razones no vacias: {readiness['reasons']}"

    # 2. Build splits
    print("\n--- 2. Verificando/generando particiones espaciales anidadas y reserva ---")
    split_summary = ev.build_splits(ROOT, out)
    print(f"Total particiones generadas: {len(split_summary)} (esperadas: 20)")
    assert len(split_summary) == 20, f"Se esperaban 20 particiones, se obtuvieron {len(split_summary)}"

    # 3. Build samples
    print("\n--- 3. Verificando/generando muestras P/U por estrato territorial ---")
    sample_summary = ev.build_samples(ROOT, out)
    print(f"Total muestras generadas: {len(sample_summary)} (esperadas: 180)")
    assert len(sample_summary) == 180, f"Se esperaban 180 muestras, se obtuvieron {len(sample_summary)}"

    # 4. Finish run
    print("\n--- 4. Verificando cierre de ejecucion E y sellado ---")
    control = ev.finish_run(ROOT, out)
    print(f"Control cierre: estado={control['estado_ejecucion']}, mode={control['mode']}, "
          f"fase_e_cerrada={control['fase_e_cientifica_cerrada']}, training_allowed={control['training_allowed']}")
    assert control['estado_ejecucion'] == 'completada'
    assert control['mode'] == 'validated'
    assert control['fase_e_cientifica_cerrada'] is True
    assert control['training_allowed'] is True

    # 5. Auditoria Exhaustiva
    print("\n" + "=" * 80)
    print("AUDITORIA DETALLADA DE LA FASE E VALIDADA")
    print("=" * 80)

    cfg, grid, relations, spec, groupmap = ev.context(ROOT, out)

    # 5.1 Verificar Positivos Revisados vs Candidatos
    selected_positives = pd.read_parquet(out / 'design/selected_positive_records.parquet')
    print(f"\n[5.1 Positivos Seleccionados en Fase E]")
    print(f"  - Registros positivos: {len(selected_positives)}")
    print(f"  - Celdas unicas positivas: {selected_positives.cell_id.nunique()}")
    print(f"  - Depositos independientes: {selected_positives.deposit_id.nunique()}")
    print(f"  - Distritos metalogeneticos: {selected_positives.district_id.nunique()}")
    print(f"  - Distribucion de protocol_role: {dict(selected_positives.protocol_role.value_counts())}")

    assert set(selected_positives.protocol_role) == {'P_reviewed'}, "HAY ROLES DISTINTOS DE P_reviewed!"
    assert not selected_positives.protocol_role.str.contains('proxy').any(), "HAY PROXIES COMO POSITIVOS!"
    assert bool(selected_positives.elegible_general_revisada.all()), "Hay registros no revisados!"

    # 5.2 Auditoria de Desarrollo vs Holdout
    units = pd.read_parquet(out / 'design/spatial_units.parquet')
    territory = grid.merge(units[['cell_id', 'block_id', 'unit_id', 'holdout', 'outer_fold']],
                           on='cell_id', validate='one_to_one')
    
    # Cruzar con positivos
    pos_cells = set(selected_positives.cell_id)
    cell_to_dep = selected_positives.groupby('cell_id')['deposit_id'].first()
    cell_to_dist = selected_positives.groupby('cell_id')['district_id'].first()
    
    territory['is_positive'] = territory.cell_id.isin(pos_cells)
    territory['deposit_id'] = territory.cell_id.map(cell_to_dep)
    territory['district_id'] = territory.cell_id.map(cell_to_dist)

    dev_mask = ~territory.holdout & territory.eligible
    hold_mask = territory.holdout & territory.eligible

    dev_cells = dev_mask.sum()
    hold_cells = hold_mask.sum()
    total_eligible = territory.eligible.sum()

    dev_pos_cells = territory.loc[dev_mask & territory.is_positive, 'cell_id'].nunique()
    hold_pos_cells = territory.loc[hold_mask & territory.is_positive, 'cell_id'].nunique()

    dev_deps = territory.loc[dev_mask & territory.is_positive, 'deposit_id'].nunique()
    hold_deps = territory.loc[hold_mask & territory.is_positive, 'deposit_id'].nunique()

    dev_dists = territory.loc[dev_mask & territory.is_positive, 'district_id'].nunique()
    hold_dists = territory.loc[hold_mask & territory.is_positive, 'district_id'].nunique()

    dev_units = territory.loc[dev_mask, 'unit_id'].nunique()
    hold_units = territory.loc[hold_mask, 'unit_id'].nunique()

    print(f"\n[5.2 Desglose Desarrollo vs Holdout (Reserva Ciega)]")
    print(f"{'Metrica':<35} | {'Desarrollo (CV)':<18} | {'Holdout (Reserva)':<18} | {'Total':<10}")
    print("-" * 88)
    print(f"{'Celdas elegibles':<35} | {dev_cells:<18} | {hold_cells:<18} | {total_eligible:<10}")
    print(f"{'% Celdas elegibles':<35} | {dev_cells/total_eligible*100:>17.2f}% | {hold_cells/total_eligible*100:>17.2f}% | {100.0:>9.2f}%")
    print(f"{'Celdas positivas revisadas':<35} | {dev_pos_cells:<18} | {hold_pos_cells:<18} | {dev_pos_cells+hold_pos_cells:<10}")
    print(f"{'% Celdas positivas':<35} | {dev_pos_cells/(dev_pos_cells+hold_pos_cells)*100:>17.2f}% | {hold_pos_cells/(dev_pos_cells+hold_pos_cells)*100:>17.2f}% | {100.0:>9.2f}%")
    print(f"{'Depositos independientes':<35} | {dev_deps:<18} | {hold_deps:<18} | {dev_deps+hold_deps:<10}")
    print(f"{'Distritos metalogeneticos':<35} | {dev_dists:<18} | {hold_dists:<18} | {dev_dists+hold_dists:<10}")
    print(f"{'Unidades conectadas (50 km)':<35} | {dev_units:<18} | {hold_units:<18} | {dev_units+hold_units:<10}")

    # Verificar solapamiento de unidades entre desarrollo y holdout
    dev_unit_set = set(territory.loc[dev_mask, 'unit_id'])
    hold_unit_set = set(territory.loc[hold_mask, 'unit_id'])
    overlap_units = dev_unit_set & hold_unit_set
    print(f"  - Solapamiento de unidades transitivas desarrollo / holdout: {len(overlap_units)} (debe ser 0)")
    assert len(overlap_units) == 0, f"Error: unidades compartidas entre desarrollo y holdout: {overlap_units}"

    # Distritos en holdout
    holdout_districts_in_groupmap = set(groupmap.loc[groupmap.cell_id.isin(territory.loc[hold_mask, 'cell_id']), 'district_id'].dropna())
    print(f"  - Distritos en territorio holdout: {holdout_districts_in_groupmap}")
    assert holdout_districts_in_groupmap == set(cfg['reserve_district_ids'])

    # 5.3 Cuarentena de la Reserva Ciega en Membresias y Muestras
    print(f"\n[5.3 Verificacion de Cuarentena Absoluta de la Reserva]")
    holdout_cells = set(territory.loc[territory.holdout, 'cell_id'])
    
    plan = read_json(out / 'split_plan.json')['splits']
    for item in plan:
        split_id = item['split_id']
        memb = pd.read_parquet(out / f'memberships/{split_id}.parquet')
        train_cells = set(memb.loc[memb.role == 'train', 'cell_id'])
        test_cells = set(memb.loc[memb.role == 'test', 'cell_id'])
        gap_cells = set(memb.loc[memb.role == 'spatial_gap', 'cell_id'])
        
        # Ninguna celda de holdout puede tener rol train, test ni gap
        assert len(train_cells & holdout_cells) == 0, f"{split_id}: Celdas de holdout en train!"
        assert len(test_cells & holdout_cells) == 0, f"{split_id}: Celdas de holdout en test!"
        
        # Todas las celdas de holdout deben tener rol holdout
        memb_holdout = set(memb.loc[memb.role == 'holdout', 'cell_id'])
        assert memb_holdout == holdout_cells, f"{split_id}: Discordancia en celdas de holdout!"

    print("  - Confirmado: CERO celdas de reserva participan en train o test en los 20 splits.")

    # Verificar en muestras P/U
    for row in sample_summary.itertuples(index=False):
        sample = pd.read_parquet(out / f'samples/{row.sample_id}.parquet')
        sample_cells = set(sample.cell_id)
        assert len(sample_cells & holdout_cells) == 0, f"{row.sample_id}: Celdas de holdout en muestra P/U!"
        assert set(sample.sample_role) == {'P_reviewed', 'U_unlabelled'}, f"{row.sample_id}: Roles invalidos!"
        assert bool(sample.training_allowed.all()), f"{row.sample_id}: training_allowed no es True!"
        assert (sample['mode'] == 'validated').all()

    print("  - Confirmado: CERO celdas de reserva participan en las 180 muestras P/U.")
    print("  - Confirmado: Todas las 180 muestras tienen sample_role in {'P_reviewed', 'U_unlabelled'} y training_allowed=True.")

    # 5.4 Auditoria de Variables Aprobadas (Fase D)
    print(f"\n[5.4 Auditoria de Variables Aprobadas (Fase D)]")
    d_dir = Path(ROOT) / cfg['phase_d_run']
    allowlist = read_json(d_dir / 'feature_allowlist.json')
    approved_cols = allowlist['approved_training_columns']
    print(f"  - Total variables aprobadas para entrenamiento: {len(approved_cols)}")
    assert len(approved_cols) == 56, f"Se esperaban 56 variables aprobadas, se encontraron {len(approved_cols)}"

    # Verificar que el contrato de aprendizaje prohibe usar holdout para seleccion o ajuste
    contract = read_json(out / 'learning_contract.json')
    print(f"\n[5.5 Contrato de Aprendizaje (learning_contract.json)]")
    print(f"  - Mode: {contract['mode']}")
    print(f"  - Reference: {contract['reference']}")
    print(f"  - Preprocessing: {contract['preprocessing']}")
    print(f"  - Holdout clause: {contract['holdout']}")
    print(f"  - Model fitting: {contract['model_fitting']}")
    assert contract['mode'] == 'validated'
    assert 'no se generan muestras para entrenar/ajustar sobre la reserva' in contract['holdout']

    # 5.6 Desglose de Folds Externos
    print(f"\n[5.6 Desglose de los 5 Folds Externos]")
    outer_summary = split_summary[split_summary.split_id.str.match(r'^outer_\d{2}$')]
    print(outer_summary[['split_id', 'train_cells', 'test_cells', 'train_p_cells', 'test_p_cells',
                         'train_p_units', 'test_p_units', 'minimum_train_test_holdout_gap_lower_bound_m']].to_string(index=False))

    # 5.7 Desglose de Folds Internos
    print(f"\n[5.7 Resumen de los 15 Folds Internos]")
    inner_summary = split_summary[split_summary.split_id.str.contains('inner')]
    print(f"  - Total splits internos: {len(inner_summary)}")
    print(f"  - Rango de test_p_units internos: {inner_summary.test_p_units.min()} - {inner_summary.test_p_units.max()}")
    print(f"  - Rango de train_p_units internos: {inner_summary.train_p_units.min()} - {inner_summary.train_p_units.max()}")
    print(f"  - Gap minimo observado en internos: {inner_summary.minimum_train_test_holdout_gap_lower_bound_m.min():.1f} m")

    print("\n" + "=" * 80)
    print("FASE E VALIDADA COMPLETADA Y AUDITADA CON EXITO")
    print(f"Run generado: {out.relative_to(ROOT)}")
    print("=" * 80)


if __name__ == '__main__':
    main()
