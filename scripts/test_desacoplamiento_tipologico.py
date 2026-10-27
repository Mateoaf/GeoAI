"""
Test de Desacoplamiento Tipologico: Oro en Roca (Primario) vs Oro Aluvial (Secundario/Placeres).
Evalua en las 7 rotaciones territoriales ciegas.
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

# Construir X_all completo con 93 variables como en NB 25
df_raw = pd.read_parquet(ROOT / 'reports/fase_d/20260923T211448_267684Z/X_features.parquet').set_index('cell_id')
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

features_nb25 = list(X_all.columns)
chem_cols = list(data.config['geochemical_columns'])

# Mapeo de celdas a tipo_au
rec = data.records.dropna(subset=['cell_id'])
roca_cells = set(rec[rec.tipo_au_revisado == 'roca'].cell_id)
aluvial_cells = set(rec[rec.tipo_au_revisado == 'aluvial'].cell_id)

def make_model(seed, max_d=5, n_est=150):
    classifier = lgb.LGBMClassifier(
        n_estimators=n_est, max_depth=max_d, num_leaves=24, learning_rate=0.04,
        reg_alpha=0.5, reg_lambda=1.0, min_child_samples=15, colsample_bytree=0.7,
        verbosity=-1, n_jobs=2, random_state=seed
    )
    return Pipeline([('preprocess', make_preprocessor(features_nb25, chem_cols)), ('model', classifier)])

rot_mono = []
rot_decoupled_max = []
rot_decoupled_por = []

for group in range(7):
    districts = design['district_groups'][str(group)]
    saved_held = pd.read_parquet(base / f'partitions/rotation_{group}_held.parquet')
    ref_train = pd.read_parquet(base / f'partitions/rotation_{group}_sample.parquet')
    
    p_train = ref_train[ref_train.label == 1]
    u_pool = ref_train[ref_train.label == 0]
    
    p_roca = p_train[p_train.cell_id.isin(roca_cells)]
    p_aluvial = p_train[p_train.cell_id.isin(aluvial_cells)]
    p_resto = p_train[~p_train.cell_id.isin(roca_cells) & ~p_train.cell_id.isin(aluvial_cells)]
    p_roca = pd.concat([p_roca, p_resto])
    
    test_X = X_all.loc[saved_held.cell_id, features_nb25]
    preds_mono = np.zeros(len(test_X), dtype='float32')
    preds_roca = np.zeros(len(test_X), dtype='float32')
    preds_aluvial = np.zeros(len(test_X), dtype='float32')
    
    n_bags = 4
    for b in range(n_bags):
        # 1. Monolito
        u_sample = u_pool.sample(n=3*len(p_train), random_state=42 + group*1000 + b*101, replace=True)
        train_df = pd.concat([p_train, u_sample])
        m_mono = make_model(42 + b)
        m_mono.fit(X_all.loc[train_df.cell_id, features_nb25], train_df.label, model__sample_weight=train_df.peso_confianza)
        preds_mono += predict(m_mono, test_X, 10000)
        
        # 2. Experto Oro en Roca
        u_roca = u_pool.sample(n=3*len(p_roca), random_state=142 + group*1000 + b*101, replace=True)
        train_roca = pd.concat([p_roca, u_roca])
        m_roca = make_model(142 + b)
        m_roca.fit(X_all.loc[train_roca.cell_id, features_nb25], train_roca.label, model__sample_weight=train_roca.peso_confianza)
        preds_roca += predict(m_roca, test_X, 10000)
        
        # 3. Experto Oro Aluvial
        u_aluvial = u_pool.sample(n=3*len(p_aluvial), random_state=242 + group*1000 + b*101, replace=True)
        train_aluvial = pd.concat([p_aluvial, u_aluvial])
        m_aluvial = make_model(242 + b)
        m_aluvial.fit(X_all.loc[train_aluvial.cell_id, features_nb25], train_aluvial.label, model__sample_weight=train_aluvial.peso_confianza)
        preds_aluvial += predict(m_aluvial, test_X, 10000)
        
    preds_mono /= n_bags
    preds_roca /= n_bags
    preds_aluvial /= n_bags
    
    # Combinaciones desacopladas
    score_max = np.maximum(preds_roca, preds_aluvial)
    score_por = 1.0 - (1.0 - preds_roca) * (1.0 - preds_aluvial)
    
    rel = data.records.loc[data.records.district_id.isin(districts)].dropna(subset=['deposit_id'])[['cell_id', 'deposit_id', 'district_id']].drop_duplicates()
    _, d_m, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': saved_held.cell_id, 'score': preds_mono}))
    _, d_mx, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': saved_held.cell_id, 'score': score_max}))
    _, d_po, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': saved_held.cell_id, 'score': score_por}))
    
    rot_mono.append(d_m.assign(group=group))
    rot_decoupled_max.append(d_mx.assign(group=group))
    rot_decoupled_por.append(d_po.assign(group=group))
    print(f"Grupo {group} completado...")

def report(dfs, name):
    df_all = pd.concat(dfs, ignore_index=True)
    n = df_all.deposit_id.nunique()
    c01 = df_all.loc[df_all.captured_at_01, 'deposit_id'].nunique()
    c05 = df_all.loc[df_all.captured_at_05, 'deposit_id'].nunique()
    c10 = df_all.loc[df_all.captured_at_10, 'deposit_id'].nunique()
    c20 = df_all.loc[df_all.captured_at_20, 'deposit_id'].nunique()
    print(f"\n{name} (Total depósitos: {n}):")
    print(f"  Top  1% Ciego: {c01:>2} ({c01/n*100:.1f}%)")
    print(f"  Top  5% Ciego: {c05:>2} ({c05/n*100:.1f}%)")
    print(f"  Top 10% Ciego: {c10:>2} ({c10/n*100:.1f}%)")
    print(f"  Top 20% Ciego: {c20:>2} ({c20/n*100:.1f}%)")

report(rot_mono, "MONOLITO BASE (NB 25)")
report(rot_decoupled_max, "DESACOPLADO TIPOLOGICO (MAX EXPERTOS: ROCA vs ALUVIAL)")
report(rot_decoupled_por, "DESACOPLADO TIPOLOGICO (UNION PROBABILISTICA: ROCA vs ALUVIAL)")
