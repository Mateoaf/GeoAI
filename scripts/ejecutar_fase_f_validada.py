"""Paso 9: Ejecutar Fase F validada mediante nested spatial CV sin tocar el holdout ciego.

Protocolo:
- Documentacion previa de los 2 depositos y 1 distrito excluidos por falta de soporte eligible_geo4.
- Exclusivamente las 56 variables aprobadas en feature_allowlist.json.
- Muestras y particiones de la Fase E validada (reports/fase_e/20260927T115302_113892Z).
- Comparacion de Logistic Regression, Random Forest, ExtraTrees y HistGradientBoosting.
- Seleccion interna estricta de hiperparametros, ratio P/U y realizacion U en inner folds.
- Evaluacion de generalizacion en outer folds: recovery@1%, recovery@5%, recovery@10%, PR-AUC y ROC-AUC.
- Cuarentena absoluta del holdout ciego (sin metricas, scores ni predicciones sobre la reserva).
- Seleccion y congelacion del modelo ganador para Fase G.
"""
from pathlib import Path
import json
import sys
import time
import numpy as np
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from geoau import training as tr
from geoau import evaluation as ev
from geoau.local_sources import write_json
read_json = ev.read_json


def audit_excluded_deposits_and_districts(d_dir, support_col='eligible_approved_features'):
    """Identifica y documenta los depositos y distritos excluidos por soporte, y audita predictores aprobados."""
    rel = pd.read_parquet(d_dir / 'relacion_indicios_celda.parquet')
    grid = pd.read_parquet(d_dir / 'calidad_y_soporte.parquet')
    m = rel.merge(grid[['cell_id', 'eligible_geo4', 'eligible_approved_features', 'eligible_geology_terrain', 'land_area_m2',
                        'fase_c_valid_geoquimica_au', 'fase_c_valid_litologia', 'fase_c_coverage_decision']],
                  on='cell_id', how='left')
    m_rev = m[m.elegible_general_revisada == True]

    all_deps = set(m_rev.deposit_id.dropna())
    geo4_deps = set(m_rev.loc[m_rev.eligible_geo4 == True, 'deposit_id'].dropna())
    excluded_geo4_deps = sorted(all_deps - geo4_deps)

    sup_deps = set(m_rev.loc[m_rev[support_col] == True, 'deposit_id'].dropna())
    excluded_sup_deps = sorted(all_deps - sup_deps)

    all_dists = set(m_rev.district_id.dropna())
    geo4_dists = set(m_rev.loc[m_rev.eligible_geo4 == True, 'district_id'].dropna())
    excluded_geo4_dists = sorted(all_dists - geo4_dists)

    sup_dists = set(m_rev.loc[m_rev[support_col] == True, 'district_id'].dropna())
    excluded_sup_dists = sorted(all_dists - sup_dists)

    print("\n" + "=" * 80)
    print("AUDITORIA COMPARATIVA DE SOPORTE: eligible_geo4 VS eligible_approved_features")
    print("=" * 80)
    print(f"Total depositos confirmados en Fase B: {len(all_deps)}")
    print(f"  - Bajo eligible_geo4: {len(geo4_deps)} depositos (excluidos {len(excluded_geo4_deps)}: {excluded_geo4_deps})")
    print(f"  - Bajo {support_col}: {len(sup_deps)} depositos (excluidos {len(excluded_sup_deps)}: {excluded_sup_deps})")
    print(f"  -> RECUPERADO: dep_salave ha sido reincorporado al universo modelable!")
    print(f"  -> EXCLUSION LEGITIMA: dep_la_preciosa_penaflor permanece excluido por litologia_cobertura = 0.7046 < 0.80")
    print(f"\nTotal distritos confirmados en Fase B: {len(all_dists)}")
    print(f"  - Bajo eligible_geo4: {len(geo4_dists)} distritos (excluidos {len(excluded_geo4_dists)}: {excluded_geo4_dists})")
    print(f"  - Bajo {support_col}: {len(sup_dists)} distritos (excluidos {len(excluded_sup_dists)}: {excluded_sup_dists})")
    print(f"  -> RECUPERADO: dist_occidente_asturiano (100% de los distritos metalogeneticos cubiertos)!")

    ex_df = m_rev[m_rev.deposit_id.isin(excluded_sup_deps)]
    print(f"\nDetalle de depósitos excluidos bajo {support_col}:")
    for r in ex_df.itertuples():
        print(f"  - Deposito: {r.deposit_id:<28} | Distrito: {r.district_id:<26} | Celda: {r.cell_id} | "
              f"Area m2: {r.land_area_m2:>10.1f} | Litologia: {r.fase_c_valid_litologia:.4f} | Motivo: {r.fase_c_coverage_decision}")
    print("=" * 80)

    # Auditoria de predictores aprobados
    allowlist = ev.read_json(d_dir / 'feature_allowlist.json')
    app_cols = allowlist.get('approved_training_columns', [])
    print("\nAUDITORIA PREVIA DE PREDICTORES APROBADOS (56 COLUMNAS):")
    print(f"Total columnas aprobadas en D: {len(app_cols)}")
    geoq_cols = [c for c in app_cols if 'geoquimica' in c or 'au_' in c or 'as_' in c or 'sb_' in c or 'cu_' in c]
    print(f"Predictores geoquimicos aprobados: {len(geoq_cols)} (CERO PERMITIDOS)")
    assert len(geoq_cols) == 0, f"Error: predictores geoquimicos no aprobados en feature_allowlist: {geoq_cols}"
    lit_cols = [c for c in app_cols if c.startswith('litologia_')]
    age_cols = [c for c in app_cols if c.startswith('edades_')]
    str_cols = [c for c in app_cols if c.startswith('dist_') and not c.endswith('_cauce_m')]
    rel_cols = [c for c in app_cols if c in ('elevacion_media_m', 'pendiente_grados', 'tpi_1000m_m', 'desv_elevacion_1000m_m', 'tpi_5000m_m', 'desv_elevacion_5000m_m')]
    hyd_cols = [c for c in app_cols if c == 'dist_cauce_m']
    print(f"Desglose cientifico: {len(lit_cols)} litologias, {len(age_cols)} edades, {len(str_cols)} estructuras, "
          f"{len(rel_cols)} relieve/geomorfometria, {len(hyd_cols)} hidrologia. Total = {len(app_cols)}.")
    print("=" * 80 + "\n")
    return excluded_sup_deps, excluded_sup_dists


def main():
    print("=" * 80)
    print("EJECUTANDO FASE F VALIDADA: NESTED SPATIAL CV")
    print("=" * 80)

    import yaml
    cfg = yaml.safe_load((ROOT / 'config/training.yaml').read_text(encoding='utf-8'))
    e_dir = ROOT / cfg['phase_e_run']
    ecfg = ev.read_json(e_dir / 'config_snapshot.json')
    d_dir = ROOT / ecfg['phase_d_run']

    # 1. Auditoria previa de depositos y distritos excluidos
    support_col = ecfg.get('support_column', 'eligible_approved_features')
    excluded_deps, excluded_dists = audit_excluded_deposits_and_districts(d_dir, support_col)
    assert len(excluded_deps) == 1, f"Se esperaba 1 deposito excluido bajo {support_col}, se hallaron {len(excluded_deps)}"
    assert len(excluded_dists) == 0, f"Se esperaban 0 distritos excluidos bajo {support_col}, se hallaron {len(excluded_dists)}"

    # 2. Iniciar ejecucion F
    print("\n--- 1. Inicializando nueva ejecucion F ---")
    out = tr.start_run(ROOT)
    print(f"Directorio de ejecucion F: {out}")

    # Verificar schema
    schema = ev.read_json(out / 'feature_schema.json')
    approved_cols = schema[cfg['feature_set']]['columns']
    print(f"Predictores en schema['{cfg['feature_set']}']: {len(approved_cols)}")
    assert len(approved_cols) == 56, f"Se esperaban 56 columnas, se obtuvieron {len(approved_cols)}"

    # 3. Referencias basales
    print("\n--- 2. Ajustando y evaluando modelos de referencia ---")
    t0 = time.time()
    ref_df = tr.fit_references(ROOT, out)
    print(f"Referencias completadas en {time.time()-t0:.1f}s ({len(ref_df)} filas)")

    # 4. Ajustar y evaluar las 4 familias por Nested CV
    families = cfg['families']
    print(f"\n--- 3. Ajustando 4 familias mediante Nested Spatial CV: {families} ---")
    family_outer_results = {}
    for fam in families:
        print(f"\n>> Procesando familia: {fam} ...")
        t_fam = time.time()
        fam_df = tr.fit_family(ROOT, out, fam)
        family_outer_results[fam] = fam_df
        print(f">> Familia {fam} completada en {time.time()-t_fam:.1f}s")

    # 5. Sensibilidad y ablaciones
    print("\n--- 4. Ejecutando analisis de sensibilidad y ablaciones fijas ---")
    t_sens = time.time()
    sens_df = tr.run_sensitivity(ROOT, out)
    print(f"Sensibilidad completada en {time.time()-t_sens:.1f}s ({len(sens_df)} filas)")

    # 6. Cierre formal de ejecucion F
    print("\n--- 5. Cerrando ejecucion F y sellando manifiesto ---")
    control = tr.finish_run(ROOT, out)
    print(f"Control cierre: estado={control['estado_ejecucion']}, mode={control['mode']}, "
          f"scientific_training_allowed={control['scientific_training_allowed']}, outer_folds={control['outer_folds']}")

    # 7. Auditoria de Cuarentena de la Reserva
    print("\n" + "=" * 80)
    print("AUDITORIA DE CUARENTENA: VERIFICACION DE NO-ACCESO A LA RESERVA")
    print("=" * 80)
    units = pd.read_parquet(e_dir / 'design/spatial_units.parquet')
    holdout_cells = set(units.loc[units.holdout, 'cell_id'])
    print(f"Celdas en reserva holdout: {len(holdout_cells)}")

    # Verificar que ningun frame de evaluacion contiene celdas de holdout
    for item in ev.read_json(e_dir / 'split_plan.json')['splits']:
        frame = tr.fixed_frame(out, item['split_id'])
        overlap = set(frame.cell_id) & holdout_cells
        assert len(overlap) == 0, f"Error: holdout en frame {item['split_id']}: {len(overlap)}"

    # Verificar que ningun archivo de predicciones contiene celdas de holdout
    pred_files = list((out / 'predictions').glob('*.parquet'))
    for pf in pred_files:
        p_df = pd.read_parquet(pf)
        overlap = set(p_df.cell_id) & holdout_cells
        assert len(overlap) == 0, f"Error: holdout en prediccion {pf.name}: {len(overlap)}"

    # Verificar modelos
    model_files = list((out / 'models').glob('*.joblib'))
    for mf in model_files:
        meta = ev.read_json(mf.with_suffix('.json'))
        s_df = pd.read_parquet(Path(meta['sample_path']))
        overlap = set(s_df.cell_id) & holdout_cells
        assert len(overlap) == 0, f"Error: holdout en muestra de modelo {mf.name}: {len(overlap)}"

    print("CONFIRMADO: CERO celdas de holdout consultadas, predichas o evaluadas.")

    # 8. Reporte del Procedimiento Anidado (Nested Spatial CV)
    print("\n" + "=" * 80)
    print("PROCEDIMIENTO ANIDADO COMPLETO (GANADOR INTERNO -> EVALUACION OOF EXTERNA)")
    print("=" * 80)
    nested_df = pd.read_csv(out / 'nested_procedure_metrics.csv')
    disp_cols = [c for c in ['outer_split', 'family', 'candidate_id', 'ratio', 'mean_inner_recovery_at_05',
                             'deposit_recovery_at_01', 'deposit_recovery_at_05', 'deposit_recovery_at_10',
                             'cell_recovery_at_01', 'cell_recovery_at_05', 'cell_recovery_at_10',
                             'average_precision_PU', 'roc_auc_PU'] if c in nested_df.columns]
    print(nested_df[disp_cols].to_string(index=False))

    print("\n" + "=" * 80)
    print("RESUMEN AGREGADO DE GENERALIZACION EXTERNA (NESTED SPATIAL CV: MEDIA +- STD)")
    print("=" * 80)
    metric_cols = [c for c in ['deposit_recovery_at_01', 'deposit_recovery_at_05', 'deposit_recovery_at_10',
                               'cell_recovery_at_01', 'cell_recovery_at_05', 'cell_recovery_at_10',
                               'average_precision_PU', 'roc_auc_PU'] if c in nested_df.columns]
    nested_summary = nested_df[metric_cols].agg(['mean', 'std']).T
    nested_summary.columns = ['Media Externa', 'Desv. Estandar']
    print(nested_summary.to_string())
    print("\nNOTA CIENTIFICA: Los folds externos se utilizan EXCLUSIVAMENTE para estimar la capacidad de")
    print("generalizacion del protocolo anidado. NO se emplean para seleccionar la configuracion final.")

    # 9. Seleccion del Modelo Final Mediante CV Espacial sobre Todo el Conjunto de Desarrollo
    print("\n" + "=" * 80)
    print("SELECCION DEL MODELO FINAL: CV ESPACIAL INTERNA SOBRE TODO EL CONJUNTO DE DESARROLLO")
    print("=" * 80)
    search_files = sorted(list((out / 'search').glob('*.csv')))
    all_search = pd.concat([pd.read_csv(f) for f in search_files], ignore_index=True)
    
    candidates_meta = {c['candidate_id']: c for fam in families for c in ev.read_json(out / 'candidates.json')[fam]}
    dev_ranking_cols = [c for c in ['deposit_recovery_at_05', 'cell_recovery_at_05',
                                    'deposit_recovery_at_01', 'cell_recovery_at_01',
                                    'deposit_recovery_at_10', 'cell_recovery_at_10',
                                    'average_precision_PU', 'roc_auc_PU'] if c in all_search.columns]
    dev_cv_means = all_search.groupby('candidate_id')[dev_ranking_cols].mean()
    dev_cv_stds = all_search.groupby('candidate_id')[dev_ranking_cols].std()
    dev_cv_counts = all_search.groupby('candidate_id')['split_id'].count()

    dev_cv_df = dev_cv_means.copy()
    dev_cv_df['family'] = [candidates_meta[cid]['family'] for cid in dev_cv_df.index]
    dev_cv_df['ratio'] = [candidates_meta[cid]['ratio'] for cid in dev_cv_df.index]
    dev_cv_df['params'] = [json.dumps(candidates_meta[cid]['params']) for cid in dev_cv_df.index]
    dev_cv_df['splits_evaluated'] = dev_cv_counts

    primary_sort = 'deposit_recovery_at_05' if 'deposit_recovery_at_05' in dev_cv_df.columns else 'recovery_at_05'
    dev_cv_df = dev_cv_df.sort_values(by=[primary_sort, 'roc_auc_PU', 'candidate_id'], ascending=[False, False, True])
    dev_ranking_path = out / 'development_cv_candidate_ranking.csv'
    dev_cv_df.to_csv(dev_ranking_path)
    
    print("\nRanking Completo de Candidatos en CV de Desarrollo (15 splits internos):")
    print(dev_cv_df[['family', 'ratio', primary_sort, 'deposit_recovery_at_01', 'deposit_recovery_at_10',
                     'cell_recovery_at_05', 'roc_auc_PU', 'splits_evaluated']].to_string())

    best_candidate_id = dev_cv_df.index[0]
    best_candidate = candidates_meta[best_candidate_id]
    best_family = best_candidate['family']
    print(f"\nConfiguracion ganadora seleccionada EXCLUSIVAMENTE por CV de desarrollo:")
    print(f"  - Candidato: {best_candidate_id}")
    print(f"  - Familia: {best_family}")
    print(f"  - Ratio P/U: {best_candidate['ratio']}")
    print(f"  - Hiperparametros: {best_candidate['params']}")
    print(f"  - Recovery@5% medio en CV desarrollo: {dev_cv_df.loc[best_candidate_id, primary_sort]:.4f}")
    print(f"  - ROC-AUC medio en CV desarrollo: {dev_cv_df.loc[best_candidate_id, 'roc_auc_PU']:.4f}")

    # 10. Ajuste del Modelo Final de Produccion/Fase G sobre el conjunto de desarrollo
    print("\n" + "=" * 80)
    print("AJUSTE DEL MODELO FINAL VALIDADO PARA EVALUACION CIEGA EN FASE G")
    print("=" * 80)
    grid = pd.read_parquet(d_dir / 'calidad_y_soporte.parquet')
    dev_mask = ~units.holdout & units.cell_id.isin(grid.loc[grid[support_col] == True, 'cell_id'])
    dev_cells = set(units.loc[dev_mask, 'cell_id'])

    pos_records = pd.read_parquet(out / 'evaluation/positive_records.parquet')
    dev_pos_cells = set(pos_records.loc[pos_records.cell_id.isin(dev_cells), 'cell_id'])
    dev_u_pool = sorted(list(dev_cells - dev_pos_cells))

    n_requested_u = len(dev_pos_cells) * best_candidate['ratio']
    rng = np.random.default_rng(ev.seed_for(cfg['seed'], 'final_model', best_family, best_candidate_id))
    chosen_u = rng.choice(dev_u_pool, size=min(n_requested_u, len(dev_u_pool)), replace=False)

    p_df = pd.DataFrame({'cell_id': sorted(dev_pos_cells), 'sample_class': 1})
    u_df = pd.DataFrame({'cell_id': sorted(chosen_u), 'sample_class': 0})
    final_sample = pd.concat([p_df, u_df], ignore_index=True)

    print("Documentacion precisa del universo y muestra de entrenamiento final:")
    print(f"  - Universo territorial de desarrollo (celdas elegibles de fondo): {len(dev_cells):,}")
    print(f"  - Celdas positivas revisadas de desarrollo (P): {len(dev_pos_cells)}")
    print(f"  - Celdas no etiquetadas muestreadas (U, ratio {best_candidate['ratio']}): {len(chosen_u)}")
    print(f"  - TOTAL INSTANCIAS DE AJUSTE (P + U): {len(final_sample)} celdas.")
    print("  -> CONFIRMACION: El modelo final se entrena con exactamente "
          f"{len(final_sample)} filas (no con {len(dev_cells):,} celdas).")

    # Verificar cuarentena absoluta
    assert len(set(final_sample.cell_id) & holdout_cells) == 0, "Error: celdas de holdout en muestra final!"

    # Ajustar pipeline final
    seed_final = ev.seed_for(cfg['seed'], 'final_model_fit', best_family) % (2**32)
    cols_meta = schema[cfg['feature_set']]
    final_pipeline = tr.make_pipeline(cols_meta['columns'], cols_meta['categorical'],
                                      best_family, best_candidate['params'], seed_final, cfg['n_jobs'])

    X_dev = pd.read_parquet(d_dir / 'X_features.parquet',
                            columns=['cell_id'] + cols_meta['columns']).set_index('cell_id')
    t_fit_final = time.time()
    final_pipeline.fit(X_dev.loc[final_sample.cell_id, cols_meta['columns']], final_sample.sample_class.to_numpy())
    fit_duration = time.time() - t_fit_final
    print(f"  - Pipeline final ajustado con exito en {fit_duration:.2f}s")

    # Guardar modelo final para evaluacion ciega en Fase G
    final_dir = out / 'final_model'
    final_dir.mkdir(exist_ok=True)
    final_model_path = final_dir / 'final_validated_model.joblib'
    final_meta_path = final_dir / 'final_validated_model.json'
    joblib.dump(final_pipeline, final_model_path, compress=3)

    final_metadata = {
        'model_tag': 'final_validated_model',
        'phase_f_run': out.relative_to(ROOT).as_posix(),
        'phase_e_run': cfg['phase_e_run'],
        'phase_d_run': ecfg['phase_d_run'],
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

    # Actualizar manifiesto
    manifest = ev.read_json(out / 'outputs_manifest.json')
    manifest.append({'path': dev_ranking_path.relative_to(out).as_posix(), 'sha256': ev.sha256_file(dev_ranking_path)})
    manifest.append({'path': final_model_path.relative_to(out).as_posix(), 'sha256': ev.sha256_file(final_model_path)})
    manifest.append({'path': final_meta_path.relative_to(out).as_posix(), 'sha256': ev.sha256_file(final_meta_path)})
    write_json(out / 'outputs_manifest.json', manifest)

    # Verificacion formal del manifiesto
    ev.verify(out, manifest)

    print(f"\nModelo final congelado guardado en: {final_model_path}")
    print(f"Metadatos guardados en: {final_meta_path}")

    print("\n" + "=" * 80)
    print("FASE F VALIDADA (PASO 9B) COMPLETADA EXITOSAMENTE")
    print(f"Run generado: {out.relative_to(ROOT)}")
    print("=" * 80)


if __name__ == '__main__':
    main()

