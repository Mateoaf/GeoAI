"""
apps/api/services/explain_service.py
Motor de Explicabilidad Aditiva Local Exacta (beta * z) para GeoAI-Au Explorer.
"""

from typing import Optional

import numpy as np
import pandas as pd

from ..data_loader import get_data_loader
from ..schemas.explain import CellExplanation, FeatureContribution


class ExplainService:
    _instance: Optional["ExplainService"] = None

    def __init__(self):
        self.data_loader = get_data_loader()
        self.model = self.data_loader.model
        self.approved_columns = self.data_loader.approved_columns
        self.coefs_dict = self.data_loader.coefficients_df.set_index("variable").to_dict(orient="index")
        self.feature_dict = self.data_loader.feature_dictionary

        # Extraer componentes del pipeline de scikit-learn
        self.guard = self.model.named_steps["guard"]
        self.preprocess = self.model.named_steps["preprocess"]
        self.clf = self.model.named_steps["model"]

        self.intercept = float(self.clf.intercept_[0])
        self.model_coefs = self.clf.coef_[0]

    @classmethod
    def get_instance(cls) -> "ExplainService":
        if cls._instance is None:
            cls._instance = ExplainService()
        return cls._instance

    def explain_cell(self, cell_id: str) -> CellExplanation | None:
        """Calcula la descomposición aditiva exacta logit(x) = intercept + sum(beta_i * z_i)."""
        if self.data_loader.features_df is None or cell_id not in self.data_loader.features_df.index:
            return None

        cell_meta = self.data_loader.get_cell_info(cell_id)
        if not cell_meta:
            return None

        # 1. Recuperar vector bruto de 56 características
        row_series = self.data_loader.features_df.loc[cell_id]
        X_df = pd.DataFrame([row_series[self.approved_columns]])

        # 2. Aplicar guard y preprocesamiento (SimpleImputer + StandardScaler)
        X_guarded = self.guard.transform(X_df)
        X_trans = self.preprocess.transform(X_guarded)
        z_vector = X_trans[0]

        # 3. Cálculo de contribuciones locales: beta_i * z_i
        contributions = self.model_coefs * z_vector
        logit_calc = self.intercept + float(np.sum(contributions))
        logit_decision = float(self.clf.decision_function(X_trans)[0])
        error = abs(logit_calc - logit_decision)
        test_passed = error < 1e-6

        # Score sigmoide
        sigmoid_val = 1.0 / (1.0 + np.exp(-logit_calc))
        prospectivity_score = float(cell_meta["score"])

        # 4. Construir lista de contribuciones detalladas
        all_contribs: list[FeatureContribution] = []
        for i, col_name in enumerate(self.approved_columns):
            raw_val = float(X_df.iloc[0, i]) if not pd.isna(X_df.iloc[0, i]) else 0.0
            z_val = float(z_vector[i])
            beta_val = float(self.model_coefs[i])
            contrib_val = float(contributions[i])

            coef_meta = self.coefs_dict.get(col_name, {})
            familia = coef_meta.get("familia", "General")
            odds_ratio = float(coef_meta.get("odds_ratio", np.exp(beta_val)))
            significado = coef_meta.get("significado_geologico", col_name)

            all_contribs.append(
                FeatureContribution(
                    variable=col_name,
                    familia=familia,
                    raw_value=round(raw_val, 4),
                    standardized_z=round(z_val, 4),
                    coefficient=round(beta_val, 4),
                    contribution=round(contrib_val, 4),
                    odds_ratio=round(odds_ratio, 3),
                    significado_geologico=significado
                )
            )

        # 5. Ordenar por contribución local
        positives = sorted([c for c in all_contribs if c.contribution > 0], key=lambda x: x.contribution, reverse=True)
        negatives = sorted([c for c in all_contribs if c.contribution < 0], key=lambda x: x.contribution)

        return CellExplanation(
            cell_id=cell_id,
            prospectivity_score=round(prospectivity_score, 5),
            intercept=round(self.intercept, 6),
            logit_calculated=round(logit_calc, 6),
            logit_decision_function=round(logit_decision, 6),
            consistency_error=float(f"{error:.2e}"),
            consistency_test_passed=test_passed,
            sigmoid_score=round(sigmoid_val, 5),
            top_positive_contributions=positives[:10],
            top_negative_contributions=negatives[:10],
            all_contributions=sorted(all_contribs, key=lambda x: abs(x.contribution), reverse=True)
        )


def get_explain_service() -> ExplainService:
    return ExplainService.get_instance()
