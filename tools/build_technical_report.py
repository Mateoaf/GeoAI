from __future__ import annotations

import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "GeoAI_OxREP_Espana_Base_Tecnica.pdf"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def page_number(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(1.8 * cm, 1.35 * cm, A4[0] - 1.8 * cm, 1.35 * cm)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1.8 * cm, 0.9 * cm, "GeoAI - OxREP España | base técnica reproducible")
    canvas.drawRightString(A4[0] - 1.8 * cm, 0.9 * cm, f"Página {document.page}")
    canvas.restoreState()


def table(data, widths, repeat_rows=1, font_size=7.5):
    result = Table(data, colWidths=widths, repeatRows=repeat_rows, hAlign="LEFT")
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#164E63")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("LEADING", (0, 0), (-1, -1), font_size + 2),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#0E7490")),
                ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#E2E8F0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return result


def build() -> None:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=30,
            textColor=colors.HexColor("#0F3D56"),
            alignment=TA_CENTER,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=17,
            textColor=colors.HexColor("#52606D"),
            alignment=TA_CENTER,
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1Blue",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0F3D56"),
            spaceBefore=10,
            spaceAfter=7,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2Teal",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor("#0F766E"),
            spaceBefore=8,
            spaceAfter=5,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyReport",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=13.2,
            textColor=colors.HexColor("#243B53"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletReport",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.1,
            leading=13,
            leftIndent=13,
            firstLineIndent=-8,
            bulletIndent=0,
            textColor=colors.HexColor("#243B53"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletCompact",
            parent=styles["BulletReport"],
            fontSize=8.7,
            leading=11.8,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReferenceReport",
            parent=styles["BodyReport"],
            fontSize=8.4,
            leading=10.2,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10.2,
            leading=14.5,
            textColor=colors.HexColor("#7C2D12"),
            backColor=colors.HexColor("#FFF7ED"),
            borderColor=colors.HexColor("#FDBA74"),
            borderWidth=0.6,
            borderPadding=9,
            spaceBefore=8,
            spaceAfter=10,
        )
    )

    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
        title="GeoAI - OxREP España: base técnica y científica reproducible",
        author="Codex",
        subject="Auditoría OxREP, dataset español, ML, validación y ontología",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=page_number)])

    commodity = rows(ROOT / "reports" / "tables" / "commodity_summary.csv")
    techniques = rows(ROOT / "reports" / "tables" / "technique_summary.csv")
    quality = rows(ROOT / "reports" / "tables" / "quality_flag_summary.csv")
    combos = rows(ROOT / "reports" / "tables" / "commodity_combinations.csv")
    validation = json.loads(
        (ROOT / "reports" / "audit" / "validation_report.json").read_text(encoding="utf-8")
    )

    story = [Spacer(1, 1.4 * cm)]
    story.append(Paragraph("GeoAI de prospectividad mineral y minería romana en España", styles["ReportTitle"]))
    story.append(
        Paragraph(
            "Auditoría OxREP 3.0, dataset español trazable y diseño científico para evaluar la señal histórica romana",
            styles["ReportSubtitle"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            "FASE DE BASE REPRODUCIBLE - NO SE HA ENTRENADO UN MODELO DEFINITIVO",
            styles["Callout"],
        )
    )
    cover_data = [
        ["Datos primarios", "OxREP Mines Database v3.0 (2025)"],
        ["Antecedente MPM", "Rodríguez-Galiano et al. (2015), Rodalquilar"],
        ["Libro auditado", "1.399 registros x 47 campos"],
        ["Subconjunto España", "930 registros; 923 con coordenadas"],
        ["Salidas", "CSV ancho/largo, GeoJSON, SQLite, tablas, gráficos y documentación"],
        ["Corte", "14 de agosto de 2026"],
    ]
    story.append(table(cover_data, [4.2 * cm, 11.2 * cm], repeat_rows=0, font_size=9))
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "Pregunta futura: ¿mejora una señal derivada de explotaciones romanas la predicción espacial de mineralización moderna por encima de X geológica? La respuesta queda reservada para el experimento espacial A/B con labels modernos.",
            styles["BodyReport"],
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("1. Resultado ejecutivo", styles["H1Blue"]))
    for text in [
        "El criterio directo country=Spain produce 929 fichas. Se añade de forma explícita mineID 132 (Lanz), almacenado por OxREP con country=Navarra y coordenadas dentro de Navarra. El valor original no se corrige: queda marcado por flag.",
        "Au domina con 598 fichas. Ag, Pb y Cu tienen 174, 169 y 169; 177 registros son multimetálicos. Fe, Sn, Hg y Zn son demasiado escasos para modelos independientes robustos sin más labels.",
        "La base está espacialmente concentrada: León y Oviedo reúnen aproximadamente la mitad de las fichas. Esto hace inadecuado un train/test aleatorio como estrategia principal.",
        "No se ha eliminado ningún caso por falta de coordenadas, categorías anómalas, texto corrupto o posible duplicidad. Se conserva mineID, fila Excel, hash del libro y hash de fila.",
        "El antecedente de Rodalquilar fundamenta la matriz MPM multifuente y RF como baseline sólido, pero sus métricas y validación no se trasladan al experimento nacional.",
    ]:
        story.append(Paragraph("- " + text, styles["BulletReport"]))
    story.append(
        Paragraph(
            "La ausencia de mina romana no implica ausencia de mineralización. Y_roman y las etiquetas por commodity deben plantearse como presence-background o positive-unlabeled.",
            styles["Callout"],
        )
    )

    story.append(Paragraph("2. Auditoría del Excel", styles["H1Blue"]))
    story.append(
        Paragraph(
            "La hoja principal ocupa A1:AU1400 y contiene 1.399 filas de datos; Sheet1 está vacía. mineID está completo y es único, con rango 1-1780 y huecos que no se imputan. No hay fórmulas. El libro no incluye diccionario de datos, CRS Lambert ni unidad/semántica formal de coordinateAccuracy.",
            styles["BodyReport"],
        )
    )
    story.append(
        Paragraph(
            "Control técnico: un renderizador de hojas mostró el índice 53 de sharedStrings en celdas cuyo string real es vacío. El pipeline usa pandas/openpyxl, que resuelven correctamente el XML; 53 no se trata como dato.",
            styles["BodyReport"],
        )
    )
    story.append(Paragraph("Criterio de selección", styles["H2Teal"]))
    story.append(
        Paragraph(
            "Se normalizan solo espacios exteriores y capitalización de country, se incluyen las 929 filas Spain y el override revisado de Lanz. No se usa province (las provincias romanas incluyen Portugal) ni una caja espacial, que capturaría Portugal y Francia. La validación administrativa point-in-polygon se realizará al congelar un límite oficial IGN.",
            styles["BodyReport"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("3. Commodities y multimetalismo", styles["H1Blue"]))
    commodity_data = [["Commodity", "Presente", "Ausente", "Desconocido", "No informado"]]
    for item in commodity:
        commodity_data.append(
            [
                item["commodity_name"],
                item["confirmed_present"],
                item["confirmed_absent"],
                item["unknown"],
                item["missing"],
            ]
        )
    story.append(table(commodity_data, [5.2 * cm, 2.4 * cm, 2.4 * cm, 2.7 * cm, 2.7 * cm], font_size=8))
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        Image(str(ROOT / "reports" / "figures" / "commodity_counts.png"), width=16.7 * cm, height=8.25 * cm)
    )
    combo_data = [["Combinación", "Registros"]] + [
        [item["commodity_combination"], item["count"]] for item in combos[:10]
    ]
    story.append(Spacer(1, 0.2 * cm))
    story.append(table(combo_data, [11.5 * cm, 3.8 * cm], font_size=8))

    story.append(PageBreak())
    story.append(Paragraph("4. Técnicas y calidad espacial", styles["H1Blue"]))
    technique_data = [["Técnica", "Presente", "Ausente", "Desconoc./NA"]]
    for item in techniques:
        unknown = sum(int(item[field]) for field in ["unknown", "missing", "invalid"])
        technique_data.append(
            [item["technique_name"], item["confirmed_present"], item["confirmed_absent"], str(unknown)]
        )
    story.append(table(technique_data, [7.3 * cm, 2.5 * cm, 2.5 * cm, 3.3 * cm], font_size=8))
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        Image(str(ROOT / "reports" / "figures" / "technique_counts.png"), width=16.7 * cm, height=7.0 * cm)
    )
    story.append(
        Paragraph(
            "Hay 923 coordenadas completas. coordinateAccuracy presenta 8 nulos, 76 ceros y 23 valores mayores de 1.000. La unidad no está codificada y cero aparece con fuentes estimadas; se conserva como valor reportado, sin convertirlo en certeza.",
            styles["BodyReport"],
        )
    )
    story.append(PageBreak())
    story.append(Paragraph("5. Distribución espacial", styles["H1Blue"]))
    story.append(
        Image(str(ROOT / "reports" / "figures" / "spatial_distribution.png"), width=16.7 * cm, height=11.7 * cm)
    )
    story.append(
        Image(str(ROOT / "reports" / "figures" / "region_counts_top20.png"), width=15.1 * cm, height=12.0 * cm)
    )

    story.append(PageBreak())
    story.append(Paragraph("6. Flags y anomalías", styles["H1Blue"]))
    story.append(
        Paragraph(
            "Los flags son diagnósticos, no criterios de borrado. Un mismo registro puede activar varios; por tanto, sus recuentos no deben sumarse.",
            styles["BodyReport"],
        )
    )
    quality_selected = [item for item in quality if int(item["count"]) > 0]
    quality_data = [["Flag", "Severidad", "n"]]
    for item in quality_selected:
        label = item["flag"].replace("flag_", "").replace("_", " ")
        quality_data.append([Paragraph(label, styles["BodyReport"]), item["severity"], item["count"]])
    story.append(table(quality_data, [11.4 * cm, 2.6 * cm, 1.5 * cm], font_size=7.2))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            "Casos destacados para revisión: pares con coordenadas compartidas; Lagueiro I/Río Ibias prácticamente coincidentes y descritos como probablemente iguales; categorías dañadas como Prima[artefacto]; y Triunfo, compatible con desplazamiento de columnas. Todos permanecen en la tabla con trazabilidad.",
            styles["BodyReport"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("7. Definición de Y y X", styles["H1Blue"]))
    for heading, body in [
        (
            "Y_roman",
            "Presencia romana frente a celdas no etiquetadas. Sirve para estudiar el proceso espacial romano y generar una señal out-of-fold, no para declarar ausencia de mineralización.",
        ),
        (
            "Y por commodity",
            "Booleanos nullable para Au, Ag, Pb, Cu, Sn, Fe, Hg, Zn y Other. False en una ficha no convierte el territorio en negativo geológico; unknown/missing quedan NA.",
        ),
        (
            "Multi-label",
            "Una celda puede contener varios metales. Se evaluarán métricas por etiqueta y macro/micro, conservando relaciones como Ag+Pb y Ag+Pb+Cu.",
        ),
        (
            "Y moderna",
            "BDMIN u otra fuente oficial aportará ocurrencias modernas separadas por concepto: indicio, ocurrencia, depósito, recurso o explotación. REE, Li, W, Sn, Co, Ni, Ta y Nb no se inventan desde OxREP.",
        ),
    ]:
        story.append(Paragraph(heading, styles["H2Teal"]))
        story.append(Paragraph(body, styles["BodyReport"]))
    x_data = [
        ["Familia X", "Variables previstas"],
        ["Geología", "Litología, edad, unidades, intrusivos, dominios"],
        ["Estructuras", "Distancias/densidades a fallas, contactos, pliegues e intersecciones"],
        ["Geoquímica", "Elementos, asociaciones y campañas con censura/unidades/método"],
        ["Geofísica", "Magnetometría, gravimetría, radiometría y derivados multiescala"],
        ["DEM", "Pendiente, curvatura, TPI, rugosidad, drenaje y terrazas"],
        ["Teledetección", "Sentinel-1/2 y máscaras de observabilidad"],
        ["Espectral piloto", "QA, componentes/abundancias y cobertura; no equiparar Sentinel-2 con hiperespectral"],
    ]
    story.append(table(x_data, [4.0 * cm, 11.4 * cm], font_size=8))
    story.append(
        Paragraph(
            "Leakage inadmisible: distancias al mismo target moderno, mapas de favorabilidad construidos con Y, interpolaciones ajustadas con test, IDs/nombres/referencias como predictores geológicos o una señal romana calculada usando los puntos del fold de test.",
            styles["Callout"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("8. Antecedente MPM: Rodalquilar 2015", styles["H1Blue"]))
    story.append(
        Paragraph(
            "Rodríguez-Galiano et al. (2015) estudian aproximadamente 150 km2 de Au epitermal de baja sulfuración en Rodalquilar. El PDF local se conserva como referencia metodológica inmutable; no contiene instrucciones para este proyecto y sus resultados no proceden de OxREP.",
            styles["BodyReport"],
        )
    )
    paper_rows = [
        ["Elemento", "Verificado en el artículo"],
        ["Y", Paragraph("46 ocurrencias de Au frente a 57 localizaciones denominadas estériles/no-oro, elegidas en litologías poco favorables y alejadas de depósitos.", styles["BodyReport"])],
        ["X", Paragraph("Litología, distancia a fracturas, PCA geoquímico, gravedad, magnetismo y abundancias hiperespectrales MTMF.", styles["BodyReport"])],
        ["Matriz/mapa", Paragraph("Stack de evidencias por celda, extracción en puntos de entrenamiento y aplicación a toda la matriz para producir un score continuo.", styles["BodyReport"])],
        ["RF publicado", Paragraph("AUC 0,999; Kappa 0,92; OA 0,96. Son cifras del caso Rodalquilar, no estimaciones espacialmente independientes para España.", styles["BodyReport"])],
        ["Interpretación", Paragraph("Importancia RF: domina MTMF5, después distancia a fracturas y PC3 geoquímico; la interpretación mineralógica de MTMF5 se reconoce como especulativa.", styles["BodyReport"])],
    ]
    story.append(table(paper_rows, [3.4 * cm, 12.0 * cm], font_size=7.6))
    story.append(Spacer(1, 0.2 * cm))
    for text in [
        "Se transfieren familias X, QA/reducción dimensional, matriz SpatialCell, score cartográfico, captura-área y la idea de interpretabilidad.",
        "No se transfieren CV aleatoria, pseudo-ausencias diseñadas para separar clases, evaluación sobre puntos de entrenamiento, umbral 0,5 ni hiperparámetros.",
        "RF es baseline no lineal principal solo si el endpoint tiene suficientes grupos positivos por outer fold; se compara con un baseline regularizado transparente.",
        "Permutation importance agrupada se calcula en outer-test; TreeSHAP queda para después de congelar métricas y conclusiones.",
    ]:
        story.append(Paragraph("- " + text, styles["BulletCompact"]))
    story.append(
        Paragraph(
            "OxREP permite ahora EDA, QA y formulación. No permite entrenar Y_roman: las 930 filas son positivas y faltan background, matriz X y labels modernos. Por coordenadas únicas, Au=589 puede llegar a sostener RF espacial; Ag=174, Pb=169 y Cu=169 requieren complejidad conservadora; Fe/Sn/Hg/Zn quedan descriptivos.",
            styles["Callout"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("9. Validación espacial y experimento A/B", styles["H1Blue"]))
    for text in [
        "Congelar una partición outer primaria de bloques contiguos y buffers; rotaciones/tamaños son sensibilidades, no réplicas independientes. Duplicados y un mismo complejo permanecen juntos.",
        "Inner CV espacial para tuning, selección, imputación, PCA/MNF, calibración, umbrales y bandwidth romano. El outer test se abre solo para evaluación.",
        "Congelar la máscara background antes de splits; entrenar dentro de cobertura y comparar uniforme, por esfuerzo, geológicamente emparejado y PU. El test pareado no cambia entre A/B.",
        "Métrica primaria PR-AUC; secundarias ROC-AUC, recall, precision y F1 con umbral fijado solo en entrenamiento. Reportar por fold, repetición y región.",
        "Modelo A: X geológica y observacional admisible -> mineralización moderna.",
        "Modelo B: exactamente A + señal romana fold-aware, con los mismos folds, seeds, background, algoritmo y presupuesto de tuning.",
        "Contraste primario delta_PR-AUC sobre predicciones outer-OOF pareadas; IC95 por bootstrap de bloques; nulo con RomanSignal permutada/desplazada por bloques y B reentrenado.",
        "Exigir además ganancia práctica en captura-área; no usar t/Wilcoxon/DeLong sobre celdas autocorreladas o folds solapados.",
        "Reservar dominio, cohorte futura o inventario upstream independiente para evaluación final; si no existe, declarar validación independiente pendiente.",
    ]:
        story.append(Paragraph("- " + text, styles["BulletCompact"]))
    story.append(
        Paragraph(
            "La señal romana solo aporta valor si la mejora de B es estable fuera de muestra, práctica, resistente a placebos y backgrounds y no depende de una región dominante.",
            styles["Callout"],
        )
    )

    story.append(Paragraph("10. Ontología mínima", styles["H1Blue"]))
    ontology_data = [
        ["Entidad", "Función mínima"],
        ["RomanMine", "Evidencia de explotación romana, precisión y flags"],
        ["MineralOccurrence", "Observación moderna georreferenciada"],
        ["Deposit", "Sistema/depósito al que puede pertenecer una ocurrencia"],
        ["Commodity", "Sustancia normalizada"],
        ["CriticalRawMaterial", "Clasificación por jurisdicción y versión"],
        ["GeologicalUnit / Structure", "Contexto litoestratigráfico y estructural"],
        ["Geochemical / GeophysicalObservation", "Valor, unidad, método y fuente"],
        ["SpatialCell", "Unidad común de modelado versionada"],
        ["DataSource", "Procedencia, edición, licencia y checksum"],
    ]
    ontology_table = table(ontology_data, [5.4 * cm, 10.0 * cm], font_size=8)
    ontology_table.setStyle(
        TableStyle(
            [
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(ontology_table)
    story.append(
        Paragraph(
            "La relación RomanMine -> Deposit es possibleHistoricalEvidenceFor, nunca identidad automática. La ausencia de relación no expresa una negación. CriticalRawMaterial es temporal y jurisdiccional, no una propiedad permanente del elemento.",
            styles["BodyReport"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("11. Fuentes externas priorizadas", styles["H1Blue"]))
    sources_data = [
        ["Prioridad", "Fuente oficial", "Papel"],
        ["P0", "GEODE 1:50.000 / litoestratigráfico 1:200.000 (IGME)", "X geológica"],
        ["P0", "BDMIN (IGME)", "Y moderna positiva"],
        ["P0", "Base de Geoquímica / Atlas (IGME)", "X geoquímica"],
        ["P0", "SIGEOF (IGME)", "X geofísica"],
        ["P0", "MDT05, límites y costa (IGN-CNIG/IHM)", "DEM y máscaras"],
        ["P1", "Sentinel-1/2, hidrografía, QAFI, SIOSE", "Enriquecimiento/controles"],
        ["P1", "Catastro y estadísticas mineras", "Sesgo/QA; no Y automática"],
        ["P2", "EGDI, MIN4EU, GEMAS, COP-DEM", "Armonización/QA"],
    ]
    sources_table = table(sources_data, [2.1 * cm, 9.7 * cm, 3.6 * cm], font_size=7.7)
    sources_table.setStyle(
        TableStyle(
            [
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(sources_table)
    story.append(
        Paragraph(
            "GEODE vectorial requiere solicitud formal; el 1:200.000 permite iniciar. No se verificó una base nacional abierta, homogénea y geocodificada de tonelajes de recursos/reservas. Las APIs deben paginarse, guardar recuentos, fecha, licencia y SHA-256.",
            styles["BodyReport"],
        )
    )
    story.append(
        Paragraph(
            "Lineage obligatorio: cada label moderno conservará fuente upstream, campaña y relaciones de derivación. MIN4EU, GEODE-MPMIN o un mapa metalogenético que replique BDMIN sirven para QA, no como validación independiente del mismo target.",
            styles["BodyReport"],
        )
    )
    story.append(
        Paragraph(
            "La cadena hiperespectral de Rodalquilar justifica pilotos solo donde exista cobertura y mecanismo geológico verificables. Sentinel-2 aporta proxies de banda ancha y no se presentará como sustituto mineralógico de Hyperion.",
            styles["BodyReport"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("12. Reproducibilidad y cierre", styles["H1Blue"]))
    checks = validation["checks"]
    check_data = [["Comprobación", "Resultado"]] + [
        [key.replace("_", " "), str(value)] for key, value in checks.items()
    ]
    check_table = table(check_data, [11.8 * cm, 3.6 * cm], font_size=7.3)
    check_table.setStyle(
        TableStyle(
            [
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(check_table)
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        Paragraph(
            "El README contiene el comando de reproducción. input_manifest registra Excel, DOCX y PDF metodológico; output_manifest registra todos los entregables. Nueve pruebas automatizadas reconcilian selección, IDs, commodities, GeoJSON, SQLite y el hash del artículo. OxREP conserva el hash 802e35d0abef469fb7683b3b82b1638224db059f19919a2e245ce44ec757815a; el PDF metodológico, cdf214f36a6b873baca278812b60f2992ef91cbfe9f76ed1876b0eb5cb9c89d0.",
            styles["BodyReport"],
        )
    )
    story.append(
        Paragraph(
            "Conclusión: la base técnica de esta fase está preparada. La hipótesis central sigue abierta y solo podrá responderse después de integrar X oficial, labels modernos y ejecutar la validación espacial predefinida.",
            styles["Callout"],
        )
    )
    story.append(Paragraph("Referencias institucionales", styles["H2Teal"]))
    for text in [
        "Wilson, A. I. (2025). Database of Roman mines, Version 3.0. https://oxrep.web.ox.ac.uk/mines-database",
        "Rodríguez-Galiano, V. et al. (2015). Machine learning predictive models for mineral prospectivity. https://doi.org/10.1016/j.oregeorev.2015.01.001",
        "IGME-CSIC, cartografía y bases oficiales: https://info.igme.es/ y https://mapas.igme.es/",
        "IGN-CNIG / Copernicus: https://centrodedescargas.cnig.es/ | https://dataspace.copernicus.eu/",
    ]:
        story.append(Paragraph(text, styles["ReferenceReport"]))

    doc.build(story)
    import sys

    source_dir = str(ROOT / "src")
    if source_dir not in sys.path:
        sys.path.insert(0, source_dir)
    from geoai_roman_spain.pipeline import refresh_output_manifest

    refresh_output_manifest(ROOT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
