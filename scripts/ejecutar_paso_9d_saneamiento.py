#!/usr/bin/env python3
"""Paso 9D: Saneamiento final de procedencia antes de abrir Fase G.

Regenera la cadena completa D -> E -> F desde cero:
1. Nueva Fase D que incorpora NATIVAMENTE eligible_approved_features y 56 predictores aprobados.
2. Sella nueva D con nuevo run_id y manifiesto SHA-256 sin tocar reports/fase_d/20260927T112256_510493Z.
3. Nueva Fase E generada desde la nueva D, con los 5 distritos de reserva y protocolo espacial congelados.
4. Nueva Fase F ajustada mediante Nested Spatial CV, selección final por CV de desarrollo y ajuste del modelo final.
5. Verificación de 478.443 celdas elegibles, 131 celdas P, 45 depósitos, 32 distritos, Salave recuperado.
6. Cuarentena absoluta del holdout: cero accesos, predicciones o evaluaciones.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import numpy as np
import pandas as pd
import yaml
import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from geoau import features as fd
from geoau import evaluation as ev
from geoau import training as tr
from geoau.local_sources import write_json, sha256_file


def regenerar_fase_d(force_new=False):
    print("\n" + "=" * 80)
    print("1. REGENERANDO FASE D CANONICA DESDE CERO")
    print("=" * 80)

    eval_cfg_path = ROOT / 'config/evaluation.yaml'
    eval_cfg = yaml.safe_load(eval_cfg_path.read_text(encoding='utf-8'))
    existing_d = ROOT / eval_cfg.get('phase_d_run', '')
    if not force_new and existing_d.exists() and (existing_d / 'outputs_manifest.json').exists():
        if existing_d.name != '20260927T112256_510493Z':
            fd.verify_records(existing_d, ev.read_json(existing_d / 'outputs_manifest.json'))
            print(f"Reutilizando Fase D nueva ya sellada y verificada: {existing_d.relative_to(ROOT)}")
            return existing_d

    cfg_path = ROOT / 'config/features.yaml'
    cfg = yaml.safe_load(cfg_path.read_text(encoding='utf-8'))
    print(f"Configuracion features.yaml: phase_c_run = {cfg['phase_c_run']}")

    # 1.1 Iniciar nueva ejecucion D
    out_d = fd.start_run(ROOT, verify_phase_c_sha256=False)
    print(f"Nuevo directorio de ejecucion D: {out_d.relative_to(ROOT)}")

    # 1.2 Reutilizar bloques predictivos verificados desde la ejecucion base
    previous = ROOT / 'reports/fase_d/20260926T212039_928615Z'
    blocks = ['geology', 'terrain', 'geochemistry', 'structural', 'hydrology']
    print(f"Copiando y verificando bloques predictivos desde {previous.name}...")
    for b in blocks:
        manifest_p = previous / 'blocks' / f'{b}_manifest.json'
        entries = ev.read_json(manifest_p)
        fd.verify_records(previous, entries)
        for item in entries:
            dst = out_d / item['path']
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(previous / item['path'], dst)
        shutil.copy2(manifest_p, out_d / 'blocks' / manifest_p.name)
        fd.verify_records(out_d, entries)
        print(f"  Bloque {b}: transferido e integro.")

    # 1.3 Ensamblar matriz y generar calidad_y_soporte.parquet
    print("Ejecutando assemble() (incorpora nativamente eligible_approved_features)...")
    x, q, y = fd.assemble(ROOT, out_d)

    # 1.4 Aplicar auditoria de predictores aprobados a feature_allowlist.json
    audit_file = ROOT / 'data/review/auditoria_predictores_fase_d.csv'
    audit_df = pd.read_csv(audit_file)
    approved_cols = audit_df.loc[audit_df['decision'] == 'approved', 'name'].tolist()
    pending_cols = audit_df.loc[audit_df['decision'] == 'pending', 'name'].tolist()
    rejected_cols = audit_df.loc[audit_df['decision'] == 'rejected', 'name'].tolist()
    assert len(approved_cols) == 56, f"Se esperaban 56 aprobadas, halladas {len(approved_cols)}"

    allowlist_data = {
        'candidate_columns': audit_df['name'].tolist(),
        'approved_training_columns': approved_cols,
        'exclude_all_other_columns': True,
        'reason': 'revisión semántica completada: 56 aprobadas, 18 pendientes, 94 rechazadas',
        'alternative_representations': 'fracciones litológicas y cronoestratigráficas continuas; moda y proporciones geoquímicas excluidas',
        'audit_summary': {
            'total_evaluated': 168,
            'approved': len(approved_cols),
            'pending': len(pending_cols),
            'rejected': len(rejected_cols),
            'audit_date': '2026-09-27'
        }
    }
    write_json(out_d / 'feature_allowlist.json', allowlist_data)

    # 1.5 Actualizar feature_dictionary.csv con decisiones
    fdict = pd.read_csv(out_d / 'feature_dictionary.csv')
    dec_map = audit_df.set_index('name')['decision'].to_dict()
    fdict['decision'] = fdict['name'].map(dec_map)
    fdict.to_csv(out_d / 'feature_dictionary.csv', index=False, encoding='utf-8-sig')

    # 1.6 Resellar outputs_manifest.json para out_d
    manifest_files = sorted(p for p in out_d.rglob('*') if p.is_file() and p.name != 'outputs_manifest.json' and not p.name.startswith('.'))
    manifest_entries = [{'path': p.relative_to(out_d).as_posix(), 'sha256': sha256_file(p)} for p in manifest_files]
    write_json(out_d / 'outputs_manifest.json', manifest_entries)
    fd.verify_records(out_d, manifest_entries)
    print(f"outputs_manifest.json sellado con {len(manifest_entries)} archivos.")

    # 1.7 Verificaciones cuantitativas de la nueva Fase D
    print("\n--- Verificaciones de Integridad de la Nueva Fase D ---")
    grid_df = pd.read_parquet(out_d / 'calidad_y_soporte.parquet')
    assert 'eligible_approved_features' in grid_df.columns, "Error: eligible_approved_features no encontrada en calidad_y_soporte.parquet"
    n_approved_cells = int(grid_df['eligible_approved_features'].sum())
    print(f"Celdas con soporte eligible_approved_features: {n_approved_cells:,} (esperado: 478.443)")
    assert n_approved_cells == 478443, f"Error: esperadas 478.443 celdas, encontradas {n_approved_cells}"

    rel_indicios = pd.read_parquet(out_d / 'relacion_indicios_celda.parquet')
    n_rev = int(rel_indicios['elegible_general_revisada'].sum())
    print(f"Positivos revisados en relacion_indicios_celda: {n_rev} (esperado: 190)")
    assert n_rev == 190, f"Error: esperados 190 positivos, encontrados {n_rev}"

    rel_dep = pd.read_parquet(out_d / 'relacion_deposit_id_celda.parquet')
    assert rel_dep['deposit_id'].nunique() == 46
    rel_dist = pd.read_parquet(out_d / 'relacion_district_id_celda.parquet')
    assert rel_dist['district_id'].nunique() == 32

    # Actualizar config/evaluation.yaml con la nueva D
    eval_cfg_path = ROOT / 'config/evaluation.yaml'
    eval_cfg = yaml.safe_load(eval_cfg_path.read_text(encoding='utf-8'))
    old_d = eval_cfg['phase_d_run']
    eval_cfg['phase_d_run'] = out_d.relative_to(ROOT).as_posix()
    eval_cfg['support_column'] = 'eligible_approved_features'
    eval_cfg_path.write_text(yaml.dump(eval_cfg, sort_keys=False), encoding='utf-8')
    print(f"config/evaluation.yaml actualizado: phase_d_run={eval_cfg['phase_d_run']} (anterior: {old_d})")

    return out_d


def regenerar_fase_e(out_d):
    print("\n" + "=" * 80)
    print("2. REGENERANDO FASE E VALIDADA DESDE LA NUEVA D")
    print("=" * 80)

    # 2.1 Iniciar nueva ejecucion E
    out_e = ev.start_run(ROOT)
    print(f"Nuevo directorio de ejecucion E: {out_e.relative_to(ROOT)}")

    # 2.2 Generar particiones espaciales anidadas y reserva
    print("Generando particiones espaciales anidadas y reserva...")
    split_summary = ev.build_splits(ROOT, out_e)
    print(f"Total particiones generadas: {len(split_summary)} (esperadas: 20)")
    assert len(split_summary) == 20, f"Se esperaban 20 particiones, se obtuvieron {len(split_summary)}"

    # 2.3 Generar muestras P/U por estrato
    print("Generando muestras P/U por estrato territorial...")
    sample_summary = ev.build_samples(ROOT, out_e)
    print(f"Total muestras generadas: {len(sample_summary)} (esperadas: 180)")
    assert len(sample_summary) == 180, f"Se esperaban 180 muestras, se obtuvieron {len(sample_summary)}"

    # 2.4 Cierre formal y sellado de Fase E
    control = ev.finish_run(ROOT, out_e)
    print(f"Fase E cerrada: estado={control['estado_ejecucion']}, mode={control['mode']}, training_allowed={control['training_allowed']}")

    # 2.5 Auditoria cuantitativa de Fase E
    print("\n--- Verificaciones Cuantitativas de la Nueva Fase E ---")
    sel_p = pd.read_parquet(out_e / 'design/selected_positive_records.parquet')
    print(f"Positivos seleccionados: {len(sel_p)} registros (esperado: 175)")
    assert len(sel_p) == 175, f"Esperados 175 registros, obtenidos {len(sel_p)}"
    print(f"Celdas positivas unicas: {sel_p.cell_id.nunique()} (esperado: 131)")
    assert sel_p.cell_id.nunique() == 131, f"Esperadas 131 celdas, obtenidas {sel_p.cell_id.nunique()}"
    print(f"Depositos independientes: {sel_p.deposit_id.nunique()} (esperado: 45)")
    assert sel_p.deposit_id.nunique() == 45, f"Esperados 45 depositos, obtenidos {sel_p.deposit_id.nunique()}"
    print(f"Distritos metalogeneticos: {sel_p.district_id.nunique()} (esperado: 32)")
    assert sel_p.district_id.nunique() == 32, f"Esperados 32 distritos, obtenidos {sel_p.district_id.nunique()}"

    # Salave recuperado
    assert 'dep_salave' in set(sel_p.deposit_id), "Error: dep_salave debe estar presente en Fase E"
    assert 'dist_occidente_asturiano' in set(sel_p.district_id), "Error: dist_occidente_asturiano debe estar presente"
    # La Preciosa excluida
    assert 'dep_la_preciosa_penaflor' not in set(sel_p.deposit_id), "Error: dep_la_preciosa_penaflor debe estar excluida"

    # Actualizar config/training.yaml con la nueva E
    train_cfg_path = ROOT / 'config/training.yaml'
    train_cfg = yaml.safe_load(train_cfg_path.read_text(encoding='utf-8'))
    old_e = train_cfg['phase_e_run']
    train_cfg['phase_e_run'] = out_e.relative_to(ROOT).as_posix()
    train_cfg_path.write_text(yaml.dump(train_cfg, sort_keys=False), encoding='utf-8')
    print(f"config/training.yaml actualizado: phase_e_run={train_cfg['phase_e_run']} (anterior: {old_e})")

    return out_e


def regenerar_fase_f(out_d, out_e):
    print("\n" + "=" * 80)
    print("3. REGENERANDO FASE F VALIDADA MEDIANTE NESTED SPATIAL CV")
    print("=" * 80)

    train_cfg_path = ROOT / 'config/training.yaml'
    cfg = yaml.safe_load(train_cfg_path.read_text(encoding='utf-8'))

    # 3.1 Iniciar nueva ejecucion F
    out_f = tr.start_run(ROOT)
    print(f"Nuevo directorio de ejecucion F: {out_f.relative_to(ROOT)}")

    # 3.2 Referencias basales
    print("\nAjustando referencias basales...")
    t0 = time.time()
    tr.fit_references(ROOT, out_f)
    print(f"Referencias completadas en {time.time()-t0:.1f}s")

    # 3.3 Ajuste de las 4 familias por Nested CV
    families = cfg['families']
    print(f"\nAjustando 4 familias mediante Nested Spatial CV: {families}")
    for fam in families:
        t_fam = time.time()
        tr.fit_family(ROOT, out_f, fam)
        print(f"  Familia {fam} completada en {time.time()-t_fam:.1f}s")

    # 3.4 Sensibilidad y ablaciones
    print("\nEjecutando sensibilidad y ablaciones fijas...")
    t_sens = time.time()
    tr.run_sensitivity(ROOT, out_f)
    print(f"Sensibilidad completada en {time.time()-t_sens:.1f}s")

    # 3.5 Cierre formal
    control = tr.finish_run(ROOT, out_f)
    print(f"Control de cierre F: estado={control['estado_ejecucion']}, outer_folds={control['outer_folds']}")

    # 3.6 Auditoria de Cuarentena
    units = pd.read_parquet(out_e / 'design/spatial_units.parquet')
    holdout_cells = set(units.loc[units.holdout, 'cell_id'])
    for item in ev.read_json(out_e / 'split_plan.json')['splits']:
        frame = tr.fixed_frame(out_f, item['split_id'])
        assert len(set(frame.cell_id) & holdout_cells) == 0, f"Error: holdout en frame {item['split_id']}"
    for pf in (out_f / 'predictions').glob('*.parquet'):
        assert len(set(pd.read_parquet(pf).cell_id) & holdout_cells) == 0, f"Error: holdout en {pf.name}"
    for mf in (out_f / 'models').glob('*.joblib'):
        meta = ev.read_json(mf.with_suffix('.json'))
        assert len(set(pd.read_parquet(Path(meta['sample_path'])).cell_id) & holdout_cells) == 0
    print("CUARENTENA CONFIRMADA: CERO celdas de holdout consultadas o evaluadas.")

    # 3.7 Seleccion del Modelo Final por CV Espacial de Desarrollo
    print("\n" + "=" * 80)
    print("SELECCION DEL MODELO FINAL POR CV ESPACIAL DE DESARROLLO")
    print("=" * 80)
    search_files = sorted(list((out_f / 'search').glob('*.csv')))
    all_search = pd.concat([pd.read_csv(f) for f in search_files], ignore_index=True)
    candidates_meta = {c['candidate_id']: c for fam in families for c in ev.read_json(out_f / 'candidates.json')[fam]}
    dev_ranking_cols = [c for c in ['deposit_recovery_at_05', 'cell_recovery_at_05',
                                    'deposit_recovery_at_01', 'cell_recovery_at_01',
                                    'deposit_recovery_at_10', 'cell_recovery_at_10',
                                    'average_precision_PU', 'roc_auc_PU'] if c in all_search.columns]
    dev_cv_df = all_search.groupby('candidate_id')[dev_ranking_cols].mean()
    dev_cv_df['family'] = [candidates_meta[cid]['family'] for cid in dev_cv_df.index]
    dev_cv_df['ratio'] = [candidates_meta[cid]['ratio'] for cid in dev_cv_df.index]
    dev_cv_df['params'] = [json.dumps(candidates_meta[cid]['params']) for cid in dev_cv_df.index]
    dev_cv_df['splits_evaluated'] = all_search.groupby('candidate_id')['split_id'].count()

    primary_sort = 'deposit_recovery_at_05'
    dev_cv_df = dev_cv_df.sort_values(by=[primary_sort, 'roc_auc_PU', 'candidate_id'], ascending=[False, False, True])
    dev_ranking_path = out_f / 'development_cv_candidate_ranking.csv'
    dev_cv_df.to_csv(dev_ranking_path)

    print("\nRanking Completo de Candidatos en CV de Desarrollo (15 splits internos):")
    print(dev_cv_df[['family', 'ratio', primary_sort, 'deposit_recovery_at_01', 'deposit_recovery_at_10',
                     'cell_recovery_at_05', 'roc_auc_PU', 'splits_evaluated']].to_string())

    best_candidate_id = dev_cv_df.index[0]
    best_candidate = candidates_meta[best_candidate_id]
    best_family = best_candidate['family']
    print(f"\nGanador seleccionado por CV de desarrollo: {best_candidate_id} ({best_family}, ratio {best_candidate['ratio']})")

    # 3.8 Ajuste del Modelo Final de Produccion sobre Desarrollo
    grid = pd.read_parquet(out_d / 'calidad_y_soporte.parquet')
    dev_mask = ~units.holdout & units.cell_id.isin(grid.loc[grid['eligible_approved_features'] == True, 'cell_id'])
    dev_cells = set(units.loc[dev_mask, 'cell_id'])

    pos_records = pd.read_parquet(out_f / 'evaluation/positive_records.parquet')
    dev_pos_cells = set(pos_records.loc[pos_records.cell_id.isin(dev_cells), 'cell_id'])
    dev_u_pool = sorted(list(dev_cells - dev_pos_cells))

    n_requested_u = len(dev_pos_cells) * best_candidate['ratio']
    rng = np.random.default_rng(ev.seed_for(cfg['seed'], 'final_model', best_family, best_candidate_id))
    chosen_u = rng.choice(dev_u_pool, size=min(n_requested_u, len(dev_u_pool)), replace=False)

    p_df = pd.DataFrame({'cell_id': sorted(dev_pos_cells), 'sample_class': 1})
    u_df = pd.DataFrame({'cell_id': sorted(chosen_u), 'sample_class': 0})
    final_sample = pd.concat([p_df, u_df], ignore_index=True)

    print(f"\nMuestra de entrenamiento final: {len(dev_pos_cells)} P + {len(chosen_u)} U = {len(final_sample)} filas.")
    assert len(set(final_sample.cell_id) & holdout_cells) == 0, "Error: holdout en muestra final!"

    schema = ev.read_json(out_f / 'feature_schema.json')
    cols_meta = schema[cfg['feature_set']]
    seed_final = ev.seed_for(cfg['seed'], 'final_model_fit', best_family) % (2**32)
    final_pipeline = tr.make_pipeline(cols_meta['columns'], cols_meta['categorical'],
                                      best_family, best_candidate['params'], seed_final, cfg['n_jobs'])

    X_dev = pd.read_parquet(out_d / 'X_features.parquet',
                            columns=['cell_id'] + cols_meta['columns']).set_index('cell_id')
    t_fit_final = time.time()
    final_pipeline.fit(X_dev.loc[final_sample.cell_id, cols_meta['columns']], final_sample.sample_class.to_numpy())
    fit_duration = time.time() - t_fit_final
    print(f"Pipeline final ajustado con exito en {fit_duration:.2f}s")

    final_dir = out_f / 'final_model'
    final_dir.mkdir(exist_ok=True)
    final_model_path = final_dir / 'final_validated_model.joblib'
    final_meta_path = final_dir / 'final_validated_model.json'
    joblib.dump(final_pipeline, final_model_path, compress=3)

    nested_df = pd.read_csv(out_f / 'nested_procedure_metrics.csv')
    final_metadata = {
        'model_tag': 'final_validated_model',
        'phase_f_run': out_f.relative_to(ROOT).as_posix(),
        'phase_e_run': out_e.relative_to(ROOT).as_posix(),
        'phase_d_run': out_d.relative_to(ROOT).as_posix(),
        'selection_procedure': 'development_spatial_cross_validation_inner_folds',
        'family': best_family,
        'candidate_id': best_candidate_id,
        'ratio': best_candidate['ratio'],
        'params': best_candidate['params'],
        'feature_set': cfg['feature_set'],
        'columns': cols_meta['columns'],
        'n_features': len(cols_meta['columns']),
        'development_eligible_universe_cells': len(dev_cells),
        'train_P_cells': len(dev_pos_cells),
        'train_U_cells': len(chosen_u),
        'train_total_fit_rows': len(final_sample),
        'fit_duration_seconds': fit_duration,
        'holdout_touched': False,
        'holdout_cells_quarantined': len(holdout_cells),
        'ready_for_phase_g_blind_evaluation': True,
        'development_cv_mean_deposit_recovery_at_05': float(dev_cv_df.loc[best_candidate_id, 'deposit_recovery_at_05']),
        'development_cv_mean_cell_recovery_at_05': float(dev_cv_df.loc[best_candidate_id, 'cell_recovery_at_05']),
        'development_cv_mean_roc_auc': float(dev_cv_df.loc[best_candidate_id, 'roc_auc_PU']),
        'development_cv_mean_pr_auc': float(dev_cv_df.loc[best_candidate_id, 'average_precision_PU']),
        'nested_spatial_cv_outer_mean_deposit_recovery_at_05': float(nested_df['deposit_recovery_at_05'].mean()),
        'nested_spatial_cv_outer_std_deposit_recovery_at_05': float(nested_df['deposit_recovery_at_05'].std()),
        'nested_spatial_cv_outer_mean_cell_recovery_at_05': float(nested_df['cell_recovery_at_05'].mean()),
        'nested_spatial_cv_outer_std_cell_recovery_at_05': float(nested_df['cell_recovery_at_05'].std()),
        'nested_spatial_cv_outer_mean_roc_auc': float(nested_df['roc_auc_PU'].mean()),
        'nested_spatial_cv_outer_mean_pr_auc': float(nested_df['average_precision_PU'].mean())
    }
    write_json(final_meta_path, final_metadata)

    # 3.9 Resellar manifiesto de Fase F
    manifest = ev.read_json(out_f / 'outputs_manifest.json')
    manifest.append({'path': dev_ranking_path.relative_to(out_f).as_posix(), 'sha256': ev.sha256_file(dev_ranking_path)})
    manifest.append({'path': final_model_path.relative_to(out_f).as_posix(), 'sha256': ev.sha256_file(final_model_path)})
    manifest.append({'path': final_meta_path.relative_to(out_f).as_posix(), 'sha256': ev.sha256_file(final_meta_path)})
    write_json(out_f / 'outputs_manifest.json', manifest)
    ev.verify(out_f, manifest)

    print(f"\nFase F sellada con manifiesto verificado.")
    return out_f, final_metadata


def main():
    print("=" * 80)
    print("EJECUTANDO PASO 9D: SANEAMIENTO FINAL DE PROCEDENCIA D -> E -> F")
    print("=" * 80)
    t_start = time.time()

    # 1. Fase D nueva
    out_d = regenerar_fase_d()

    # 2. Fase E nueva
    out_e = regenerar_fase_e(out_d)

    # 3. Fase F nueva
    out_f, final_meta = regenerar_fase_f(out_d, out_e)

    total_time = time.time() - t_start
    print("\n" + "=" * 80)
    print("CADENA COMPLETA D -> E -> F REGENERADA Y SELLADA CON EXITO")
    print("=" * 80)
    print(f"Nueva Fase D: {out_d.relative_to(ROOT)}")
    print(f"Nueva Fase E: {out_e.relative_to(ROOT)}")
    print(f"Nueva Fase F: {out_f.relative_to(ROOT)}")
    print(f"Tiempo total: {total_time:.1f}s")
    print(f"Ganador seleccionado: {final_meta['candidate_id']} ({final_meta['family']}, ratio {final_meta['ratio']})")
    print(f"Rendimiento CV desarrollo deposit_recovery@5%: {final_meta['development_cv_mean_deposit_recovery_at_05']:.4f}")
    print(f"Rendimiento CV desarrollo ROC-AUC: {final_meta['development_cv_mean_roc_auc']:.4f}")


if __name__ == '__main__':
    main()
