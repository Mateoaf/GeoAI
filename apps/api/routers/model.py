"""
apps/api/routers/model.py
Rutas para consulta de coeficientes del modelo de producción e hiperparámetros.
"""

from fastapi import APIRouter

from ..data_loader import get_data_loader

router = APIRouter(tags=["Model Architecture & Coefficients"])

@router.get("/api/model/coefficients")
def get_model_coefficients():
    loader = get_data_loader()
    df = loader.coefficients_df.copy()
    items = df.to_dict(orient="records")
    return {
        "model_id": "logistic_01",
        "family": "Logistic Regression L2",
        "intercept": float(loader.model.named_steps["model"].intercept_[0]),
        "total_variables": len(items),
        "odds_ratio_interpretation": "exp(beta) representa el cambio multiplicativo en odds por incremento de 1 desviación estándar (+1 sigma) de la variable tras StandardScaler.",
        "coefficients": items
    }


@router.get("/api/model/summary")
def get_model_summary():
    loader = get_data_loader()
    return {
        "model_metadata": loader.model_meta,
        "pipeline_steps": [
            {"step": "guard", "class": "FeatureGuard", "description": "Garantiza orden exacto y 56 columnas aprobadas."},
            {"step": "preprocess", "class": "ColumnTransformer", "description": "SimpleImputer(strategy='median') + StandardScaler()"},
            {"step": "model", "class": "LogisticRegression", "description": "penalty='l2', C=0.1, solver='lbfgs', max_iter=3000"}
        ]
    }
