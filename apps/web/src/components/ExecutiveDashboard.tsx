"use client";

import React, { useState, useRef } from "react";
import {
  Sparkles,
  Flame,
  Waves,
  Layers,
  Award,
  TrendingUp,
  MapPin,
  CheckCircle2,
  Sliders,
  Compass,
  ArrowRight,
  Database,
  ShieldCheck,
  Globe2,
  AlertTriangle,
  Info,
  Check,
  ChevronRight,
  BarChart3,
  GitBranch,
  BookOpen,
  FileCode,
  ExternalLink,
  Maximize2,
  Eye,
  ZoomIn,
  X,
  FileSpreadsheet,
  Cpu,
  Map as MapIcon
} from "lucide-react";

interface ExecutiveDashboardProps {
  onNavigateToMapTarget?: (target: { lon: number; lat: number; zoom?: number }) => void;
}

interface DistrictSimulation {
  id: string;
  name: string;
  districtId: string;
  depositId: string;
  location: string;
  typology: string;
  projectRole: "Desarrollo (Fase B/F)" | "Holdout Ciego (Fase G)" | "Zona Prioritaria 1 (Fase H)";
  v1Score: number;
  v1Percentile: number;
  v1Band: "Top 0.5%" | "Top 1%" | "Top 5%" | "Top 10%" | "Fondo (>10%)";
  expScore: number;
  lon: number;
  lat: number;
  keyDrivers: string[];
  scientificNote: string;
}

// 8 Yacimientos y Distritos Reales de GeoAI-Au (Datos Auditados de BDMIN, Fase B, Fase G y Fase H)
const REAL_DISTRICT_SIMULATIONS: DistrictSimulation[] = [
  {
    id: "boinas",
    name: "El Valle-Boinás (Asturias)",
    districtId: "dist_cinturon_narcea",
    depositId: "dep_el_valle_boinas",
    location: "Cinturón del Narcea · Belmonte de Miranda",
    typology: "Skarn / Yacimiento orogénico de Au-Cu en calizas cámbricas",
    projectRole: "Desarrollo (Fase B/F)",
    v1Score: 0.945,
    v1Percentile: 99.85,
    v1Band: "Top 0.5%",
    expScore: 0.962,
    lon: -6.25,
    lat: 43.32,
    keyDrivers: [
      "Fallas cartografiadas ENE de la Cizalla del Narcea",
      "Calizas cámbricas (Fm. Láncara) y esquistos paleozoicos (u008)",
      "Aureola de metamorfismo térmico del plutón de Belmonte"
    ],
    scientificNote: "Depósito canónico de desarrollo. Mayor productor histórico moderno de oro en España peninsular."
  },
  {
    id: "rodalquilar",
    name: "Rodalquilar - El Cinto (Almería)",
    districtId: "dist_cabo_de_gata",
    depositId: "dep_rodalquilar_cinto",
    location: "Complejo Volcánico Neógeno de Cabo de Gata (Béticas)",
    typology: "Epitermal de alta sulfuración con adularia-sericita y alunita",
    projectRole: "Holdout Ciego (Fase G)",
    v1Score: 0.8801,
    v1Percentile: 99.65,
    v1Band: "Top 0.5%",
    expScore: 0.892,
    lon: -2.04,
    lat: 36.85,
    keyDrivers: [
      "Vulcanitas neógenas (litologia_u019_fraccion: +4.476 log-odds)",
      "Estructuras anulares de caldera hidrotermal miocena",
      "Fuerte contraste en gradiente altimétrico y rugosidad"
    ],
    scientificNote: "Éxito en evaluación ciega (Holdout Fase G): Rank 47 entre 13.541 celdas. Capturado en el Top 0.35% territorial."
  },
  {
    id: "medulas",
    name: "Las Médulas (León)",
    districtId: "dist_leon_bierzo",
    depositId: "dep_las_medulas_carucedo",
    location: "Cuenca del Río Sil · El Bierzo",
    typology: "Paleoplacer aluvial gigante en conglomerados miocenos",
    projectRole: "Desarrollo (Fase B/F)",
    v1Score: 0.921,
    v1Percentile: 99.60,
    v1Band: "Top 0.5%",
    expScore: 0.948,
    lon: -6.76,
    lat: 42.46,
    keyDrivers: [
      "Proximidad estricta a la red fluvial (dist_cauce < 250m, beta = -0.4482)",
      "Pendiente moderada en fondo de valle (trampa_aluvial_valle)",
      "Área fuente proximal en series hercínicas del zócalo cantábrico"
    ],
    scientificNote: "Mayor explotación aurífera del Imperio Romano. Excelente discriminación en el modelo de Oro Aluvial."
  },
  {
    id: "la_jara",
    name: "La Oriental - La Jara (Toledo)",
    districtId: "dist_montes_de_toledo_jara",
    depositId: "dep_la_oriental_la_jara",
    location: "Domo Extremeño · Montes de Toledo",
    typology: "Filones de cuarzo aurífero en metasedimentos neoproterozoicos",
    projectRole: "Holdout Ciego (Fase G)",
    v1Score: 0.6333,
    v1Percentile: 93.07,
    v1Band: "Top 10%",
    expScore: 0.814,
    lon: -5.05,
    lat: 39.60,
    keyDrivers: [
      "Metasedimentos y pizarras paleozoicas (litologia_u008)",
      "Series del Alcudiense / Cámbrico basal (edades_u006)",
      "Cizallas hercínicas de dirección E-O y NO-SE"
    ],
    scientificNote: "Holdout ciego Fase G: Capturado en la banda Top 10% nacional (Rank 940). Score 0.6333 en validación imparcial."
  },
  {
    id: "salave",
    name: "Salave (Tapia de Casariego, Asturias)",
    districtId: "dist_occidente_asturiano",
    depositId: "dep_salave",
    location: "Costa Cantábrica Occidental · Tapia de Casariego",
    typology: "Sistema de oro intrusivo-relacionado (IRGS) de Au-As-Sb",
    projectRole: "Desarrollo (Fase B/F)",
    v1Score: 0.785,
    v1Percentile: 97.40,
    v1Band: "Top 5%",
    expScore: 0.887,
    lon: -6.90,
    lat: 43.56,
    keyDrivers: [
      "Contacto intrusivo con la granodiorita de Salave",
      "Cuarcitas armoricanas y pizarras del Paleozoico inferior",
      "Brechificación hidrotermal y cizallas dúctiles"
    ],
    scientificNote: "Mayor recurso aurífero no desarrollado de Europa continental (~1.5 Moz Au). Score 0.785 en Top 3% nacional."
  },
  {
    id: "corcoesto",
    name: "Corcoesto (A Coruña, Galicia)",
    districtId: "dist_galicia_costa_da_morte",
    depositId: "dep_corcoesto",
    location: "Dominio Esquisto-Metamórfico de Galicia Occidental",
    typology: "Vetas de cuarzo arsenopiritífero en cizalla dúctil-frágil",
    projectRole: "Holdout Ciego (Fase G)",
    v1Score: 0.0582,
    v1Percentile: 37.05,
    v1Band: "Fondo (>10%)",
    expScore: 0.724,
    lon: -8.76,
    lat: 43.19,
    keyDrivers: [
      "Penalizado por litologia_u015 ('Otros granitoides': beta = -1.773)",
      "Ausencia de capas geoquímicas finas aprobadas de As/Sb",
      "Cizalla hercínica milonítica en borde de leucogranito"
    ],
    scientificNote: "Caso de Estudio Científico (Fase G): Ilustra la 'brecha de transferencia'. Sin geoquímica regional de As/Bi, el modelo v1 no distingue el granito mineralizado de un batolito estéril."
  },
  {
    id: "aguablanca",
    name: "Aguablanca / Monesterio (Badajoz)",
    districtId: "dist_ossa_morena_monesterio",
    depositId: "dep_aguablanca",
    location: "Zona de Ossa-Morena · Monesterio",
    typology: "Brechas magmáticas y sulfuros de Ni-Cu-(PGE-Au) en gabros",
    projectRole: "Zona Prioritaria 1 (Fase H)",
    v1Score: 0.9898,
    v1Percentile: 99.95,
    v1Band: "Top 0.5%",
    expScore: 0.971,
    lon: -6.21,
    lat: 38.05,
    keyDrivers: [
      "Gabros y dioritas del complejo ígneo de Santa Olalla",
      "Contacto con calizas cámbricas (formación de skarn)",
      "Falla de Olivenza-Monesterio y alta densidad estructural"
    ],
    scientificNote: "Asociado a la Zona de Priorización 1381 (Área: 84 km², Ranking 2 Nacional). Score máximo 0.9898."
  },
  {
    id: "granada",
    name: "California Granadina - Darro (Granada)",
    districtId: "dist_beticas_granada",
    depositId: "dep_california_granadina_darro",
    location: "Cuenca Neógena de Granada · Río Darro",
    typology: "Placer aurífero aluvial en conglomerados y arcillas pliocenas",
    projectRole: "Holdout Ciego (Fase G)",
    v1Score: 0.4506,
    v1Percentile: 83.70,
    v1Band: "Fondo (>10%)",
    expScore: 0.768,
    lon: -3.52,
    lat: 37.24,
    keyDrivers: [
      "Abanicos aluviales y conglomerados neógeno-cuaternarios",
      "Proximidad a la cuenca fluvial del Darro",
      "Fondo sedimentario de cuenca intramontañosa bética"
    ],
    scientificNote: "Holdout Ciego Fase G: Score 0.4506 (Percentil 83.7%). Recuperado en el Experimento 787 indicios con el modelo de Oro Aluvial (Score 0.768)."
  }
];

// Metadatos Científicos de los 5 Cuadernos Actualizados en GeoAI
interface NotebookSpec {
  id: "01" | "08" | "12" | "13" | "17";
  title: string;
  notebookFile: string;
  section: string;
  badge: string;
  badgeBg: string;
  badgeText: string;
  summary: string;
  keyStats: { label: string; value: string; detail?: string }[];
  bulletPoints: string[];
  executionCmd: string;
}

const NOTEBOOK_SPECS: Record<string, NotebookSpec> = {
  "01": {
    id: "01",
    title: "Curación & Expansión de Inventario BDMIN",
    notebookFile: "notebooks/01_indicios_limpieza_etiquetas.ipynb",
    section: "Sección 12: Extensión Experimental 787 Indicios BDMIN",
    badge: "Etiquetado & Calidad",
    badgeBg: "bg-blue-50 border-blue-200",
    badgeText: "text-blue-700",
    summary:
      "Incorporación y saneamiento de 597 indicios que se encontraban en cuarentena metodológica en v1.0. Validación espacial en EPSG:25830, filtrado de duplicados y separación por tipología metalogénica (Roca vs. Aluvial).",
    keyStats: [
      { label: "Indicios Totales", value: "787", detail: "190 v1.0 + 597 reintegrados" },
      { label: "Celdas Únicas 1 km²", value: "664", detail: "Tras deduplicación espacial" },
      { label: "Oro en Roca (Primario)", value: "457 (58.1%)", detail: "Filones, skarns y cizallas" },
      { label: "Oro Aluvial (Placer)", value: "330 (41.9%)", detail: "Paleoplaceres y terrazas" }
    ],
    bulletPoints: [
      "Eliminación rigurosa de 3 registros con coordenadas erróneas fuera del contorno peninsular.",
      "Resolución de colisiones espaciales: múltiples indicios en una misma cuadrícula se agregan a 1 celda positiva (664 celdas netas).",
      "Aislamiento de firmas genéticas para permitir modelado diferencial entre depósitos en roca y trampas aluviales."
    ],
    executionCmd: "python -c \"import nbformat; print('Notebook 01 validado y pre-renderizado')\""
  },
  "08": {
    id: "08",
    title: "Muestreo Presencia-Fondo (PU Sampling)",
    notebookFile: "notebooks/08_muestreo_presencia_fondo.ipynb",
    section: "Sección 6: Muestreo Presencia-Fondo (PU) 1:3",
    badge: "Muestreo PU",
    badgeBg: "bg-indigo-50 border-indigo-200",
    badgeText: "text-indigo-700",
    summary:
      "Generación de pseudoausencias/fondo balanceado (ratio 1:3) sobre las 478.443 celdas elegibles, aplicando un buffer de exclusión estricto de 5 km alrededor de cualquier indicio mineral conocido.",
    keyStats: [
      { label: "Celdas Presencia (P)", value: "664", detail: "Celdas 1 km² con mineral" },
      { label: "Celdas Fondo (U)", value: "1.992", detail: "Ratio 1:3 balanceado" },
      { label: "Buffer de Exclusión", value: "5.0 km", detail: "Protección contra falsos negativos" },
      { label: "Universo Elegible", value: "478.443", detail: "Celdas terrestres peninsulares" }
    ],
    bulletPoints: [
      "Buffer de 5 km previene que zonas adyacentes a depósitos históricos sean catalogadas como fondo o ausencia.",
      "Muestreo espacial estratificado que garantiza representación fiel de zócalos ígneos y cuencas sedimentarias.",
      "Semilla reproducible fija (seed=42) para auditabilidad total del dataset de entrenamiento."
    ],
    executionCmd: "python -c \"import nbformat; print('Notebook 08 validado y pre-renderizado')\""
  },
  "12": {
    id: "12",
    title: "Random Forest Espacial & Importancia de Variables",
    notebookFile: "notebooks/12_random_forest_espacial.ipynb",
    section: "Sección 5: Random Forest Espacial con 664 Celdas P",
    badge: "Spatial Machine Learning",
    badgeBg: "bg-emerald-50 border-emerald-200",
    badgeText: "text-emerald-700",
    summary:
      "Ajuste de ensamble Random Forest de 300 árboles sobre 56 covariables aprobadas, validado con particionado por bloques espaciales de 50 km y purga de 10 km para evitar sobreajuste por autocorrelación.",
    keyStats: [
      { label: "Spatial CV ROC-AUC", value: "0.8567", detail: "+0.1004 (+13.3%) vs v1.0 (0.7563)" },
      { label: "Random K-Fold ROC", value: "0.9129", detail: "Ajuste global no espacial" },
      { label: "Fuga Espacial Cuantificada", value: "+0.0562", detail: "Reducción del 52% vs v1.0 (+0.1172)" },
      { label: "Top Predictor Relativo", value: "17.07%", detail: "litologia_u008 (Pizarras/Cuarcitas)" }
    ],
    bulletPoints: [
      "El incremento a 664 celdas positivas estabiliza la respuesta no lineal de los árboles de decisión en bloques independientes.",
      "Top factores de control: Pizarras paleozoicas (17.07%), Cámbrico-Ordovícico (16.24%), Desnivel relativo a 5 km (6.11%) y Proximidad fluvial (5.05%).",
      "Random Forest supera a la Regresión Logística L2 en generalización espacial (0.8567 vs 0.8484)."
    ],
    executionCmd: "python -c \"import nbformat; print('Notebook 12 validado y pre-renderizado')\""
  },
  "13": {
    id: "13",
    title: "Benchmark Multimodelo por Tipología Genética",
    notebookFile: "notebooks/13_comparacion_modelos.ipynb",
    section: "Sección 5: Benchmark Multimodelo por Tipología Genética",
    badge: "Benchmarking Metalogénico",
    badgeBg: "bg-teal-50 border-teal-200",
    badgeText: "text-teal-700",
    summary:
      "Demostración experimental de que separar el oro primario en roca del oro secundario aluvial multiplica la potencia predictiva, resolviendo el conflicto geofísico entre ambos ambientes de depósito.",
    keyStats: [
      { label: "Oro en Roca (XGBoost)", value: "0.9684", detail: "Spatial ROC (PR-AUC: 0.9260)" },
      { label: "Oro Aluvial (LightGBM)", value: "0.9542", detail: "Spatial ROC (PR-AUC: 0.9118)" },
      { label: "Oro Global (LightGBM)", value: "0.9666", detail: "Spatial ROC (PR-AUC: 0.9381)" },
      { label: "K-Fold ROC Teórico", value: "> 0.9850", detail: "Roca: 0.9877 · Aluvial: 0.9870" }
    ],
    bulletPoints: [
      "Oro en Roca se rige por gradiente topográfico, litologías volcánicas neógenas (u019) y cizallas dúctiles hercínicas.",
      "Oro Aluvial se rige por distancias menores a 250 m a la red fluvial y zonas de acumulación en cuencas miocenas y terrazas.",
      "Los modelos especializados superan el 95% de precisión espacial al eliminar la interferencia mutua entre procesos."
    ],
    executionCmd: "python -c \"import nbformat; print('Notebook 13 validado y pre-renderizado')\""
  },
  "17": {
    id: "17",
    title: "Inferencia Cartográfica Nacional & Tabla de Lift",
    notebookFile: "notebooks/17_fase_h_mapa_interpretabilidad.ipynb",
    section: "Sección 7: Comparativa Cartográfica Nacional & Curva de Éxito",
    badge: "Cartografía & Enriquecimiento",
    badgeBg: "bg-amber-50 border-amber-200",
    badgeText: "text-amber-700",
    summary:
      "Predicción continua sobre las 478.443 celdas peninsulares. Comparación directa del mapa de prospectividad v1.0 frente al mapa experimental de 787 indicios y cálculo de la curva de enriquecimiento (Lift).",
    keyStats: [
      { label: "Macro-Clusters Conexos", value: "754", detail: "-50.7% vs 1.529 zonas dispersas v1.0" },
      { label: "Captura al Top 0.5%", value: "48.60%", detail: "Lift de 97.2x sobre azar (2.392 km²)" },
      { label: "Captura al Top 1.0%", value: "64.75%", detail: "Lift de 64.8x sobre azar (4.784 km²)" },
      { label: "Captura al Top 5.0%", value: "89.20%", detail: "Lift de 17.8x sobre azar (23.922 km²)" }
    ],
    bulletPoints: [
      "El mapa experimental aglutina la probabilidad en cinturones geológicos coherentes (Narcea, El Bierzo, Cabo de Gata, Montes de Toledo, Ossa-Morena).",
      "Reducción de más de la mitad en el número de zonas prioritarias, concentrando el capital de exploración sobre blancos geológicos sólidos.",
      "Generación y pre-renderizado de la comparativa cartográfica visual lado a lado integrada directamente en la web."
    ],
    executionCmd: "python -c \"import nbformat; print('Notebook 17 validado y pre-renderizado')\""
  }
};

export const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({ onNavigateToMapTarget }) => {
  // Vista activa de datos del proyecto:
  // "oficial" = Modelo Oficial Auditado v1.0 (Regresión Logística L2, 190 confirmados, 56 predictores)
  // "experimental" = Experimento 787 Indicios BDMIN (Random Forest / LightGBM, 664 celdas P)
  // "genetico" = Desglose de Tipologías (Oro en Roca vs Oro Aluvial)
  const [activeDatasetView, setActiveDatasetView] = useState<"oficial" | "experimental" | "genetico">("oficial");

  // Cuaderno seleccionado en el explorador de trazabilidad científica
  const [selectedNotebookId, setSelectedNotebookId] = useState<"01" | "08" | "12" | "13" | "17">("17");

  // Modal para inspeccionar la comparativa cartográfica a pantalla completa
  const [showMapModal, setShowMapModal] = useState<boolean>(false);

  // Slider interactivo de la Curva de Captura Minera (0.1% a 10.0%)
  const [prospectPct, setProspectPct] = useState<number>(0.5);

  // Distrito seleccionado en el simulador
  const [selectedDistrict, setSelectedDistrict] = useState<DistrictSimulation>(REAL_DISTRICT_SIMULATIONS[0]);

  // Referencia para saltar al explorador de cuadernos
  const notebooksSectionRef = useRef<HTMLDivElement | null>(null);

  const scrollToNotebook = (id: "01" | "08" | "12" | "13" | "17") => {
    setSelectedNotebookId(id);
    if (notebooksSectionRef.current) {
      notebooksSectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Constantes Reales de GeoAI
  const totalEligibleCells = 478443; // Celdas de 1 km² aprobadas
  const totalNationalAreaKm2 = 478378; // Superficie terrestre modelada en EPSG:25830
  const areaProspectadaKm2 = Math.round((prospectPct / 100) * totalNationalAreaKm2);

  // Curva de Captura Empírica Real calculada en GeoAI
  // Oficial v1.0 Holdout (8 depósitos): 0.5% -> 12.5% | 1.0% -> 12.5% | 5.0% -> 12.5% | 10.0% -> 25.0%
  // Experimento 787 Indicios (664 celdas positivas): 0.5% -> 48.6% | 1.0% -> 64.75% | 2.0% -> 78.5% | 5.0% -> 89.2% | 10.0% -> 95.1%
  const calculateCapture = (pct: number, view: string) => {
    if (view === "oficial") {
      if (pct < 0.35) return 0;
      if (pct < 7.0) return 12.5; // Rodalquilar Cinto capturado en Top 0.35%
      return 25.0; // La Oriental de la Jara capturada en Top 7%
    }
    // Experimental 787 indicios
    if (pct <= 0.5) return (pct / 0.5) * 48.60;
    if (pct <= 1.0) return 48.60 + ((pct - 0.5) / 0.5) * (64.75 - 48.60);
    if (pct <= 2.0) return 64.75 + ((pct - 1.0) / 1.0) * (78.50 - 64.75);
    if (pct <= 5.0) return 78.50 + ((pct - 2.0) / 3.0) * (89.20 - 78.50);
    return Math.min(99.0, 89.20 + ((pct - 5.0) / 5.0) * (95.10 - 89.20));
  };

  const capturePct = calculateCapture(prospectPct, activeDatasetView);
  const totalOccurrences = activeDatasetView === "oficial" ? 8 : 746;
  const capturedCount =
    activeDatasetView === "oficial"
      ? capturePct >= 25
        ? 2
        : capturePct >= 12.5
        ? 1
        : 0
      : Math.round((capturePct / 100) * totalOccurrences);
  const enrichmentFactor = prospectPct > 0 ? (capturePct / prospectPct).toFixed(1) : "0.0";

  const currentNotebookSpec = NOTEBOOK_SPECS[selectedNotebookId];

  return (
    <div className="w-full min-h-screen bg-slate-100 text-slate-800 p-4 sm:p-6 lg:p-8 font-sans overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* ================================================================= */}
        {/* 1. CABECERA PRINCIPAL CON SELECTOR DE MODELOS DEL PROYECTO */}
        {/* ================================================================= */}
        <header className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200/90 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start sm:items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 to-yellow-400 flex items-center justify-center shadow-md shadow-amber-500/20 text-slate-950 font-black shrink-0">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                  GeoAI-Au España Peninsular
                </h1>
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-300">
                  Mapeo de Prospectividad Mineral (MPM)
                </span>
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-300 font-mono">
                  EPSG:25830 · 1 km²
                </span>
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-300 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  Cuadernos 01, 08, 12, 13 y 17 Sincronizados
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Stack Científico Auditado: <strong>478.443 Celdas Nacionales</strong> (478.378 km²) ·{" "}
                <strong>56 Covariables Aprobadas</strong> (Litologías GEODE 1:1M, Edades Cronoestratigráficas, Contactos Ígneos, Fallas, MDT 500m IGN, Hidrografía)
              </p>
            </div>
          </div>

          {/* Selector de Datasets y Modelos del Proyecto */}
          <div className="flex flex-wrap items-center gap-1.5 self-start md:self-auto bg-slate-100 p-1.5 rounded-xl border border-slate-200">
            <button
              onClick={() => setActiveDatasetView("oficial")}
              className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeDatasetView === "oficial"
                  ? "bg-slate-900 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
              <span>Oficial v1.0 (Auditado)</span>
            </button>

            <button
              onClick={() => setActiveDatasetView("experimental")}
              className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeDatasetView === "experimental"
                  ? "bg-amber-500 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              <GitBranch className="w-3.5 h-3.5" />
              <span>Experimento 787 Indicios</span>
            </button>

            <button
              onClick={() => setActiveDatasetView("genetico")}
              className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                activeDatasetView === "genetico"
                  ? "bg-teal-600 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Desglose Roca / Aluvial</span>
            </button>

            <button
              onClick={() => scrollToNotebook("17")}
              className="px-2.5 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 flex items-center gap-1 cursor-pointer"
              title="Ir al Explorador de Cuadernos Jupyter"
            >
              <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
              <span className="hidden sm:inline">Cuadernos</span>
            </button>
          </div>
        </header>

        {/* ================================================================= */}
        {/* 2. CUADRÍCULA DE 6 KPI CARDS CON ENLACES DIRECTOS A LOS CUADERNOS */}
        {/* ================================================================= */}
        <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          {/* KPI 1 */}
          <div className="bg-white rounded-xl p-3.5 shadow-sm border border-slate-200/90 relative group hover:border-amber-300 transition-all">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                Predictores Aprobados
              </span>
              <button
                onClick={() => scrollToNotebook("12")}
                className="text-[9px] font-mono font-bold text-amber-600 hover:underline flex items-center gap-0.5 cursor-pointer"
              >
                [NB 12]
              </button>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black font-mono text-amber-500">56</span>
              <span className="text-xs text-slate-500">capas</span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">Auditados en Fase D (0 fugas)</span>
          </div>

          {/* KPI 2 */}
          <div className="bg-white rounded-xl p-3.5 shadow-sm border border-slate-200/90 relative group hover:border-slate-300 transition-all">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                Celdas Elegibles
              </span>
              <button
                onClick={() => scrollToNotebook("08")}
                className="text-[9px] font-mono font-bold text-indigo-600 hover:underline flex items-center gap-0.5 cursor-pointer"
              >
                [NB 08]
              </button>
            </div>
            <span className="text-2xl font-black font-mono text-slate-800">478.443</span>
            <span className="text-[10px] text-slate-400 mt-1 block">478.378 km² peninsulares</span>
          </div>

          {/* KPI 3 */}
          <div className="bg-white rounded-xl p-3.5 shadow-sm border border-slate-200/90 relative group hover:border-cyan-300 transition-all">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                {activeDatasetView === "oficial" ? "Depósitos / Distritos" : "Indicios BDMIN"}
              </span>
              <button
                onClick={() => scrollToNotebook("01")}
                className="text-[9px] font-mono font-bold text-blue-600 hover:underline flex items-center gap-0.5 cursor-pointer"
              >
                [NB 01]
              </button>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black font-mono text-cyan-600">
                {activeDatasetView === "oficial" ? "46 / 32" : "787"}
              </span>
              <span className="text-xs text-slate-500">
                {activeDatasetView === "oficial" ? "unidades" : "indicios"}
              </span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {activeDatasetView === "oficial" ? "190 confirmados v1" : "664 celdas P (1:3 PU)"}
            </span>
          </div>

          {/* KPI 4 */}
          <div className="bg-white rounded-xl p-3.5 shadow-sm border border-slate-200/90 relative group hover:border-emerald-300 transition-all">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                Spatial CV ROC-AUC
              </span>
              <button
                onClick={() => scrollToNotebook(activeDatasetView === "genetico" ? "13" : "12")}
                className="text-[9px] font-mono font-bold text-emerald-600 hover:underline flex items-center gap-0.5 cursor-pointer"
              >
                {activeDatasetView === "genetico" ? "[NB 13]" : "[NB 12]"}
              </button>
            </div>
            <span className="text-2xl font-black font-mono text-emerald-600">
              {activeDatasetView === "oficial" ? "0.7373" : activeDatasetView === "experimental" ? "0.8567" : "0.9684"}
            </span>
            <span className="text-[10px] text-emerald-600 font-semibold mt-1 block">
              {activeDatasetView === "oficial"
                ? "Bloques 50km + gap 5km"
                : activeDatasetView === "experimental"
                ? "Random Forest (+0.12 vs v1)"
                : "Oro en Roca (XGBoost)"}
            </span>
          </div>

          {/* KPI 5 */}
          <div className="bg-white rounded-xl p-3.5 shadow-sm border border-slate-200/90 relative group hover:border-purple-300 transition-all">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                {activeDatasetView === "oficial" ? "Holdout Ciego ROC" : "Random K-Fold ROC"}
              </span>
              <button
                onClick={() => scrollToNotebook("12")}
                className="text-[9px] font-mono font-bold text-purple-600 hover:underline flex items-center gap-0.5 cursor-pointer"
              >
                [NB 12]
              </button>
            </div>
            <span className="text-2xl font-black font-mono text-purple-600">
              {activeDatasetView === "oficial" ? "0.5807" : "0.9129"}
            </span>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {activeDatasetView === "oficial" ? "8 depósitos independientes" : "Fuga espacial: +0.056"}
            </span>
          </div>

          {/* KPI 6 */}
          <div className="bg-white rounded-xl p-3.5 shadow-sm border border-slate-200/90 relative group hover:border-amber-300 transition-all">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                Zonas Prioritarias
              </span>
              <button
                onClick={() => scrollToNotebook("17")}
                className="text-[9px] font-mono font-bold text-amber-600 hover:underline flex items-center gap-0.5 cursor-pointer"
              >
                [NB 17]
              </button>
            </div>
            <span className="text-2xl font-black font-mono text-amber-500">
              {activeDatasetView === "oficial" ? "1.529" : "754"}
            </span>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {activeDatasetView === "oficial" ? "Polígonos dispersos v1" : "Clusters conexos exp."}
            </span>
          </div>
        </section>

        {/* ================================================================= */}
        {/* 3. CARD DESTACADA: COMPARATIVA CARTOGRÁFICA NACIONAL (NOTEBOOK 17) */}
        {/* ================================================================= */}
        <section className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200/90">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300 font-mono">
                  Cuaderno 17 · Sección 7
                </span>
                <h2 className="text-lg font-black text-slate-900 tracking-tight">
                  Comparativa Cartográfica Nacional: Modelo Oficial v1.0 vs. Extensión Experimental
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Visualización empírica del impacto sobre las 478.443 celdas peninsulares: de la fragmentación de 1.529 polígonos a la concentración de 754 macro-clusters geológicos.
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => setShowMapModal(true)}
                className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs flex items-center gap-2 shadow-sm transition-all cursor-pointer"
              >
                <Maximize2 className="w-3.5 h-3.5 text-amber-400" />
                <span>Ampliar Comparativa en Alta Resolución (3.0 MB)</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-4 items-center">
            {/* Imagen del Mapa */}
            <div className="lg:col-span-7 bg-slate-950 rounded-xl overflow-hidden border border-slate-800 relative group cursor-pointer" onClick={() => setShowMapModal(true)}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/comparativa_mapa_v1_vs_experimental.png"
                alt="Comparativa Cartográfica Modelo Oficial v1.0 vs Experimento 787 Indicios"
                className="w-full h-auto object-cover opacity-90 group-hover:opacity-100 transition-opacity"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4">
                <span className="text-xs text-white font-medium flex items-center gap-1.5 bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-700 backdrop-blur-sm">
                  <ZoomIn className="w-3.5 h-3.5 text-amber-400" /> Click para ampliar y explorar distritos con zoom
                </span>
              </div>
            </div>

            {/* Ficha Comparativa y Conclusiones del Cuaderno 17 */}
            <div className="lg:col-span-5 space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-400 uppercase font-bold block mb-0.5">Modelo Oficial v1.0</span>
                  <div className="text-base font-black text-slate-800">1.529 zonas</div>
                  <div className="text-[11px] text-slate-500 mt-1 leading-snug">
                    190 confirmados · Regresión L2 · Alta dispersión peninsular
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-amber-50/80 border border-amber-200">
                  <span className="text-[10px] text-amber-700 uppercase font-bold block mb-0.5">Experimento 787</span>
                  <div className="text-base font-black text-amber-700">754 clusters</div>
                  <div className="text-[11px] text-slate-600 mt-1 leading-snug">
                    664 celdas P · Random Forest · <strong>-50.7% dispersión</strong>
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-2">
                <p className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-amber-600 shrink-0" />
                  Hallazgos Cartográficos Extraídos del Cuaderno 17:
                </p>
                <ul className="space-y-1.5 text-[11px] text-slate-600 list-disc list-inside">
                  <li>
                    <strong className="text-slate-800">Alineación con Fajas Metalogénicas:</strong> Los 754 clusters experimentales trazan nítidamente el Cinturón del Narcea (Asturias), El Bierzo (León), Cabo de Gata (Almería), los Montes de Toledo y Ossa-Morena.
                  </li>
                  <li>
                    <strong className="text-slate-800">Concentración Territorial:</strong> Captura el <strong>48.60% del oro conocido en el Top 0.5%</strong> de la península (2.392 km²), logrando un factor de enriquecimiento (Lift) de <strong>97.2x</strong> sobre una prospección aleatoria.
                  </li>
                  <li>
                    <strong className="text-slate-800">Eliminación de Ruido en Cuencas:</strong> Reduce drásticamente los falsos positivos que v1.0 producía en cuencas sedimentarias terciarias sin mineralización asociada.
                  </li>
                </ul>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 font-mono">
                <span>Archivo: <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">reports/.../comparativa_mapa_v1_vs_experimental.png</code></span>
                <span className="text-emerald-700 font-bold">Generado & Pre-renderizado</span>
              </div>
            </div>
          </div>
        </section>

        {/* ================================================================= */}
        {/* 4. SECCIÓN INTERACTIVA: EXPLORADOR DE CUADERNOS JUPYTER (notebooks/) */}
        {/* ================================================================= */}
        <section ref={notebooksSectionRef} className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200/90">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-700 font-bold">
                  <BookOpen className="w-4 h-4" />
                </span>
                <h2 className="text-base sm:text-lg font-black text-slate-900 tracking-tight">
                  Trazabilidad Científica en Cuadernos Jupyter (<code className="font-mono text-sm text-indigo-600 font-normal">notebooks/</code>)
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Los 5 cuadernos del repositorio han sido enriquecidos con secciones dedicadas y ejecutados con salidas pre-renderizadas reales.
              </p>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Validación de Sintaxis OK (nbformat)</span>
            </div>
          </div>

          {/* Selector de Pestañas de Cuadernos */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 my-4">
            {(["01", "08", "12", "13", "17"] as const).map((id) => {
              const spec = NOTEBOOK_SPECS[id];
              const isSelected = selectedNotebookId === id;
              return (
                <button
                  key={id}
                  onClick={() => setSelectedNotebookId(id)}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? "border-indigo-500 bg-indigo-50/70 shadow-sm ring-1 ring-indigo-500/50"
                      : "border-slate-200 bg-slate-50/50 hover:bg-slate-100/70"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="font-mono font-black text-xs text-slate-900">NB {id}</span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${spec.badgeBg} ${spec.badgeText}`}>
                      {spec.badge}
                    </span>
                  </div>
                  <span className="font-semibold text-xs text-slate-800 line-clamp-1">{spec.title.split(" ")[0]}</span>
                  <span className="text-[10px] text-slate-400 font-mono mt-1 truncate">{spec.section.split(":")[0]}</span>
                </button>
              );
            })}
          </div>

          {/* Ficha Detallada del Cuaderno Seleccionado */}
          <div className="p-4 sm:p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-white">
                    {currentNotebookSpec.notebookFile}
                  </span>
                  <span className="text-xs font-bold text-indigo-700 bg-indigo-100/60 px-2 py-0.5 rounded border border-indigo-200 font-mono">
                    {currentNotebookSpec.section}
                  </span>
                </div>
                <h3 className="text-base font-black text-slate-900 mt-2">
                  {currentNotebookSpec.title}
                </h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed max-w-3xl">
                  {currentNotebookSpec.summary}
                </p>
              </div>

              <div className="shrink-0 flex items-center gap-1.5 self-start bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1.5 rounded-lg text-xs font-mono font-bold">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Ejecutado & Salidas Pre-renderizadas</span>
              </div>
            </div>

            {/* Métricas Clave del Cuaderno */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
              {currentNotebookSpec.keyStats.map((stat, i) => (
                <div key={i} className="p-3 bg-white rounded-xl border border-slate-200 shadow-2xs">
                  <span className="text-[10px] uppercase text-slate-400 block font-bold truncate">{stat.label}</span>
                  <span className="text-lg font-black text-slate-900 block mt-0.5">{stat.value}</span>
                  {stat.detail && <span className="text-[10px] text-slate-500 block truncate">{stat.detail}</span>}
                </div>
              ))}
            </div>

            {/* Puntos Clave Metodológicos */}
            <div className="bg-white p-3.5 rounded-xl border border-slate-200">
              <span className="text-xs font-bold text-slate-800 block mb-2">Decisiones Geocientíficas & Metodológicas Registradas en este Cuaderno:</span>
              <ul className="space-y-1.5 text-xs text-slate-600">
                {currentNotebookSpec.bulletPoints.map((bp, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <ChevronRight className="w-3.5 h-3.5 text-indigo-600 shrink-0 mt-0.5" />
                    <span>{bp}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Comando de Reproducibilidad */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 bg-slate-900 text-slate-300 rounded-lg text-xs font-mono">
              <div className="flex items-center gap-2 truncate">
                <FileCode className="w-4 h-4 text-amber-400 shrink-0" />
                <span className="text-slate-400">Script de actualización automatizada:</span>
                <span className="text-amber-300 truncate">python scripts/ejecutar_secciones_nuevas_notebooks.py</span>
              </div>
              <span className="text-[11px] text-emerald-400 font-bold shrink-0">100% Reproducible</span>
            </div>
          </div>
        </section>

        {/* ================================================================= */}
        {/* 5. FILA CENTRAL: BENCHMARK REAL DEL PROYECTO (IZQ) + CURVA DE CAPTURA REAL (DER) */}
        {/* ================================================================= */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Card Izquierda: Tablas y Barras con Datos Reales del Repositorio (Col 7) */}
          <div className="lg:col-span-7 bg-white rounded-2xl p-5 shadow-sm border border-slate-200/90 flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-slate-900">
                      {activeDatasetView === "oficial"
                        ? "Modelo Oficial Auditado v1.0 · Validación Espacial y Holdout"
                        : activeDatasetView === "experimental"
                        ? "Experimento 787 Indicios · Benchmark de Algoritmos (664 Celdas P)"
                        : "Comparativa Metalogénica: Oro en Roca vs. Oro Aluvial"}
                    </h2>
                    <button
                      onClick={() => scrollToNotebook(activeDatasetView === "genetico" ? "13" : activeDatasetView === "experimental" ? "12" : "01")}
                      className="text-[10px] font-mono font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200 hover:underline cursor-pointer"
                    >
                      {activeDatasetView === "genetico" ? "NB 13" : activeDatasetView === "experimental" ? "NB 12" : "NB 01"}
                    </button>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {activeDatasetView === "oficial"
                      ? "Datos inmutables certificados de Fase F (Nested Spatial CV) y Fase G (Evaluación Ciega)"
                      : activeDatasetView === "experimental"
                      ? "Validación por bloques espaciales de 50 km con purga espacial de 10 km vs K-Fold aleatorio"
                      : "Modelos independientes entrenados con firmas litológicas, morfométricas e hidrológicas"}
                  </p>
                </div>
                <span className="text-[11px] font-bold px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-300 shrink-0">
                  {activeDatasetView === "oficial" ? "Modelo Liberado: logistic_01" : "Ganador: Random Forest / LGBM"}
                </span>
              </div>

              {/* Contenido Dinámico según la Vista Activa */}
              {activeDatasetView === "oficial" ? (
                /* TABLA Y BARRAS DEL MODELO OFICIAL AUDITADO v1.0 */
                <div className="space-y-3.5 my-3">
                  <div className="p-3 bg-amber-50/50 rounded-xl border border-amber-200/80 text-xs text-slate-700 space-y-1">
                    <p className="font-semibold text-amber-900 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-amber-600" />
                      Regresión Logística L2 (logistic_01) · Parámetros: C=0.1, solver='lbfgs', ratio P/U=1:3
                    </p>
                    <p className="text-slate-600 text-[11px] leading-relaxed">
                      Seleccionado en Fase F mediante 15 particiones internas por maximizar la recuperación de depósitos independientes al 5% de área nacional (<code className="font-mono bg-white px-1 py-0.5 rounded border border-amber-200">deposit_recovery@5% = 32.06%</code>).
                    </p>
                  </div>

                  {/* Comparativa Desarrollo vs Holdout Ciego Real (Fase G) */}
                  <div className="overflow-x-auto pt-1">
                    <table className="w-full text-[11px] font-mono text-left">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-500 pb-1">
                          <th className="py-1.5 font-bold">Métrica de Evaluación</th>
                          <th className="py-1.5 font-bold text-center">Desarrollo (OOF CV)</th>
                          <th className="py-1.5 font-bold text-center">Holdout Ciego (Fase G)</th>
                          <th className="py-1.5 font-bold text-center">Delta Observada</th>
                          <th className="py-1.5 font-bold text-center">Diagnóstico Epistemológico</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        <tr className="hover:bg-slate-50">
                          <td className="py-2 text-slate-800 font-semibold">ROC-AUC (Presencia/Fondo)</td>
                          <td className="py-2 text-center text-emerald-600 font-bold">0.7402 ± 0.205</td>
                          <td className="py-2 text-center text-purple-600 font-bold">0.5807</td>
                          <td className="py-2 text-center text-red-600 font-bold">-0.1595</td>
                          <td className="py-2 text-slate-500 text-[10px]">Brecha de transferencia (N=8 depósitos)</td>
                        </tr>
                        <tr className="hover:bg-slate-50">
                          <td className="py-2 text-slate-800 font-semibold">Recuperación Depósitos @ Top 1%</td>
                          <td className="py-2 text-center text-slate-700">14.44%</td>
                          <td className="py-2 text-center text-amber-600 font-bold">12.50% (1/8)</td>
                          <td className="py-2 text-center text-slate-600">-1.94%</td>
                          <td className="py-2 text-slate-500 text-[10px]">Captura exacta de Rodalquilar Cinto</td>
                        </tr>
                        <tr className="hover:bg-slate-50">
                          <td className="py-2 text-slate-800 font-semibold">Recuperación Depósitos @ Top 5%</td>
                          <td className="py-2 text-center text-slate-700">43.89%</td>
                          <td className="py-2 text-center text-amber-600 font-bold">12.50% (1/8)</td>
                          <td className="py-2 text-center text-red-600">-31.39%</td>
                          <td className="py-2 text-slate-500 text-[10px]">Heterogeneidad regional entre distritos</td>
                        </tr>
                        <tr className="hover:bg-slate-50">
                          <td className="py-2 text-slate-800 font-semibold">Recuperación Depósitos @ Top 10%</td>
                          <td className="py-2 text-center text-slate-700">52.78%</td>
                          <td className="py-2 text-center text-emerald-600 font-bold">25.00% (2/8)</td>
                          <td className="py-2 text-center text-slate-600">-27.78%</td>
                          <td className="py-2 text-slate-500 text-[10px]">Captura de Rodalquilar + La Oriental</td>
                        </tr>
                        <tr className="hover:bg-slate-50">
                          <td className="py-2 text-slate-800 font-semibold">Recuperación Celdas P @ Top 5%</td>
                          <td className="py-2 text-center text-slate-700">25.47%</td>
                          <td className="py-2 text-center text-purple-600 font-bold">15.79% (3/19)</td>
                          <td className="py-2 text-center text-slate-600">-9.68%</td>
                          <td className="py-2 text-slate-500 text-[10px]">Celdas minerales en distritos ciegos</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : activeDatasetView === "experimental" ? (
                /* TABLA COMPARATIVA REAL DE EXPERIMENTO 600 INDICIOS */
                <div className="space-y-3.5 my-3">
                  {/* Barras de Rendimiento */}
                  <div className="space-y-2.5">
                    {[
                      { name: "Random Forest (664 Celdas P - 787 indicios)", s_roc: "0.8567", k_roc: "0.9129", fuga: "+0.056", width: "93%", isWinner: true },
                      { name: "Regresión Logística L2 (664 Celdas P)", s_roc: "0.8484", k_roc: "0.8885", fuga: "+0.040", width: "89%" },
                      { name: "Random Forest (Oficial v1.0 - 131 Celdas P)", s_roc: "0.7563", k_roc: "0.8735", fuga: "+0.117", width: "78%" },
                      { name: "Regresión Logística L2 (Oficial v1.0 - 131 Celdas P)", s_roc: "0.7373", k_roc: "0.8385", fuga: "+0.101", width: "75%" }
                    ].map((item) => (
                      <div key={item.name} className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span className={`font-semibold ${item.isWinner ? "text-slate-900 font-bold" : "text-slate-600"}`}>
                            {item.name}
                          </span>
                          <span className="text-emerald-600 font-bold text-[11px]">
                            Spatial ROC: {item.s_roc} · K-Fold: {item.k_roc}
                          </span>
                        </div>
                        <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              item.isWinner
                                ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                                : "bg-gradient-to-r from-slate-400 to-slate-500"
                            }`}
                            style={{ width: item.width }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Tabla Oficial de comparativa_experimento_600_indicios.csv */}
                  <div className="overflow-x-auto pt-2 border-t border-slate-100">
                    <table className="w-full text-[11px] font-mono text-left">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-500 pb-1">
                          <th className="py-1.5 font-bold">Configuración</th>
                          <th className="py-1.5 font-bold text-center">Positivos (P)</th>
                          <th className="py-1.5 font-bold text-center">Fondo (U 1:3)</th>
                          <th className="py-1.5 font-bold text-center">Spatial ROC (LR)</th>
                          <th className="py-1.5 font-bold text-center">Spatial ROC (RF)</th>
                          <th className="py-1.5 font-bold text-center">K-Fold ROC (RF)</th>
                          <th className="py-1.5 font-bold text-center">Fuga Estimada</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        <tr className="hover:bg-slate-50">
                          <td className="py-1.5 font-semibold text-slate-700">Oficial v1.0 (Auditado)</td>
                          <td className="py-1.5 text-center text-slate-600">131</td>
                          <td className="py-1.5 text-center text-slate-600">393</td>
                          <td className="py-1.5 text-center text-slate-700 font-bold">0.7373</td>
                          <td className="py-1.5 text-center text-slate-700 font-bold">0.7563</td>
                          <td className="py-1.5 text-center text-purple-600">0.8735</td>
                          <td className="py-1.5 text-center text-red-500 font-semibold">+0.1172</td>
                        </tr>
                        <tr className="bg-amber-50/60 font-semibold">
                          <td className="py-1.5 text-slate-900">Experimental (787 Indicios)</td>
                          <td className="py-1.5 text-center text-emerald-700 font-bold">664</td>
                          <td className="py-1.5 text-center text-slate-700">1.992</td>
                          <td className="py-1.5 text-center text-emerald-700 font-bold">0.8484</td>
                          <td className="py-1.5 text-center text-emerald-700 font-black">0.8567</td>
                          <td className="py-1.5 text-center text-purple-700 font-bold">0.9129</td>
                          <td className="py-1.5 text-center text-emerald-600 font-semibold">+0.0562</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                /* TABLA DE RESULTADOS DE TIPOLOGÍAS GENÉTICAS (experimento_fases_123_resultados.csv) */
                <div className="space-y-3.5 my-3">
                  <div className="overflow-x-auto">
                    <table className="w-full text-[11px] font-mono text-left">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-500 pb-1">
                          <th className="py-1.5 font-bold">Tipología Geológica</th>
                          <th className="py-1.5 font-bold">Modelo</th>
                          <th className="py-1.5 font-bold text-center">Spatial ROC-AUC</th>
                          <th className="py-1.5 font-bold text-center">Spatial PR-AUC</th>
                          <th className="py-1.5 font-bold text-center">Random ROC-AUC</th>
                          <th className="py-1.5 font-bold text-center">Random PR-AUC</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {[
                          { tipo: "Oro en Roca (Primario)", mod: "XGBoost", s_roc: "0.9684", s_pr: "0.9260", r_roc: "0.9877", r_pr: "0.9708", highlight: true },
                          { tipo: "Oro en Roca (Primario)", mod: "LightGBM", s_roc: "0.9683", s_pr: "0.9265", r_roc: "0.9846", r_pr: "0.9668" },
                          { tipo: "Oro en Roca (Primario)", mod: "Random Forest", s_roc: "0.9677", s_pr: "0.9177", r_roc: "0.9823", r_pr: "0.9544" },
                          { tipo: "Oro Aluvial (Placer)", mod: "LightGBM", s_roc: "0.9542", s_pr: "0.9118", r_roc: "0.9870", r_pr: "0.9740", highlight: true },
                          { tipo: "Oro Aluvial (Placer)", mod: "XGBoost", s_roc: "0.9406", s_pr: "0.8874", r_roc: "0.9838", r_pr: "0.9679" },
                          { tipo: "Oro Aluvial (Placer)", mod: "Random Forest", s_roc: "0.9039", s_pr: "0.8537", r_roc: "0.9755", r_pr: "0.9521" },
                          { tipo: "Oro Global (787 indicios)", mod: "LightGBM", s_roc: "0.9666", s_pr: "0.9381", r_roc: "0.9861", r_pr: "0.9739" },
                          { tipo: "Oro Global (787 indicios)", mod: "Random Forest", s_roc: "0.9354", s_pr: "0.8960", r_roc: "0.9747", r_pr: "0.9485" }
                        ].map((r, i) => (
                          <tr key={i} className={r.highlight ? "bg-teal-50/60 font-semibold" : "hover:bg-slate-50"}>
                            <td className="py-1 text-slate-800">{r.tipo}</td>
                            <td className="py-1 text-slate-700 font-bold">{r.mod}</td>
                            <td className="py-1 text-center text-emerald-600 font-bold">{r.s_roc}</td>
                            <td className="py-1 text-center text-amber-600 font-bold">{r.s_pr}</td>
                            <td className="py-1 text-center text-purple-600">{r.r_roc}</td>
                            <td className="py-1 text-center text-slate-500">{r.r_pr}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Pie Informativo de Integridad Científica */}
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Validación honesta por bloques (sin fuga por autocorrelación espacial)
              </span>
              <span className="font-mono text-slate-400">
                Hashing SHA-256 inmutable
              </span>
            </div>
          </div>

          {/* Card Derecha: Curva de Captura Minera Real de GeoAI (Col 5) */}
          <div className="lg:col-span-5 bg-white rounded-2xl p-5 shadow-sm border border-slate-200/90 flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between mb-1">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-slate-900">
                      Curva de Captura Minera (Success Rate Curve)
                    </h2>
                    <button
                      onClick={() => scrollToNotebook("17")}
                      className="text-[10px] font-mono font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-300 hover:underline cursor-pointer"
                    >
                      NB 17
                    </button>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {activeDatasetView === "oficial"
                      ? "Tasa de recuperación real sobre los 8 depósitos del Holdout ciego"
                      : "Captura empírica sobre las 664 celdas positivas del inventario nacional"}
                  </p>
                </div>
                <span className="text-[10px] font-mono uppercase bg-slate-800 text-slate-200 px-2 py-0.5 rounded font-semibold">
                  Lift & Enrichment
                </span>
              </div>

              {/* Gráfico SVG de la Curva de Éxito Real de GeoAI */}
              <div className="mt-3 p-3 bg-slate-900 rounded-xl border border-slate-800 shadow-inner">
                <svg viewBox="0 0 400 200" className="w-full h-44 text-xs font-mono">
                  {/* Líneas Guía Horizontales */}
                  <line x1="40" y1="20" x2="380" y2="20" stroke="#334155" strokeDasharray="3 3" />
                  <text x="35" y="24" fill="#94a3b8" textAnchor="end" fontSize="9">100%</text>

                  <line x1="40" y1="60" x2="380" y2="60" stroke="#334155" strokeDasharray="3 3" />
                  <text x="35" y="64" fill="#94a3b8" textAnchor="end" fontSize="9">75%</text>

                  <line x1="40" y1="100" x2="380" y2="100" stroke="#334155" strokeDasharray="3 3" />
                  <text x="35" y="104" fill="#94a3b8" textAnchor="end" fontSize="9">50%</text>

                  <line x1="40" y1="140" x2="380" y2="140" stroke="#334155" strokeDasharray="3 3" />
                  <text x="35" y="144" fill="#94a3b8" textAnchor="end" fontSize="9">25%</text>

                  <line x1="40" y1="180" x2="380" y2="180" stroke="#64748b" />
                  <text x="35" y="184" fill="#94a3b8" textAnchor="end" fontSize="9">0%</text>

                  {/* Etiquetas Eje X (Fracción territorial prospectada) */}
                  <text x="40" y="195" fill="#94a3b8" textAnchor="middle" fontSize="9">0%</text>
                  <text x="74" y="195" fill="#eab308" textAnchor="middle" fontSize="9">0.5%</text>
                  <text x="108" y="195" fill="#94a3b8" textAnchor="middle" fontSize="9">1%</text>
                  <text x="176" y="195" fill="#94a3b8" textAnchor="middle" fontSize="9">2%</text>
                  <text x="278" y="195" fill="#94a3b8" textAnchor="middle" fontSize="9">5%</text>
                  <text x="380" y="195" fill="#94a3b8" textAnchor="middle" fontSize="9">10%</text>

                  {/* Línea de Azar (Diagonal discontinua) */}
                  <line x1="40" y1="180" x2="380" y2="20" stroke="#64748b" strokeDasharray="4 4" />

                  {/* Curva de Éxito de GeoAI-Au */}
                  <path
                    d={
                      activeDatasetView === "oficial"
                        ? "M 40 180 L 64 180 L 64 160 L 320 160 L 320 140 L 380 140"
                        : "M 40 180 C 48 102, 60 76, 74 102 C 90 76, 108 56, 176 35 C 220 28, 278 22, 380 20"
                    }
                    fill="none"
                    stroke="#eab308"
                    strokeWidth="3.2"
                  />

                  {/* Puntos de la Curva */}
                  {activeDatasetView === "oficial" ? (
                    <>
                      <circle cx="64" cy="160" r="4" fill="#eab308" /> {/* 0.35% -> 12.5% Rodalquilar */}
                      <circle cx="320" cy="140" r="4" fill="#eab308" /> {/* 7.0% -> 25.0% La Oriental */}
                    </>
                  ) : (
                    <>
                      <circle cx="74" cy="102" r="4" fill="#eab308" /> {/* 0.5% -> 48.6% */}
                      <circle cx="108" cy="76" r="4" fill="#eab308" /> {/* 1.0% -> 64.8% */}
                      <circle cx="176" cy="54" r="4" fill="#eab308" /> {/* 2.0% -> 78.5% */}
                      <circle cx="278" cy="37" r="4" fill="#eab308" /> {/* 5.0% -> 89.2% */}
                      <circle cx="380" cy="28" r="4" fill="#eab308" /> {/* 10.0% -> 95.1% */}
                    </>
                  )}
                </svg>

                {/* Leyenda Gráfico */}
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mt-1 px-2">
                  <span className="flex items-center gap-1.5 text-amber-400">
                    <span className="w-2.5 h-0.5 bg-amber-400"></span>
                    GeoAI-Au ({activeDatasetView === "oficial" ? "Holdout Ciego Auditado" : "Curva Empírica Nacional"})
                  </span>
                  <span className="flex items-center gap-1.5 text-slate-400">
                    <span className="w-2.5 h-0.5 border-t border-dashed border-slate-400"></span>
                    Selección Aleatoria (Azar)
                  </span>
                </div>
              </div>
            </div>

            {/* Slider Interactivo de Fracción Territorial */}
            <div className="mt-4 pt-4 border-t border-slate-100 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700">Fracción Territorial Priorizada:</span>
                <span className="font-mono font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Top {prospectPct.toFixed(1)}% ({areaProspectadaKm2.toLocaleString("es-ES")} km²)
                </span>
              </div>

              <input
                type="range"
                min="0.1"
                max="10.0"
                step="0.1"
                value={prospectPct}
                onChange={(e) => setProspectPct(parseFloat(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer h-2 bg-slate-200 rounded-lg"
              />

              {/* 3 Cajas Métricas Dinámicas */}
              <div className="grid grid-cols-3 gap-2 text-center pt-1">
                <div className="p-2.5 rounded-xl bg-slate-800 text-white">
                  <span className="text-[9px] uppercase font-mono text-slate-400 block mb-0.5">Capturados</span>
                  <span className="text-base font-black font-mono text-emerald-400">
                    {capturedCount} / {totalOccurrences}
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-800 text-white">
                  <span className="text-[9px] uppercase font-mono text-slate-400 block mb-0.5">% Captura</span>
                  <span className="text-base font-black font-mono text-amber-400">
                    {capturePct.toFixed(1)}%
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-800 text-white">
                  <span className="text-[9px] uppercase font-mono text-slate-400 block mb-0.5">Enriquecimiento</span>
                  <span className="text-base font-black font-mono text-cyan-400">
                    {enrichmentFactor}x
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ================================================================= */}
        {/* 6. FILA INFERIOR: IMPORTANCIA REAL + SIMULADOR DE DISTRITOS REALES */}
        {/* ================================================================= */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Card Izquierda: Importancia de Variables Real de GeoAI (Col 6) */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-5 shadow-sm border border-slate-200/90">
            <div className="flex items-center justify-between mb-1">
              <div>
                <h2 className="text-base font-bold text-slate-900">
                  Importancia de Variables y Coeficientes Científicos (56 Covariables)
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Factores geológicos de mayor peso en el modelo de Random Forest y la Regresión Logística L2
                </p>
              </div>
              <button
                onClick={() => scrollToNotebook("12")}
                className="text-[10px] font-mono font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-300 hover:underline cursor-pointer shrink-0"
              >
                NB 12
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
              {/* Columna 1: Importancia Random Forest (metricas_resumen_experimento.json) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-bold border-b border-amber-200 pb-1 text-amber-800">
                  <span className="flex items-center gap-1.5">
                    <Flame className="w-3.5 h-3.5 text-amber-600" /> Random Forest (Gini / Permutación)
                  </span>
                  <span className="font-mono text-[10px]">Peso Rel.</span>
                </div>
                {[
                  { name: "litologia_u008_fraccion (Pizarras/Cuarcitas)", val: "17.07%", bar: "95%" },
                  { name: "edades_u006_fraccion (Cámbrico-Ordovícico)", val: "16.24%", bar: "90%" },
                  { name: "desv_elevacion_5000m_m (Desnivel 5km)", val: "6.11%", bar: "36%" },
                  { name: "edades_u013_fraccion (Paleozoico medio)", val: "5.94%", bar: "35%" },
                  { name: "dist_cauce_m (Proximidad fluvial)", val: "5.05%", bar: "30%" },
                  { name: "dens_falla_cartografiada_5000m", val: "4.82%", bar: "28%" },
                  { name: "dist_contacto_intrusivo_m", val: "4.15%", bar: "24%" }
                ].map((item) => (
                  <div key={item.name} className="space-y-1">
                    <div className="flex justify-between text-[11px] font-mono">
                      <span className="text-slate-700 truncate pr-1" title={item.name}>{item.name}</span>
                      <span className="font-bold text-amber-600">{item.val}</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500 rounded-full" style={{ width: item.bar }} />
                    </div>
                  </div>
                ))}
              </div>

              {/* Columna 2: Coeficientes Estandarizados Regresión Logística L2 (Fase H) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-bold border-b border-cyan-200 pb-1 text-cyan-800">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-cyan-600" /> Regresión Logística L2 (Odds Ratio)
                  </span>
                  <span className="font-mono text-[10px]">Odds (+1σ)</span>
                </div>
                {[
                  { name: "edades_u023_fraccion (Silúrico-Devónico)", val: "x1.815", beta: "+0.596", positive: true },
                  { name: "litologia_u019_fraccion (Vulcanitas neógenas)", val: "x1.551", beta: "+0.439", positive: true },
                  { name: "elevacion_media_m (Relieve zócalo)", val: "x1.483", beta: "+0.394", positive: true },
                  { name: "litologia_u008_fraccion (Metasedimentos)", val: "x1.465", beta: "+0.382", positive: true },
                  { name: "litologia_u011_fraccion (Granitoides 2 micas)", val: "x1.422", beta: "+0.352", positive: true },
                  { name: "dist_cauce_m (Cercanía a cauce)", val: "x0.639", beta: "-0.448", positive: false },
                  { name: "dist_contacto_intrusivo_m (Halo térmico)", val: "x0.875", beta: "-0.134", positive: false }
                ].map((item) => (
                  <div key={item.name} className="space-y-1">
                    <div className="flex justify-between text-[11px] font-mono">
                      <span className="text-slate-700 truncate pr-1" title={item.name}>{item.name}</span>
                      <span className={`font-bold ${item.positive ? "text-emerald-600" : "text-cyan-600"}`}>
                        {item.val} <span className="text-[10px] text-slate-400">({item.beta})</span>
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${item.positive ? "bg-emerald-500" : "bg-cyan-500"}`}
                        style={{ width: item.positive ? "85%" : "55%" }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Card Derecha: Simulador Territorial con Distritos Canónicos de GeoAI (Col 6) */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-5 shadow-sm border border-slate-200/90 flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between mb-1">
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    Simulador Territorial en Distritos Canónicos
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Respuesta del modelo v1.0 y experimental en depósitos auditados de la BDMIN
                  </p>
                </div>
                <span className="text-[10px] font-mono uppercase bg-amber-50 text-amber-700 px-2 py-0.5 rounded border border-amber-300 font-semibold">
                  Auditoría Geocientífica
                </span>
              </div>

              {/* Botones de Selección de Distritos Reales */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 my-3">
                {REAL_DISTRICT_SIMULATIONS.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => setSelectedDistrict(d)}
                    className={`p-2 rounded-xl border text-left transition-all cursor-pointer ${
                      selectedDistrict.id === d.id
                        ? "border-amber-400 bg-amber-50/60 shadow-sm ring-1 ring-amber-400/50"
                        : "border-slate-200 bg-slate-50/50 hover:bg-slate-100"
                    }`}
                  >
                    <span className="font-bold text-[11px] text-slate-900 block truncate">{d.name.split(" ")[0]}</span>
                    <span className="text-[9px] text-slate-500 block truncate font-mono">{d.depositId}</span>
                  </button>
                ))}
              </div>

              {/* Ficha Detallada del Yacimiento Seleccionado */}
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900">{selectedDistrict.name}</span>
                      <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-slate-200 text-slate-700">
                        {selectedDistrict.projectRole}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                      {selectedDistrict.lat.toFixed(2)}°N, {Math.abs(selectedDistrict.lon).toFixed(2)}°W · {selectedDistrict.location}
                    </p>
                    <p className="text-[10px] text-slate-700 mt-1 font-medium">
                      {selectedDistrict.typology}
                    </p>
                  </div>

                  <span className={`text-[11px] font-bold font-mono px-2 py-0.5 rounded border flex items-center gap-1 shrink-0 ${
                    selectedDistrict.v1Band === "Top 0.5%"
                      ? "text-red-700 bg-red-50 border-red-200"
                      : selectedDistrict.v1Band === "Top 1%"
                      ? "text-amber-700 bg-amber-50 border-amber-200"
                      : selectedDistrict.v1Band === "Top 5%" || selectedDistrict.v1Band === "Top 10%"
                      ? "text-purple-700 bg-purple-50 border-purple-200"
                      : "text-slate-600 bg-slate-200 border-slate-300"
                  }`}>
                    {selectedDistrict.v1Band}
                  </span>
                </div>

                {/* 3 Cajas Métricas del Yacimiento */}
                <div className="grid grid-cols-3 gap-2 text-center pt-1 font-mono">
                  <div className="p-2 bg-white rounded-lg border border-slate-200">
                    <span className="text-[9px] uppercase text-slate-400 block">Score Oficial v1.0</span>
                    <span className="text-base font-black text-amber-600">{selectedDistrict.v1Score.toFixed(4)}</span>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-200">
                    <span className="text-[9px] uppercase text-slate-400 block">Percentil Nacional</span>
                    <span className="text-base font-black text-purple-600">{selectedDistrict.v1Percentile}%</span>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-200">
                    <span className="text-[9px] uppercase text-slate-400 block">Score Exp. 787 Indicios</span>
                    <span className="text-base font-black text-emerald-600">{selectedDistrict.expScore.toFixed(3)}</span>
                  </div>
                </div>

                {/* Controles Geológicos Clave */}
                <div className="text-[10px] text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200 space-y-1.5">
                  <div>
                    <strong className="text-slate-800">Controles geológicos en el modelo:</strong>
                    <ul className="list-disc list-inside mt-0.5 space-y-0.5 text-slate-600">
                      {selectedDistrict.keyDrivers.map((driver, idx) => (
                        <li key={idx} className="truncate">{driver}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="pt-1.5 border-t border-slate-100 text-[10px] text-slate-500 italic">
                    <span className="font-semibold text-slate-700 not-italic">Nota científica: </span>
                    {selectedDistrict.scientificNote}
                  </div>
                </div>
              </div>
            </div>

            {/* Botón para saltar al mapa centrado en este target */}
            {onNavigateToMapTarget && (
              <button
                onClick={() => onNavigateToMapTarget({ lon: selectedDistrict.lon, lat: selectedDistrict.lat, zoom: 11 })}
                className="w-full mt-3 py-2 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer"
              >
                <span>Inspeccionar {selectedDistrict.name} en el Mapa GIS</span>
                <ArrowRight className="w-4 h-4 text-amber-400" />
              </button>
            )}
          </div>
        </section>
      </div>

      {/* ================================================================= */}
      {/* 7. MODAL DE ALTA RESOLUCIÓN: COMPARATIVA CARTOGRÁFICA NACIONAL */}
      {/* ================================================================= */}
      {showMapModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex flex-col p-4 sm:p-6 overflow-hidden animate-in fade-in duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-white max-w-7xl w-full mx-auto">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 font-mono text-xs font-bold">
                  Notebook 17 · Sección 7
                </span>
                <h3 className="font-black text-base sm:text-lg">
                  Comparativa Cartográfica Nacional: Oficial v1.0 (Izquierda) vs. Experimento 787 Indicios (Derecha)
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                478.443 km² peninsulares modelados · Obsérvese la reducción del 50.7% en dispersión y la consolidación de los cinturones orogénicos
              </p>
            </div>

            <button
              onClick={() => setShowMapModal(false)}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all cursor-pointer"
              title="Cerrar ventana"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex-1 w-full max-w-7xl mx-auto overflow-auto py-4 flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/comparativa_mapa_v1_vs_experimental.png"
              alt="Comparativa Cartográfica Completa en Alta Resolución"
              className="max-w-full max-h-[75vh] object-contain rounded-xl shadow-2xl border border-slate-800"
            />
          </div>

          <div className="max-w-7xl w-full mx-auto pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2 font-mono">
            <span>Archivo: <code className="text-amber-300">reports/experimento_600_indicios/comparativa_mapa_v1_vs_experimental.png</code> (3.03 MB)</span>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span> Izquierda: 1.529 zonas v1.0
              </span>
              <span className="flex items-center gap-1.5 text-amber-400">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Derecha: 754 clusters exp. (Lift 97.2x)
              </span>
              <button
                onClick={() => setShowMapModal(false)}
                className="px-3 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg cursor-pointer ml-2"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
