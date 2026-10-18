import pandas as pd
from fastapi import APIRouter

from .. import config
from ..data_loader import get_data_loader

router = APIRouter(tags=["Model Architecture & Coefficients"])

@router.get("/api/model/coefficients")
def get_model_coefficients():
    loader = get_data_loader()
    df = loader.coefficients_df.copy()
    items = df.to_dict(orient="records")
    is_64 = len(items) == 64
    return {
        "model_id": "GeoAI_64_Predictores" if is_64 else "logistic_01",
        "family": "Componente Logístico Regularizado L2 (64 Predictores)" if is_64 else "Logistic Regression L2",
        "intercept": float(loader.model.named_steps["model"].intercept_[0]),
        "total_variables": len(items),
        "numeric_variables": len(getattr(loader, "numeric_columns", [])),
        "geochemical_variables": len(getattr(loader, "geochemical_columns", [])),
        "odds_ratio_interpretation": "exp(beta) representa el cambio multiplicativo en odds por incremento de 1 desviación estándar (+1 sigma) de la variable tras preprocesamiento.",
        "coefficients": items
    }


@router.get("/api/model/summary")
def get_model_summary():
    loader = get_data_loader()
    return {
        "model_metadata": loader.model_meta,
        "pipeline_steps": [
            {"step": "preprocess", "class": "ColumnTransformer", "description": "SimpleImputer + StandardScaler (56 numéricas) y OneHotEncoder (8 clases modales geoquímicas IGME)"},
            {"step": "model", "class": "LogisticRegression", "description": "penalty='l2', solver='lbfgs', max_iter=3000"}
        ]
    }


@router.get("/api/model/geochemistry")
def get_model_geochemistry():
    loader = get_data_loader()
    cob_df = pd.DataFrame()
    if config.PATH_COBERTURA_GEOQUIMICA_CSV.exists():
        cob_df = pd.read_csv(config.PATH_COBERTURA_GEOQUIMICA_CSV)
    imp_df = pd.DataFrame()
    if config.PATH_IMPORTANCIA_GEOQUIMICA_CSV.exists():
        imp_df = pd.read_csv(config.PATH_IMPORTANCIA_GEOQUIMICA_CSV)
    ley_df = pd.DataFrame()
    if config.PATH_LEYENDAS_GEOQUIMICAS_CSV.exists():
        ley_df = pd.read_csv(config.PATH_LEYENDAS_GEOQUIMICAS_CSV)

    return {
        "geochemical_columns": getattr(loader, "geochemical_columns", []),
        "coverage": cob_df.to_dict(orient="records"),
        "importance": imp_df.to_dict(orient="records"),
        "legends": ley_df.to_dict(orient="records"),
    }
