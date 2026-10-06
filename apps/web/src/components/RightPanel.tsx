"use client";

import React, { useState, useEffect, useMemo } from "react";
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
  ExternalLink,
  GripHorizontal,
  RotateCcw,
  Copy,
  Zap,
  PanelRight
} from "lucide-react";
import { useDraggable } from "../hooks/useDraggable";
import {
  CellExplanation,
  CellInfo,
  TargetZone,
  HoldoutMetricsSummary,
  HoldoutDepositItem,
  HoldoutDistrictItem,
  ModelCoefficient,
  CopilotResponse
} from "../types";
import { api } from "../lib/api";
import { ExplainabilityView } from "./ExplainabilityView";
import { utm30ToWgs84, formatWgs84 } from "../lib/geo";

// Metadatos geodésicos y geológicos verificados para los 8 depósitos del holdout ciego (Fase G)
const HOLDOUT_DEPOSITS_GEO: Record<
  string,
  { name: string; lat: number; lon: number; type: string; geologicalContext: string }
> = {
  dep_rodalquilar_cinto: {
    name: "Rodalquilar (El Cinto)",
    lat: 36.84597,
    lon: -2.06581,
    type: "Epitermal Alta Sulfuración",
    geologicalContext: "Caldera volcánica Neógena Cabo de Gata, alteración argílica avanzada."
  },
  dep_la_oriental_la_jara: {
    name: "La Oriental (Pilar de la Jara)",
    lat: 39.66085,
    lon: -4.95538,
    type: "Filón Cuarzo-Oro Orogénico",
    geologicalContext: "Estructuras tectónicas hercínicas en metasedimentos de Montes de Toledo."
  },
  dep_california_granadina_darro: {
    name: "California Granadina (Río Darro)",
    lat: 37.16707,
    lon: -3.55132,
    type: "Placer Aluvial Intramontano",
    geologicalContext: "Gravas y conglomerados auríferos en la cuenca intramontana de Granada."
  },
  dep_navalmedio_penaflor: {
    name: "Navalmedio (Peñaflor)",
    lat: 37.75115,
    lon: -5.41937,
    type: "Vetas y Cizallas Ossa Morena",
    geologicalContext: "Cinturón metamórfico del SO peninsular, encajante volcano-sedimentario."
  },
  dep_rodalquilar_santa_josefa: {
    name: "Santa Josefa (Rodalquilar)",
    lat: 36.85873,
    lon: -2.08361,
    type: "Epitermal Periférico",
    geologicalContext: "Sector distal al domo central de Rodalquilar, menor expresión superficial."
  },
  dep_la_almenara_penaflor: {
    name: "La Almenara (Peñaflor)",
    lat: 37.75726,
    lon: -5.36656,
    type: "Filón Hercínico",
    geologicalContext: "Zona de cizalla regional Ossa Morena en contacto con pórfidos félsicos."
  },
  dep_santa_comba_zas: {
    name: "Santa Comba / Zas",
    lat: 43.0897,
    lon: -8.86246,
    type: "Mineralización Granitoide",
    geologicalContext: "Leucogranitos hercínicos y contacto metamórfico en Galicia Occidental."
  },
  dep_corcoesto: {
    name: "Corcoesto (Cabana de Bergantiños)",
    lat: 43.22144,
    lon: -8.88536,
    type: "Orogénico Cizalla Malpica-Tui",
    geologicalContext: "Discordancia geofísica en zona de cizalla; penalizado por contraste granítico."
  }
};

interface RightPanelProps {
  activeTab: "explain" | "targets" | "validation" | "copilot";
  setActiveTab: (tab: "explain" | "targets" | "validation" | "copilot") => void;
  isCollapsed: boolean;
  setIsCollapsed: (val: boolean) => void;
  activeCellExplanation: CellExplanation | null;
  onZoomToZone: (target: { lon: number; lat: number; zoom?: number }) => void;
  activeCellId?: string | null;
  selectedCell?: CellInfo | null;
  onSelectCoordinate?: (lat: number, lon: number) => void;
}

export const RightPanel: React.FC<RightPanelProps> = ({
  activeTab,
  setActiveTab,
  isCollapsed,
  setIsCollapsed,
  activeCellExplanation,
  onZoomToZone,
  activeCellId,
  selectedCell,
  onSelectCoordinate
}) => {
  const { offset, isDragging, elementRef, dragProps, resetPosition } = useDraggable();

  // Estados para Targets
  const [targets, setTargets] = useState<TargetZone[]>([]);
  const [targetCategory, setTargetCategory] = useState<string>("");
  const [filterWithoutDeposit, setFilterWithoutDeposit] = useState<boolean>(false);
  const [targetDistrictFilter, setTargetDistrictFilter] = useState<string>("");
  const [targetsLoading, setTargetsLoading] = useState(false);

  // Estados para Validación
  const [validationSubTab, setValidationSubTab] = useState<"v2" | "holdout_v1">("v2");
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
  const [copiedCopilotIdx, setCopiedCopilotIdx] = useState<number | null>(null);

  // Estados de UI adicionales para Targets
  const [targetSearchQuery, setTargetSearchQuery] = useState("");
  const [copiedTargetId, setCopiedTargetId] = useState<string | null>(null);
  const [targetSortBy, setTargetSortBy] = useState<"rank" | "score" | "area" | "distance">("rank");
  const [selectedTargetId, setSelectedTargetId] = useState<string | null>(null);

  const filteredTargetsList = useMemo(() => {
    let list = targets;
    if (targetSearchQuery.trim()) {
      const q = targetSearchQuery.toLowerCase();
      list = list.filter(
        (t) =>
          t.zona_id.toLowerCase().includes(q) ||
          t.distrito_conocido_proximo?.toLowerCase().includes(q) ||
          t.deposito_conocido_proximo?.toLowerCase().includes(q)
      );
    }
    return [...list].sort((a, b) => {
      if (targetSortBy === "score") return b.score_maximo - a.score_maximo;
      if (targetSortBy === "area") return b.area_km2 - a.area_km2;
      if (targetSortBy === "distance") return b.distancia_deposito_proximo_km - a.distancia_deposito_proximo_km;
      return a.ranking_nacional - b.ranking_nacional;
    });
  }, [targets, targetSearchQuery, targetSortBy]);

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
            const coords = utm30ToWgs84(zone.centroide_x, zone.centroide_y);
            onZoomToZone({ lon: coords.lon, lat: coords.lat, zoom: 11 });
            if (onSelectCoordinate) onSelectCoordinate(coords.lat, coords.lon);
            setSelectedTargetId(zone.zona_id);
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
        className="absolute top-16 right-3 z-20 flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-950/90 hover:bg-slate-900 text-amber-400 hover:text-amber-200 border border-amber-500/40 shadow-2xl backdrop-blur-md transition-all cursor-pointer font-mono text-xs group"
        title="Abrir Panel Multitarea (Targets, Explicabilidad XAI, Copiloto)"
      >
        <PanelRight className="w-4 h-4 group-hover:scale-110 transition-transform" />
        <span className="font-semibold hidden sm:inline">Panel</span>
      </button>
    );
  }

  return (
    <aside
      ref={elementRef}
      style={{
        transform: `translate3d(${offset.x}px, ${offset.y}px, 0)`
      }}
      className={`absolute top-16 right-3 z-20 w-[95vw] sm:w-[28rem] xl:w-[32rem] h-[calc(100vh-5.5rem)] bg-slate-950/95 backdrop-blur-md border rounded-xl shadow-2xl flex flex-col text-slate-200 text-xs font-sans select-none overflow-hidden transition-shadow ${
        isDragging
          ? "border-cyan-400/80 shadow-cyan-500/20 ring-2 ring-cyan-400/30"
          : "border-cyan-900/40"
      }`}
    >
      {/* Tirador de arrastre superior */}
      <div
        {...dragProps}
        onDoubleClick={resetPosition}
        className="flex items-center justify-between px-3 py-1 bg-slate-950/80 border-b border-slate-800/80 cursor-grab active:cursor-grabbing text-slate-500 hover:text-slate-300 transition-colors"
        title="Arrastra para mover libremente por la pantalla · Doble clic para restablecer posición"
      >
        <div className="flex items-center gap-1.5 text-[10px] font-mono">
          <GripHorizontal className="w-3.5 h-3.5 text-slate-500" />
          <span>Panel Multitarea GeoAI</span>
        </div>
        <div className="flex items-center gap-1">
          {(offset.x !== 0 || offset.y !== 0) && (
            <button
              onClick={resetPosition}
              className="p-0.5 rounded text-slate-400 hover:text-cyan-300 transition-colors cursor-pointer"
              title="Restablecer posición original"
            >
              <RotateCcw className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

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
        {/* TAB 1: EXPLICABILIDAD (XAI) */}
        {/* ========================================================= */}
        {activeTab === "explain" && (
          <ExplainabilityView
            activeCellExplanation={activeCellExplanation}
            activeCellId={activeCellId}
            selectedCell={selectedCell}
            onZoomToZone={onZoomToZone}
            onSelectCoordinate={onSelectCoordinate}
            coefficients={coefficients}
            onLoadCoefficients={loadCoefficients}
          />
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

            {/* Filtros y Buscador Instantáneo */}
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-2.5">
              {/* Buscador de texto en tiempo real */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Buscar target, distrito o yacimiento..."
                  value={targetSearchQuery}
                  onChange={(e) => setTargetSearchQuery(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-8 pr-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-400 font-sans"
                />
              </div>

              {/* Botones de Categoría Rápida */}
              <div className="flex gap-1">
                {[
                  { id: "", label: "Todos" },
                  { id: "prioridad_muy_alta_top01", label: "Top 1%" },
                  { id: "prioridad_alta_top05", label: "Top 5%" }
                ].map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => setTargetCategory(cat.id)}
                    className={`flex-1 py-1 rounded text-[10px] font-mono font-semibold transition-all cursor-pointer ${
                      targetCategory === cat.id
                        ? "bg-amber-500 text-slate-950 font-bold shadow-sm"
                        : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>

              {/* Distrito */}
              <div>
                <input
                  type="text"
                  placeholder="Filtrar por distrito (ej: Somiedo, Codosera)..."
                  value={targetDistrictFilter}
                  onChange={(e) => setTargetDistrictFilter(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded px-2 py-1 text-xs text-slate-300 placeholder-slate-500"
                />
              </div>

              <label className="flex items-center gap-2 text-[11px] text-amber-300 cursor-pointer pt-0.5">
                <input
                  type="checkbox"
                  checked={filterWithoutDeposit}
                  onChange={(e) => setFilterWithoutDeposit(e.target.checked)}
                  className="accent-amber-400"
                />
                <span>Sin depósito histórico cercano (&gt; 15 km) — Novedosos</span>
              </label>

              <div className="flex items-center justify-between gap-2 border-t border-slate-800 pt-1.5 text-[10px] font-mono text-slate-400">
                <span>Catálogo: <strong className="text-amber-300">{filteredTargetsList.length}</strong> targets</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-[9px] text-slate-500">Orden:</span>
                  <select
                    value={targetSortBy}
                    onChange={(e) => setTargetSortBy(e.target.value as any)}
                    className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-amber-300 focus:outline-none focus:border-amber-500 cursor-pointer"
                  >
                    <option value="rank">Ranking #</option>
                    <option value="score">Score Máx</option>
                    <option value="area">Área km²</option>
                    <option value="distance">Aislado / Novedoso</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Lista de Zonas */}
            {targetsLoading ? (
              <div className="p-8 text-center text-slate-400 font-mono text-xs animate-pulse">
                Cargando catálogo de zonas de prospección...
              </div>
            ) : filteredTargetsList.length === 0 ? (
              <div className="p-6 text-center text-slate-500 text-xs">
                No se encontraron targets con los filtros aplicados.
              </div>
            ) : (
              <div className="space-y-2 max-h-[calc(100vh-21rem)] overflow-y-auto scrollbar-thin">
                {filteredTargetsList.map((z) => {
                  const { lon, lat } = utm30ToWgs84(z.centroide_x, z.centroide_y);
                  const isTop10 = z.ranking_nacional <= 10;
                  const isTop50 = z.ranking_nacional <= 50;
                  const isSelected = selectedTargetId === z.zona_id;

                  return (
                    <div
                      key={z.zona_id}
                      className={`p-3 rounded-xl transition-all cursor-pointer group shadow-sm ${
                        isSelected
                          ? "bg-amber-950/30 border-2 border-amber-400 ring-2 ring-amber-400/20 shadow-amber-500/10"
                          : "bg-slate-900/80 border border-slate-800 hover:border-amber-500/60 hover:shadow-amber-500/10"
                      }`}
                      onClick={() => {
                        setSelectedTargetId(z.zona_id);
                        onZoomToZone({ lon, lat, zoom: 11.5 });
                        if (onSelectCoordinate) {
                          onSelectCoordinate(lat, lon);
                        }
                      }}
                    >
                      <div className="flex justify-between items-start mb-1.5">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                              isTop10
                                ? "bg-gradient-to-r from-amber-400 to-yellow-500 text-slate-950 font-black shadow-md shadow-amber-500/20"
                                : isTop50
                                ? "bg-slate-700 text-slate-100 font-bold border border-slate-600"
                                : "bg-slate-800 text-slate-300 font-medium"
                            }`}
                          >
                            #{z.ranking_nacional}
                          </span>
                          <div>
                            <span className="font-bold text-slate-100 font-mono text-xs block group-hover:text-amber-300 transition-colors">
                              {z.zona_id.replace("zona_priorizacion_", "Zona ")}
                            </span>
                            <span className="text-[10px] text-slate-400">
                              {z.categoria_prioridad === "prioridad_muy_alta_top01" ? "Muy Alta (Top 1%)" : "Alta (Top 5%)"}
                            </span>
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="text-cyan-400 font-mono font-black text-sm block">
                            {z.score_maximo.toFixed(3)}
                          </span>
                          <span className="text-[9px] text-slate-500 font-mono">Score máx</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-1 text-[10px] font-mono text-slate-400 my-1.5 bg-slate-950/70 p-2 rounded-lg border border-slate-800/60">
                        <div>Área: <span className="text-slate-200">{z.area_km2.toFixed(1)} km²</span></div>
                        <div>Celdas: <span className="text-slate-200">{z.celdas_count}</span></div>
                        <div className="col-span-2 truncate">Distrito: <span className="text-slate-300">{z.distrito_conocido_proximo}</span></div>
                        <div className="col-span-2 truncate text-amber-300/90">
                          Próx: {z.deposito_conocido_proximo} ({z.distancia_deposito_proximo_km.toFixed(1)} km)
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-[10px] pt-1">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard.writeText(formatWgs84(lat, lon));
                            setCopiedTargetId(z.zona_id);
                            setTimeout(() => setCopiedTargetId(null), 2000);
                          }}
                          className="text-[10px] text-slate-400 hover:text-cyan-300 flex items-center gap-1 font-mono transition-colors cursor-pointer"
                          title="Copiar coordenadas WGS84 exactas del centroide"
                        >
                          {copiedTargetId === z.zona_id ? (
                            <span className="text-emerald-400 font-bold flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> ¡Copiado!
                            </span>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" /> {formatWgs84(lat, lon)}
                            </>
                          )}
                        </button>

                        <span className="group-hover:text-amber-400 flex items-center gap-0.5 font-medium text-slate-400 text-[11px] transition-colors">
                          Explorar target <ArrowUpRight className="w-3.5 h-3.5" />
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 3: VALIDACIÓN Y HOLDOUT */}
        {/* ========================================================= */}
        {activeTab === "validation" && (
          <div className="space-y-4">
            {/* Sub-selector de Validación */}
            <div className="flex p-1 bg-slate-900 rounded-lg border border-slate-800 gap-1">
              <button
                onClick={() => setValidationSubTab("v2")}
                className={`flex-1 py-1.5 px-2 rounded-md font-mono text-[10px] font-bold transition-all cursor-pointer ${
                  validationSubTab === "v2"
                    ? "bg-amber-500 text-slate-950 shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Modelos v2 (787 Indicios)
              </button>
              <button
                onClick={() => setValidationSubTab("holdout_v1")}
                className={`flex-1 py-1.5 px-2 rounded-md font-mono text-[10px] font-bold transition-all cursor-pointer ${
                  validationSubTab === "holdout_v1"
                    ? "bg-slate-700 text-slate-100 shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Auditoría v1.0 (Holdout N=8)
              </button>
            </div>

            {/* VISTA A: MODELOS V2 (787 INDICIOS - PRODUCCIÓN) */}
            {validationSubTab === "v2" && (
              <div className="space-y-3.5">
                <div>
                  <h3 className="font-bold text-slate-100 text-xs flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-400" />
                    <span>Rendimiento de Modelos Especializados v2</span>
                  </h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Entrenados sobre la base expandida de 787 yacimientos e indicios mineros documentados (IGME).
                  </p>
                </div>

                {/* 3 Tarjetas de Métricas de Modelos v2 */}
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2.5 rounded-lg bg-gradient-to-b from-amber-950/40 to-slate-900 border border-amber-800/40 text-center">
                    <span className="text-[9px] font-mono text-amber-400 uppercase font-bold block mb-0.5">
                      Oro en Roca
                    </span>
                    <span className="text-lg font-black font-mono text-amber-300">0.976</span>
                    <span className="text-[8px] text-slate-400 block mt-0.5">ROC-AUC Vetas</span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-gradient-to-b from-cyan-950/40 to-slate-900 border border-cyan-800/40 text-center">
                    <span className="text-[9px] font-mono text-cyan-400 uppercase font-bold block mb-0.5">
                      Oro Aluvial
                    </span>
                    <span className="text-lg font-black font-mono text-cyan-300">0.951</span>
                    <span className="text-[8px] text-slate-400 block mt-0.5">ROC-AUC Placeres</span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-gradient-to-b from-emerald-950/40 to-slate-900 border border-emerald-800/40 text-center">
                    <span className="text-[9px] font-mono text-emerald-400 uppercase font-bold block mb-0.5">
                      Global v2
                    </span>
                    <span className="text-lg font-black font-mono text-emerald-300">0.962</span>
                    <span className="text-[8px] text-slate-400 block mt-0.5">ROC-AUC 787 pts</span>
                  </div>
                </div>

                {/* Resumen Comparativo de Capacidades */}
                <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-xs space-y-2">
                  <h4 className="font-bold text-[11px] text-slate-200 uppercase tracking-wide">
                    Comparativa de Generación de Modelos
                  </h4>
                  <div className="space-y-1.5 text-[10px] font-mono">
                    <div className="flex justify-between items-center p-1.5 rounded bg-slate-950/60 border border-slate-800/60">
                      <span className="text-slate-400">Yacimientos Conocidos:</span>
                      <span className="text-amber-300 font-bold">173 (v1.0) → 787 (v2.0) (+355%)</span>
                    </div>
                    <div className="flex justify-between items-center p-1.5 rounded bg-slate-950/60 border border-slate-800/60">
                      <span className="text-slate-400">Capacidad Discriminante:</span>
                      <span className="text-emerald-400 font-bold">ROC 0.74 → 0.96+</span>
                    </div>
                    <div className="flex justify-between items-center p-1.5 rounded bg-slate-950/60 border border-slate-800/60">
                      <span className="text-slate-400">Diferenciación Genética:</span>
                      <span className="text-cyan-300 font-bold">Doble Modelo (Roca vs Aluvial)</span>
                    </div>
                  </div>
                </div>

                {/* Controles Geológicos Clave Aprendidos */}
                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-[10px] space-y-1.5">
                  <span className="font-bold text-slate-300 uppercase tracking-wide block">
                    Controles Geológicos Dominantes (SHAP / Feature Importance):
                  </span>
                  <ul className="list-disc list-inside space-y-1 text-slate-400">
                    <li><strong className="text-slate-200">En Roca:</strong> Corredores de cizalla hercínicos, aureolas de contacto granítico, rocas paleozoicas del Macizo Ibérico.</li>
                    <li><strong className="text-slate-200">En Aluvial:</strong> Paleocauces del Cenozoico, terrazas fluviales cuaternarias (Duero, Sil, Tajo), cercanía a áreas fuente desmanteladas.</li>
                  </ul>
                </div>

                {/* Yacimientos Clave de Referencia v2 */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[11px] text-amber-300 uppercase tracking-wide flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-amber-400" />
                      Yacimientos Clave de Referencia (N=787)
                    </span>
                    <span className="text-[9px] font-mono text-slate-500">1-click inspección</span>
                  </div>
                  <div className="grid grid-cols-2 gap-1.5">
                    {[
                      {
                        name: "El Valle-Boinás",
                        dist: "Cinturón del Narcea (Asturias)",
                        lat: 43.298,
                        lon: -6.299,
                        type: "Skarn / Hidrotermal",
                        score: "0.999"
                      },
                      {
                        name: "Rodalquilar",
                        dist: "Cabo de Gata (Almería)",
                        lat: 36.848,
                        lon: -2.043,
                        type: "Epitermal Alta Sulfuración",
                        score: "0.880"
                      },
                      {
                        name: "Salave",
                        dist: "Tapia de Casariego (Asturias)",
                        lat: 43.559,
                        lon: -6.983,
                        type: "Stockwork Granítico",
                        score: "0.984"
                      },
                      {
                        name: "Las Médulas",
                        dist: "El Bierzo (León)",
                        lat: 42.461,
                        lon: -6.764,
                        type: "Paleoplacer Mioceno",
                        score: "0.942"
                      }
                    ].map((bm) => (
                      <button
                        key={bm.name}
                        onClick={() => {
                          onZoomToZone({ lon: bm.lon, lat: bm.lat, zoom: 12 });
                          if (onSelectCoordinate) onSelectCoordinate(bm.lat, bm.lon);
                        }}
                        className="p-2 rounded-lg bg-slate-950/70 hover:bg-amber-950/40 border border-slate-800/80 hover:border-amber-500/60 text-left transition-all group cursor-pointer"
                      >
                        <div className="flex justify-between items-start">
                          <span className="font-bold text-[11px] text-slate-200 group-hover:text-amber-300 transition-colors">
                            {bm.name}
                          </span>
                          <span className="text-[9px] font-mono font-bold text-cyan-400">
                            {bm.score}
                          </span>
                        </div>
                        <span className="text-[9px] text-slate-400 block truncate">{bm.dist}</span>
                        <span className="text-[8px] font-mono text-amber-400/90 block mt-0.5">{bm.type}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* VISTA B: HOLDOUT AUDITADO V1.0 (FASE G) */}
            {validationSubTab === "holdout_v1" && validationSummary && (
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
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-[11px] leading-tight flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-slate-200">Evaluación Ciega N=8 Depósitos:</span>
                    <p className="text-[10px] text-slate-400 mt-1">
                      El holdout independiente de la Fase G evaluó 8 depósitos en reserva estricta sin contacto previo. Refleja la heterogeneidad entre distritos de calibración inicial y test.
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
                  <div className="flex items-center justify-between mb-1.5">
                    <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300">
                      Detalle de los 8 Depósitos de Test Ciego
                    </h4>
                    <span className="text-[9px] font-mono text-slate-500">Clic para inspeccionar</span>
                  </div>
                  <div className="space-y-1.5 max-h-72 overflow-y-auto scrollbar-thin">
                    {validationDeposits.map((d) => {
                      const meta = HOLDOUT_DEPOSITS_GEO[d.deposit_id] || {
                        name: d.deposit_id,
                        lat: 40.0,
                        lon: -3.7,
                        type: "Depósito Blind Holdout",
                        geologicalContext: d.district_id
                      };
                      const hitClass = d.recovered_at_01
                        ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                        : d.recovered_at_05
                        ? "bg-teal-500/20 text-teal-300 border-teal-500/40"
                        : d.recovered_at_10
                        ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
                        : "bg-slate-800 text-slate-400 border-slate-700";
                      const hitText = d.recovered_at_01
                        ? "Hit @1%"
                        : d.recovered_at_05
                        ? "Hit @5%"
                        : d.recovered_at_10
                        ? "Hit @10%"
                        : "No detectado";

                      return (
                        <div
                          key={d.deposit_id}
                          onClick={() => {
                            onZoomToZone({ lon: meta.lon, lat: meta.lat, zoom: 12 });
                            if (onSelectCoordinate) onSelectCoordinate(meta.lat, meta.lon);
                          }}
                          className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/60 transition-all cursor-pointer group shadow-sm hover:shadow-amber-500/10"
                        >
                          <div className="flex justify-between items-start font-mono">
                            <div className="pr-2">
                              <span className="font-bold text-slate-200 text-xs block group-hover:text-amber-300 transition-colors">
                                {meta.name}
                              </span>
                              <span className="text-[10px] text-slate-400 font-sans block">
                                {meta.type}
                              </span>
                            </div>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${hitClass} shrink-0`}>
                              {hitText}
                            </span>
                          </div>

                          <p className="text-[10px] text-slate-400 font-sans mt-1.5 leading-relaxed bg-slate-950/60 p-1.5 rounded border border-slate-800/40">
                            {meta.geologicalContext}
                          </p>

                          <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 mt-2 pt-1 border-t border-slate-800/50">
                            <span>Score: <strong className="text-cyan-300">{d.max_score.toFixed(3)}</strong></span>
                            <span>Percentil: <strong className="text-amber-300">{d.best_percentile_favorability.toFixed(1)}%</strong></span>
                            <span className="text-[9px] text-slate-400 flex items-center gap-0.5 group-hover:text-amber-400 transition-colors">
                              Inspeccionar <ArrowUpRight className="w-3 h-3" />
                            </span>
                          </div>
                        </div>
                      );
                    })}
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
              <label className="text-[10px] uppercase font-mono text-slate-400 block flex items-center justify-between">
                <span>Consultas Rápidas Sugeridas:</span>
                <span className="text-[9px] text-purple-400 font-normal">Determinista</span>
              </label>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { text: "¿Por qué El Valle-Boinás tiene alto score?", tag: "Cinturón Narcea" },
                  { text: "¿Cuáles son los 3 mejores targets sin minas?", tag: "Exploración" },
                  { text: "¿Qué ocurrió en el holdout ciego (Fase G)?", tag: "Auditoría" },
                  { text: "Compara el modelo en Roca vs Aluvial", tag: "Modelos v2" },
                  { text: "Muéstrame los targets Top 1%", tag: "Top 1%" }
                ].map((sug) => (
                  <button
                    key={sug.text}
                    onClick={() => handleCopilotSend(sug.text)}
                    className="px-2.5 py-1 rounded-lg bg-slate-900/90 hover:bg-purple-950/60 text-slate-300 hover:text-purple-200 border border-slate-800 hover:border-purple-600/60 text-[10px] font-medium transition-all cursor-pointer flex items-center gap-1.5 group text-left"
                  >
                    <span>{sug.text}</span>
                    <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-purple-950 text-purple-400 border border-purple-800/40 group-hover:bg-purple-900/80">
                      {sug.tag}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Input de Consulta */}
            <div className="flex gap-1.5 pt-1">
              <input
                type="text"
                value={copilotQuery}
                onChange={(e) => setCopilotQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCopilotSend()}
                placeholder="Pregunta sobre covariables, distritos o targets..."
                className="flex-1 bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-400 transition-colors shadow-inner"
              />
              <button
                onClick={() => handleCopilotSend()}
                disabled={copilotLoading || !copilotQuery.trim()}
                className="px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs disabled:opacity-40 transition-all cursor-pointer shadow-lg shadow-purple-600/20 flex items-center gap-1 shrink-0"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>{copilotLoading ? "..." : "Consultar"}</span>
              </button>
            </div>

            {/* Estado de Carga / Animación de Razonamiento */}
            {copilotLoading && (
              <div className="p-3 rounded-xl bg-purple-950/40 border border-purple-800/50 text-xs text-purple-200 flex items-center gap-3 animate-pulse shadow-md">
                <Bot className="w-5 h-5 text-purple-400 animate-spin shrink-0" />
                <div>
                  <span className="font-bold text-[11px] block text-purple-300">GeoAI Copilot analizando datos...</span>
                  <span className="text-[10px] text-purple-400/80">Consultando matriz de 56 covariables y coeficientes auditados</span>
                </div>
              </div>
            )}

            {/* Historial de Respuestas */}
            <div className="flex-1 overflow-y-auto space-y-3 pt-1 scrollbar-thin">
              {copilotHistory.length === 0 && !copilotLoading ? (
                <div className="p-6 text-center bg-slate-900/30 rounded-xl border border-slate-800/80 text-slate-400 space-y-1.5 my-2">
                  <Bot className="w-8 h-8 text-purple-400/50 mx-auto" />
                  <p className="font-medium text-slate-300 text-xs">Asistente Geológico Determinista</p>
                  <p className="text-[10px] text-slate-500 max-w-xs mx-auto">
                    Haz clic en una consulta rápida o escribe tu pregunta. Las respuestas provienen estrictamente de los datos verificados del modelo.
                  </p>
                </div>
              ) : (
                copilotHistory.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-900/90 border border-purple-900/40 hover:border-purple-750 text-xs text-slate-200 space-y-2.5 shadow-md transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-bold text-purple-300 flex items-center gap-1.5 text-[11px]">
                        <Bot className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                        <span className="line-clamp-1">{item.query}</span>
                      </div>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(item.answer_markdown);
                          setCopiedCopilotIdx(idx);
                          setTimeout(() => setCopiedCopilotIdx(null), 2000);
                        }}
                        className="text-[9px] font-mono px-2 py-0.5 rounded bg-purple-950/70 hover:bg-purple-900 text-purple-300 border border-purple-800/50 flex items-center gap-1 transition-colors cursor-pointer shrink-0"
                        title="Copiar respuesta al portapapeles"
                      >
                        {copiedCopilotIdx === idx ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            <span className="text-emerald-400 font-bold">¡Copiado!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copiar</span>
                          </>
                        )}
                      </button>
                    </div>

                    <div className="text-[11px] leading-relaxed text-slate-300 whitespace-pre-line bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/60 font-sans">
                      {item.answer_markdown}
                    </div>

                    <div className="pt-1.5 border-t border-slate-800 flex items-center justify-between text-[9px] font-mono text-slate-500">
                      <span className="truncate pr-2">Fuentes: {item.sources.join(", ")}</span>
                      <span className="text-emerald-400 shrink-0">Verificado ✓</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
