"""
Test de Desacoplamiento por Sistema Mineral en las 7 particiones ciegas nacionales.
Compara:
1. Modelo Monolitico NB 25 (93 vars)
2. Desacoplamiento por Pilares del Sistema Mineral (Geoquimico, Estructural, Magmatico/Alteracion, Litoestratigrafico)
3. Operadores de Integracion (Probabilistic OR, Fuzzy Gamma, Meta-Learner)
"""
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.pipeline import Pipeline
import lightgbm as lgb
from geoau.geochemical_experiment import load_data, make_preprocessor, predict
from geoau.national_evaluation import deposit_metrics, PERCENTAGES

ROOT = Path(".")
data = load_data(ROOT)
base = data.output
eval_dir = ROOT / "reports/evaluacion_configuracion_nacional_20261021"
design = json.loads((eval_dir / "evaluation_design.json").read_text(encoding="utf-8"))

# 1. Cargar matriz de 93 variables
df_raw = pd.read_parquet(ROOT / 'reports/fase_d/20260923T211448_267684Z/X_features.parquet').set_index('cell_id')
df_fav_nb25 = pd.read_parquet(ROOT / 'reports/reentrenamiento_geoquimica_continua_20261021/favorabilidad_nacional_geoquimica_continua.parquet').set_index('cell_id')

X_all = data.features.copy()

grade_weights = {
    'litologia_u000_fraccion': 0.0, 'litologia_u001_fraccion': 1.0, 'litologia_u002_fraccion': 0.0,
    'litologia_u003_fraccion': 0.0, 'litologia_u004_fraccion': 0.0, 'litologia_u005_fraccion': 0.0,
    'litologia_u006_fraccion': 0.0, 'litologia_u007_fraccion': 0.5, 'litologia_u008_fraccion': 2.0,
    'litologia_u009_fraccion': 0.0, 'litologia_u010_fraccion': 3.0, 'litologia_u011_fraccion': 2.5,
    'litologia_u012_fraccion': 0.0, 'litologia_u013_fraccion': 2.0, 'litologia_u014_fraccion': 3.0,
    'litologia_u015_fraccion': 2.5, 'litologia_u016_fraccion': 1.5, 'litologia_u018_fraccion': 1.5,
    'litologia_u019_fraccion': 1.0
}
X_all['grado_metamorfico'] = sum(X_all[col] * w for col, w in grade_weights.items()).astype('float32')
X_all['afinidad_esquistos_verdes'] = np.exp(-((X_all['grado_metamorfico'] - 2.0)**2) / (2 * 0.5**2)).astype('float32')

hercinico = X_all['edades_u000_fraccion'] + X_all['edades_u001_fraccion'] + X_all['edades_u008_fraccion']
granitoides = X_all['litologia_u011_fraccion'] + X_all['litologia_u015_fraccion'] + X_all['litologia_u014_fraccion']
X_all['plutonismo_varisco'] = (granitoides * hercinico).astype('float32')
X_all['prox_termica_varisca'] = (np.exp(-X_all['dist_contacto_intrusivo_cartografiada_m'] / 15000.0) * (hercinico + X_all['edades_u013_fraccion'])).astype('float32')

neogeno = X_all['edades_u011_fraccion'] + X_all['edades_u012_fraccion'] + X_all['edades_u016_fraccion']
X_all['volcanismo_neogeno'] = (X_all['litologia_u019_fraccion'] * neogeno).astype('float32')

f_comp = X_all['litologia_u008_fraccion'] + X_all['litologia_u010_fraccion'] + X_all['litologia_u011_fraccion'] + X_all['litologia_u015_fraccion'] + X_all['litologia_u000_fraccion']
f_incomp = X_all['litologia_u016_fraccion'] + X_all['litologia_u013_fraccion'] + X_all['litologia_u001_fraccion']
X_all['contraste_reologico'] = (4.0 * f_comp * f_incomp).astype('float32')
X_all['trampa_estructural_reologica'] = (np.exp(-X_all['dist_falla_cartografiada_m'] / 5000.0) * X_all['contraste_reologico']).astype('float32')

df_grav = pd.read_parquet(ROOT / 'reports/reentrenamiento_gravimetria_20261021/favorabilidad_nacional_gravimetria.parquet').set_index('cell_id')
X_all['bouguer_gradiente'] = df_grav.loc[X_all.index, 'bouguer_gradiente_mgal_km'].astype('float32')
X_all['bouguer_residual_local_zscore'] = df_grav.loc[X_all.index, 'bouguer_residual_local_zscore'].astype('float32')

df_mag = pd.read_parquet(ROOT / 'reports/reentrenamiento_aeromagnetometria_20261021/favorabilidad_nacional_aeromagnetometria.parquet').set_index('cell_id')
X_all['magnetometria_gradiente'] = df_mag.loc[X_all.index, 'magnetometria_gradiente_nt_km'].astype('float32')
X_all['magnetometria_residual_local_zscore'] = df_mag.loc[X_all.index, 'magnetometria_residual_local_zscore'].astype('float32')

X_all['dens_falla_1000m'] = df_raw.loc[X_all.index, 'dens_aprox_falla_cartografiada_1000m_km_km2'].astype('float32')
p_falla = np.exp(-np.nan_to_num(X_all['dist_falla_cartografiada_m'], nan=15000.0) / 3000.0)
p_cabalg = np.exp(-np.nan_to_num(X_all['dist_cabalgamiento_cartografiada_m'], nan=15000.0) / 3000.0)
X_all['nodo_dilatacion_falla_cabalgamiento'] = (p_falla * p_cabalg).astype('float32')
X_all['trampa_dilatacional_reologica'] = (X_all['dens_falla_1000m'] * X_all['contraste_reologico']).astype('float32')
X_all['acoplamiento_sutura_falla'] = (X_all['bouguer_gradiente'] * p_falla).astype('float32')

df_sat = pd.read_parquet(ROOT / 'data/raw/satelite_mcd43a4/variables_alteracion_hidrotermal.parquet').set_index('cell_id')
X_all['ratio_alteracion_filica_swir'] = df_sat.loc[X_all.index, 'ratio_alteracion_filica_swir'].astype('float32')
X_all['ratio_gossan_oxidos_hierro'] = df_sat.loc[X_all.index, 'ratio_gossan_oxidos_hierro'].astype('float32')
X_all['ndvi_cobertura_vegetal'] = df_sat.loc[X_all.index, 'ndvi_cobertura_vegetal'].astype('float32')
X_all['anomalia_hidrotermal_multiespectral_zscore'] = df_sat.loc[X_all.index, 'anomalia_hidrotermal_multiespectral_zscore'].astype('float32')

# Geoquimica continua
import rasterio
from scipy.ndimage import gaussian_filter
rows = np.array([int(c.split('_r')[1].split('_c')[0]) for c in X_all.index])
cols = np.array([int(c.split('_c')[1]) for c in X_all.index])

elements = ['As', 'Sb', 'Bi', 'Cu', 'Hg', 'W', 'Pb', 'Zn']
for elem in elements:
    ds = rasterio.open(ROOT / f'AtlasGeoquimico_{elem}_Sedimentos_2012.tif')
    b = ds.read(2)
    b[b <= 0] = np.nan
    b_1km = np.nanmean([b[0::2, 0::2], b[1::2, 0::2], b[0::2, 1::2], b[1::2, 1::2]], axis=0)
    vals = b_1km[rows, cols]
    med = np.nanmedian(vals)
    vals = np.where(np.isnan(vals), med, vals)
    log_vals = np.log10(np.maximum(vals, 1e-3) + 1.0).astype('float32')
    X_all[f'geoq_{elem.lower()}_concentracion_log'] = log_vals

z_as = (X_all['geoq_as_concentracion_log'] - X_all['geoq_as_concentracion_log'].mean()) / X_all['geoq_as_concentracion_log'].std()
z_sb = (X_all['geoq_sb_concentracion_log'] - X_all['geoq_sb_concentracion_log'].mean()) / X_all['geoq_sb_concentracion_log'].std()
z_bi = (X_all['geoq_bi_concentracion_log'] - X_all['geoq_bi_concentracion_log'].mean()) / X_all['geoq_bi_concentracion_log'].std()
z_w  = (X_all['geoq_w_concentracion_log'] - X_all['geoq_w_concentracion_log'].mean()) / X_all['geoq_w_concentracion_log'].std()
X_all['indice_pathfinders_oro'] = (z_as + z_sb + 0.8 * z_bi + 0.5 * z_w).astype('float32')

grid_as_sb = np.full((910, 1100), np.nan, dtype='float32')
grid_as_sb[rows, cols] = (z_as + z_sb).values
valid = ~np.isnan(grid_as_sb)
clean = np.where(valid, grid_as_sb, 0.0)
norm = np.where(valid, 1.0, 0.0)
smooth = gaussian_filter(clean, sigma=25)
weights = gaussian_filter(norm, sigma=25)
local_mean = np.where(weights > 0.01, smooth / weights, 0.0)
res_as_sb = grid_as_sb[rows, cols] - local_mean[rows, cols]
X_all['anomalia_local_as_sb_zscore'] = np.clip(res_as_sb, -4.0, 4.0).astype('float32')

print(f"Total features disponibles en X_all: {len(X_all.columns)}")

# Definicion de los 4 Pilares del Sistema Mineral:
chem_cols = list(data.config['geochemical_columns'])

pilar_geoq = [c for c in X_all.columns if c.startswith('geoq_') or c in ['indice_pathfinders_oro', 'anomalia_local_as_sb_zscore'] or c in chem_cols]

pilar_struct = [
    'bouguer_gradiente', 'bouguer_residual_local_zscore', 'dens_falla_1000m',
    'dist_falla_cartografiada_m', 'dist_cabalgamiento_cartografiada_m',
    'nodo_dilatacion_falla_cabalgamiento', 'trampa_dilatacional_reologica',
    'acoplamiento_sutura_falla', 'contraste_reologico', 'trampa_estructural_reologica'
]

pilar_mag_alt = [
    'plutonismo_varisco', 'prox_termica_varisca', 'dist_contacto_intrusivo_cartografiada_m',
    'volcanismo_neogeno', 'ratio_alteracion_filica_swir', 'ratio_gossan_oxidos_hierro',
    'anomalia_hidrotermal_multiespectral_zscore', 'ndvi_cobertura_vegetal',
    'magnetometria_gradiente', 'magnetometria_residual_local_zscore'
]

pilar_lito_topo = [c for c in X_all.columns if c not in pilar_geoq and c not in pilar_struct and c not in pilar_mag_alt]

print(f"Pilar Geoquimica: {len(pilar_geoq)} vars")
print(f"Pilar Estructura y Vias: {len(pilar_struct)} vars")
print(f"Pilar Magmatismo y Alteracion: {len(pilar_mag_alt)} vars")
print(f"Pilar Litologia y Entorno: {len(pilar_lito_topo)} vars")

def build_branch_model(cols, chem_subset, seed, n_est=120, max_d=4):
    clf = lgb.LGBMClassifier(
        n_estimators=n_est, max_depth=max_d, num_leaves=16, learning_rate=0.04,
        reg_alpha=0.5, reg_lambda=1.0, min_child_samples=15, colsample_bytree=0.8,
        verbosity=-1, n_jobs=2, random_state=seed
    )
    return Pipeline([('preprocess', make_preprocessor(cols, chemical=chem_subset)), ('model', clf)])

# Evaluacion en las 7 rotaciones
rot_results_monolith = []
rot_results_fuzzy_or = []
rot_results_mean = []
rot_results_geoq_dominant = []

for group in range(7):
    districts = design['district_groups'][str(group)]
    saved_held = pd.read_parquet(base / f'partitions/rotation_{group}_held.parquet')
    ref_train = pd.read_parquet(base / f'partitions/rotation_{group}_sample.parquet')
    
    p_train = ref_train[ref_train.label == 1]
    u_pool = ref_train[ref_train.label == 0]
    
    test_held_cells = saved_held.cell_id
    preds_mono = np.zeros(len(test_held_cells), dtype='float32')
    preds_p_geoq = np.zeros(len(test_held_cells), dtype='float32')
    preds_p_struct = np.zeros(len(test_held_cells), dtype='float32')
    preds_p_magalt = np.zeros(len(test_held_cells), dtype='float32')
    preds_p_lito = np.zeros(len(test_held_cells), dtype='float32')
    
    # 4 bags por rotacion para rapidez de test
    n_bags = 4
    for b in range(n_bags):
        u_sample = u_pool.sample(n=3*len(p_train), random_state=42 + group*1000 + b*101, replace=True)
        train_df = pd.concat([p_train, u_sample])
        weights = train_df.peso_confianza
        train_cells = train_df.cell_id
        
        # 1. Monolito
        all_cols = list(X_all.columns)
        m_mono = build_branch_model(all_cols, chem_cols, 42 + b, n_est=150, max_d=5)
        m_mono.fit(X_all.loc[train_cells, all_cols], train_df.label, model__sample_weight=weights)
        preds_mono += predict(m_mono, X_all.loc[test_held_cells, all_cols], 10000)
        
        # 2. Ramas desacopladas
        m_g = build_branch_model(pilar_geoq, [c for c in chem_cols if c in pilar_geoq], 42 + b)
        m_g.fit(X_all.loc[train_cells, pilar_geoq], train_df.label, model__sample_weight=weights)
        preds_p_geoq += predict(m_g, X_all.loc[test_held_cells, pilar_geoq], 10000)
        
        m_s = build_branch_model(pilar_struct, [], 42 + b)
        m_s.fit(X_all.loc[train_cells, pilar_struct], train_df.label, model__sample_weight=weights)
        preds_p_struct += predict(m_s, X_all.loc[test_held_cells, pilar_struct], 10000)
        
        m_m = build_branch_model(pilar_mag_alt, [], 42 + b)
        m_m.fit(X_all.loc[train_cells, pilar_mag_alt], train_df.label, model__sample_weight=weights)
        preds_p_magalt += predict(m_m, X_all.loc[test_held_cells, pilar_mag_alt], 10000)
        
        m_l = build_branch_model(pilar_lito_topo, [], 42 + b)
        m_l.fit(X_all.loc[train_cells, pilar_lito_topo], train_df.label, model__sample_weight=weights)
        preds_p_lito += predict(m_l, X_all.loc[test_held_cells, pilar_lito_topo], 10000)
        
    preds_mono /= n_bags
    preds_p_geoq /= n_bags
    preds_p_struct /= n_bags
    preds_p_magalt /= n_bags
    preds_p_lito /= n_bags
    
    # Operador Difuso / Probabilistic OR:
    # Favorabilidad = 1 - (1 - S_geoq) * (1 - S_struct) * (1 - S_magalt)
    score_fuzzy_or = 1.0 - (1.0 - preds_p_geoq) * (1.0 - preds_p_struct) * (1.0 - preds_p_magalt)
    
    # Media ponderada geocientifica:
    score_mean = 0.35 * preds_p_geoq + 0.25 * preds_p_struct + 0.25 * preds_p_magalt + 0.15 * preds_p_lito
    
    # Geoquimica dominante modulada por via estructural/termica:
    score_geoq_dom = preds_p_geoq * (0.5 + 0.5 * np.maximum(preds_p_struct, preds_p_magalt))
    
    rel = data.records.loc[data.records.district_id.isin(districts)].dropna(subset=['deposit_id'])[['cell_id', 'deposit_id', 'district_id']].drop_duplicates()
    
    _, d_mono, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': test_held_cells, 'score': preds_mono}))
    _, d_for, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': test_held_cells, 'score': score_fuzzy_or}))
    _, d_mean, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': test_held_cells, 'score': score_mean}))
    _, d_gdom, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': test_held_cells, 'score': score_geoq_dom}))
    
    rot_results_monolith.append(d_mono.assign(group=group))
    rot_results_fuzzy_or.append(d_for.assign(group=group))
    rot_results_mean.append(d_mean.assign(group=group))
    rot_results_geoq_dominant.append(d_gdom.assign(group=group))
    print(f"Grupo {group} evaluado...")

def summarize(dfs, name):
    df_all = pd.concat(dfs, ignore_index=True)
    n = df_all.deposit_id.nunique()
    c01 = df_all.loc[df_all.captured_at_01, 'deposit_id'].nunique()
    c05 = df_all.loc[df_all.captured_at_05, 'deposit_id'].nunique()
    c10 = df_all.loc[df_all.captured_at_10, 'deposit_id'].nunique()
    c20 = df_all.loc[df_all.captured_at_20, 'deposit_id'].nunique()
    print(f"\n{name} (Total: {n}):")
    print(f"  Top  1% Ciego: {c01:>2} ({c01/n*100:.1f}%)")
    print(f"  Top  5% Ciego: {c05:>2} ({c05/n*100:.1f}%)")
    print(f"  Top 10% Ciego: {c10:>2} ({c10/n*100:.1f}%)")
    print(f"  Top 20% Ciego: {c20:>2} ({c20/n*100:.1f}%)")

summarize(rot_results_monolith, "1. MONOLITO BASE (NB 25)")
summarize(rot_results_fuzzy_or, "2. DESACOPLADO (PROBABILISTIC OR)")
summarize(rot_results_mean, "3. DESACOPLADO (MEDIA PONDERADA DE PILARES)")
summarize(rot_results_geoq_dominant, "4. DESACOPLADO (GEOQUIMICA MODULADA)")
