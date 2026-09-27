"""
apps/api/services/copilot_service.py
Copiloto GeoAI determinista basado en datos científicos canónicos auditados.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from ..data_loader import get_data_loader
from .explain_service import get_explain_service
from ..schemas.copilot import CopilotQuery, CopilotResponse, CopilotAction


class CopilotProvider(ABC):
    """Interfaz abstracta para proveedores de copiloto (determinista o LLM/RAG)."""

    @abstractmethod
    def answer(self, request: CopilotQuery) -> CopilotResponse:
        pass


class DeterministicCopilotProvider(CopilotProvider):
    """Proveedor determinista basado estrictamente en los artefactos sellados de GeoAI-Au v1.0."""

    def __init__(self):
        self.data_loader = get_data_loader()
        self.explain_service = get_explain_service()

    def answer(self, request: CopilotQuery) -> CopilotResponse:
        query_text = request.query.strip().lower()
        context = request.context or {}
        active_cell_id = context.get("cell_id")

        # 1. ¿Por qué esta celda tiene score alto? / ¿Qué variables influyen más aquí?
        if "score alto" in query_text or "variables influyen" in query_text or "por qué" in query_text:
            if active_cell_id:
                exp = self.explain_service.explain_cell(active_cell_id)
                if exp:
                    top_pos = exp.top_positive_contributions[:3]
                    top_neg = exp.top_negative_contributions[:2]

                    pos_lines = "\n".join([f"- **{p.variable}** (+{p.contribution:.2f}): {p.significado_geologico}" for p in top_pos])
                    neg_lines = "\n".join([f"- **{n.variable}** ({n.contribution:.2f}): {n.significado_geologico}" for n in top_neg])

                    markdown = (
                        f"### Explicación Aditiva para Celda `{active_cell_id}`\n\n"
                        f"**Prospectivity Score**: `{exp.prospectivity_score:.4f}` | **Logit**: `{exp.logit_calculated:.3f}`\n\n"
                        f"#### Factores que más AUMENTAN la favorabilidad:\n{pos_lines}\n\n"
                        f"#### Factores que REDUCEN la favorabilidad:\n{neg_lines}\n\n"
                        f"> **Nota de Integridad**: Descomposición lineal exacta $\\beta \\cdot z$. No representa causalidad física demostrada sino asociación aprendida por el modelo regularizado."
                    )
                    return CopilotResponse(
                        query=request.query,
                        answer_markdown=markdown,
                        sources=["final_validated_model.joblib", "coeficientes_estandarizados.csv", "X_features.parquet"],
                        suggested_queries=[
                            "¿Cuáles son las mejores zonas de Ossa Morena?",
                            "Compara esta zona con Rodalquilar",
                            "¿Qué ocurrió en el holdout?"
                        ]
                    )
            return CopilotResponse(
                query=request.query,
                answer_markdown="Selecciona primero una celda en el mapa para analizar las variables que determinan su favorabilidad local.",
                sources=["mapa_nacional_prospectividad.geoparquet"],
                suggested_queries=["Muéstrame targets Top 1%", "¿Qué ocurrió en el holdout?"]
            )

        # 2. ¿Cuáles son las mejores zonas de Ossa Morena?
        elif "ossa morena" in query_text:
            df_targets = self.data_loader.targets_df
            om_targets = df_targets[df_targets["distrito_conocido_proximo"].str.contains("ossa_morena", case=False, na=False)].sort_values("ranking_nacional")
            if not om_targets.empty:
                top_om = om_targets.head(3)
                rows = "\n".join([
                    f"- **#{r.ranking_nacional} {r.zona_id}** ({r.categoria_prioridad}): Score máx {r.score_maximo:.4f}, área {r.area_km2:.0f} km², próximo a `{r.deposito_conocido_proximo}` ({r.distancia_deposito_proximo_km:.1f} km)."
                    for _, r in top_om.iterrows()
                ])
                best_zone_id = top_om.iloc[0]["zona_id"]
                markdown = (
                    f"### Zonas Prioritarias en Ossa Morena\n\n"
                    f"El distrito Ossa Morena presenta importantes áreas de alta favorabilidad asociadas a skarns y plutonismo hercínico:\n\n"
                    f"{rows}\n\n"
                    f"> **Aviso**: La proximidad al depósito histórico es una anotación post-hoc y no interviene en la predicción."
                )
                return CopilotResponse(
                    query=request.query,
                    answer_markdown=markdown,
                    sources=["zonas_prospectividad_ranking.csv"],
                    suggested_queries=["Muéstrame targets Top 1%", "Compara esta zona con Rodalquilar"],
                    action=CopilotAction(
                        action_type="zoom_to_zone",
                        payload={"zona_id": best_zone_id}
                    )
                )

        # 3. ¿Qué ocurrió en el holdout?
        elif "holdout" in query_text or "validación" in query_text or "fase g" in query_text:
            val = self.data_loader.validation_summary
            markdown = (
                f"### Resultados de la Evaluación Ciega en Holdout (Fase G)\n\n"
                f"- **Depósitos de test**: 8 depósitos en 5 distritos aislados (13.541 celdas).\n"
                f"- **Deposit Recovery @1%**: `{val.get('deposit_recovery_at_01', 0)*100:.1f}%` (1/8: Rodalquilar Cinto)\n"
                f"- **Deposit Recovery @5%**: `{val.get('deposit_recovery_at_05', 0)*100:.1f}%` (1/8: Rodalquilar Cinto)\n"
                f"- **Deposit Recovery @10%**: `{val.get('deposit_recovery_at_10', 0)*100:.1f}%` (2/8: Rodalquilar Cinto y La Oriental)\n"
                f"- **ROC-AUC P/U**: `{val.get('roc_auc_PU', 0):.4f}`\n\n"
                f"**Brecha de Transferencia Observada ($N=8$)**:\n"
                f"La caída frente a la validación cruzada en desarrollo (ROC-AUC 0,7402 vs 0,5807) se debe a la marcada heterogeneidad genética entre los distritos de entrenamiento (orogénicos y placeres) y los distritos de test (epitermales en Cabo de Gata y leucogranitos en Costa da Morte)."
            )
            return CopilotResponse(
                query=request.query,
                answer_markdown=markdown,
                sources=["holdout_overall_metrics.json", "development_vs_holdout_comparison.csv"],
                suggested_queries=["¿Cuáles son las mejores zonas de Ossa Morena?", "Muéstrame targets Top 1%"]
            )

        # 4. Compara esta zona con Rodalquilar
        elif "rodalquilar" in query_text:
            markdown = (
                f"### Caso de Estudio: Distrito Epitermal de Rodalquilar\n\n"
                f"- **Depósito Clave**: Rodalquilar Cinto (`dep_rodalquilar_cinto`).\n"
                f"- **Tipología**: Epitermal de alta sulfuración en arco volcánico neógeno.\n"
                f"- **Desempeño en Holdout**: Identificado exitosamente en el Top 1% del holdout ciego.\n"
                f"- **Predictores dominantes**: Altas fracciones de unidades volcánicas terciarias combinadas con moderada elevación topográfica y ausencia de formaciones metamórficas paleozoicas.\n\n"
                f"Si seleccionas una celda en el mapa, puedes contrastar sus contribuciones litológicas frente al perfil volcánico de Cabo de Gata."
            )
            return CopilotResponse(
                query=request.query,
                answer_markdown=markdown,
                sources=["holdout_by_deposit.csv", "contribuciones_locales_casos_estudio.csv"],
                suggested_queries=["¿Qué ocurrió en el holdout?", "¿Cuáles son las mejores zonas de Ossa Morena?"]
            )

        # 5. Muéstrame targets Top 1%
        elif "top 1" in query_text or "targets" in query_text:
            df_targets = self.data_loader.targets_df
            top1_count = len(df_targets[df_targets["categoria_prioridad"] == "prioridad_muy_alta_top01"])
            top5_count = len(df_targets[df_targets["categoria_prioridad"] == "prioridad_alta_top05"])
            markdown = (
                f"### Catálogo de Zonas de Prospectividad Aurífera\n\n"
                f"- **Total Zonas Priorizadas**: 1.529 clusters espaciales contiguos.\n"
                f"- **Banda Top 1% (Prioridad Muy Alta)**: `{top1_count}` zonas delimitadas (score $\\ge 0,8333$, $4.784\\text{ km}^2$).\n"
                f"- **Banda Top 1-5% (Prioridad Alta)**: `{top5_count}` zonas delimitadas (score $\\ge 0,6526$, $19.135\\text{ km}^2$).\n\n"
                f"Puedes explorar la lista interactiva, filtrar por distrito o buscar zonas que no tengan depósitos conocidos cercanos en la pestaña **Targets** del panel derecho."
            )
            return CopilotResponse(
                query=request.query,
                answer_markdown=markdown,
                sources=["zonas_prospectividad_ranking.csv", "control_cierre.json"],
                suggested_queries=["¿Cuáles son las mejores zonas de Ossa Morena?", "¿Qué ocurrió en el holdout?"],
                action=CopilotAction(
                    action_type="select_tab",
                    payload={"tab": "targets"}
                )
            )

        # Respuesta genérica orientativa
        markdown = (
            f"### Asistente Geocientífico GeoAI-Au\n\n"
            f"Puedo responder preguntas basadas en los datos y modelos auditados del proyecto:\n\n"
            f"- **'¿Por qué esta celda tiene score alto?'**: Descompone las variables de la celda activa.\n"
            f"- **'¿Cuáles son las mejores zonas de Ossa Morena?'**: Muestra los targets del distrito.\n"
            f"- **'¿Qué ocurrió en el holdout?'**: Resumen cuantitativo de la evaluación ciega en Fase G.\n"
            f"- **'Compara esta zona con Rodalquilar'**: Contexto metalogenético del epitermal de Almería.\n"
            f"- **'Muéstrame targets Top 1%'**: Estadísticas y acceso a zonas prioritarias."
        )
        return CopilotResponse(
            query=request.query,
            answer_markdown=markdown,
            sources=["MODEL_CARD.md", "control_cierre.json"],
            suggested_queries=[
                "Muéstrame targets Top 1%",
                "¿Qué ocurrió en el holdout?",
                "¿Cuáles son las mejores zonas de Ossa Morena?"
            ]
        )


def get_copilot_service() -> CopilotProvider:
    return DeterministicCopilotProvider()
