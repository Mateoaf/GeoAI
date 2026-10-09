/**
 * apps/web/src/lib/glossary.ts
 * Diccionario de términos geocientíficos e inteligencia artificial
 * redactado en lenguaje sencillo y divulgativo para el público general.
 */

export interface GlossaryEntry {
  title: string;
  category: "Dato Real Confirmado" | "Predicción de IA" | "Métrica de Calidad" | "Concepto Geológico" | "Herramienta GIS";
  summary: string;
  example?: string;
  badgeColor?: string;
}

export const GLOSSARY: Record<string, GlossaryEntry> = {
  yacimientos_mayores: {
    title: "Yacimientos Mayores (46)",
    category: "Dato Real Confirmado",
    summary:
      "Son las 46 minas y explotaciones de oro más importantes y conocidas de la historia de España. No son estimaciones de una máquina: son lugares reales donde se ha extraído oro durante siglos. Se usan como 'patrón oro' para verificar si la IA es capaz de redescubrirlos a ciegas.",
    example: "Ejemplos: Las Médulas (León), Rodalquilar (Almería), El Valle-Boinás (Asturias) o Salave (Asturias).",
    badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40"
  },

  distritos_metalogenicos: {
    title: "Distritos Metalogénicos (32)",
    category: "Concepto Geológico",
    summary:
      "Grandes comarcas o regiones geológicas de España que comparten el mismo origen geológico y una concentración natural de minerales similar. Es como una 'denominación de origen' geológica.",
    example: "Ejemplos: Cinturón del Narcea en Asturias, Complejo Volcánico de Cabo de Gata o los Montes de Toledo.",
    badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
  },

  zonas_prospectividad: {
    title: "Zonas de Prospectividad (1.529)",
    category: "Predicción de IA",
    summary:
      "Polígonos de terreno delimitados por la IA donde coinciden múltiples pistas geológicas favorables a la vez (rocas adecuadas, fallas, anomalías de arroyos y relieve). Indican los lugares prioritarios donde una expedición minera moderna debería ir a tomar muestras de campo.",
    example: "Están clasificadas en Top 1% (máxima urgencia de exploración) y Top 5% (alto interés).",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
  },

  indicios_bdmin: {
    title: "Indicios Mineros BDMIN (787)",
    category: "Dato Real Confirmado",
    summary:
      "Puntos del Banco de Datos Mineros del Instituto Geológico y Minero de España (IGME) donde históricamente alguien encontró una pepita, una veta o un antiguo pozo minero con oro. Incluyen tanto minas de roca como bateos de río.",
    example: "787 puntos catalogados: 543 en roca/filones y 244 en ríos/placeres.",
    badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40"
  },

  pu_learning: {
    title: "Favorabilidad PU Calibrada (c=0.72)",
    category: "Predicción de IA",
    summary:
      "Técnica avanzada de IA ('Positive-Unlabeled Learning'). El reto en minería es que sabemos dónde hay oro confirmado (Positivos), pero del resto de España no podemos decir que esté vacío, simplemente 'no se ha explorado todavía' (No etiquetado). Este modelo corrige ese sesgo para no penalizar zonas inexploradas.",
    example: "c=0.72 significa que el modelo estima que conocemos aproximadamente el 72% de las evidencias superficiales.",
    badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/40"
  },

  incertidumbre_epistemica: {
    title: "Incertidumbre Epistémica (σ)",
    category: "Métrica de Calidad",
    summary:
      "Mide cuánta duda o desacuerdo tienen los modelos matemáticos sobre un punto del mapa. Si el color es amarillo, significa que falta información o que las rocas son atípicas; NO significa que haya oro. Las zonas violetas tienen datos claros y seguros.",
    example: "En amarillo: 'Cuidado, aquí los datos son escasos o contradictorios'. En morado: 'Alta certeza'.",
    badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40"
  },

  oro_roca: {
    title: "Oro en Roca (Vetas & Skarns)",
    category: "Predicción de IA",
    summary:
      "Oro primario atrapado en su roca madre subterránea original: vetas de cuarzo, fracturas tectónicas profundas o zonas donde un magma caliente horneó calizas (skarns). Requiere minería de interior o a cielo abierto sobre roca dura.",
    example: "Típico del Macizo Ibérico (Galicia, Asturias, Salamanca, Extremadura).",
    badgeColor: "bg-rose-500/20 text-rose-300 border-rose-500/40"
  },

  oro_aluvial: {
    title: "Oro Aluvial (Placeres Cuaternarios)",
    category: "Predicción de IA",
    summary:
      "Oro secundario que fue arrancado de las montañas por la lluvia y los ríos a lo largo de millones de años, concentrándose en arenas, gravas y terrazas fluviales. Es el oro que se extrae mediante bateo o lavado de sedimentos.",
    example: "Como el lavado de arenas de Las Médulas o las terrazas del Río Sil y Río Darro.",
    badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/40"
  },

  ensamble_multitipologia: {
    title: "Ensamble Multitipología v2",
    category: "Predicción de IA",
    summary:
      "Unión de los modelos de roca y de río mediante un ensamble de algoritmos Gradient Boosting. Permite detectar zonas híbridas donde puede haber yacimientos en la montaña y depósitos en el valle adyacente.",
    example: "Especialmente útil en cuencas de transición montaña-llanura sedimentaria.",
    badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
  },

  bandas_prioritarias: {
    title: "Bandas Top 1% / 5% / 10%",
    category: "Predicción de IA",
    summary:
      "Filtro territorial estricto. El Top 1% representa el 1% de toda la península ibérica (unos 4.700 km²) con las condiciones geológicas más raras y favorables según la IA. El Top 5% amplía la búsqueda a zonas de alta probabilidad complementarias.",
    example: "Rojo: Top 1% (Crítico). Ámbar: Top 5% (Alto). Verde: Top 10% (Moderado).",
    badgeColor: "bg-red-500/20 text-red-300 border-red-500/40"
  },

  percentil_territorial: {
    title: "Percentil Territorial",
    category: "Métrica de Calidad",
    summary:
      "Una escala del 0% al 100% que compara cada kilómetro cuadrado de España con todos los demás. Si una celda tiene percentil 98%, significa que supera en condiciones geológicas favorables al 98% de todo el territorio nacional.",
    example: "Un percentil >95% equivale a estar en el Top 5% más favorable del país.",
    badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/40"
  },

  linea_base_v1: {
    title: "Línea Base v1.0 (Regresión Logística)",
    category: "Métrica de Calidad",
    summary:
      "El modelo científico original y transparente del proyecto. Al ser una ecuación matemática lineal aditiva, cada puntuación puede explicarse punto por punto exactamente (explicabilidad al 100%). Sirve como control para comprobar cuánto mejora la IA moderna.",
    example: "Garantiza que no haya 'cajas negras' incomprensibles en las decisiones geológicas.",
    badgeColor: "bg-slate-500/20 text-slate-300 border-slate-500/40"
  },

  buffer_espacial: {
    title: "Buffer Espacial GIS",
    category: "Herramienta GIS",
    summary:
      "Herramienta de análisis geodésico que traza un círculo de 5, 10 o 20 kilómetros alrededor del punto que elijas. En milisegundos analiza cuántos indicios mineros hay dentro, el yacimiento histórico más cercano y el potencial mineral acumulado.",
    example: "Haz clic en el mapa tras activarlo para inspeccionar una comarca entera.",
    badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
  },

  score_favorabilidad: {
    title: "Índice de Favorabilidad (0 a 1)",
    category: "Predicción de IA",
    summary:
      "Puntuación relativa que mide la afinidad geológica de una celda con los depósitos auríferos conocidos. IMPORTANTE: No es una probabilidad garantizada de que haya oro bajo el suelo, sino un indicador de que las condiciones geológicas son propicias.",
    example: "0.10 es fondo geológico habitual; >0.70 es una fuerte anomalía favorable.",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
  },

  distancia_z: {
    title: "Distancia Z al Dominio Conocido",
    category: "Métrica de Calidad",
    summary:
      "Mide cuántas desviaciones estadísticas se aparta este terreno respecto a las características medias de las minas de oro conocidas de España. Cuanto más baja sea la distancia Z, más se parece el terreno a un yacimiento típico probado.",
    example: "Valores menores a 5σ indican que el terreno encaja bien con la geología aurífera probada.",
    badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
  },

  matriz_fiabilidad: {
    title: "Matriz de Fiabilidad 2D",
    category: "Métrica de Calidad",
    summary:
      "Cruza dos dimensiones cruciales: el potencial estimado (Favorabilidad) y la calidad de los datos (Certeza). 'Prioridad A' es la mejor combinación: alto potencial respaldado por datos sólidos sin dudas estadísticas.",
    example: "'Frontera' = buen potencial pero datos con incertidumbre; 'Prioridad A' = objetivo claro de prospección.",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
  },

  extrapolacion_ood: {
    title: "Extrapolación OOD (Fuera de Distribución)",
    category: "Métrica de Calidad",
    summary:
      "Aviso de seguridad del modelo. Salta cuando la IA se encuentra con una geología tan inusual o poco común en España que casi no tiene datos parecidos con los que comparar. Avisa de que la predicción debe interpretarse con cautela geológica.",
    example: "OOD = 'Out Of Distribution' (terreno desconocido para el entrenamiento del algoritmo).",
    badgeColor: "bg-rose-500/20 text-rose-300 border-rose-500/40"
  },

  xai_explicabilidad: {
    title: "Explicabilidad XAI (¿Por qué esta celda?)",
    category: "Métrica de Calidad",
    summary:
      "Desglose transparente que responde a la pregunta: ¿por qué la IA le dio esa nota a este lugar? Muestra qué factores geológicos sumaron puntos (ej. cercanía a fallas, presencia de arsénico o granitos) y cuáles restaron puntos.",
    example: "Permite a los geólogos auditar y entender el razonamiento exacto de la máquina.",
    badgeColor: "bg-teal-500/20 text-teal-300 border-teal-500/40"
  },

  disciplina_geologica: {
    title: "Aportación Neta por Disciplina",
    category: "Concepto Geológico",
    summary:
      "Agrupa las 56 variables geológicas analizadas en 5 disciplinas científicas: Estructuras (fallas y fracturas), Litología (tipos de roca), Edades (periodos geológicos), Relieve (montañas y pendientes) e Hidrografía (arroyos y ríos). Permite ver de un vistazo qué aspecto natural aporta más o penaliza en esta zona.",
    example: "Si 'Estructuras' es +0.59, significa que las fracturas tectónicas son el motor principal de favorabilidad aquí.",
    badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
  },

  z_score: {
    title: "Puntuación Z (z-score / Desviación σ)",
    category: "Métrica de Calidad",
    summary:
      "Mide lo rara o anómala que es esta característica comparada con la media de España, en unidades de desviación típica (σ). Un valor de +2.60σ significa que esta zona tiene una condición atípica muy pronunciada (supera a casi el 99% de España). Un valor negativo significa que está por debajo del promedio nacional.",
    example: "+2.60σ en cercanía a fallas = la celda está pegada a una fractura tectónica mucho más que la media peninsular.",
    badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40"
  },

  beta_modelo: {
    title: "Peso del Modelo (Coeficiente β)",
    category: "Predicción de IA",
    summary:
      "El multiplicador de importancia que el modelo estadístico le asigna a cada variable. Si es positivo (+), tener más de esta variable favorece la existencia de oro. Si es negativo (-), la presencia de este factor resta probabilidad.",
    example: "+0.212 significa que la variable suma puntos matemáticos al potencial del terreno.",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
  },

  odds_ratio: {
    title: "Multiplicador de Probabilidad (Odds Ratio)",
    category: "Métrica de Calidad",
    summary:
      "Factor que indica cuánto se multiplican las posibilidades relativas de albergar un yacimiento aurífero por cada incremento en esta variable. 1.00x es neutro (no cambia nada); 1.24x multiplica un 24% las probabilidades.",
    example: "1.48x significa que la probabilidad relativa de mineralización aumenta casi un 50% con este factor.",
    badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
  },

  valor_real: {
    title: "Valor Real Medido",
    category: "Concepto Geológico",
    summary:
      "La magnitud física cruda y medible sobre el terreno antes de cualquier procesamiento matemático: metros de distancia a una falla, metros de altitud sobre el mar, o fracción de superficie de una roca determinada.",
    example: "Ej: 7075.84 metros a la falla, 889.91 metros de altitud media, o 0.00 de fracción de cuarcitas.",
    badgeColor: "bg-slate-500/20 text-slate-300 border-slate-500/40"
  },

  divergencia_impacto: {
    title: "Impacto Local (Divergencia β·z)",
    category: "Predicción de IA",
    summary:
      "El empuje matemático neto de esta característica en este punto concreto (resultado de multiplicar el peso β por la anomalía z). La barra verde que apunta a la derecha (+) suma puntos al potencial aurífero; la barra roja a la izquierda (-) actúa como freno y resta puntos.",
    example: "La longitud de la barra muestra la fuerza con la que esta variable empuja a favor o en contra.",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
  },

  intercepto_beta0: {
    title: "Intercepto β₀ (Tasa Base)",
    category: "Predicción de IA",
    summary:
      "La tasa base previa de oro en España antes de analizar ninguna roca o falla. Como el oro es un metal precioso extremadamente escaso en la corteza terrestre, por defecto la probabilidad inicial en cualquier punto es bajísima (~0.16%). Las características geológicas deben compensar y remontar este punto de partida.",
    example: "Punto de partida conservador para evitar falsas expectativas.",
    badgeColor: "bg-slate-500/20 text-slate-300 border-slate-500/40"
  },

  impulso_neto: {
    title: "Impulso Neto Σ(β·z)",
    category: "Predicción de IA",
    summary:
      "La suma acumulada de todos los factores a favor (aceleradores) menos todos los factores en contra (frenos). Si es positivo y alto, las evidencias geológicas superan ampliamente a la rareza natural del oro.",
    example: "+4.12 indica un fortísimo impulso geológico favorable que remonta el fondo estéril.",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
  },

  logit_total: {
    title: "Logit Total (Log-Odds)",
    category: "Predicción de IA",
    summary:
      "La puntuación matemática combinada (Intercepto + Impulso). Mediante la fórmula sigmoide σ(logit) = 1 / (1 + e^-logit), este número se convierte matemáticamente en el porcentaje final de favorabilidad (entre 0% y 100%).",
    example: "Un logit negativo da probabilidades bajas; un logit de 0 da 50%; números positivos dan >80%.",
    badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
  },

  cierre_numerico: {
    title: "Test de Cierre Numérico",
    category: "Métrica de Calidad",
    summary:
      "Auditoría matemática automática que verifica en tiempo real que la suma de las 56 variables coincide con la predicción del modelo con un error menor a 10⁻¹⁵. Demuestra transparencia científica absoluta y ausencia total de sesgos ocultos.",
    example: "Garantiza que la IA no esconde ningún factor opaco.",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
  }
};
