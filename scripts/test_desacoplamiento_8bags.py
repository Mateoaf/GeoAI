"""
Test de ajuste fino de la fusion del Ensamble Desacoplado por Sistema Mineral:
1. Max de los 3 expertos
2. Ensamble suave (Soft Mixture of Experts)
3. Fusion Difusa (Fuzzy Gamma Operator)
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

# Construir X_all completo
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

# Nuevas variables diagnosticas
X_all['trampa_valle_aluvial'] = (np.exp(-X_all['dist_cauce_m'] / 300.0) * np.exp(-X_all['pendiente_grados'] / 6.0)).astype('float32')
X_all['vector_epitermal_hidrotermal'] = (np.maximum(X_all['volcanismo_neogeno'], 0.1) * X_all['ratio_alteracion_filica_swir'] * X_all['ratio_gossan_oxidos_hierro']).astype('float32')

features_nb26 = list(X_all.columns)
chem_cols = list(data.config['geochemical_columns'])

rec = data.records.dropna(subset=['cell_id'])
aluvial_cells = set(rec[rec.tipo_au_revisado == 'aluvial'].cell_id)
epitermal_cells = set(rec[(rec.district_id == 'dist_cabo_de_gata') | (rec.Provincia.isin(['ALMERIA', 'GRANADA']))].cell_id)
roca_cells = set(rec[rec.tipo_au_revisado == 'roca'].cell_id) - epitermal_cells

def make_model(seed, max_d=5, n_est=150):
    classifier = lgb.LGBMClassifier(
        n_estimators=n_est, max_depth=max_d, num_leaves=24, learning_rate=0.04,
        reg_alpha=0.5, reg_lambda=1.0, min_child_samples=12, colsample_bytree=0.7,
        verbosity=-1, n_jobs=2, random_state=seed
    )
    return Pipeline([('preprocess', make_preprocessor(features_nb26, chem_cols)), ('model', classifier)])

# Evaluar 8 bags completos por rotacion
rot_opt_a = []
rot_opt_b = []
rot_opt_c = []

for group in range(7):
    districts = design['district_groups'][str(group)]
    saved_held = pd.read_parquet(base / f'partitions/rotation_{group}_held.parquet')
    ref_train = pd.read_parquet(base / f'partitions/rotation_{group}_sample.parquet')
    
    p_train = ref_train[ref_train.label == 1]
    u_pool = ref_train[ref_train.label == 0]
    
    p_roca = p_train[p_train.cell_id.isin(roca_cells)]
    p_aluv = p_train[p_train.cell_id.isin(aluvial_cells)]
    p_epith = p_train[p_train.cell_id.isin(epitermal_cells)]
    p_resto = p_train[~p_train.cell_id.isin(roca_cells) & ~p_train.cell_id.isin(aluvial_cells) & ~p_train.cell_id.isin(epitermal_cells)]
    p_roca = pd.concat([p_roca, p_resto])
    
    test_X = X_all.loc[saved_held.cell_id, features_nb26]
    preds_mono = np.zeros(len(test_X), dtype='float32')
    preds_roca = np.zeros(len(test_X), dtype='float32')
    preds_aluv = np.zeros(len(test_X), dtype='float32')
    preds_epith = np.zeros(len(test_X), dtype='float32')
    
    n_bags = 8
    for b in range(n_bags):
        # Monolito
        u_sample = u_pool.sample(n=3*len(p_train), random_state=42 + group*1000 + b*101, replace=True)
        train_mono = pd.concat([p_train, u_sample])
        m_mono = make_model(42 + b)
        m_mono.fit(X_all.loc[train_mono.cell_id, features_nb26], train_mono.label, model__sample_weight=train_mono.peso_confianza)
        preds_mono += predict(m_mono, test_X, 10000)
        
        # Orogenico / Roca
        u_roca = u_pool.sample(n=3*len(p_roca), random_state=142 + group*1000 + b*101, replace=True)
        train_roca = pd.concat([p_roca, u_roca])
        m_roca = make_model(142 + b)
        m_roca.fit(X_all.loc[train_roca.cell_id, features_nb26], train_roca.label, model__sample_weight=train_roca.peso_confianza)
        preds_roca += predict(m_roca, test_X, 10000)
        
        # Aluvial
        u_aluv = u_pool.sample(n=3*len(p_aluv), random_state=242 + group*1000 + b*101, replace=True)
        train_aluv = pd.concat([p_aluv, u_aluv])
        m_aluv = make_model(242 + b)
        m_aluv.fit(X_all.loc[train_aluv.cell_id, features_nb26], train_aluv.label, model__sample_weight=train_aluv.peso_confianza)
        preds_aluv += predict(m_aluv, test_X, 10000)
        
        # Epitermal
        if len(p_epith) >= 2:
            u_epith = u_pool.sample(n=5*len(p_epith), random_state=342 + group*1000 + b*101, replace=True)
            train_epith = pd.concat([p_epith, u_epith])
            m_epith = make_model(342 + b, max_d=3, n_est=80)
            m_epith.fit(X_all.loc[train_epith.cell_id, features_nb26], train_epith.label, model__sample_weight=train_epith.peso_confianza)
            preds_epith += predict(m_epith, test_X, 10000)
        else:
            v_sat = X_all.loc[saved_held.cell_id, 'ratio_alteracion_filica_swir'] * X_all.loc[saved_held.cell_id, 'ratio_gossan_oxidos_hierro']
            v_geoq = np.maximum(X_all.loc[saved_held.cell_id, 'geoq_sb_concentracion_log'], 0) + np.maximum(X_all.loc[saved_held.cell_id, 'geoq_as_concentracion_log'], 0)
            preds_epith += (v_sat * v_geoq * (1.0 + 3.0 * X_all.loc[saved_held.cell_id, 'volcanismo_neogeno'])).values
            
    preds_mono /= n_bags
    preds_roca /= n_bags
    preds_aluv /= n_bags
    preds_epith /= n_bags
    preds_epith = (preds_epith - preds_epith.min()) / (preds_epith.max() - preds_epith.min() + 1e-6)
    
    # Opcion A: Max de los 3 expertos
    s_a = np.maximum(np.maximum(preds_roca, preds_aluv), preds_epith * 0.7)
    
    # Opcion B: Fusion Probabilistica (Unión OR de los 3 sistemas)
    s_b = 1.0 - (1.0 - preds_roca) * (1.0 - preds_aluv) * (1.0 - preds_epith * 0.6)
    
    # Opcion C: Meta-Ensamble Balanceado (Monolito + Max Tipológico)
    s_c = 0.4 * preds_mono + 0.6 * np.maximum(np.maximum(preds_roca, preds_aluv), preds_epith * 0.7)
    
    rel = data.records.loc[data.records.district_id.isin(districts)].dropna(subset=['deposit_id'])[['cell_id', 'deposit_id', 'district_id']].drop_duplicates()
    _, d_a, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': saved_held.cell_id, 'score': s_a}))
    _, d_b, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': saved_held.cell_id, 'score': s_b}))
    _, d_c, _ = deposit_metrics(rel, pd.DataFrame({'cell_id': saved_held.cell_id, 'score': s_c}))
    
    rot_opt_a.append(d_a.assign(group=group))
    rot_opt_b.append(d_b.assign(group=group))
    rot_opt_c.append(d_c.assign(group=group))
    print(f"Grupo {group} (8 bags) completado...")

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

report(rot_opt_a, "OPCIÓN A: MAX DE 3 SISTEMAS (OROGÉNICO, ALUVIAL, EPITERMAL)")
report(rot_opt_b, "OPCIÓN B: UNIÓN PROBABILÍSTICA OR DE 3 SISTEMAS")
report(rot_opt_c, "OPCIÓN C: META-ENSAMBLE BALANCEADO (GLOBAL + 3 SISTEMAS)")
