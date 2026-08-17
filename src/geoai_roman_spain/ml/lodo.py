"""
Módulo de Validación Cruzada por Distritos (Leave-One-District-Out - LODO).
Evalúa la capacidad del modelo para generalizar sus firmas geocientíficas
en distritos mineros completamente ciegos no utilizados durante el entrenamiento.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.calibration import CalibratedClassifierCV
import lightgbm as lgb

def assign_mining_district(df: pd.DataFrame) -> pd.Series:
    """
    Asigna cada muestra a uno de los 5 grandes distritos geológico-mineros de la Península:
    1. Noroeste_Aurifero (Galicia, Asturias, León, Zamora)
    2. Faja_Piritica_Iberica (Huelva, Sevilla, Suroeste)
    3. Sierra_Morena_Linares (Jaén, Córdoba, Ciudad Real, Badajoz)
    4. Sureste_Betico (Murcia, Almería, Granada)
    5. Centro_Iberico_Meseta (Resto de zonas y cuencas)
    """
    districts = []
    for _, row in df.iterrows():
        lat = row.get('latitude', 40.0)
        lng = row.get('longitude', -4.0)
        
        if lat >= 41.5 and lng <= -5.0:
            districts.append('Noroeste_Aurifero')
        elif lat <= 38.2 and lng <= -5.8:
            districts.append('Faja_Piritica_Iberica')
        elif 37.8 <= lat <= 39.2 and -5.8 <= lng <= -2.5:
            districts.append('Sierra_Morena_Linares')
        elif lat <= 38.2 and lng >= -3.5:
            districts.append('Sureste_Betico')
        else:
            districts.append('Centro_Iberico_Meseta')
            
    return pd.Series(districts, index=df.index)

def evaluate_leave_one_district_out(
    df: pd.DataFrame,
    features_num: list,
    features_cat: list,
    target_col: str,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Ejecuta el protocolo LODO: entrena en N-1 distritos y evalúa en el distrito excluido.
    """
    all_features = features_num + features_cat
    y = df[target_col].values
    districts = assign_mining_district(df)
    unique_districts = districts.unique()
    
    results = []
    
    for test_dist in unique_districts:
        train_mask = (districts != test_dist).values
        val_mask = (districts == test_dist).values
        
        y_train, y_val = y[train_mask], y[val_mask]
        
        if len(np.unique(y_train)) < 2 or len(np.unique(y_val)) < 2:
            continue
            
        X_train = df.iloc[train_mask][all_features]
        X_val = df.iloc[val_mask][all_features]
        
        preprocessor = ColumnTransformer([
            ('num', StandardScaler(), features_num),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), features_cat)
        ])
        
        clf = lgb.LGBMClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            random_state=random_state,
            verbose=-1
        )
        
        pipeline = Pipeline([('prep', preprocessor), ('clf', clf)])
        cal = CalibratedClassifierCV(estimator=pipeline, method='isotonic', cv=3)
        cal.fit(X_train, y_train)
        
        y_prob = cal.predict_proba(X_val)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)
        
        results.append({
            'Distrito_Excluido': test_dist,
            'N_Train': int(np.sum(train_mask)),
            'N_Val': int(np.sum(val_mask)),
            'Positivos_Val': int(np.sum(y_val)),
            'ROC_AUC': round(roc_auc_score(y_val, y_prob), 4),
            'PR_AUC': round(average_precision_score(y_val, y_prob), 4),
            'Brier_Score': round(brier_score_loss(y_val, y_prob), 4),
            'F1_Score': round(f1_score(y_val, y_pred, zero_division=0), 4)
        })
        
    return pd.DataFrame(results)
