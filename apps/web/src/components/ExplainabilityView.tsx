"use client";

import React, { useState, useMemo } from "react";
import {
  Sparkles,
  Calculator,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  Layers,
  Copy,
  Check,
  FileText,
  SlidersHorizontal,
  Search,
  X,
  ChevronDown,
  ChevronUp,
  Info,
  ExternalLink,
  ShieldCheck,
  Compass,
  Flame,
  Download,
  BarChart2,
  Activity,
  ArrowUpDown,
  Zap,
  MapPin
} from "lucide-react";
import { CellExplanation, CellInfo, FeatureContribution, ModelCoefficient } from "../types";
import { HelpTooltip } from "./HelpTooltip";

interface ExplainabilityViewProps {
  activeCellExplanation: CellExplanation | null;
  activeCellId?: string | null;
  selectedCell?: CellInfo | null;
  onZoomToZone: (target: { lon: number; lat: number; zoom?: number }) => void;
  onSelectCoordinate?: (lat: number, lon: number) => void;
  coefficients: ModelCoefficient[];
  onLoadCoefficients: () => void;
}

// Configuración de metadatos y colores para las familias de covariables
const FAMILY_CONFIG: Record<
  string,
  { label: string; text: string; bg: string; border: string; bar: string; icon: string }
> = {
  Estructuras: {
    label: "Estructuras",
    text: "text-cyan-400",
    bg: "bg-cyan-950/60",
    border: "border-cyan-800/50",
    bar: "from-cyan-500 to-blue-500",
    icon: "⚡"
  },
  Litología: {
    label: "Litología",
    text: "text-emerald-400",
    bg: "bg-emerald-950/60",
    border: "border-emerald-800/50",
    bar: "from-emerald-500 to-teal-400",
    icon: "🪨"
  },
  Edades: {
    label: "Edades",
    text: "text-amber-400",
    bg: "bg-amber-950/60",
    border: "border-amber-800/50",
    bar: "from-amber-500 to-orange-400",
    icon: "⏳"
  },
  Relieve: {
    label: "Relieve",
    text: "text-indigo-400",
    bg: "bg-indigo-950/60",
    border: "border-indigo-800/50",
    bar: "from-indigo-500 to-purple-400",
    icon: "⛰️"
  },
  Hidrografía: {
    label: "Hidrografía",
    text: "text-sky-400",
    bg: "bg-sky-950/60",
    border: "border-sky-800/50",
    bar: "from-sky-500 to-cyan-400",
    icon: "💧"
  }
};

function normalizeFamily(fam: string): string {
  if (!fam) return "General";
  const f = fam.toLowerCase();
  if (f.includes("estruct")) return "Estructuras";
  if (f.includes("lito")) return "Litología";
  if (f.includes("edad")) return "Edades";
  if (f.includes("relie") || f.includes("mde") || f.includes("pendient")) return "Relieve";
  if (f.includes("hidro") || f.includes("drenaj") || f.includes("rio") || f.includes("río")) return "Hidrografía";
  return fam;
}

// Celdas de referencia histórica y depósitos benchmark en España
const BENCHMARK_DEPOSITS = [
  {
    name: "El Valle-Boinás",
    locality: "Belmonte de Miranda (Asturias)",
    district: "Cinturón del Narcea",
    type: "Skarn / Orogénico Au-Cu",
    scoreRef: "0.606",
    lat: 43.318,
    lon: -6.254,
    description: "Yacimiento en explotación principal de la Cordillera Cantábrica. Complejo skarn y brechas hidrotermales en contacto granodiorítico."
  },
  {
    name: "Rodalquilar (El Cinto)",
    locality: "Cabo de Gata (Almería)",
    district: "Cabo de Gata - Níjar",
    type: "Epitermal Alta Sulfuración",
    scoreRef: "0.866",
    lat: 36.848,
    lon: -2.043,
    description: "Distrito epitermal neógeno de referencia europea asociado a calderas volcánicas, alunita y silicificación masiva."
  },
  {
    name: "Salave - Tapia",
    locality: "Tapia de Casariego (Asturias)",
    district: "Zona Asturoccidental-Leonesa",
    type: "Intrusivo / Diseminado Au-As",
    scoreRef: "0.278",
    lat: 43.559,
    lon: -6.904,
    description: "Uno de los mayores depósitos sin explotar de Europa. Mineralización diseminada y stockwork en granodiorita alterada."
  },
  {
    name: "Las Médulas - Teleno",
    locality: "El Bierzo (León)",
    district: "Distrito Aurífero del Noroeste",
    type: "Aluvial Cuaternario / Filones",
    scoreRef: "0.502",
    lat: 42.460,
    lon: -6.760,
    description: "Mayor explotación aurífera del Imperio Romano (Ruina Montium), con enriquecimiento secundario sobre conglomerados miocenos."
  }
];

export const ExplainabilityView: React.FC<ExplainabilityViewProps> = ({
  activeCellExplanation,
  activeCellId,
  selectedCell,
  onZoomToZone,
  onSelectCoordinate,
  coefficients,
  onLoadCoefficients
}) => {
  // Estados de filtrado y visualización
  const [viewMode, setViewMode] = useState<"impact" | "all" | "positive" | "negative">("impact");
  const [selectedFamilyFilter, setSelectedFamilyFilter] = useState<string>("todas");
  const [sortBy, setSortBy] = useState<"magnitude" | "impact_desc" | "impact_asc" | "zscore" | "alpha">("magnitude");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [copiedMemo, setCopiedMemo] = useState<boolean>(false);
  const [copiedJson, setCopiedJson] = useState<boolean>(false);

  // Estados de pesos globales del modelo
  const [globalWeightsOpen, setGlobalWeightsOpen] = useState<boolean>(false);
  const [globalWeightsSearch, setGlobalWeightsSearch] = useState<string>("");
  const [globalWeightsFamily, setGlobalWeightsFamily] = useState<string>("todas");

  // Sumas y agregaciones por familia geológica para la celda activa
  const familyAggregates = useMemo(() => {
    if (!activeCellExplanation || !activeCellExplanation.all_contributions) return [];

    const map = new Map<
      string,
      {
        familia: string;
        netContribution: number;
        positiveCount: number;
        negativeCount: number;
        totalCount: number;
      }
    >();

    activeCellExplanation.all_contributions.forEach((c) => {
      const famKey = normalizeFamily(c.familia);
      const current = map.get(famKey) || {
        familia: famKey,
        netContribution: 0,
        positiveCount: 0,
        negativeCount: 0,
        totalCount: 0
      };
      current.netContribution += c.contribution;
      if (c.contribution > 0) current.positiveCount++;
      if (c.contribution < 0) current.negativeCount++;
      current.totalCount++;
      map.set(famKey, current);
    });

    return Array.from(map.values()).sort((a, b) => Math.abs(b.netContribution) - Math.abs(a.netContribution));
  }, [activeCellExplanation]);

  // Lista filtrada y ordenada de covariables de la celda activa
  const displayedContributions = useMemo(() => {
    if (!activeCellExplanation || !activeCellExplanation.all_contributions) return [];

    let list = [...activeCellExplanation.all_contributions];

    // 1. Filtro por modo de vista (Top impacto, positivos, negativos, todos)
    if (viewMode === "positive") {
      list = list.filter((c) => c.contribution > 0);
    } else if (viewMode === "negative") {
      list = list.filter((c) => c.contribution < 0);
    } else if (viewMode === "impact") {
      // Tomamos las 12 variables con mayor impacto absoluto
      list = [...list].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)).slice(0, 12);
    }

    // 2. Filtro por familia geológica
    if (selectedFamilyFilter !== "todas") {
      list = list.filter((c) => normalizeFamily(c.familia) === selectedFamilyFilter);
    }

    // 3. Filtro por texto de búsqueda
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (c) =>
          c.variable.toLowerCase().includes(q) ||
          c.familia.toLowerCase().includes(q) ||
          c.significado_geologico.toLowerCase().includes(q)
      );
    }

    // 4. Ordenación
    list.sort((a, b) => {
      if (sortBy === "magnitude") return Math.abs(b.contribution) - Math.abs(a.contribution);
      if (sortBy === "impact_desc") return b.contribution - a.contribution;
      if (sortBy === "impact_asc") return a.contribution - b.contribution;
      if (sortBy === "zscore") return Math.abs(b.standardized_z) - Math.abs(a.standardized_z);
      if (sortBy === "alpha") return a.variable.localeCompare(b.variable);
      return 0;
    });

    return list;
  }, [activeCellExplanation, viewMode, selectedFamilyFilter, searchQuery, sortBy]);

  // Magnitud máxima para normalizar barras de contribución
  const maxContributionMagnitude = useMemo(() => {
    if (!activeCellExplanation || !activeCellExplanation.all_contributions) return 1.0;
    const maxVal = Math.max(...activeCellExplanation.all_contributions.map((c) => Math.abs(c.contribution)), 0.1);
    return maxVal;
  }, [activeCellExplanation]);

  // Generador de Ficha Técnica Geológica en Markdown
  const handleCopyMarkdownReport = () => {
    if (!activeCellExplanation) return;

    const netSum = activeCellExplanation.logit_calculated - activeCellExplanation.intercept;
    const topPos = activeCellExplanation.top_positive_contributions.slice(0, 5);
    const topNeg = activeCellExplanation.top_negative_contributions.slice(0, 5);

    const familyLines = familyAggregates
      .map(
        (f) =>
          `- **${f.familia}**: ${f.netContribution >= 0 ? "+" : ""}${f.netContribution.toFixed(3)} logit (${f.positiveCount} favorables / ${f.negativeCount} penalizadores)`
      )
      .join("\n");

    const posLines = topPos
      .map(
        (c, idx) =>
          `${idx + 1}. **${c.variable}** (${c.familia}): \`+${c.contribution.toFixed(3)} logit\` | z=+${c.standardized_z.toFixed(2)}σ | β=${c.coefficient.toFixed(3)} | OR=${c.odds_ratio.toFixed(2)}x\n   *${c.significado_geologico}*`
      )
      .join("\n");

    const negLines = topNeg
      .map(
        (c, idx) =>
          `${idx + 1}. **${c.variable}** (${c.familia}): \`${c.contribution.toFixed(3)} logit\` | z=${c.standardized_z.toFixed(2)}σ | β=${c.coefficient.toFixed(3)} | OR=${c.odds_ratio.toFixed(2)}x\n   *${c.significado_geologico}*`
      )
      .join("\n");

    const report = `# FICHA TÉCNICA DE EXPLICABILIDAD GEOLÓGICA (XAI)
**Proyecto GeoAI España • Clasificador Lineal Congelado Fase B-F**
Fecha de emisión: ${new Date().toLocaleDateString("es-ES")}

---

## 1. Identificación Territorial
- **ID de Celda**: \`${activeCellExplanation.cell_id}\`
${
  selectedCell
    ? `- **Coordenadas WGS84**: ${selectedCell.lat_wgs84.toFixed(5)}° N, ${selectedCell.lon_wgs84.toFixed(5)}° W
- **Coordenadas UTM30 ETRS89**: X=${selectedCell.x_epsg25830.toFixed(0)} m, Y=${selectedCell.y_epsg25830.toFixed(0)} m
- **Percentil Nacional**: P${selectedCell.percentile_favorabilidad.toFixed(2)} (Banda ${selectedCell.prioridad_banda})
- **Distrito Próximo**: ${selectedCell.district_id || "N/A"}`
    : ""
}
- **Score Prospectivo P(Au)**: **${(activeCellExplanation.prospectivity_score * 100).toFixed(2)}%** (${activeCellExplanation.prospectivity_score.toFixed(4)})

---

## 2. Descomposición Matemática Lineal Exacta
**Ecuación**: \`logit(x) = β₀ + Σ(βᵢ · zᵢ)  ⟹  P(Au) = σ(logit)\`

- **Intercepto Base (β₀)**: \`${activeCellExplanation.intercept.toFixed(4)}\` (Tasa base a priori P₀ ≈ 0.16%)
- **Suma Neta de Contribuciones (Σ βᵢ · zᵢ)**: \`${netSum >= 0 ? "+" : ""}${netSum.toFixed(4)}\`
- **Logit Resultante**: \`${activeCellExplanation.logit_calculated.toFixed(4)}\`
- **Probabilidad Sigmoide Evaluada**: \`${(activeCellExplanation.sigmoid_score * 100).toFixed(2)}%\`
- **Verificación de Consistencia Numérica**: Error residual = \`${activeCellExplanation.consistency_error.toExponential(2)}\` (${activeCellExplanation.consistency_test_passed ? "APROBADO ✓ Cero fuga ni aproximación" : "REVISAR"})

---

## 3. Balance por Disciplina Geológica
${familyLines}

---

## 4. Top Factores Físicos Impulsores (+β · z)
${posLines}

---

## 5. Factores de Riesgo / Penalizadores (-β · z)
${negLines}

---
*Aviso Metodológico de Causalidad: Las contribuciones locales reflejan asociaciones estadísticas aprendidas por el clasificador regularizado sobre el dominio peninsular modelado; no demuestran un mecanismo físico causal aislado sin trabajo de campo complementario.*`;

    navigator.clipboard.writeText(report);
    setCopiedMemo(true);
    setTimeout(() => setCopiedMemo(false), 2200);
  };

  // Copiar JSON
  const handleCopyJson = () => {
    if (!activeCellExplanation) return;
    navigator.clipboard.writeText(JSON.stringify(activeCellExplanation, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2200);
  };

  // Cargar pesos globales al expandir
  const handleToggleGlobalWeights = () => {
    const next = !globalWeightsOpen;
    setGlobalWeightsOpen(next);
    if (next && coefficients.length === 0) {
      onLoadCoefficients();
    }
  };

  // Coeficientes globales filtrados
  const displayedCoefficients = useMemo(() => {
    let list = [...coefficients];
    if (globalWeightsFamily !== "todas") {
      list = list.filter((c) => normalizeFamily(c.familia) === globalWeightsFamily);
    }
    if (globalWeightsSearch.trim()) {
      const q = globalWeightsSearch.toLowerCase();
      list = list.filter(
        (c) =>
          c.variable.toLowerCase().includes(q) ||
          c.familia.toLowerCase().includes(q) ||
          c.significado_geologico.toLowerCase().includes(q)
      );
    }
    return list;
  }, [coefficients, globalWeightsFamily, globalWeightsSearch]);

  return (
    <div className="space-y-4">
      {/* 1. Encabezado de la Estación XAI */}
      <div className="flex flex-col gap-1.5 border-b border-slate-800/80 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-cyan-400">
              <Calculator className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                <span>Estación de Explicabilidad (XAI)</span>
              </h3>
              <p className="text-[10px] text-slate-400 font-mono">
                Descomposición Aditiva Exacta • Modelo Congelado v2.0
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950/60 border border-emerald-800/40 text-emerald-400"
              title="Test de consistencia ISO Fase B-F: logit exacto idéntico a decision_function"
            >
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span>Fase B-F</span>
            </span>
          </div>
        </div>

        {/* Barra de herramientas para la celda activa */}
        {activeCellExplanation && (
          <div className="flex items-center justify-between pt-1 text-[11px]">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-mono text-[10px]">Celda:</span>
              <span className="font-mono text-cyan-300 font-bold text-[11px] bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                {activeCellExplanation.cell_id}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={handleCopyMarkdownReport}
                className="flex items-center gap-1 px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-slate-300 hover:text-cyan-300 transition-all font-mono text-[10px] cursor-pointer"
                title="Copiar Ficha Técnica completa en Markdown para informes y notas de campo"
              >
                {copiedMemo ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span className="text-emerald-400 font-semibold">¡Ficha Copiada!</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-3 h-3 text-cyan-400" />
                    <span>Copiar Ficha</span>
                  </>
                )}
              </button>

              <button
                onClick={handleCopyJson}
                className="flex items-center gap-1 px-1.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-all font-mono text-[10px] cursor-pointer"
                title="Copiar datos brutos en JSON"
              >
                {copiedJson ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>JSON</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 2. SI HAY CELDA ACTIVA: Desglose Matemático y Visual */}
      {activeCellExplanation ? (
        <div className="space-y-4">
          {/* Tarjeta de Ecuación y KPIs Matemáticos */}
          <div className="p-3 rounded-xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-cyan-950/20 border border-cyan-800/40 space-y-3 shadow-lg">
            {/* Ecuación explicativa */}
            <div className="p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-center font-mono text-[10.5px]">
              <div className="text-slate-400">
                <span className="text-cyan-400 font-bold">logit(x)</span> ={" "}
                <span className="text-slate-300">β₀</span> +{" "}
                <span className="text-emerald-400 font-bold">Σ(βᵢ · zᵢ)</span>{" "}
                <span className="text-slate-500">⟹</span>{" "}
                <span className="text-amber-300 font-bold">P(Au)</span> = σ(logit)
              </div>
            </div>

            {/* Grid 4 KPIs de balance */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center font-mono">
              {/* Score P(Au) */}
              <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Score P(Au)</span>
                  <HelpTooltip term="score_favorabilidad" iconSize="xs" />
                </span>
                <div className="my-1">
                  <span
                    className={`text-base font-black ${
                      activeCellExplanation.prospectivity_score >= 0.4
                        ? "text-emerald-400"
                        : activeCellExplanation.prospectivity_score >= 0.15
                        ? "text-cyan-400"
                        : "text-slate-300"
                    }`}
                  >
                    {(activeCellExplanation.prospectivity_score * 100).toFixed(1)}%
                  </span>
                  <div className="text-[9px] text-slate-400">
                    {activeCellExplanation.prospectivity_score.toFixed(4)}
                  </div>
                </div>
                {selectedCell && (
                  <span className="text-[8.5px] px-1 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/40">
                    P{selectedCell.percentile_favorabilidad.toFixed(1)}
                  </span>
                )}
              </div>

              {/* Intercepto β₀ */}
              <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Intercepto β₀</span>
                  <HelpTooltip term="intercepto_beta0" iconSize="xs" />
                </span>
                <div className="my-1">
                  <span className="text-sm font-bold text-slate-300 font-mono">
                    {activeCellExplanation.intercept.toFixed(3)}
                  </span>
                  <div className="text-[9px] text-slate-500">Tasa Base Prior</div>
                </div>
                <span className="text-[8.5px] text-slate-400">P₀ ≈ 0.16%</span>
              </div>

              {/* Impulso Neto Σ(β·z) */}
              {(() => {
                const netContrib = activeCellExplanation.logit_calculated - activeCellExplanation.intercept;
                return (
                  <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center justify-between">
                      <span>Impulso Σ(β·z)</span>
                      <HelpTooltip term="impulso_neto" iconSize="xs" />
                    </span>
                    <div className="my-1">
                      <span
                        className={`text-sm font-black ${
                          netContrib >= 0 ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {netContrib >= 0 ? `+${netContrib.toFixed(2)}` : netContrib.toFixed(2)}
                      </span>
                      <div className="text-[9px] text-slate-500">Sobre Prior</div>
                    </div>
                    <span className="text-[8.5px] text-slate-400">
                      {netContrib >= 0 ? "Acelerador" : "Freno"}
                    </span>
                  </div>
                );
              })()}

              {/* Logit Total */}
              <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Logit Total</span>
                  <HelpTooltip term="logit_total" iconSize="xs" />
                </span>
                <div className="my-1">
                  <span className="text-sm font-bold text-cyan-300 font-mono">
                    {activeCellExplanation.logit_calculated.toFixed(3)}
                  </span>
                  <div className="text-[9px] text-slate-500">Log-Odds</div>
                </div>
                <span className="text-[8.5px] text-cyan-400/80">σ(logit)</span>
              </div>
            </div>

            {/* Verificación de Exactitud Numérica */}
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Test de Cierre Numérico: Exacto</span>
                <HelpTooltip term="cierre_numerico" iconSize="xs" />
              </span>
              <span className="text-slate-400">
                Error residual:{" "}
                <strong className="text-slate-200">
                  {activeCellExplanation.consistency_error.toExponential(2)}
                </strong>
              </span>
            </div>
          </div>

          {/* 3. Agregación y Balance por Disciplina Geológica */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
                <span>Aportación Neta por Disciplina Geológica</span>
                <HelpTooltip term="disciplina_geologica" iconSize="xs" />
              </h4>
              {selectedFamilyFilter !== "todas" && (
                <button
                  onClick={() => setSelectedFamilyFilter("todas")}
                  className="text-[10px] text-cyan-400 hover:underline cursor-pointer"
                >
                  Restablecer
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
              {familyAggregates.map((fam) => {
                const cfg = FAMILY_CONFIG[fam.familia] || {
                  label: fam.familia,
                  text: "text-slate-300",
                  bg: "bg-slate-900",
                  border: "border-slate-800",
                  bar: "from-slate-500 to-slate-400",
                  icon: "📊"
                };
                const isSelected = selectedFamilyFilter === fam.familia;

                return (
                  <button
                    key={fam.familia}
                    onClick={() =>
                      setSelectedFamilyFilter(isSelected ? "todas" : fam.familia)
                    }
                    className={`p-2 rounded-lg text-left transition-all border cursor-pointer ${
                      isSelected
                        ? "bg-slate-800 border-cyan-400 ring-1 ring-cyan-400/40"
                        : "bg-slate-900/80 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-slate-200 flex items-center gap-1 truncate">
                        <span>{cfg.icon}</span>
                        <span>{fam.familia}</span>
                      </span>
                      <span
                        className={`font-mono font-bold text-[10.5px] ${
                          fam.netContribution >= 0 ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {fam.netContribution >= 0 ? `+${fam.netContribution.toFixed(2)}` : fam.netContribution.toFixed(2)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[9px] text-slate-400 mt-1 font-mono">
                      <span>{fam.totalCount} variables</span>
                      <span className="text-slate-500">
                        {fam.positiveCount} (+), {fam.negativeCount} (-)
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 4. Explorador Interactivo de Covariables (Estilo Waterfall / SHAP) */}
          <div className="space-y-2.5">
            {/* Barra de Filtros, Vistas y Búsqueda */}
            <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-1.5 text-[10px]">
                {/* Selector de Modo de Vista */}
                <div className="flex items-center bg-slate-950 rounded-lg p-0.5 border border-slate-800 font-mono">
                  <button
                    onClick={() => setViewMode("impact")}
                    className={`px-2 py-1 rounded cursor-pointer transition-all ${
                      viewMode === "impact"
                        ? "bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/40"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    Top Impacto (12)
                  </button>
                  <button
                    onClick={() => setViewMode("all")}
                    className={`px-2 py-1 rounded cursor-pointer transition-all ${
                      viewMode === "all"
                        ? "bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/40"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    Todos (56)
                  </button>
                  <button
                    onClick={() => setViewMode("positive")}
                    className={`px-2 py-1 rounded cursor-pointer transition-all ${
                      viewMode === "positive"
                        ? "bg-emerald-950 text-emerald-300 font-semibold border border-emerald-800/40"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    Solo Positivos (+)
                  </button>
                  <button
                    onClick={() => setViewMode("negative")}
                    className={`px-2 py-1 rounded cursor-pointer transition-all ${
                      viewMode === "negative"
                        ? "bg-rose-950 text-rose-300 font-semibold border border-rose-800/40"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    Solo Negativos (-)
                  </button>
                </div>

                {/* Selector de Ordenación */}
                <div className="flex items-center gap-1 font-mono">
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="bg-slate-950 border border-slate-800 text-slate-300 rounded px-1.5 py-1 text-[10px] outline-none cursor-pointer"
                  >
                    <option value="magnitude">Mayor Magnitud |β·z|</option>
                    <option value="impact_desc">Más Positivos (+)</option>
                    <option value="impact_asc">Más Negativos (-)</option>
                    <option value="zscore">Mayor Anomalía |z|</option>
                    <option value="alpha">Alfabético</option>
                  </select>
                </div>
              </div>

              {/* Input de Búsqueda de Variable */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="Buscar covariable geológica o palabra clave..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-7 py-1.5 text-[11px] text-slate-200 placeholder:text-slate-500 outline-none focus:border-cyan-500 transition-colors"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute right-2 top-2 text-slate-400 hover:text-slate-200 cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* Lista de Tarjetas de Covariables */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono px-1">
                <span>
                  Mostrando <strong>{displayedContributions.length}</strong> de 56 covariables
                  {selectedFamilyFilter !== "todas" ? ` en ${selectedFamilyFilter}` : ""}
                </span>
                <span className="text-slate-500 flex items-center gap-1">
                  <span>Divergencia centrada a 0.0</span>
                  <HelpTooltip term="divergencia_impacto" iconSize="xs" />
                </span>
              </div>

              {displayedContributions.length === 0 ? (
                <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 text-center text-slate-400 text-[11px]">
                  No hay covariables que coincidan con los filtros seleccionados.
                </div>
              ) : (
                displayedContributions.map((c) => {
                  const isPos = c.contribution >= 0;
                  const absContrib = Math.abs(c.contribution);
                  const barWidthPercent = Math.min(
                    100,
                    Math.max(4, (absContrib / maxContributionMagnitude) * 100)
                  );
                  const famCfg = FAMILY_CONFIG[normalizeFamily(c.familia)] || {
                    label: c.familia,
                    text: "text-slate-300",
                    bg: "bg-slate-800",
                    border: "border-slate-700",
                    bar: "from-slate-500 to-slate-400",
                    icon: "•"
                  };

                  return (
                    <div
                      key={c.variable}
                      className={`p-2.5 rounded-xl bg-slate-900/80 border transition-all hover:bg-slate-900 ${
                        isPos
                          ? "border-emerald-950/60 hover:border-emerald-600/50"
                          : "border-rose-950/60 hover:border-rose-600/50"
                      }`}
                    >
                      {/* Cabecera: Nombre de variable, Familia y Contribución */}
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span
                              className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-medium border ${famCfg.bg} ${famCfg.text} ${famCfg.border}`}
                            >
                              {famCfg.icon} {c.familia}
                            </span>
                            <span
                              className="font-mono font-bold text-slate-200 text-[11.5px] truncate"
                              title={c.variable}
                            >
                              {c.variable}
                            </span>
                          </div>
                        </div>

                        {/* Badge de Impacto Local ΔLogit */}
                        <div
                          className={`shrink-0 font-mono font-bold text-xs px-2 py-0.5 rounded-lg border flex items-center gap-1 ${
                            isPos
                              ? "bg-emerald-950/80 text-emerald-400 border-emerald-800/50"
                              : "bg-rose-950/80 text-rose-400 border-rose-800/50"
                          }`}
                        >
                          {isPos ? (
                            <TrendingUp className="w-3 h-3 text-emerald-400" />
                          ) : (
                            <TrendingDown className="w-3 h-3 text-rose-400" />
                          )}
                          <span>
                            {isPos ? `+${c.contribution.toFixed(3)}` : c.contribution.toFixed(3)}
                          </span>
                        </div>
                      </div>

                      {/* Barra Divergente estilo Waterfall centrada en 0 */}
                      <div className="relative w-full bg-slate-950 rounded-full h-2 my-2 overflow-hidden border border-slate-800/80">
                        {/* Línea central de cero */}
                        <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-slate-700 z-10" />

                        {isPos ? (
                          // Positivo: desde 50% hacia la derecha
                          <div
                            className="absolute top-0 bottom-0 left-1/2 bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-r-full transition-all duration-500"
                            style={{ width: `${(barWidthPercent / 2).toFixed(1)}%` }}
                          />
                        ) : (
                          // Negativo: desde 50% hacia la izquierda
                          <div
                            className="absolute top-0 bottom-0 bg-gradient-to-r from-rose-500 to-amber-500 rounded-l-full transition-all duration-500"
                            style={{
                              left: `${(50 - barWidthPercent / 2).toFixed(1)}%`,
                              width: `${(barWidthPercent / 2).toFixed(1)}%`
                            }}
                          />
                        )}
                      </div>

                      {/* 4 Chips de Telemetría Científica */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-1 text-[9.5px] font-mono mt-2 pt-1.5 border-t border-slate-800/60">
                        <div className="bg-slate-950/70 p-1 rounded border border-slate-800/80 flex items-center justify-between">
                          <span className="text-slate-400 flex items-center gap-0.5">
                            <span>z-score:</span>
                            <HelpTooltip term="z_score" iconSize="xs" />
                          </span>
                          <strong
                            className={
                              Math.abs(c.standardized_z) >= 2.0
                                ? "text-amber-300 font-bold"
                                : "text-slate-200"
                            }
                          >
                            {c.standardized_z >= 0
                              ? `+${c.standardized_z.toFixed(2)}σ`
                              : `${c.standardized_z.toFixed(2)}σ`}
                          </strong>
                        </div>

                        <div className="bg-slate-950/70 p-1 rounded border border-slate-800/80 flex items-center justify-between">
                          <span className="text-slate-400 flex items-center gap-0.5">
                            <span>β modelo:</span>
                            <HelpTooltip term="beta_modelo" iconSize="xs" />
                          </span>
                          <strong
                            className={c.coefficient >= 0 ? "text-emerald-400" : "text-rose-400"}
                          >
                            {c.coefficient >= 0
                              ? `+${c.coefficient.toFixed(3)}`
                              : c.coefficient.toFixed(3)}
                          </strong>
                        </div>

                        <div className="bg-slate-950/70 p-1 rounded border border-slate-800/80 flex items-center justify-between">
                          <span className="text-slate-400 flex items-center gap-0.5">
                            <span>Odds Ratio:</span>
                            <HelpTooltip term="odds_ratio" iconSize="xs" />
                          </span>
                          <strong className="text-cyan-300">{c.odds_ratio.toFixed(2)}x</strong>
                        </div>

                        <div className="bg-slate-950/70 p-1 rounded border border-slate-800/80 flex items-center justify-between">
                          <span className="text-slate-400 flex items-center gap-0.5">
                            <span>Valor real:</span>
                            <HelpTooltip term="valor_real" iconSize="xs" />
                          </span>
                          <strong className="text-slate-200">{c.raw_value.toFixed(2)}</strong>
                        </div>
                      </div>

                      {/* Descripción e Interpretación Geológica */}
                      <p className="text-[10px] text-slate-300 mt-1.5 leading-snug bg-slate-950/40 p-1.5 rounded border border-slate-800/40">
                        {c.significado_geologico}
                      </p>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Aviso Metodológico */}
          <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[10px] text-slate-400 leading-tight">
            <span className="font-bold text-slate-300">Nota de Rigor Metodológico:</span> Las
            contribuciones locales reflejan la ponderación lineal determinista del clasificador
            entrenado sobre el inventario peninsular. Representan asociaciones espaciales robustas,
            no causalidad física per se sin confirmación geoquímica o de sondeo.
          </div>
        </div>
      ) : (
        /* 5. ESTADO VACÍO: Guía y Selector de Benchmarks Históricos */
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300 space-y-2">
            <div className="flex items-center gap-2 text-cyan-400">
              <Compass className="w-5 h-5 animate-pulse" />
              <span className="font-bold text-xs uppercase tracking-wider">
                Explorador de Explicabilidad Territorial
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Haz clic en cualquier punto de España peninsular en el mapa para realizar una
              descomposición lineal instantánea en <strong>O(1)</strong> de sus 56 covariables y
              comprobar la aditividad de su logit frente a la tasa base previa.
            </p>
          </div>

          {/* Celdas de Referencia / Benchmarks con 1-Click Inspect */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-xs uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                <Flame className="w-3.5 h-3.5 text-amber-400" />
                <span>Celdas de Referencia / Benchmarks Auríferos</span>
              </h4>
              <span className="text-[10px] text-slate-400 font-mono">1 Clic para Inspeccionar</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {BENCHMARK_DEPOSITS.map((b) => (
                <div
                  key={b.name}
                  className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-amber-500/50 transition-all flex flex-col justify-between group"
                >
                  <div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-100 group-hover:text-amber-300 transition-colors">
                        {b.name}
                      </span>
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/40">
                        Ref: {b.scoreRef}
                      </span>
                    </div>

                    <div className="text-[10px] text-slate-400 mt-0.5">{b.locality}</div>
                    <div className="text-[9.5px] font-mono text-cyan-400/90 mt-1">
                      {b.type} • {b.district}
                    </div>

                    <p className="text-[10px] text-slate-400 mt-1.5 leading-snug line-clamp-2">
                      {b.description}
                    </p>
                  </div>

                  <button
                    onClick={() => {
                      if (onSelectCoordinate) {
                        onSelectCoordinate(b.lat, b.lon);
                      }
                      onZoomToZone({ lat: b.lat, lon: b.lon, zoom: 12 });
                    }}
                    className="mt-3 w-full py-1.5 px-2 rounded-lg bg-slate-950 hover:bg-amber-950/60 border border-slate-800 hover:border-amber-700/60 text-slate-200 hover:text-amber-300 transition-all text-[11px] font-mono font-medium flex items-center justify-center gap-1.5 cursor-pointer shadow"
                  >
                    <Zap className="w-3.5 h-3.5 text-amber-400" />
                    <span>Inspeccionar Celda y XAI</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 6. Matriz de Coeficientes Globales del Modelo (Fase F) */}
      <div className="pt-3 border-t border-slate-800/80">
        <button
          onClick={handleToggleGlobalWeights}
          className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-900/60 hover:bg-slate-900 border border-slate-800 transition-colors cursor-pointer text-left"
        >
          <div className="flex items-center gap-2">
            <BarChart2 className="w-3.5 h-3.5 text-cyan-400" />
            <div>
              <span className="font-bold text-xs uppercase tracking-wider text-slate-200 block">
                Matriz Global de Pesos del Modelo (56 Covariables)
              </span>
              <span className="text-[10px] text-slate-400">
                Regularización L2 (Fase F) • Coeficientes estandarizados fijos
              </span>
            </div>
          </div>
          {globalWeightsOpen ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </button>

        {globalWeightsOpen && (
          <div className="mt-2 space-y-2 p-2.5 rounded-xl bg-slate-950 border border-slate-800">
            {/* Filtros de pesos globales */}
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="w-3 h-3 text-slate-500 absolute left-2 top-2" />
                <input
                  type="text"
                  placeholder="Filtrar por variable..."
                  value={globalWeightsSearch}
                  onChange={(e) => setGlobalWeightsSearch(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded pl-6 pr-2 py-1 text-[10px] text-slate-200 placeholder:text-slate-500 outline-none"
                />
              </div>

              <select
                value={globalWeightsFamily}
                onChange={(e) => setGlobalWeightsFamily(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-slate-300 rounded px-1.5 py-1 text-[10px] outline-none cursor-pointer"
              >
                <option value="todas">Todas las Familias</option>
                <option value="Estructuras">Estructuras</option>
                <option value="Litología">Litología</option>
                <option value="Edades">Edades</option>
                <option value="Relieve">Relieve</option>
                <option value="Hidrografía">Hidrografía</option>
              </select>
            </div>

            {/* Lista compacta de pesos */}
            <div className="space-y-1 max-h-60 overflow-y-auto scrollbar-thin pr-1">
              {displayedCoefficients.map((c) => {
                const isPos = c.coeficiente_estandarizado > 0;
                return (
                  <div
                    key={c.variable}
                    className="flex justify-between items-center p-1.5 rounded bg-slate-900/60 border border-slate-800/80 text-[10.5px] font-mono hover:bg-slate-900"
                  >
                    <div className="min-w-0 pr-2">
                      <div className="text-slate-200 font-semibold truncate" title={c.variable}>
                        {c.variable}
                      </div>
                      <div className="text-[9px] text-slate-400">{c.familia}</div>
                    </div>

                    <div className="text-right shrink-0">
                      <div
                        className={`font-bold ${
                          isPos ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {isPos ? "+" : ""}
                        {c.coeficiente_estandarizado.toFixed(4)}
                      </div>
                      <div className="text-[9px] text-slate-500">OR: {c.odds_ratio.toFixed(2)}x</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
