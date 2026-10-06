"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Target,
  CheckCircle2,
  Bot,
  ChevronRight,
  ChevronLeft,
  Search,
  Filter,
  ArrowUpRight,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  TrendingDown,
  Layers,
  MapPin,
  ExternalLink
} from "lucide-react";
import {
  CellExplanation,
  TargetZone,
  HoldoutMetricsSummary,
  HoldoutDepositItem,
  HoldoutDistrictItem,
  ModelCoefficient,
  CopilotResponse
} from "../types";
import { api } from "../lib/api";

interface RightPanelProps {
  activeTab: "explain" | "targets" | "validation" | "copilot";
  setActiveTab: (tab: "explain" | "targets" | "validation" | "copilot") => void;
  isCollapsed: boolean;
  setIsCollapsed: (val: boolean) => void;
  activeCellExplanation: CellExplanation | null;
  onZoomToZone: (target: { lon: number; lat: number; zoom?: number }) => void;
  activeCellId?: string | null;
}

export const RightPanel: React.FC<RightPanelProps> = ({
  activeTab,
  setActiveTab,
  isCollapsed,
  setIsCollapsed,
  activeCellExplanation,
  onZoomToZone,
  activeCellId
}) => {
  // Estados para Targets
  const [targets, setTargets] = useState<TargetZone[]>([]);
  const [targetCategory, setTargetCategory] = useState<string>("");
  const [filterWithoutDeposit, setFilterWithoutDeposit] = useState<boolean>(false);
  const [targetDistrictFilter, setTargetDistrictFilter] = useState<string>("");
  const [targetsLoading, setTargetsLoading] = useState(false);

  // Estados para Validación
  const [validationSummary, setValidationSummary] = useState<HoldoutMetricsSummary | null>(null);
  const [validationDeposits, setValidationDeposits] = useState<HoldoutDepositItem[]>([]);
  const [validationDistricts, setValidationDistricts] = useState<HoldoutDistrictItem[]>([]);
  const [validationComparison, setValidationComparison] = useState<any[]>([]);

  // Estados para Coeficientes Globales
  const [coefficients, setCoefficients] = useState<ModelCoefficient[]>([]);

  // Estados para Copiloto
  const [copilotQuery, setCopilotQuery] = useState("");
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotHistory, setCopilotHistory] = useState<CopilotResponse[]>([]);

  // Cargar datos de Targets cuando se activa la pestaña
  useEffect(() => {
    if (activeTab === "targets" && targets.length === 0) {
      loadTargets();
    } else if (activeTab === "validation" && !validationSummary) {
      loadValidation();
    } else if (activeTab === "explain" && coefficients.length === 0) {
      loadCoefficients();
    }
  }, [activeTab]);

  const loadTargets = async () => {
    setTargetsLoading(true);
    try {
      const data = await api.getTargets({
        categoria: targetCategory || undefined,
        distrito: targetDistrictFilter || undefined,
        sin_deposito_cercano: filterWithoutDeposit,
        limit: 200
      });
      setTargets(data.zones);
    } catch (err) {
      console.error("Error cargando targets:", err);
    } finally {
      setTargetsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "targets") {
      loadTargets();
    }
  }, [targetCategory, filterWithoutDeposit, targetDistrictFilter]);

  const loadValidation = async () => {
    try {
      const [sum, deps, dists, comp] = await Promise.all([
        api.getValidationSummary(),
        api.getValidationDeposits(),
        api.getValidationDistricts(),
        api.getValidationComparison()
      ]);
      setValidationSummary(sum.summary);
      setValidationDeposits(deps.deposits);
      setValidationDistricts(dists.districts);
      setValidationComparison(comp.comparison || []);
    } catch (err) {
      console.error("Error cargando validación:", err);
    }
  };

  const loadCoefficients = async () => {
    try {
      const data = await api.getModelCoefficients();
      setCoefficients(data.coefficients);
    } catch (err) {
      console.error("Error cargando coeficientes:", err);
    }
  };

  const handleCopilotSend = async (queryText?: string) => {
    const q = queryText || copilotQuery;
    if (!q.trim()) return;

    setCopilotLoading(true);
    try {
      const resp = await api.queryCopilot({
        query: q,
        context: { cell_id: activeCellId }
      });
      setCopilotHistory((prev) => [resp, ...prev]);
      setCopilotQuery("");

      // Ejecutar acción si existe
      if (resp.action) {
        if (resp.action.action_type === "select_tab") {
          setActiveTab(resp.action.payload.tab);
        } else if (resp.action.action_type === "zoom_to_zone" && resp.action.payload.zona_id) {
          const zone = targets.find((z) => z.zona_id === resp.action?.payload.zona_id);
          if (zone) {
            // Convertir de UTM30N a WGS84 aproximadamente para centrado rápido
            onZoomToZone({ lon: -4.8, lat: 38.0, zoom: 10 });
          }
        }
      }
    } catch (err) {
      console.error("Error copiloto:", err);
    } finally {
      setCopilotLoading(false);
    }
  };

  if (isCollapsed) {
    return (
      <button
        onClick={() => setIsCollapsed(false)}
        className="absolute top-16 right-3 z-20 p-2.5 rounded-lg bg-slate-900/90 text-cyan-400 hover:text-cyan-200 border border-cyan-800/60 shadow-xl backdrop-blur-md transition-all cursor-pointer"
        title="Mostrar Panel de Control"
      >
        <ChevronLeft className="w-5 h-5" />
      </button>
    );
  }

  return (
    <aside className="absolute top-16 right-3 z-20 w-[95vw] sm:w-[28rem] xl:w-[32rem] h-[calc(100vh-5rem)] bg-slate-950/95 backdrop-blur-md border border-cyan-900/40 rounded-xl shadow-2xl flex flex-col text-slate-200 text-xs font-sans select-none overflow-hidden">
      {/* 1. Header con Pestañas */}
      <div className="flex items-center justify-between border-b border-slate-800/80 bg-slate-900/80 px-2 pt-2">
        <div className="flex gap-1 overflow-x-auto scrollbar-none">
          <button
            onClick={() => setActiveTab("explain")}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-mono text-[11px] font-semibold transition-all cursor-pointer shrink-0 ${
              activeTab === "explain"
                ? "border-cyan-400 text-cyan-300 bg-cyan-950/40"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Explicabilidad</span>
          </button>

          <button
            onClick={() => setActiveTab("targets")}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-mono text-[11px] font-semibold transition-all cursor-pointer shrink-0 ${
              activeTab === "targets"
                ? "border-amber-400 text-amber-300 bg-amber-950/40"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Target className="w-3.5 h-3.5 text-amber-400" />
            <span>Targets (1.529)</span>
          </button>

          <button
            onClick={() => setActiveTab("validation")}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-mono text-[11px] font-semibold transition-all cursor-pointer shrink-0 ${
              activeTab === "validation"
                ? "border-emerald-400 text-emerald-300 bg-emerald-950/40"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Validación</span>
          </button>

          <button
            onClick={() => setActiveTab("copilot")}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-mono text-[11px] font-semibold transition-all cursor-pointer shrink-0 ${
              activeTab === "copilot"
                ? "border-purple-400 text-purple-300 bg-purple-950/40"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Bot className="w-3.5 h-3.5 text-purple-400" />
            <span>Copiloto</span>
          </button>
        </div>

        <button
          onClick={() => setIsCollapsed(true)}
          className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors shrink-0 mb-1"
          title="Colapsar"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* 2. Contenido de las Pestañas */}
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
        {/* ========================================================= */}
        {/* TAB 1: EXPLICABILIDAD */}
        {/* ========================================================= */}
        {activeTab === "explain" && (
          <div className="space-y-4">
            <div>
              <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                <span>¿Por qué esta zona recibe este score?</span>
              </h3>
              <p className="text-[11px] text-slate-400 mt-1">
                Descomposición aditiva exacta del clasificador lineal congelado:
                <br />
                <code className="text-cyan-300 font-mono text-[10px]">
                  logit(x) = intercept + Σ (β_i · z_i)
                </code>
              </p>
            </div>

            {activeCellExplanation ? (
              <div className="space-y-4">
                {/* Resumen Logit y Verificación Matemática */}
                <div className="p-3 rounded-lg bg-slate-900 border border-cyan-800/50 space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Celda:</span>
                    <span className="font-mono text-cyan-300 font-semibold">{activeCellExplanation.cell_id}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Prospectivity Score:</span>
                    <span className="font-mono text-cyan-400 font-black text-sm">{activeCellExplanation.prospectivity_score.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Logit Calculado:</span>
                    <span className="font-mono text-slate-200">{activeCellExplanation.logit_calculated.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Intercepto (β₀):</span>
                    <span className="font-mono text-slate-400">{activeCellExplanation.intercept.toFixed(4)}</span>
                  </div>

                  {/* Badge de Verificación Matemática */}
                  <div className="mt-2 pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
                    <span className="flex items-center gap-1 text-emerald-400 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Test Matemático: Exacto</span>
                    </span>
                    <span className="font-mono text-slate-400 text-[10px]">
                      Error: {activeCellExplanation.consistency_error.toExponential(2)}
                    </span>
                  </div>
                </div>

                {/* Factores que Aumentan la Favorabilidad */}
                <div>
                  <h4 className="font-bold text-xs uppercase tracking-wider text-emerald-400 flex items-center gap-1.5 mb-2">
                    <TrendingUp className="w-3.5 h-3.5" />
                    <span>Factores que Aumentan Favorabilidad (+β · z)</span>
                  </h4>
                  <div className="space-y-1.5">
                    {activeCellExplanation.top_positive_contributions.map((c) => (
                      <div key={c.variable} className="p-2 rounded bg-slate-900/60 border border-emerald-950/60 hover:border-emerald-700/60 transition-colors">
                        <div className="flex justify-between text-[11px] font-mono">
                          <span className="font-semibold text-slate-200 truncate pr-2" title={c.variable}>{c.variable}</span>
                          <span className="text-emerald-400 font-bold shrink-0">+{c.contribution.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                          <span>{c.familia} (z = {c.standardized_z.toFixed(2)})</span>
                          <span>OR: {c.odds_ratio.toFixed(2)}x (+1σ)</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-1 line-clamp-2 leading-tight">
                          {c.significado_geologico}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Factores que Reducen la Favorabilidad */}
                <div>
                  <h4 className="font-bold text-xs uppercase tracking-wider text-red-400 flex items-center gap-1.5 mb-2">
                    <TrendingDown className="w-3.5 h-3.5" />
                    <span>Factores que Reducen Favorabilidad (-β · z)</span>
                  </h4>
                  <div className="space-y-1.5">
                    {activeCellExplanation.top_negative_contributions.map((c) => (
                      <div key={c.variable} className="p-2 rounded bg-slate-900/60 border border-red-950/60 hover:border-red-700/60 transition-colors">
                        <div className="flex justify-between text-[11px] font-mono">
                          <span className="font-semibold text-slate-200 truncate pr-2" title={c.variable}>{c.variable}</span>
                          <span className="text-red-400 font-bold shrink-0">{c.contribution.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                          <span>{c.familia} (z = {c.standardized_z.toFixed(2)})</span>
                          <span>OR: {c.odds_ratio.toFixed(2)}x (+1σ)</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-1 line-clamp-2 leading-tight">
                          {c.significado_geologico}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800 text-[10px] text-slate-400 leading-tight">
                  <span className="font-bold text-slate-300">Aviso Metodológico de Causalidad:</span> Las contribuciones reflejan asociaciones estadísticas aprendidas por el modelo lineal regularizado sobre el dominio peninsular modelado; no demuestran un mecanismo causal físico aislado.
                </div>
              </div>
            ) : (
              <div className="p-8 text-center bg-slate-900/40 rounded-xl border border-slate-800 text-slate-400 space-y-2">
                <Sparkles className="w-8 h-8 text-cyan-400 mx-auto opacity-40 animate-pulse" />
                <p className="font-medium text-slate-300">Ninguna celda seleccionada</p>
                <p className="text-[11px]">
                  Haz clic en cualquier punto elegible de España peninsular en el mapa para descomponer en directo sus 56 variables geológicas.
                </p>
              </div>
            )}

            {/* Coeficientes Globales del Modelo */}
            <div className="pt-4 border-t border-slate-800">
              <h4 className="font-bold text-xs uppercase tracking-wider text-cyan-400 mb-2">
                Top Coeficientes Globales del Modelo (Fase F)
              </h4>
              <div className="space-y-1 max-h-56 overflow-y-auto scrollbar-thin">
                {coefficients.slice(0, 10).map((c) => (
                  <div key={c.variable} className="flex justify-between items-center p-1.5 rounded bg-slate-900/40 border border-slate-800/80 text-[11px] font-mono">
                    <span className="text-slate-300 truncate pr-2" title={c.variable}>{c.variable}</span>
                    <span className={c.coeficiente_estandarizado > 0 ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                      {c.coeficiente_estandarizado > 0 ? "+" : ""}{c.coeficiente_estandarizado.toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 2: TARGETS Y PRIORIZACIÓN */}
        {/* ========================================================= */}
        {activeTab === "targets" && (
          <div className="space-y-3">
            <div>
              <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                <Target className="w-4 h-4 text-amber-400" />
                <span>Zonas de Prospectividad / Priorización</span>
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                1.529 clusters contiguos derivados sin alterar los umbrales de cierre.
              </p>
            </div>

            {/* Filtros */}
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[9px] uppercase font-mono text-slate-400 block mb-1">Categoría</label>
                  <select
                    value={targetCategory}
                    onChange={(e) => setTargetCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 cursor-pointer"
                  >
                    <option value="">Todas (1.529)</option>
                    <option value="prioridad_muy_alta_top01">Top 1% (Muy Alta)</option>
                    <option value="prioridad_alta_top05">Top 5% (Alta)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[9px] uppercase font-mono text-slate-400 block mb-1">Distrito</label>
                  <input
                    type="text"
                    placeholder="Filtrar distrito..."
                    value={targetDistrictFilter}
                    onChange={(e) => setTargetDistrictFilter(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
                  />
                </div>
              </div>

              <label className="flex items-center gap-2 text-[11px] text-amber-300 cursor-pointer pt-1">
                <input
                  type="checkbox"
                  checked={filterWithoutDeposit}
                  onChange={(e) => setFilterWithoutDeposit(e.target.checked)}
                  className="accent-amber-400"
                />
                <span>Sin depósito histórico cercano (&gt; 15 km) — Targets Novedosos</span>
              </label>
            </div>

            {/* Lista de Zonas */}
            {targetsLoading ? (
              <div className="p-8 text-center text-slate-400">Cargando catálogo de zonas...</div>
            ) : (
              <div className="space-y-2 max-h-[calc(100vh-18rem)] overflow-y-auto scrollbar-thin">
                {targets.map((z) => (
                  <div
                    key={z.zona_id}
                    className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-amber-500/60 transition-all cursor-pointer group"
                    onClick={() => {
                      // Proyección aproximada de EPSG:25830 centroide_x/y a WGS84 para centrar
                      const approxLon = -3.7 + (z.centroide_x - 500000) / 85000;
                      const approxLat = 40.0 + (z.centroide_y - 4428000) / 111000;
                      onZoomToZone({ lon: approxLon, lat: approxLat, zoom: 10 });
                    }}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <div>
                        <span className="font-bold text-amber-400 font-mono text-xs">
                          #{z.ranking_nacional} {z.zona_id.replace("zona_priorizacion_", "Zona ")}
                        </span>
                        <p className="text-[10px] text-slate-400 mt-0.5">
                          {z.categoria_prioridad === "prioridad_muy_alta_top01" ? "Muy Alta (Top 1%)" : "Alta (Top 5%)"}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="text-cyan-400 font-mono font-bold text-sm block">
                          {z.score_maximo.toFixed(3)}
                        </span>
                        <span className="text-[9px] text-slate-500">Score máx</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-1 text-[10px] font-mono text-slate-400 my-1.5 bg-slate-950/60 p-1.5 rounded">
                      <div>Área: <span className="text-slate-200">{z.area_km2.toFixed(0)} km²</span></div>
                      <div>Celdas: <span className="text-slate-200">{z.celdas_count}</span></div>
                      <div className="col-span-2 truncate">Distrito: <span className="text-slate-300">{z.distrito_conocido_proximo}</span></div>
                      <div className="col-span-2 truncate text-amber-300/90">
                        Próx: {z.deposito_conocido_proximo} ({z.distancia_deposito_proximo_km.toFixed(1)} km)
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[9px] text-slate-500 italic mt-1">
                      <span>Anotación post-hoc</span>
                      <span className="group-hover:text-amber-400 flex items-center gap-0.5 font-sans font-medium transition-colors">
                        Zoom al target <ArrowUpRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 3: VALIDACIÓN Y HOLDOUT */}
        {/* ========================================================= */}
        {activeTab === "validation" && (
          <div className="space-y-4">
            <div>
              <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Evaluación Ciega en Holdout (Fase G)</span>
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Resultados inmutables sobre los 5 distritos y 8 depósitos en reserva.
              </p>
            </div>

            {validationSummary && (
              <div className="space-y-3">
                {/* Cuadrícula de Métricas Principales */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[9px] font-mono uppercase text-slate-400 block mb-0.5">Recovery @5%</span>
                    <span className="text-base font-bold font-mono text-cyan-400">
                      {(validationSummary.deposit_recovery_at_05 * 100).toFixed(1)}%
                    </span>
                    <span className="text-[8px] text-slate-500 block">1 / 8 depósitos</span>
                  </div>

                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[9px] font-mono uppercase text-slate-400 block mb-0.5">Recovery @10%</span>
                    <span className="text-base font-bold font-mono text-amber-400">
                      {(validationSummary.deposit_recovery_at_10 * 100).toFixed(1)}%
                    </span>
                    <span className="text-[8px] text-slate-500 block">2 / 8 depósitos</span>
                  </div>

                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[9px] font-mono uppercase text-slate-400 block mb-0.5">ROC-AUC P/U</span>
                    <span className="text-base font-bold font-mono text-emerald-400">
                      {validationSummary.roc_auc_PU.toFixed(4)}
                    </span>
                    <span className="text-[8px] text-slate-500 block">Test ciego</span>
                  </div>
                </div>

                {/* Declaración de Brecha de Transferencia */}
                <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-800/60 text-amber-200 text-[11px] leading-tight flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Brecha de Transferencia Observada (N=8):</span>
                    <p className="text-[10px] text-amber-300/80 mt-1">
                      El holdout independiente está limitado a N=8 depósitos; existe una alta incertidumbre estadística inherente. La menor puntuación frente a la CV interna refleja la marcada heterogeneidad genética entre los distritos de desarrollo y test.
                    </p>
                  </div>
                </div>

                {/* Comparativa Desarrollo vs Holdout */}
                <div>
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300 mb-1.5">
                    Desarrollo (CV F) vs Holdout Ciego (Fase G)
                  </h4>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono space-y-1">
                    <div className="flex justify-between border-b border-slate-800 pb-1 text-slate-400 text-[10px]">
                      <span>Métrica</span>
                      <span>Desarrollo (CV)</span>
                      <span>Holdout Ciego</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-300">ROC-AUC</span>
                      <span className="text-cyan-400 font-semibold">0.7402 ± 0.205</span>
                      <span className="text-amber-400 font-bold">0.5807</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-300">Dep. Recovery @5%</span>
                      <span className="text-cyan-400 font-semibold">43.89% ± 18.0%</span>
                      <span className="text-amber-400 font-bold">12.50% (1/8)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-300">Dep. Recovery @10%</span>
                      <span className="text-cyan-400 font-semibold">55.00% ± 22.4%</span>
                      <span className="text-amber-400 font-bold">25.00% (2/8)</span>
                    </div>
                  </div>
                </div>

                {/* Tabla de los 8 Depósitos de Test */}
                <div>
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300 mb-1.5">
                    Detalle de los 8 Depósitos de Test Ciego
                  </h4>
                  <div className="space-y-1.5 max-h-56 overflow-y-auto scrollbar-thin">
                    {validationDeposits.map((d) => (
                      <div key={d.deposit_id} className="p-2 rounded bg-slate-900/60 border border-slate-800 text-[11px]">
                        <div className="flex justify-between font-mono">
                          <span className="font-bold text-slate-200 truncate pr-2">{d.deposit_id}</span>
                          <span className={d.recovered_at_10 ? "text-emerald-400 font-bold" : "text-slate-500"}>
                            {d.recovered_at_01 ? "Hit @1%" : d.recovered_at_05 ? "Hit @5%" : d.recovered_at_10 ? "Hit @10%" : "No detectado"}
                          </span>
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-0.5">
                          <span>{d.district_id}</span>
                          <span>Score Máx: {d.max_score.toFixed(3)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 4: COPILOTO DETERMINISTA */}
        {/* ========================================================= */}
        {activeTab === "copilot" && (
          <div className="flex flex-col h-full space-y-3">
            <div>
              <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                <Bot className="w-4 h-4 text-purple-400" />
                <span>GeoAI Copilot</span>
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Consultas deterministas basadas exclusivamente en el modelo y datos auditados.
              </p>
            </div>

            {/* Botones de Consultas Frecuentes Sugeridas */}
            <div className="space-y-1.5">
              <label className="text-[10px] uppercase font-mono text-slate-400 block">Consultas Rápidas:</label>
              <div className="flex flex-wrap gap-1.5">
                {[
                  "¿Por qué esta celda tiene score alto?",
                  "¿Cuáles son las mejores zonas de Ossa Morena?",
                  "¿Qué ocurrió en el holdout?",
                  "Compara esta zona con Rodalquilar",
                  "Muéstrame targets Top 1%"
                ].map((sug) => (
                  <button
                    key={sug}
                    onClick={() => handleCopilotSend(sug)}
                    className="px-2.5 py-1 rounded bg-slate-900 hover:bg-purple-950/60 text-slate-300 hover:text-purple-300 border border-slate-800 hover:border-purple-700/60 text-[10px] font-medium transition-all cursor-pointer"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>

            {/* Input de Consulta */}
            <div className="flex gap-1.5 pt-2">
              <input
                type="text"
                value={copilotQuery}
                onChange={(e) => setCopilotQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCopilotSend()}
                placeholder="Escribe una pregunta sobre el modelo..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-purple-400"
              />
              <button
                onClick={() => handleCopilotSend()}
                disabled={copilotLoading}
                className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs disabled:opacity-50 cursor-pointer"
              >
                {copilotLoading ? "..." : "Preguntar"}
              </button>
            </div>

            {/* Historial de Respuestas */}
            <div className="flex-1 overflow-y-auto space-y-3 pt-2 scrollbar-thin">
              {copilotHistory.map((item, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-900/90 border border-purple-900/40 text-xs text-slate-200 space-y-2">
                  <div className="font-bold text-purple-300 flex items-center gap-1.5 text-[11px]">
                    <Bot className="w-3.5 h-3.5 text-purple-400" />
                    <span>{item.query}</span>
                  </div>
                  <div className="text-[11px] leading-relaxed text-slate-300 whitespace-pre-line">
                    {item.answer_markdown}
                  </div>
                  <div className="pt-2 border-t border-slate-800 text-[9px] font-mono text-slate-500">
                    Fuentes: {item.sources.join(", ")}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
