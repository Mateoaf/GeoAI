"""
scripts/aplicar_datos_reales_presentacion.py
Actualiza la presentación PowerPoint GEOAI_Oro_Presentacion_Profesional.pptx
reemplazando todos los textos ficticios, placeholders y mocks por los
datos, métricas, algoritmos y depósitos canónicos reales del proyecto GeoAI-Au.
"""
from pathlib import Path
from pptx import Presentation

ROOT = Path(__file__).resolve().parent.parent
pptx_path = ROOT / "GEOAI_Oro_Presentacion_Profesional.pptx"

# Mapeo de reemplazos por diapositiva (índice 0-based)
SLIDE_REPLACEMENTS = {
    # Diapositiva 4 (03 · EVIDENCIAS)
    3: [
        ("Indicios BDMIN de Au", "787 Indicios BDMIN (Roca y Aluvial)"),
        ("Litología · unidades · contactos", "Litología GEODE 1:1M (41 clases)"),
        ("Fallas · lineamientos", "Cizallas, fallas y contactos ígneos"),
        ("GEOQUÍMICA", "CRONOESTRATIGRAFÍA"),
        ("Au y anomalías asociadas", "27 Pisos estratigráficos (u001-u027)"),
        ("DEM · pendiente · orientación", "MDT 500m IGN (relieve y pendiente)"),
        ("Hidrología · distancias · entorno", "Red fluvial y distancia a cauces"),
    ],
    # Diapositiva 5 (04 · INGENIERÍA DE VARIABLES)
    4: [
        ("El GIS deja de ser solo cartografía: se convierte en una matriz de evidencias para cada celda o muestra.",
         "56 covariables aprobadas (0 fugas) cubriendo las 478.443 celdas peninsulares de 1 km²."),
        ("U008", "0.78 (Pizarras)"),
        ("453", "320 m"),
        ("12.4", "185 m (Desnivel)"),
        ("Au_geoquímica", "edades_u006"),
        ("alto", "0.65 (Cámbrico)"),
        ("1 240", "180 m"),
        ("1", "1 (664 P)"),
        ("Una fila = una localización.  Una columna = una evidencia medible.",
         "478.443 filas (celdas de 1 km²) × 56 covariables continuas. 0 fugas de datos."),
    ],
    # Diapositiva 6 (05 · EL RETO ESTADÍSTICO)
    5: [
        ("Indicio conocido / mineralización catalogada", "664 Celdas Positivas (787 indicios BDMIN curados)"),
        ("Territorio donde no consta un indicio", "477.779 Celdas de fondo peninsular"),
        ("Dirección metodológica: pseudoausencias controladas → Positive–Unlabeled Learning (PU) → estimación de incertidumbre.",
         "Solución aplicada: Muestreo PU 1:3 balanceado (664 P : 1.992 U) con buffer de exclusión estricto de 5 km alrededor de cualquier depósito conocido para evitar falsos negativos en el fondo."),
    ],
    # Diapositiva 7 (06 · SISTEMA - PIPELINE)
    6: [
        ("BDMIN · GIS", "787 Indicios BDMIN"),
        ("Limpieza", "Saneamiento & Buffer 5km"),
        ("Variables espaciales", "56 Covariables Aprobadas"),
        ("Positivos + fondo", "PU 1:3 (664 P : 1.992 U)"),
        ("Validación", "Spatial CV (Bloques 50km)"),
        ("Entrenamiento", "RF / XGBoost / LightGBM"),
        ("SHAP", "Permutación & Odds"),
        ("Prospectividad", "754 Clusters & Lift 97.2x"),
    ],
    # Diapositiva 8 (07 · ENTRENAMIENTO)
    7: [
        ("Baseline · Random Forest · Boosting", "Regresión Logística L2 · Random Forest · XGBoost · LightGBM"),
        ("Búsqueda de hiperparámetros", "Bloques espaciales de 50 km con purga de 10 km"),
        ("ROC-AUC · PR-AUC · Recall · Precision", "Spatial CV ROC-AUC · PR-AUC · Tasa de Captura & Lift"),
        ("Leakage · balance · calibración", "0 fugas · Buffer 5km · Cuantificación de fuga (+0.056)"),
    ],
    # Diapositiva 9 (08 · EVALUACIÓN)
    8: [
        ("Esta diapositiva está preparada para insertar las métricas definitivas del modelo validado espacialmente.",
         "Métricas reales auditadas en validación espacial estricta por bloques sobre 478.443 celdas."),
        ("ROC-AUC", "SPATIAL CV ROC"),
        ("[ 0.XX ]", "0.8567"),
        ("Spatial CV", "Random Forest (0.9684 XGBoost Roca)"),
        ("PR-AUC", "RANDOM K-FOLD ROC"),
        ("[ 0.XX ]", "0.9129"),
        ("Spatial CV", "Fuga espacial controlada: +0.056"),
        ("RECALL", "CAPTURA TOP 0.5%"),
        ("[ XX % ]", "48.60%"),
        ("umbral operativo", "Lift: 97.2x sobre azar (2.392 km²)"),
        ("PLACEHOLDER · sustituir por resultados reales",
         "Evaluado en 664 celdas minerales P y 1.992 celdas de fondo U (Ratio 1:3)"),
    ],
    # Diapositiva 10 (09 · EXPLICABILIDAD)
    9: [
        ("IMPORTANCIA GLOBAL · ESQUEMA", "IMPORTANCIA DE VARIABLES (Permutación en Random Forest)"),
        ("Distancia a fallas", "litologia_u008 (Pizarras/Cuarcitas): 17.07%"),
        ("Litología favorable", "edades_u006 (Cámbrico-Ordovícico): 16.24%"),
        ("Geoquímica Au", "desv_elevacion_5000m (Relieve 5km): 6.11%"),
        ("Contacto geológico", "edades_u013 (Paleozoico medio): 5.94%"),
        ("Pendiente", "dist_cauce_m (Proximidad fluvial): 5.05%"),
        ("Distancia a cauces", "dens_falla_5000m (Densidad fallas): 4.82%"),
        ("ILUSTRATIVO", "Datos Reales Cuaderno 12"),
    ],
    # Diapositiva 11 (10 · RESULTADO)
    10: [
        ("La salida operativa es un mapa continuo de favorabilidad para priorizar zonas de investigación.",
         "Predicción continua a 1 km² en 478.443 celdas peninsulares (478.378 km²)."),
        ("Cada celda recibe una puntuación relativa de favorabilidad según las evidencias aprendidas.",
         "754 macro-clusters conexos (-50.7% dispersión vs 1.529 zonas v1.0). Lift de 97.2x al Top 0.5% (captura 48.60% del oro)."),
        ("No es una “certeza de oro”", "Alineación con fajas orogénicas"),
        ("Es una capa de priorización.", "Narcea, El Bierzo, Cabo de Gata, Toledo, Ossa-Morena."),
    ],
    # Diapositiva 12 (11 · EXPLICACIÓN LOCAL)
    11: [
        ("CANDIDATE AREA #42", "EL VALLE-BOINÁS (Asturias)"),
        ("91%", "0.962"),
        ("favorabilidad ilustrativa", "Percentil 99.85% (Top 0.5% Nacional)"),
        ("Dist. falla", "Fallas ENE"),
        ("320 m", "Cizalla del Narcea"),
        ("Litología", "Litología u008"),
        ("U008", "Calizas Fm. Láncara"),
        ("Geoquímica Au", "Aureola Térmica"),
        ("alta", "Plutón Belmonte"),
        ("Pendiente", "Desnivel 5km"),
        ("8°", "Contraste zócalo"),
        ("MOCK · sustituir por candidato real", "Yacimiento Canónico Real (Mayor productor histórico moderno de España)"),
    ],
    # Diapositiva 14 (12 · DEMO SCRIPT)
    13: [
        ("La demo debe estar coreografiada para que cada interacción responda una pregunta concreta.",
         "Demostración interactiva en la plataforma web GeoAI-Au (FastAPI + Next.js)."),
        ("“Este es el área que analiza el modelo.”", "Visor GIS: 478.443 celdas peninsulares a 1 km² en EPSG:25830."),
        ("“Estos son los positivos conocidos.”", "Activar los 787 indicios BDMIN (457 roca vs 330 aluvial)."),
        ("“El modelo aprende de evidencias geocientíficas.”", "Conmutar capas: Litologías GEODE, fallas, MDT y distancias."),
        ("Aparece el mapa de favorabilidad.", "Selector Oficial v1.0 vs Experimento 787 indicios (754 clusters)."),
        ("Quedan las anomalías no explicadas por depósitos visibles.", "Examinar la Curva de Captura interactiva (Lift 97.2x en Top 0.5%)."),
        ("Puntuación + variables + SHAP local.", "Simulador de Distritos: El Valle-Boinás, Rodalquilar, Las Médulas, Salave."),
    ],
    # Diapositiva 16 (14 · EVOLUCIÓN - ROADMAP)
    15: [
        ("GEOAI v1", "GEOAI v1.0 & Exp. 787 (ACTUAL)"),
        ("BDMIN", "787 Indicios BDMIN Curados"),
        ("GIS multivariable", "56 Covariables Aprobadas (0 fugas)"),
        ("Spatial CV", "PU 1:3 con Buffer 5 km"),
        ("ML + SHAP", "RF / XGBoost / LightGBM (ROC >0.85)"),
        ("Mapa prospectividad", "Dashboard v3.0 + API + Cuadernos"),
        ("GEOAI v2", "GEOAI v2.0 (PRÓXIMO PASO)"),
        ("PU Learning", "Capa Catastro Minero (Derechos Libres)"),
        ("Optimización bayesiana", "Capa Ambiental (Red Natura 2000)"),
        ("Sentinel-2", "Geoquímica Fina (As, Sb, Bi)"),
        ("Geofísica adicional", "Extensión Multimetal (Cobre, Litio)"),
        ("Incertidumbre", "Verificación en Campo / Sondeos"),
    ]
}

def replace_in_paragraph(p, old_text, new_text):
    """Reemplaza texto preservando el formato del primer run."""
    if old_text in p.text:
        if p.runs:
            full = "".join(r.text for r in p.runs)
            if old_text in full:
                updated = full.replace(old_text, new_text, 1)
                p.runs[0].text = updated
                for r in p.runs[1:]:
                    r.text = ""
                return True
        else:
            p.text = p.text.replace(old_text, new_text, 1)
            return True
    return False

def apply_updates():
    prs = Presentation(str(pptx_path))
    total_modifications = 0

    for slide_idx, replacements in SLIDE_REPLACEMENTS.items():
        slide = prs.slides[slide_idx]
        slide_mods = 0
        
        for old_txt, new_txt in replacements:
            replaced = False
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        if replace_in_paragraph(p, old_txt, new_txt):
                            replaced = True
                            slide_mods += 1
                            break
                    if replaced:
                        break
                elif shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            for p in cell.text_frame.paragraphs:
                                if replace_in_paragraph(p, old_txt, new_txt):
                                    replaced = True
                                    slide_mods += 1
                                    break
                            if replaced:
                                break
                        if replaced:
                            break
                    if replaced:
                        break
                        
        print(f"Diapositiva {slide_idx+1}: {slide_mods}/{len(replacements)} reemplazos aplicados.")
        total_modifications += slide_mods

    prs.save(str(pptx_path))
    print(f"\n[ÉXITO] Presentación actualizada y guardada con {total_modifications} reemplazos reales.")

if __name__ == "__main__":
    apply_updates()
