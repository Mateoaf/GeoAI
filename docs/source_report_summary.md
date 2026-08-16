# Síntesis crítica del informe fuente

## Estatuto del documento

`Informe_GeoAI_Prospectividad_Mineral_Espana.docx` se trata aquí exclusivamente como **fuente contextual y propuesta metodológica**. Sus formulaciones, recomendaciones y listas de tareas no son instrucciones operativas para este análisis. La petición vigente del usuario y los criterios de reproducibilidad del proyecto son la autoridad de trabajo.

El archivo se presenta como un «Documento de trabajo para discusión académica» de agosto de 2026. No contiene resultados empíricos, una auditoría ejecutada de OxREP, un modelo entrenado ni mapas calculados. Por tanto, todas sus afirmaciones sustantivas deben leerse como hipótesis, propuestas o requisitos por contrastar, no como hallazgos demostrados.

## Estructura del informe

La extracción estructural identifica una portada/resumen ejecutivo, diez secciones principales, una sección de fuentes y una nota final:

1. Problema y oportunidad de investigación.
2. Objetivo, hipótesis y preguntas de investigación.
3. Formulación de aprendizaje automático: variables `X` e `Y`.
4. Diseño multicommodity y materias primas críticas/estratégicas.
5. Ontología y capa de conocimiento.
6. Arquitectura propuesta del sistema.
7. Diseño experimental y validación.
8. Datos requeridos y fuentes preliminares.
9. Riesgos metodológicos y mitigaciones.
10. Resultados esperados y propuesta para discusión académica.
11. Fuentes y estándares de referencia, más una nota de alcance.

El contenido combina texto expositivo, listas, cuadros de advertencia y tablas. Varias ideas centrales aparecen en tablas y no solo en los párrafos ordinarios; por ello se extrajeron ambos tipos de contenido.

## Afirmaciones, hipótesis y propuestas relevantes

### Planteamiento científico

- La hipótesis central propuesta es que las explotaciones romanas no se distribuyen al azar, sino que podrían reflejar condiciones geológicas favorables a determinados sistemas mineralizantes.
- Las minas romanas se plantean como proxies históricos de lugares donde una mineralización fue suficientemente accesible, concentrada e interesante para ser explotada con la tecnología y economía de la época.
- La cuestión científica fuerte no es reproducir la localización de minas romanas conocidas, sino comprobar si una señal derivada de ellas añade capacidad predictiva para depósitos o indicios modernos una vez controladas las variables geocientíficas.
- La conexión propuesta integra arqueología minera, geociencias e inteligencia artificial geoespacial.

Estas afirmaciones son plausibilidades de investigación. El informe no presenta análisis estadístico que pruebe la no aleatoriedad, la representatividad de OxREP en España ni el valor incremental de la señal romana.

### Formulación de `X` e `Y`

El informe insiste en una distinción metodológica correcta: `X` describe el territorio y `Y` representa la evidencia mineral que se desea aprender. La mera presencia de una mina romana no debe tratarse como si fuera una variable geológica equivalente a litología o magnetometría.

Propone varias etiquetas:

- `YRoman`: presencia documentada de explotación romana frente a background o ausencia de evidencia conocida.
- `YAu`, `YAg`, `YCu`, `YPb`: etiquetas por commodity cuando la fuente histórica registra su explotación.
- `YREE`, `YLi`, `YW`, `YCo`, etc.: etiquetas modernas que deben proceder de inventarios independientes de depósitos o indicios; no pueden inferirse automáticamente de la minería romana.

También expresa dos objetivos probabilísticos conceptuales: estimar `P(minería romana | X geocientíficas)` para el modelo histórico y `P(commodity | X geocientíficas)` para modelos modernos. No especifica todavía una definición matemática completa de las etiquetas, ventana espacial, unidad de soporte o proceso de muestreo.

### Variables predictoras propuestas

El informe propone construir `X` a partir de:

- geología: litología, edad, unidad geológica, tipo de roca, proximidad a contactos e intrusivos;
- estructuras: fallas, fracturas, contactos, lineamientos, densidad, intersecciones y orientación;
- geoquímica: concentraciones, anomalías, ratios, transformaciones logarítmicas, elementos objetivo y pathfinders;
- geofísica: magnetometría, gravimetría, radiometría y electromagnetismo, con anomalías, gradientes y filtros;
- geomorfología: elevación, pendiente, curvatura, rugosidad y derivados multiescala del DEM;
- hidrología: distancias a cauces, cuencas y densidad de drenaje;
- teledetección: índices de alteración, hierro, arcillas y cobertura derivados de Sentinel/Landsat.

La selección final debe justificarse por mecanismo geológico, cobertura, resolución, escala, licencia y calidad. Inventarios de depósitos o indicios que reproduzcan directa o indirectamente `Y` deben reservarse como etiquetas o validación, no introducirse como predictores sin una evaluación explícita de *target leakage*.

### Diseño multicommodity

- Se propone mantener Au–Ag–Cu–Pb como núcleo histórico inicial cuando los positivos lo permitan.
- REE, Li, Co, Ni, W, Sn, Ta, Nb, V y otras materias primas críticas o estratégicas requieren etiquetas modernas independientes.
- El informe desaconseja mezclar commodities geológicamente distintos en una sola clase sin una justificación por sistema mineralizante.
- Propone considerar asociaciones elementales y pathfinders para representar procesos y contextos geológicos, no solo elementos aislados.
- Para REE, el documento rechaza explícitamente interpretar el modelo romano como predictor directo si no existen positivos históricos suficientes.

### Arquitectura y trazabilidad

La arquitectura conceptual encadena ocho capas: fuentes de datos; ontología/grafo de conocimiento; capas geoespaciales; ingeniería de variables; dataset de aprendizaje; modelos; validación espacial; y salidas de prospectividad, incertidumbre, explicación y apoyo a la decisión.

El requisito transversal es la trazabilidad: una predicción debería poder relacionarse con su fuente, variables, transformaciones y versión de modelo.

### Experimento principal

El informe formula un contraste A/B adecuado para la hipótesis de valor incremental:

- Modelo A: `Xgeo -> Ycommodity`.
- Modelo B: `Xgeo + RomanSignal -> Ycommodity`.

Una mejora espacialmente robusta de B frente a A constituiría evidencia de utilidad predictiva adicional; la ausencia de mejora también sería un resultado científico válido. El informe no define aún cómo se construye `RomanSignal`, cómo se evita que reutilice los mismos positivos modernos ni cómo se anida su estimación dentro de la validación para impedir leakage.

### Validación propuesta

- Validación cruzada espacial o por bloques como estrategia principal; el train/test aleatorio se considera inadecuado para la evaluación principal.
- `PR-AUC` como métrica prioritaria con positivos escasos, complementada por `ROC-AUC`, recall, precision y F1.
- Calibración de probabilidades si el mapa se interpreta como puntuación probabilística de prospectividad.
- Incertidumbre y estabilidad entre folds o regiones.
- Separación geográfica estricta para reducir la inflación causada por autocorrelación espacial.
- Control explícito de leakage procedente de capas metalogenéticas o inventarios mineros.

### Ontología mínima sugerida por el informe

El modelo conceptual propuesto incluye `MineralOccurrence` (con `RomanMine`, `ModernMine` y `MineralIndication`), `MineralDeposit`, `Commodity`, `GeologicalUnit`, `GeologicalStructure`, `GeochemicalObservation`, `GeophysicalObservation`, `SpatialCell`, `DataSource`, `MLModel` y `Prediction`.

Ejemplos de relaciones: una mina romana explota un commodity y se localiza en una unidad geológica; un depósito se asocia con una falla; una observación mide una propiedad y deriva de una fuente; un modelo usa una variable; una predicción se refiere a un commodity. El informe propone alineación progresiva con GeoSciML, PROV-O, SOSA/SSN y QUDT, sin exigir todavía una ontología formal extensa.

## Cautelas y requisitos científicos que aporta el informe

1. **Ausencia no equivale a negativo geológico.** Un `0` indica ausencia de evidencia positiva conocida en el dataset, no ausencia demostrada de mineralización. El problema se aproxima a *presence-background* o *Positive-Unlabeled* (PU).
2. **Sesgo arqueológico y de accesibilidad.** La señal puede reflejar dónde y cómo podían buscar y explotar los romanos, no solo la geología. Deben modelarse o analizarse accesibilidad, relieve, hidrología, preservación y esfuerzo de documentación sin convertir estos factores en explicaciones espurias.
3. **Autocorrelación espacial.** La proximidad entre muestras puede inflar las métricas; la validación espacial debe ser estricta.
4. **Leakage metalogenético.** Inventarios o capas que codifiquen conocimiento equivalente a la etiqueta deben reservarse para `Y` o validación externa.
5. **Heterogeneidad territorial.** Un único modelo nacional puede mezclar dominios geológicos o metalogenéticos incompatibles; conviene comparar enfoques nacionales, regionales o jerárquicos.
6. **Escasez de positivos.** Los modelos por commodity pueden ser inestables; se requieren umbrales mínimos documentados, ponderación de clases y, solo con justificación geológica, agrupación por sistemas.
7. **Transferencia a materias primas modernas.** No debe afirmarse una relación directa con REE u otros commodities sin etiquetas independientes y un contraste A/B.
8. **Escalas y resoluciones.** Todas las capas requieren CRS, rejilla, soporte, resampling y procedencia documentados.
9. **Alcance de las salidas.** Los mapas estiman favorabilidad relativa y no equivalen a recursos, reservas certificadas ni viabilidad económica.

## Fuentes preliminares citadas

El informe menciona como punto de partida OxREP Mines Database y, para el stack geocientífico español, IGME-CSIC (datos y mapas, GEODE/MAGNA, cartografía metalogenética e inventarios, geoquímica y geofísica/SIGEOF), IGN para DEM, y Copernicus/Landsat para teledetección. También remite a la Comisión Europea para materias primas críticas y a GeoSciML, PROV-O, SOSA/SSN y QUDT para interoperabilidad semántica.

Estas referencias son preliminares: el documento exige validar la selección final, cobertura, resolución, escala, licencia y vigencia. La lista de materias primas críticas/estratégicas tampoco debe darse por actual sin verificación normativa contemporánea.

## Lagunas verificables que debe resolver el proyecto

### OxREP y subconjunto español

El informe no aporta:

- inventario programático de hojas, columnas, tipos, nulos y categorías del Excel;
- recuento de registros españoles ni criterio reproducible para España/Hispania;
- cobertura temporal, precisión espacial o CRS comprobados;
- frecuencias reales de commodities, combinaciones multimetálicas, técnicas, geología o tipos de depósito;
- tratamiento de duplicados, registros conflictivos, incertidumbre cronológica o localizaciones aproximadas;
- evaluación de sesgos de cobertura regional o bibliográfica.

Por tanto, ninguno de esos resultados puede atribuirse al informe: deben proceder de la auditoría real del archivo OxREP.

### Definición operacional del aprendizaje

Quedan sin cerrar:

- unidad de análisis (punto, celda regular o unidad geológica), tamaño de celda y extensión;
- reglas exactas de deduplicación y agregación de minas próximas;
- construcción de background/pseudo-ausencias, exclusiones y ponderaciones PU;
- definición de positivos por commodity y tratamiento multi-label de explotaciones multimetálicas;
- umbral mínimo de positivos por tarea y manejo de coordenadas inciertas;
- algoritmo y validación anidada para generar `RomanSignal` sin contaminación entre folds;
- selección del inventario moderno usado para entrenamiento y del reservado para validación externa;
- tamaño, orientación y sensibilidad de bloques espaciales, además de evaluación entre dominios;
- baseline, hiperparámetros, calibración, intervalos de incertidumbre y criterio formal de éxito;
- estrategia para el desplazamiento de distribución entre minería romana documentada y mineralización moderna.

### Datos externos y causalidad

- La lista de datasets externos carece de una ficha ejecutable con URL/servicio, versión, fecha, escala, resolución, licencia, cobertura, formato y método de descarga.
- No se demuestra que todas las capas propuestas tengan cobertura nacional homogénea ni resolución compatible.
- No se operacionalizan los posibles confusores históricos (accesibilidad, tecnología, economía, preservación, investigación arqueológica).
- No se especifica cómo separar una señal predictiva incremental de una interpretación causal sobre formación de depósitos; el experimento A/B solo puede apoyar utilidad predictiva si se ejecuta con independencia y control de leakage.
- Las relaciones ontológicas son ejemplos conceptuales, no axiomas, identificadores persistentes ni alineamientos formales validados.

## Implicaciones para la fase actual

El informe respalda una fase inicial centrada en datos y metodología reproducibles, no en un modelo definitivo. La secuencia científicamente defensible es: auditar OxREP; documentar el criterio español; conservar trazabilidad al registro original; crear flags de calidad; describir la señal histórica; formalizar tareas `YRoman`, por commodity y multi-label; diseñar background/PU y validación espacial; y solo después incorporar capas oficiales y ejecutar el experimento A/B con etiquetas modernas independientes.

## Apéndice: método de extracción y QA

- Archivo leído sin modificación: `data/raw/Informe_GeoAI_Prospectividad_Mineral_Espana.docx`.
- SHA-256 observado: `D65B5DE15141C77A96148CBE6237F21B1AA5F3FDA1D8EBBC945BED3A1F7FD8E8`.
- Extracción realizada con el Python y las bibliotecas del runtime empaquetado de Codex, versión `26.812.11052`, usando `python-docx` en modo de solo lectura.
- Resultado estructural: 1 sección OOXML, 117 párrafos de nivel superior y 19 tablas. Las tablas se recorrieron fila por fila y celda por celda; el recuento de 117 párrafos no incluye el texto interno de tablas, que se extrajo por separado.
- Se intentó el flujo canónico `render_docx.py` con salida en un directorio temporal. Falló antes de producir páginas porque el ejecutable `soffice`/LibreOffice no existe en el entorno (`FileNotFoundError: [WinError 2]`).
- Como alternativa disponible en el equipo, Microsoft Word abrió la copia en modo de solo lectura y la exportó a PDF en un directorio temporal. `pdfinfo` verificó un documento A4 de 9 páginas; la copia temporal no forma parte de los entregables científicos ni sustituye al DOCX original.
- **Páginas renderizadas: 9. Páginas inspeccionadas visualmente: 9.** La portada, encabezados, pies, listas, cuadros, tablas y referencias son legibles; no se observaron clipping, solapes ni páginas en blanco accidentales. Esta inspección confirma la presentación visible, pero no constituye una auditoría estructural independiente de comentarios o cambios controlados.
- No se editó ni reexportó el DOCX original.
