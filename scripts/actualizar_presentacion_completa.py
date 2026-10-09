#!/usr/bin/env python3
"""
scripts/actualizar_presentacion_completa.py
Actualiza la presentación PowerPoint GEOAI_Oro_Presentacion_Profesional.pptx:
1. Actualiza diapositivas existentes con los hitos de GeoAI v3.0 (PU Learning, Buffered CV 15km, Incertidumbre, 3 Modos).
2. Genera 5 diapositivas técnicas de Explicabilidad de Código de los Notebooks más relevantes.
3. Inserta y renumera las diapositivas con formato visual profesional y coherente con el tema oscuro.
"""
import sys
import shutil
from pathlib import Path
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

ROOT = Path(__file__).resolve().parent.parent
PPTX_PATH = ROOT / "GEOAI_Oro_Presentacion_Profesional.pptx"
BACKUP_PATH = ROOT / "reports" / "GEOAI_Oro_Presentacion_Profesional_BACKUP_ANTES_V3.pptx"

# Paleta oficial
CLR_BG = RGBColor(0x0B, 0x0F, 0x14)        # Fondo obsidiana
CLR_CARD_BG = RGBColor(0x18, 0x21, 0x2C)   # Fondo tarjetas
CLR_CARD_BORDER = RGBColor(0x24, 0x31, 0x3D) # Borde tarjetas
CLR_CODE_BG = RGBColor(0x0E, 0x14, 0x1D)   # Terminal de código
CLR_CODE_BORDER = RGBColor(0x2D, 0x37, 0x48) # Borde código
CLR_TXT_WHITE = RGBColor(0xF4, 0xF6, 0xF8) # Texto principal
CLR_TXT_MUTED = RGBColor(0x98, 0xA6, 0xB5) # Subtítulos
CLR_TXT_SLATE = RGBColor(0x71, 0x80, 0x91) # Metadatos / categorías
CLR_GOLD = RGBColor(0xE6, 0xB8, 0x4B)      # Acento dorado
CLR_CYAN = RGBColor(0x06, 0xB6, 0xD4)      # Acento cian
CLR_EMERALD = RGBColor(0x10, 0xB9, 0x81)   # Acento esmeralda
CLR_PURPLE = RGBColor(0xA8, 0x55, 0xF7)    # Acento púrpura
CLR_ROSE = RGBColor(0xF4, 0x3F, 0x5E)      # Acento rosa
CLR_RED_DOT = RGBColor(0xEF, 0x44, 0x44)
CLR_YELLOW_DOT = RGBColor(0xF5, 0x9E, 0x0B)
CLR_GREEN_DOT = RGBColor(0x10, 0xB9, 0x81)

def update_existing_slides(prs):
    print("-> Actualizando diapositivas existentes con avances de GeoAI v3.0...")
    
    # -------------------------------------------------------------------------
    # DIAPOSITIVA 6 (05 · EL RETO ESTADÍSTICO)
    # -------------------------------------------------------------------------
    slide_6 = prs.slides[5]
    for shape in slide_6.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "Solución aplicada:" in p.text or "Muestreo PU 1:3" in p.text:
                    p.text = (
                        "Solución aplicada v3.0: Formulación formal Positive-Unlabeled (PU) Learning. "
                        "Estimador de propensión de Elkan & Noto (2008) (c ≈ 0.72) bajo supuesto SCAR, "
                        "calibrando la probabilidad no sesgada P(y=1|x) = min(1.0, e(x)/c) y eliminando el sesgo "
                        "de tratar el territorio inexplorado como estéril."
                    )

    # -------------------------------------------------------------------------
    # DIAPOSITIVA 7 (06 · SISTEMA - PIPELINE)
    # -------------------------------------------------------------------------
    slide_7 = prs.slides[6]
    for shape in slide_7.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                txt = p.text.strip()
                if txt == "PU 1:3 (664 P : 1.992 U)":
                    p.text = "PU Bagging & Elkan-Noto"
                elif txt == "Spatial CV (Bloques 50km)":
                    p.text = "Buffered CV (15km Dead-Zone)"
                elif txt == "RF / XGBoost / LightGBM":
                    p.text = "PU Bagging + LGBM Regularizado"
                elif txt == "Permutación & Odds":
                    p.text = "Permutación, SHAP & Fiabilidad"
                elif txt == "754 Clusters & Lift 97.2x":
                    p.text = "754 Clusters & Incertidumbre σ"

    # -------------------------------------------------------------------------
    # DIAPOSITIVA 8 (07 · ENTRENAMIENTO)
    # -------------------------------------------------------------------------
    slide_8 = prs.slides[7]
    for shape in slide_8.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                txt = p.text.strip()
                if "Regresión Logística L2 · Random Forest" in txt:
                    p.text = "Bagging PU Calibrado · LightGBM · Random Forest · Línea Base L2"
                elif "Bloques espaciales de 50 km con purga de 10 km" in txt:
                    p.text = "Macro-bloques de 50 km con Zona Muerta de 15 km (Buffered Spatial CV)"
                elif "Spatial CV ROC-AUC · PR-AUC" in txt:
                    p.text = "Buffered ROC-AUC · Recovery@10% · PR-AUC · Incertidumbre Epistémica σ"
                elif "0 fugas · Buffer 5km" in txt:
                    p.text = "0 fugas · Aislamiento Tobler 15 km · Cuantificación brecha espacial (+0.13)"
                elif "Una métrica alta no es suficiente" in txt:
                    p.text = (
                        "La validación aleatoria sobreestima un 12% el ROC-AUC por autocorrelación territorial. "
                        "La Dead-Zone de 15 km garantiza evaluación ciega honesta para descubrir nuevos distritos."
                    )

    # -------------------------------------------------------------------------
    # DIAPOSITIVA 9 (08 · EVALUACIÓN)
    # -------------------------------------------------------------------------
    slide_9 = prs.slides[8]
    for shape in slide_9.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                txt = p.text.strip()
                if txt == "0.8567":
                    p.text = "0.7924"
                elif "Random Forest (0.9684 XGBoost Roca)" in txt:
                    p.text = "Bagging PU v3.0 (0.818 Bloques 50km)"
                elif txt == "0.9129":
                    p.text = "0.9234"
                elif "Fuga espacial controlada:" in txt:
                    p.text = "Sobreoptimismo por proximidad (+0.131)"
                elif txt == "CAPTURA TOP 0.5%":
                    p.text = "RECOVERY @ 10% & LIFT"
                elif txt == "48.60%":
                    p.text = "33.9% / 97.2x"
                elif "Lift: 97.2x sobre azar" in txt:
                    p.text = "33.9% oro en Top 10% (Lift 97.2x al Top 0.5%)"
                elif "Evaluado en 664 celdas" in txt:
                    p.text = "Auditoría exhaustiva 4 Modelos × 3 Protocolos CV en 478.443 celdas peninsulares (Cuaderno 18)."

    # -------------------------------------------------------------------------
    # DIAPOSITIVA 11 (10 · RESULTADO)
    # -------------------------------------------------------------------------
    slide_11 = prs.slides[10]
    for shape in slide_11.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                txt = p.text.strip()
                if "754 macro-clusters conexos" in txt:
                    p.text = (
                        "Salida triple v3.0: Favorabilidad Media Calibrada μ(x), Incertidumbre Epistémica σ(x) "
                        "y Distancia Out-of-Domain DZ. 754 macro-clusters conexos (-50.7% dispersión) y Lift 97.2x."
                    )

    # -------------------------------------------------------------------------
    # DIAPOSITIVA 14 (12 · DEMO SCRIPT)
    # -------------------------------------------------------------------------
    slide_14 = prs.slides[13]
    for shape in slide_14.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                txt = p.text.strip()
                if txt == "ACTIVAR GEOAI":
                    p.text = "MOTOR v3.0 PRODUCCIÓN"
                elif "Selector Oficial v1.0 vs Experimento 787" in txt:
                    p.text = "Motor v3.0 Oficial (Score PU e Incertidumbre), conmutar a Tipologías o Benchmarking."
                elif txt == "OCULTAR BDMIN":
                    p.text = "MATRIZ DE FIABILIDAD"
                elif "Examinar la Curva de Captura" in txt:
                    p.text = "Cruzar alta favorabilidad con baja incertidumbre epistémica (σ) para priorizar sondeos."
                elif txt == "PULSAR CANDIDATO":
                    p.text = "SIMULADOR DE DISTRITOS"
                elif "Simulador de Distritos:" in txt:
                    p.text = "Inspección local multivariable y descomposición SHAP: El Valle-Boinás, Rodalquilar, Las Médulas."

    # -------------------------------------------------------------------------
    # DIAPOSITIVA 16 (14 · EVOLUCIÓN)
    # -------------------------------------------------------------------------
    slide_16 = prs.slides[15]
    for shape in slide_16.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                txt = p.text.strip()
                if "GEOAI v1.0 & Exp. 787" in txt:
                    p.text = "GeoAI v3.0 (PRODUCCIÓN)"
                elif txt == "PU 1:3 con Buffer 5 km":
                    p.text = "PU Bagging Calibrado (c=0.72)"
                elif "RF / XGBoost / LightGBM" in txt:
                    p.text = "Dead-Zone 15 km & Matriz Fiabilidad"
                elif "Dashboard v3.0 + API + Cuadernos" in txt:
                    p.text = "Plataforma Web 3 Vistas + 18 Cuadernos"
                elif "GEOAI v2.0 (PRÓXIMO PASO)" in txt:
                    p.text = "GEOAI v3.5 (INTEGRACIÓN MINERA)"
                elif txt == "Capa Catastro Minero (Derechos Libres)":
                    p.text = "Catastro Minero (Derechos Libres vs Concesiones)"
                elif txt == "Capa Ambiental (Red Natura 2000)":
                    p.text = "Restricciones Ambientales (Red Natura 2000)"

def build_code_explainability_slide(prs, cfg):
    """
    Crea una diapositiva con estilo de terminal de código y tarjetas de explicabilidad geocientífica.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    
    # 1. Fondo uniforme #0B0F14
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = CLR_BG
    
    # 2. Header Top Left: Brand
    tb_brand = slide.shapes.add_textbox(Inches(0.6), Inches(0.32), Inches(3.0), Inches(0.28))
    p = tb_brand.text_frame.paragraphs[0]
    p.text = "GEOAI"
    p.font.name = "Noto Sans"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = CLR_TXT_WHITE
    
    # 3. Header Top Right: Category
    tb_cat = slide.shapes.add_textbox(Inches(7.5), Inches(0.32), Inches(5.2), Inches(0.28))
    p = tb_cat.text_frame.paragraphs[0]
    p.text = cfg["category"]
    p.font.name = "Noto Sans"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.alignment = PP_ALIGN.RIGHT
    p.font.color.rgb = CLR_TXT_SLATE
    
    # 4. Section Tag (Gold)
    tb_sec = slide.shapes.add_textbox(Inches(0.6), Inches(0.68), Inches(12.0), Inches(0.26))
    p = tb_sec.text_frame.paragraphs[0]
    p.text = cfg["section_tag"]
    p.font.name = "Noto Sans"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = CLR_GOLD
    
    # 5. Big Title
    tb_title = slide.shapes.add_textbox(Inches(0.6), Inches(0.95), Inches(12.0), Inches(0.45))
    p = tb_title.text_frame.paragraphs[0]
    p.text = cfg["title"]
    p.font.name = "Noto Sans"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = CLR_TXT_WHITE
    
    # 6. Subtitle
    tb_sub = slide.shapes.add_textbox(Inches(0.6), Inches(1.42), Inches(12.0), Inches(0.4))
    p = tb_sub.text_frame.paragraphs[0]
    p.text = cfg["subtitle"]
    p.font.name = "Noto Sans"
    p.font.size = Pt(10.5)
    p.font.color.rgb = CLR_TXT_MUTED
    
    # -------------------------------------------------------------------------
    # COLUMNA IZQUIERDA: TERMINAL DE CÓDIGO
    # -------------------------------------------------------------------------
    left_x = Inches(0.6)
    left_y = Inches(1.95)
    left_w = Inches(5.8)
    left_h = Inches(4.55)
    
    # Contenedor terminal
    term_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_x, left_y, left_w, left_h)
    term_box.fill.solid()
    term_box.fill.fore_color.rgb = CLR_CODE_BG
    term_box.line.color.rgb = CLR_CODE_BORDER
    term_box.line.width = Pt(1)
    
    # Barra de ventana terminal (3 puntos mac + nombre archivo)
    dot_y = left_y + Inches(0.14)
    dot_r = Inches(0.10)
    for i, clr in enumerate([CLR_RED_DOT, CLR_YELLOW_DOT, CLR_GREEN_DOT]):
        d = slide.shapes.add_shape(MSO_SHAPE.OVAL, left_x + Inches(0.18 + i*0.16), dot_y, dot_r, dot_r)
        d.fill.solid()
        d.fill.fore_color.rgb = clr
        d.line.fill.background()
        
    tb_file = slide.shapes.add_textbox(left_x + Inches(0.8), left_y + Inches(0.06), left_w - Inches(0.9), Inches(0.26))
    p = tb_file.text_frame.paragraphs[0]
    p.text = cfg["file_badge"]
    p.font.name = "Consolas"
    p.font.size = Pt(8.5)
    p.font.color.rgb = CLR_TXT_SLATE
    
    # Contenido del código
    tb_code = slide.shapes.add_textbox(left_x + Inches(0.15), left_y + Inches(0.40), left_w - Inches(0.3), left_h - Inches(0.5))
    tf = tb_code.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    
    for idx, (code_line, style) in enumerate(cfg["code_lines"]):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = code_line
        p.font.name = "Consolas"
        p.font.size = Pt(9.0)
        p.space_after = Pt(1)
        p.space_before = Pt(0)
        
        if style == "comment":
            p.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8) # Gris comentario
            p.font.italic = True
        elif style == "keyword":
            p.font.color.rgb = RGBColor(0x38, 0xBD, 0xF8) # Azul cielo palabra clave
        elif style == "string_num":
            p.font.color.rgb = RGBColor(0xFB, 0xBF, 0x24) # Amarillo dorado string/num
        elif style == "highlight":
            p.font.color.rgb = RGBColor(0x34, 0xD3, 0x99) # Verde esmeralda llamada clave
            p.font.bold = True
        else:
            p.font.color.rgb = RGBColor(0xEA, 0xEE, 0xF3) # Blanco código
            
    # -------------------------------------------------------------------------
    # COLUMNA DERECHA: 3 TARJETAS DE EXPLICABILIDAD CIENTÍFICA
    # -------------------------------------------------------------------------
    right_x = Inches(6.55)
    card_w = Inches(6.05)
    card_h = Inches(1.22)
    card_gap = Inches(0.12)
    
    cards_data = cfg["cards"]
    for i, cdata in enumerate(cards_data):
        card_y = left_y + i * (card_h + card_gap)
        cbox = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_x, card_y, card_w, card_h)
        cbox.fill.solid()
        cbox.fill.fore_color.rgb = CLR_CARD_BG
        cbox.line.color.rgb = CLR_CARD_BORDER
        cbox.line.width = Pt(1)
        
        # Textbox interior
        tb_card = slide.shapes.add_textbox(right_x + Inches(0.18), card_y + Inches(0.10), card_w - Inches(0.36), card_h - Inches(0.20))
        ctf = tb_card.text_frame
        ctf.word_wrap = True
        ctf.margin_top = Inches(0)
        ctf.margin_bottom = Inches(0)
        ctf.margin_left = Inches(0)
        ctf.margin_right = Inches(0)
        
        # P1: Tag + Título
        p1 = ctf.paragraphs[0]
        run_tag = p1.add_run()
        run_tag.text = cdata["tag"].upper() + " · "
        run_tag.font.name = "Noto Sans"
        run_tag.font.size = Pt(8.5)
        run_tag.font.bold = True
        run_tag.font.color.rgb = cdata["tag_color"]
        
        run_title = p1.add_run()
        run_title.text = cdata["title"]
        run_title.font.name = "Noto Sans"
        run_title.font.size = Pt(10.5)
        run_title.font.bold = True
        run_title.font.color.rgb = CLR_TXT_WHITE
        p1.space_after = Pt(2)
        
        # P2: Explicación narrativa
        p2 = ctf.add_paragraph()
        p2.text = cdata["body"]
        p2.font.name = "Noto Sans"
        p2.font.size = Pt(9.0)
        p2.font.color.rgb = CLR_TXT_MUTED
        p2.space_before = Pt(1)

    # -------------------------------------------------------------------------
    # CALLOUT INFERIOR DERECHO: TAKEAWAY / IMPACTO EN DEFENSA
    # -------------------------------------------------------------------------
    banner_y = left_y + 3 * (card_h + card_gap)
    banner_h = Inches(0.52)
    bbox = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_x, banner_y, card_w, banner_h)
    bbox.fill.solid()
    bbox.fill.fore_color.rgb = RGBColor(0x11, 0x1E, 0x2E)
    bbox.line.color.rgb = CLR_GOLD
    bbox.line.width = Pt(1)
    
    tb_banner = slide.shapes.add_textbox(right_x + Inches(0.15), banner_y + Inches(0.06), card_w - Inches(0.3), banner_h - Inches(0.12))
    btf = tb_banner.text_frame
    btf.word_wrap = True
    btf.margin_top = Inches(0)
    btf.margin_bottom = Inches(0)
    p_b = btf.paragraphs[0]
    
    r_icon = p_b.add_run()
    r_icon.text = "🎯 CLAVE PARA TFG/TFM: "
    r_icon.font.name = "Noto Sans"
    r_icon.font.size = Pt(9.0)
    r_icon.font.bold = True
    r_icon.font.color.rgb = CLR_GOLD
    
    r_txt = p_b.add_run()
    r_txt.text = cfg["takeaway"]
    r_txt.font.name = "Noto Sans"
    r_txt.font.size = Pt(8.5)
    r_txt.font.color.rgb = CLR_TXT_WHITE

    return slide

def generate_all_technical_slides(prs):
    print("-> Generando las 5 diapositivas de explicabilidad de código...")
    
    # -------------------------------------------------------------------------
    # SLIDE TÉCNICA 1: PU LEARNING & ESTIMADOR ELKAN-NOTO (NB 18)
    # -------------------------------------------------------------------------
    cfg_1 = {
        "category": "CODE EXPLAINABILITY · POSITIVE-UNLABELED LEARNING",
        "section_tag": "CUADERNO DIDÁCTICO 18 · ESTIMADOR DE PROPENSIÓN DE ELKAN & NOTO (2008)",
        "title": "Código Clave: Calibración Insesgada de Probabilidad P(y=1|x)",
        "subtitle": "Corrige el sesgo de considerar estériles las celdas sin minas catalogadas mediante el factor de propensión c = 0.72.",
        "file_badge": "notebooks/18_modelos_avanzados_pu_ebm_incertidumbre.ipynb (Celdas 5-6)",
        "code_lines": [
            ("# 1. Clasificador de propensión de registro e(x) = P(s=1|x)", "comment"),
            ("rf_preliminar.fit(X_train, s_train)  # s=1 (minas), s=0 (fondo)", "code"),
            ("", "code"),
            ("# 2. Factor de propensión bajo supuesto SCAR (Elkan-Noto):", "comment"),
            ("X_pos = X_train[s_train == 1]", "code"),
            ("prob_pos = rf_preliminar.predict_proba(X_pos)[:, 1]", "code"),
            ("c_factor = float(np.mean(prob_pos))  # c = 0.7208", "highlight"),
            ("print(f'Propensión estimada: {c_factor:.4f} (Factor 1/c = {1/c_factor:.2f}x)')", "code"),
            ("", "code"),
            ("# 3. Probabilidad posterior insesgada de presencia mineral:", "comment"),
            ("prob_s = rf_preliminar.predict_proba(X_grid)[:, 1]", "code"),
            ("p_y1_calibrada = np.minimum(1.0, prob_s / c_factor)", "highlight"),
            ("", "code"),
            ("# 4. Normalización final y ordenación de prioridades:", "comment"),
            ("grid['score_pu_calibrado'] = p_y1_calibrada", "code")
        ],
        "cards": [
            {
                "tag": "Reto Geológico",
                "tag_color": CLR_GOLD,
                "title": "Fondo No Etiquetado (s=0) ≠ Esterilidad (y=0)",
                "body": "En exploración minera una celda sin indicio no es estéril, sino no explorada. La regresión estándar asigna y=0 al fondo, penalizando injustamente yacimientos ocultos o cubiertos."
            },
            {
                "tag": "Matemática Insesgada",
                "tag_color": CLR_CYAN,
                "title": "Teorema de Elkan-Noto & Factor de Escala c = 0.72",
                "body": "Bajo la hipótesis SCAR, P(s=1|y=1)=c constante. El estimador empírico demuestra que solo el 72% de los yacimientos han sido catalogados. Al dividir entre c (escala 1.39x), se recupera la probabilidad real."
            },
            {
                "tag": "Impacto Minero",
                "tag_color": CLR_EMERALD,
                "title": "Desbloqueo de Nuevas Áreas de Prospección",
                "body": "Elimina el sesgo conservador hacia distritos históricos conocidos, revelando cuadrículas con evidencias geológicas idénticas a las grandes minas pero sin laboreo previo."
            }
        ],
        "takeaway": "Demuestra ante el tribunal que GeoAI no comete el error habitual de clasificar ausencias geológicas como ceros negativos."
    }
    s1 = build_code_explainability_slide(prs, cfg_1)

    # -------------------------------------------------------------------------
    # SLIDE TÉCNICA 2: BUFFERED SPATIAL CV & DEAD-ZONE 15 KM (NB 07 & 18)
    # -------------------------------------------------------------------------
    cfg_2 = {
        "category": "CODE EXPLAINABILITY · VALIDACIÓN ESPACIAL HONESTA",
        "section_tag": "CUADERNOS 07 & 18 · BUFFERED SPATIAL CROSS-VALIDATION (15 KM DEAD-ZONE)",
        "title": "Código Clave: Aislamiento de Tobler & Purga Espacial Estricta",
        "subtitle": "Elimina la fuga por autocorrelación espacial garantizando evaluación honesta para descubrir nuevos distritos.",
        "file_badge": "notebooks/18_modelos_avanzados_pu_ebm_incertidumbre.ipynb (Celdas 7-8)",
        "code_lines": [
            ("# 1. Asignación a Macro-Bloques Espaciales de 50x50 km:", "comment"),
            ("block_col = (coords[:, 0] - x_min) // 50000", "code"),
            ("block_row = (coords[:, 1] - y_min) // 50000", "code"),
            ("block_id  = (block_row * n_cols + block_col).astype(int)", "code"),
            ("", "code"),
            ("# 2. K-Fold sobre bloques e imposición de Zona Muerta:", "comment"),
            ("for train_blk, test_blk in kf.split(np.unique(block_id)):", "code"),
            ("    test_idx = np.isin(block_id, test_blk)", "code"),
            ("    test_coords = coords[test_idx]", "code"),
            ("    ", "code"),
            ("    # 3. Purga estricta: excluir entrenamiento a < 15 km de test", "comment"),
            ("    dists = cdist(coords[train_raw_idx], test_coords)", "code"),
            ("    min_dist = np.min(dists, axis=1)", "code"),
            ("    train_clean_idx = train_raw_idx[min_dist > 15000]", "highlight")
        ],
        "cards": [
            {
                "tag": "Primera Ley de Tobler",
                "tag_color": CLR_GOLD,
                "title": "Fuga Invisible por Proximidad Geológica",
                "body": "Celdas a 1-5 km de un indicio comparten el mismo zócalo litológico o sistema de fallas. Un K-Fold aleatorio permite memorizar la vecindad inflando artificialmente el ROC a 0.923."
            },
            {
                "tag": "Zona Muerta 15 km",
                "tag_color": CLR_CYAN,
                "title": "Aislamiento Euclídeo de Fronteras de Test",
                "body": "Se crea un 'cordón sanitario' de 15 km donde ninguna celda vecina entra en entrenamiento. El pliegue de prueba se evalúa a ciegas simulando la exploración de una región completamente nueva."
            },
            {
                "tag": "Brecha Revelada",
                "tag_color": CLR_EMERALD,
                "title": "Generalización Real Honesta (ROC 0.792)",
                "body": "La caída de ROC desde 0.92 (Random) a 0.792 (Buffered) no es un fallo, sino la demostración rigurosa de que GeoAI mide capacidad real de extrapolación territorial y no memorización."
            }
        ],
        "takeaway": "Prueba de rigor científico: la mayoría de papers de ML geológico sobrestiman métricas por no usar dead-zone espacial."
    }
    s2 = build_code_explainability_slide(prs, cfg_2)

    # -------------------------------------------------------------------------
    # SLIDE TÉCNICA 3: INCERTIDUMBRE EPISTÉMICA & MATRIZ 2D (NB 18)
    # -------------------------------------------------------------------------
    cfg_3 = {
        "category": "CODE EXPLAINABILITY · INCERTIDUMBRE TERRITORIAL",
        "section_tag": "CUADERNO DIDÁCTICO 18 · BAGGING PU & DETECCIÓN OUT-OF-DISTRIBUTION",
        "title": "Código Clave: Descomposición μ(x), σ(x) y Distancia Z",
        "subtitle": "Generación de la Matriz 2D de Fiabilidad para priorizar sondeos únicamente donde la certidumbre es máxima.",
        "file_badge": "notebooks/18_modelos_avanzados_pu_ebm_incertidumbre.ipynb (Celdas 12-13)",
        "code_lines": [
            ("# 1. Bagging PU Ensemble (B=20 réplicas con remuestreo de U):", "comment"),
            ("preds_replicas = []", "code"),
            ("for b, model_b in enumerate(ensemble_pu):", "code"),
            ("    p_b = model_b.predict_proba(X_grid)[:, 1] / c_factor", "code"),
            ("    preds_replicas.append(np.minimum(1.0, p_b))", "code"),
            ("P_mat = np.array(preds_replicas)", "code"),
            ("", "code"),
            ("# 2. Favorabilidad Media e Incertidumbre Epistémica (Std):", "comment"),
            ("mu_score    = np.mean(P_mat, axis=0)  # Puntuación media", "highlight"),
            ("sigma_score = np.std(P_mat, axis=0)   # Dispersión inter-modelo", "highlight"),
            ("", "code"),
            ("# 3. Distancia Z-Score al dominio minero explorado:", "comment"),
            ("z_dist = np.sqrt(np.sum(((X_grid - mean_P) / std_P)**2, axis=1))", "code"),
            ("is_ood = z_dist > 3.0  # Extrapolación / Novedad litológica", "highlight")
        ],
        "cards": [
            {
                "tag": "Incertidumbre Epistémica",
                "tag_color": CLR_PURPLE,
                "title": "Variabilidad por Muestreo del Fondo (σ)",
                "body": "Al variar el fondo no etiquetado en 20 réplicas bagging, la desviación típica σ mide cuánto duda el modelo. Si las 20 réplicas coinciden en dar alto score, la certeza geológica es máxima."
            },
            {
                "tag": "Detección Out-of-Domain",
                "tag_color": CLR_CYAN,
                "title": "Distancia Z-Score en 56 Covariables (DZ > 3.0)",
                "body": "Calcula la distancia normalizada multivariable respecto a los yacimientos conocidos. Si DZ > 3.0, el modelo está extrapolando en formaciones litológicas sin análogo conocido."
            },
            {
                "tag": "Decisión de Perforación",
                "tag_color": CLR_EMERALD,
                "title": "Matriz 2D: Minimización de Riesgo Financiero",
                "body": "Un sondeo minero cuesta >150.000€. GeoAI permite asignar presupuesto prioritario a celdas de Alta Favorabilidad + Baja Incertidumbre, evitando costosos fallos en zonas dudosas."
            }
        ],
        "takeaway": "Un modelo que predice un número sin cuantificar su incertidumbre y extrapolación carece de utilidad industrial."
    }
    s3 = build_code_explainability_slide(prs, cfg_3)

    # -------------------------------------------------------------------------
    # SLIDE TÉCNICA 4: PERMUTATION IMPORTANCE & SHAP LOCAL (NB 12 & 17)
    # -------------------------------------------------------------------------
    cfg_4 = {
        "category": "CODE EXPLAINABILITY · AUDITORÍA GEOCIENTÍFICA SHAP",
        "section_tag": "CUADERNOS 12 & 17 · PERMUTATION IMPORTANCE ESPACIAL & TREESHAP LOCAL",
        "title": "Código Clave: Explicabilidad Aditiva y Plausibilidad Varisca",
        "subtitle": "Audita matemáticamente qué variables impulsan cada predicción y confirma alineación con el orógeno varisco.",
        "file_badge": "notebooks/12_random_forest_espacial.ipynb & 17_fase_h (Secciones XAI)",
        "code_lines": [
            ("# 1. Importancia por Permutación sobre Folds Espaciales:", "comment"),
            ("perm_res = permutation_importance(", "code"),
            ("    best_rf, X_spatial_val, y_spatial_val,", "code"),
            ("    scoring='roc_auc', n_repeats=10, random_state=42", "highlight"),
            (")", "code"),
            ("# litologia_u008: 17.07% | edades_u006: 16.24% | relieve: 6.11%", "comment"),
            ("", "code"),
            ("# 2. Descomposición Local TreeSHAP para El Valle-Boinás:", "comment"),
            ("explainer = shap.TreeExplainer(best_rf)", "code"),
            ("shap_vals = explainer.shap_values(X_boinas)", "highlight"),
            ("", "code"),
            ("# 3. Atribución aditiva de evidencias geológicas locales:", "comment"),
            ("# Base value: 0.14 | Salida final celda: 0.962", "comment"),
            ("# + Cizalla Narcea (+0.32) + Calizas Láncara (+0.28) + Plutón (+0.19)", "comment")
        ],
        "cards": [
            {
                "tag": "Permutación Espacial",
                "tag_color": CLR_GOLD,
                "title": "Resistencia a la Multicolinealidad",
                "body": "A diferencia del Gini importance tradicional (que favorece variables continuas o correlacionadas), la permutación sobre bloques espaciales mide la pérdida real de discriminación al destruir una señal."
            },
            {
                "tag": "Firma Metalogenética",
                "tag_color": CLR_CYAN,
                "title": "Coherencia Geocientífica Confirmada",
                "body": "Los predictores dominantes (pizarras u008 y cámbrico u006) reflejan las trampas químicas y estratigráficas donde precipita el oro orogénico en el Macizo Ibérico, descartando espuriedades."
            },
            {
                "tag": "Defensa en Comité",
                "tag_color": CLR_EMERALD,
                "title": "Desglose Transparente por Yacimiento",
                "body": "En la mina canónica de El Valle-Boinás (0.962), SHAP demuestra exactamente cuántos puntos aporta la cercanía a la falla principal, el tipo de roca y la aureola térmica granítica."
            }
        ],
        "takeaway": "El modelo no actúa como una caja negra: cada predicción territorial cuenta con su desglose auditado ante geólogos senior."
    }
    s4 = build_code_explainability_slide(prs, cfg_4)

    # -------------------------------------------------------------------------
    # SLIDE TÉCNICA 5: ESPECIALIZACIÓN METALOGENÉTICA ROCA VS ALUVIAL (NB 13)
    # -------------------------------------------------------------------------
    cfg_5 = {
        "category": "CODE EXPLAINABILITY · BIFURCACIÓN METALOCÉNICA",
        "section_tag": "CUADERNO DIDÁCTICO 13 · DESACOPLAMIENTO DE TIPOLOGÍAS MINERALES",
        "title": "Código Clave: Modelado Independiente (Oro en Roca vs Aluvial)",
        "subtitle": "Desacopla sistemas hidrotermales de fractura de trampas sedimentarias cuaternarias para máxima precisión.",
        "file_badge": "notebooks/13_comparacion_modelos.ipynb (Entrenamiento Especializado)",
        "code_lines": [
            ("# 1. Segmentación del catálogo mineral según génesis:", "comment"),
            ("mask_roca    = df_indicios['tipo_au'] == 'roca'     # 457 indicios", "highlight"),
            ("mask_aluvial = df_indicios['tipo_au'] == 'aluvial'  # 330 indicios", "highlight"),
            ("", "code"),
            ("# 2. Pipelines independientes con firmas contrastadas:", "comment"),
            ("model_roca = LightGBM(max_depth=5, learning_rate=0.03)", "code"),
            ("model_roca.fit(X_roca, y_roca)       # Prioriza fallas y skarns", "code"),
            ("", "code"),
            ("model_aluv = LightGBM(max_depth=4, learning_rate=0.02)", "code"),
            ("model_aluv.fit(X_aluv, y_aluv)       # Prioriza cauces y terrazas", "code"),
            ("", "code"),
            ("# 3. Evaluación en Spatial CV independiente:", "comment"),
            ("# -> ROC Oro en Roca: 0.976 | Foco: Cizallas y aureolas térmicas", "comment"),
            ("# -> ROC Oro Aluvial: 0.951 | Foco: Paleorredes y abanicos aluviales", "comment")
        ],
        "cards": [
            {
                "tag": "Conflicto Genético",
                "tag_color": CLR_GOLD,
                "title": "Controles Físicos Opuestos",
                "body": "Un yacimiento en roca primaria requiere fallas activas y fuertes contrastes topográficos. Un placer aluvial requiere baja pendiente, terrazas fluviales y meteorización de gravas."
            },
            {
                "tag": "Bifurcación Algorítmica",
                "tag_color": CLR_CYAN,
                "title": "Modelos Especializados (ROC 0.976 vs 0.951)",
                "body": "Al desacoplar el target, el modelo de roca deja de verse contaminado por la señal fluvial, y el modelo aluvial no se ve penalizado por estar lejos de fallas orogénicas profundas."
            },
            {
                "tag": "Aplicación de Negocio",
                "tag_color": CLR_EMERALD,
                "title": "Estrategia de Explotación Diferenciada",
                "body": "Permite al cliente o empresa minera filtrar objetivos según el método de explotación: minería subterránea/cielo abierto de alta ley en roca vs gravas de lavado aluvial continuo."
            }
        ],
        "takeaway": "Resolución de la fricción geológica: no existe un único 'oro', sino dos sistemas con leyes físicas completamente diferentes."
    }
    s5 = build_code_explainability_slide(prs, cfg_5)

    return [s1, s2, s3, s4, s5]

def reorder_slides(prs):
    """
    Inserta las 5 diapositivas creadas justo después de la Diapositiva 10 (09 · EXPLICABILIDAD).
    """
    print("-> Reordenando diapositivas en la secuencia didáctica final...")
    sldIdLst = prs.slides._sldIdLst
    total_slides = len(sldIdLst)
    print(f"Total diapositivas antes de reordenar: {total_slides}")
    
    # Las 5 diapositivas nuevas fueron agregadas al final (índices 17, 18, 19, 20, 21)
    # Queremos moverlas justo después de la diapositiva 10 (índice 9), es decir, en los índices 10, 11, 12, 13, 14.
    new_slide_elems = [sldIdLst[i] for i in range(17, total_slides)]
    
    # Remover del final
    for elem in new_slide_elems:
        sldIdLst.remove(elem)
        
    # Insertar en orden a partir del índice 10
    target_pos = 10
    for i, elem in enumerate(new_slide_elems):
        sldIdLst.insert(target_pos + i, elem)
        
    print(f"-> Diapositivas técnicas insertadas en posiciones 11 a 15 (1-based).")

def update_slide_numbers_and_titles(prs):
    """
    Actualiza la numeración en la esquina inferior de todas las diapositivas y títulos numerados.
    """
    print("-> Actualizando indicadores numéricos y títulos de sección...")
    total = len(prs.slides)
    
    for idx, slide in enumerate(prs.slides):
        real_num = idx + 1
        
        # 1. Actualizar placeholder de número de diapositiva
        for shape in slide.shapes:
            if "slide number" in shape.name.lower():
                if shape.has_text_frame:
                    shape.text_frame.text = str(real_num)
            elif shape.has_text_frame and shape.text_frame.text.strip().isdigit() and len(shape.text_frame.text.strip()) <= 2:
                # Solo actualizar si parece ser un contador
                val = int(shape.text_frame.text.strip())
                if 1 <= val <= total:
                    shape.text_frame.text = str(real_num)

        # 2. Actualizar numeración de sección de las diapositivas posteriores a las técnicas
        # Diapositiva 16 (antes 11): 10 · RESULTADO
        if real_num == 16:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        if "10 · RESULTADO" in p.text:
                            p.text = "15 · RESULTADO TERRITORIAL"
        # Diapositiva 17 (antes 12): 11 · EXPLICACIÓN LOCAL
        elif real_num == 17:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        if "11 · EXPLICACIÓN LOCAL" in p.text:
                            p.text = "16 · EXPLICACIÓN LOCAL EN YACIMIENTO"
        # Diapositiva 19 (antes 14): 12 · DEMO SCRIPT
        elif real_num == 19:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        if "12 · DEMO" in p.text:
                            p.text = "18 · DEMO INTERACTIVA"
        # Diapositiva 20 (antes 15): 13 · QUÉ HEMOS CONSTRUIDO
        elif real_num == 20:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        if "13 · QUÉ HEMOS CONSTRUIDO" in p.text:
                            p.text = "19 · ARQUITECTURA DE VALOR"
        # Diapositiva 21 (antes 16): 14 · EVOLUCIÓN
        elif real_num == 21:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        if "14 · EVOLUCIÓN" in p.text:
                            p.text = "20 · ROADMAP & EVOLUCIÓN"

def main():
    print("=" * 80)
    print("ACTUALIZACIÓN PROFESIONAL DE PRESENTACIÓN GEOAI v3.0 CON EXPLICABILIDAD DE CÓDIGO")
    print("=" * 80)
    
    # 1. Verificar backup
    if not BACKUP_PATH.exists():
        shutil.copyfile(PPTX_PATH, BACKUP_PATH)
        print(f"[OK] Backup creado en: {BACKUP_PATH}")
        
    prs = Presentation(str(PPTX_PATH))
    print(f"Presentación cargada. Diapositivas iniciales: {len(prs.slides)}")
    
    # 2. Actualizar diapositivas existentes
    update_existing_slides(prs)
    
    # 3. Generar las 5 diapositivas técnicas de código
    generate_all_technical_slides(prs)
    
    # 4. Reordenar diapositivas en la secuencia didáctica final
    reorder_slides(prs)
    
    # 5. Actualizar numeración consecutiva
    update_slide_numbers_and_titles(prs)
    
    # 6. Guardar archivo final
    prs.save(str(PPTX_PATH))
    print(f"[ÉXITO] Presentación actualizada y guardada en: {PPTX_PATH.relative_to(ROOT)}")
    print(f"Total diapositivas finales: {len(prs.slides)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
