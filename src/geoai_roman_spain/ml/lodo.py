"""
Validación Leave-One-District-Out (LODO).
Evalúa la capacidad de generalización y transferencia del modelo entrenando en N-1 provincias
metalogénicas y evaluando a ciegas sobre el distrito reservado.
"""
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from .spatial_cv import evaluate_fold_metrics

# Definición espacial de distritos y provincias metalogénicas de Hispania
DISTRICT_DEFINITIONS = {
    "Noroeste_Galaico_Leones": {
        "name": "Noroeste Galaico-Leonés (Au orogénico / Las Médulas, Salave, Teleno)",
        "bounds_wgs84": {"lat_min": 41.5, "lat_max": 43.8, "lng_min": -9.3, "lng_max": -5.2}
    },
    "Faja_Piritica_Iberica": {
        "name": "Faja Pirítica Ibérica (Cu-VMS / Riotinto, Tharsis, Aznalcóllar)",
        "bounds_wgs84": {"lat_min": 37.0, "lat_max": 38.2, "lng_min": -8.5, "lng_max": -5.8}
    },
    "Sierra_Morena_Linares": {
        "name": "Sierra Morena / Linares-La Carolina (Pb-Ag filoniano / Los Pedroches)",
        "bounds_wgs84": {"lat_min": 38.0, "lat_max": 39.0, "lng_min": -5.5, "lng_max": -3.0}
    },
    "Sureste_Betico": {
        "name": "Sureste Bético / Mazarrón-Rodalquilar (Au-Ag-Pb epitermal neógeno)",
        "bounds_wgs84": {"lat_min": 36.5, "lat_max": 38.0, "lng_min": -3.0, "lng_max": -0.5}
    },
    "Zona_Centroiberica": {
        "name": "Zona Centroibérica / Sistema Central (Filones de Cuarzo-Sulfuros)",
        "bounds_wgs84": {"lat_min": 39.5, "lat_max": 41.5, "lng_min": -7.0, "lng_max": -3.5}
    }
}

def assign_metallogenic_districts(df: pd.DataFrame) -> pd.Series:
    """Asigna a cada coordenada su provincia metalogénica correspondiente."""
    districts = pd.Series("Otras_Regiones_Indiferenciadas", index=df.index)
    
    for dist_id, spec in DISTRICT_DEFINITIONS.items():
        b = spec["bounds_wgs84"]
        mask = (
            (df['latitude'] >= b['lat_min']) & (df['latitude'] <= b['lat_max']) &
            (df['longitude'] >= b['lng_min']) & (df['longitude'] <= b['lng_max'])
        )
        districts[mask] = dist_id
        
    return districts

def run_lodo_benchmark(df: pd.DataFrame, target_col: str = 'target_class', seed: int = 42) -> dict:
    """
    Ejecuta el experimento Leave-One-District-Out completo.
    """
    df_lodo = df.copy()
    df_lodo['district'] = assign_metallogenic_districts(df_lodo)
    
    candidate_num = [
        'Real_Elevation_MDT_m', 'Real_Slope_Deg', 'Real_TPI_1km', 'Real_TRI_Roughness',
        'Real_IGME_Dist_Fault_m', 'Real_IGME_Dist_Contact_m', 'Real_IGME_Fault_Length_Density_5km'
    ]
    features_num = [c for c in candidate_num if c in df_lodo.columns and df_lodo[c].notna().sum() == len(df_lodo)]
    features_cat = ['Real_IGME_Lithology_General', 'Real_IGME_Era', 'Real_IGME_Dominio']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), features_num),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), features_cat)
        ]
    )
    
    lodo_results = {}
    
    for dist_id, spec in DISTRICT_DEFINITIONS.items():
        test_mask = (df_lodo['district'] == dist_id)
        train_mask = ~test_mask
        
        n_test_pos = int(df_lodo.loc[test_mask, target_col].sum())
        n_test_bg = int((df_lodo.loc[test_mask, target_col] == 0).sum())
        n_train_pos = int(df_lodo.loc[train_mask, target_col].sum())
        
        # Clasificación de robustez muestral
        status = "ROBUST" if n_test_pos >= 15 else "EXPLORATORY_LOW_N"
        
        if n_test_pos == 0 or n_test_bg == 0:
            lodo_results[dist_id] = {
                "district_name": spec["name"],
                "status": "INSUFFICIENT_DATA",
                "n_train_pos": n_train_pos,
                "n_test_pos": n_test_pos,
                "n_test_bg": n_test_bg,
                "metrics": None
            }
            continue
            
        X_train = df_lodo.loc[train_mask, features_num + features_cat]
        y_train = df_lodo.loc[train_mask, target_col].values
        X_test = df_lodo.loc[test_mask, features_num + features_cat]
        y_test = df_lodo.loc[test_mask, target_col].values
        
        pipe = Pipeline([
            ('prep', preprocessor),
            ('clf', LGBMClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=seed, verbose=-1))
        ])
        
        pipe.fit(X_train, y_train)
        probs = pipe.predict_proba(X_test)[:, 1]
        
        metrics = evaluate_fold_metrics(y_test, probs)
        
        lodo_results[dist_id] = {
            "district_name": spec["name"],
            "status": status,
            "n_train_pos": n_train_pos,
            "n_test_pos": n_test_pos,
            "n_test_bg": n_test_bg,
            "metrics": metrics
        }
        
    return lodo_results
