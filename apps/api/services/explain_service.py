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
        self.coefs_dict = self.data_loader.coefficients_df.set_index("variable").to_dict(orient="index") if self.data_loader.coefficients_df is not None else {}
        self.feature_dict = self.data_loader.feature_dictionary

        # Extraer componentes del pipeline de scikit-learn
        self.has_guard = "guard" in self.model.named_steps
        self.guard = self.model.named_steps.get("guard")
        self.preprocess = self.model.named_steps["preprocess"]
        self.clf = self.model.named_steps["model"]

        self.intercept = float(self.clf.intercept_[0])
        self.model_coefs = self.clf.coef_[0]

        # Mapear nombres de columnas codificadas a columnas originales
        self.feature_names_out = list(self.preprocess.get_feature_names_out())
        self.var_to_indices: dict[str, list[int]] = {}
        self.var_main_index: dict[str, int] = {}

        for idx, feat_name in enumerate(self.feature_names_out):
            if feat_name.startswith("numeric__missingindicator_"):
                orig_name = feat_name.replace("numeric__missingindicator_", "")
                self.var_to_indices.setdefault(orig_name, []).append(idx)
            elif feat_name.startswith("numeric__"):
                orig_name = feat_name.replace("numeric__", "")
                self.var_to_indices.setdefault(orig_name, []).append(idx)
                self.var_main_index[orig_name] = idx
            elif feat_name.startswith("geochemical__"):
                prefix_clean = feat_name.replace("geochemical__", "")
                parts = prefix_clean.split("_")
                orig_name = "_".join(parts[:-1]) if len(parts) >= 2 else prefix_clean
                self.var_to_indices.setdefault(orig_name, []).append(idx)
            else:
                self.var_to_indices.setdefault(feat_name, []).append(idx)
                self.var_main_index[feat_name] = idx

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

        # 1. Recuperar vector bruto de características
        row_series = self.data_loader.features_df.loc[cell_id]
        X_df = pd.DataFrame([row_series[self.approved_columns]])

        # 2. Aplicar guard (si existe) y preprocesamiento
        if self.has_guard and self.guard is not None:
            X_in = self.guard.transform(X_df)
        else:
            X_in = X_df

        X_trans = self.preprocess.transform(X_in)
        z_vector = X_trans[0]

        # 3. Cálculo de contribuciones locales por término codificado
        encoded_contribs = self.model_coefs * z_vector
        logit_decision = float(self.clf.decision_function(X_trans)[0])

        all_contribs: list[FeatureContribution] = []
        raw_sum_contribs = 0.0

        for col_name in self.approved_columns:
            val_obj = row_series[col_name]
            is_missing = pd.isna(val_obj)
            idx_list = self.var_to_indices.get(col_name, [])
            contrib_val = float(np.sum(encoded_contribs[idx_list])) if idx_list else 0.0
            raw_sum_contribs += contrib_val

            coef_meta = self.coefs_dict.get(col_name, {})
            familia = str(coef_meta.get("familia", "General"))
            significado = str(coef_meta.get("significado_geologico", col_name))
            gain_share = float(coef_meta.get("gain_share", 0.0))

            if col_name in self.var_main_index:
                main_idx = self.var_main_index[col_name]
                raw_val = float(val_obj) if not is_missing else 0.0
                z_val = float(z_vector[main_idx])
                beta_val = float(self.model_coefs[main_idx])
                odds_ratio = float(np.exp(beta_val))
            else:
                raw_val = float(val_obj) if not is_missing else -1.0
                active_idx = next((idx for idx in idx_list if z_vector[idx] > 0.5), idx_list[0] if idx_list else 0)
                z_val = 1.0
                beta_val = float(self.model_coefs[active_idx]) if idx_list else 0.0
                odds_ratio = float(np.exp(beta_val))

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

        logit_calc = self.intercept + raw_sum_contribs
        error = abs(logit_calc - logit_decision)
        test_passed = error < 1e-4

        # Score sigmoide
        sigmoid_val = float(1.0 / (1.0 + np.exp(-logit_calc)))
        prospectivity_score = float(cell_meta.get("score", sigmoid_val))

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
