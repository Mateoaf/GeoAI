"use client";

import React from "react";
import {
  Layers,
  MapPin,
  Target,
  Eye,
  Sliders,
  Map as MapIcon,
  ChevronLeft,
  ChevronRight,
  GripHorizontal,
  RotateCcw,
  Flame,
  Waves,
  Compass,
  CircleDot,
  Sparkles,
  Crosshair,
  Zap
} from "lucide-react";
import { useDraggable } from "../hooks/useDraggable";
import { RasterLayerType } from "../types";
import { HelpTooltip } from "./HelpTooltip";

interface LeftLayerPanelProps {
  activeRasterLayer: RasterLayerType;
  setActiveRasterLayer: (layer: RasterLayerType) => void;
  rasterOpacity: number;
  setRasterOpacity: (val: number) => void;
  showZones: boolean;
  setShowZones: (val: boolean) => void;
  showDeposits: boolean;
  setShowDeposits: (val: boolean) => void;
  showIndicios?: boolean;
  setShowIndicios?: (val: boolean) => void;
  indicioFilter?: "todos" | "roca" | "aluvial";
  setIndicioFilter?: (val: "todos" | "roca" | "aluvial") => void;
  showDistricts?: boolean;
  setShowDistricts?: (val: boolean) => void;
  bufferToolActive?: boolean;
  setBufferToolActive?: (val: boolean) => void;
  bufferRadiusKm?: number;
  setBufferRadiusKm?: (val: number) => void;
  baseMap: "dark" | "street" | "satellite";
  setBaseMap: (val: "dark" | "street" | "satellite") => void;
  isCollapsed: boolean;
  setIsCollapsed: (val: boolean) => void;
  onToggleAB?: () => void;
}

export const LeftLayerPanel: React.FC<LeftLayerPanelProps> = ({
  activeRasterLayer,
  setActiveRasterLayer,
  rasterOpacity,
  setRasterOpacity,
  showZones,
  setShowZones,
  showDeposits,
  setShowDeposits,
  showIndicios = true,
  setShowIndicios,
  indicioFilter = "todos",
  setIndicioFilter,
  showDistricts = true,
  setShowDistricts,
  bufferToolActive = false,
  setBufferToolActive,
  bufferRadiusKm = 10,
  setBufferRadiusKm,
  baseMap,
  setBaseMap,
  isCollapsed,
  setIsCollapsed,
  onToggleAB
}) => {
  const { offset, isDragging, elementRef, dragProps, resetPosition } = useDraggable();

  if (isCollapsed) {
    return (
      <button
        onClick={() => setIsCollapsed(false)}
        className="absolute top-16 left-3 z-20 flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-950/90 text-cyan-400 hover:text-cyan-200 border border-cyan-800/70 shadow-2xl backdrop-blur-md transition-all cursor-pointer group hover:border-cyan-400"
        title="Mostrar Capas GeoAI"
      >
        <Layers className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
        <span className="font-mono text-[11px] font-bold text-slate-200">Capas</span>
      </button>
    );
  }

  return (
    <aside
      ref={elementRef}
      style={{
        transform: `translate3d(${offset.x}px, ${offset.y}px, 0)`
      }}
      className={`absolute top-16 left-3 z-20 w-72 max-h-[calc(100vh-5.5rem)] overflow-y-auto bg-slate-950/95 backdrop-blur-md border rounded-xl shadow-2xl p-3.5 text-slate-200 text-xs font-sans select-none scrollbar-thin transition-shadow ${
        isDragging
          ? "border-cyan-400/80 shadow-cyan-500/20 ring-2 ring-cyan-400/30"
          : "border-cyan-900/40"
      }`}
    >
      {/* Header del Panel con Tirador de Arrastre */}
      <div
        {...dragProps}
        onDoubleClick={resetPosition}
        className="flex items-center justify-between border-b border-slate-800/80 pb-2 mb-3 cursor-grab active:cursor-grabbing hover:bg-slate-900/40 -mx-1 px-1 rounded transition-colors"
        title="Arrastra para mover el panel · Doble clic para reiniciar posición"
      >
        <div className="flex items-center gap-2">
          <GripHorizontal className="w-4 h-4 text-slate-500 hover:text-cyan-400 transition-colors" />
          <Layers className="w-4 h-4 text-cyan-400" />
          <h2 className="font-bold tracking-wider uppercase text-cyan-300 text-[11px]">
            Capas GeoAI
          </h2>
        </div>
        <div className="flex items-center gap-1">
          {(offset.x !== 0 || offset.y !== 0) && (
            <button
              onClick={resetPosition}
              className="p-1 rounded text-slate-400 hover:text-cyan-300 hover:bg-slate-800/60 transition-colors cursor-pointer"
              title="Restablecer posición inicial"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={() => setIsCollapsed(true)}
            className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors cursor-pointer"
            title="Colapsar panel"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 1. Capas Predictivas Raster */}
      <div className="mb-4">
        {/* Grupo 1: Motor Oficial de Producción GeoAI v3.0 */}
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-[10px] uppercase font-mono tracking-wider text-purple-400 font-bold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
            Motor Oficial GeoAI v3.0 (Producción)
          </label>
          <span className="text-[9px] bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded font-mono font-bold">15km CV</span>
        </div>
        <div className="space-y-1.5 mb-3">
          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "v3_pu_score" ? "bg-purple-950/50 border-purple-500/50 text-purple-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm"></span>
              <span>Favorabilidad PU Calibrada (c=0.72)</span>
              <HelpTooltip term="pu_learning" />
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "v3_pu_score"}
              onChange={() => setActiveRasterLayer("v3_pu_score")}
              className="accent-purple-400 cursor-pointer"
            />
          </label>

          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "v3_uncertainty" ? "bg-purple-950/50 border-purple-500/50 text-purple-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-fuchsia-400 shadow-sm"></span>
              <span>Incertidumbre Epistémica (σ)</span>
              <HelpTooltip term="incertidumbre_epistemica" />
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "v3_uncertainty"}
              onChange={() => setActiveRasterLayer("v3_uncertainty")}
              className="accent-purple-400 cursor-pointer"
            />
          </label>
        </div>

        {/* Grupo 2: Modelos Metalogenéticos Especializados */}
        <div className="flex items-center justify-between mb-1.5 pt-2 border-t border-slate-800/80">
          <label className="text-[10px] uppercase font-mono tracking-wider text-amber-400 font-bold">
            Especialización Metalogenética
          </label>
          <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-mono font-bold">Tipologías</span>
        </div>
        <div className="space-y-1.5 mb-3">
          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "rock_score" ? "bg-amber-950/50 border-amber-500/50 text-amber-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm"></span>
              <span>Oro en Roca (Vetas & Skarns)</span>
              <HelpTooltip term="oro_roca" />
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "rock_score"}
              onChange={() => setActiveRasterLayer("rock_score")}
              className="accent-amber-400 cursor-pointer"
            />
          </label>

          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "alluvial_score" ? "bg-amber-950/50 border-amber-500/50 text-amber-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-400 shadow-sm"></span>
              <span>Oro Aluvial (Placeres Cuaternarios)</span>
              <HelpTooltip term="oro_aluvial" />
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "alluvial_score"}
              onChange={() => setActiveRasterLayer("alluvial_score")}
              className="accent-amber-400 cursor-pointer"
            />
          </label>

          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "global_v2_score" ? "bg-amber-950/50 border-amber-500/50 text-amber-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-sm"></span>
              <span>Ensamble Multitipología v2</span>
              <HelpTooltip term="ensamble_multitipologia" />
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "global_v2_score"}
              onChange={() => setActiveRasterLayer("global_v2_score")}
              className="accent-amber-400 cursor-pointer"
            />
          </label>
        </div>

        {/* Grupo 3: Zonificación Territorial y Prioridades */}
        <div className="flex items-center justify-between mb-1.5 pt-2 border-t border-slate-800/80">
          <label className="text-[10px] uppercase font-mono tracking-wider text-cyan-400 font-bold">
            Zonificación y Prioridades
          </label>
        </div>
        <div className="space-y-1.5 mb-3">
          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "priority" ? "bg-cyan-950/50 border-cyan-500/50 text-cyan-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-sm"></span>
              <span>Bandas Top 1% / 5% / 10%</span>
              <HelpTooltip term="bandas_prioritarias" />
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "priority"}
              onChange={() => setActiveRasterLayer("priority")}
              className="accent-cyan-400 cursor-pointer"
            />
          </label>

          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "percentile" ? "bg-cyan-950/50 border-cyan-500/50 text-cyan-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-400 shadow-sm"></span>
              <span>Percentil Territorial Continuo</span>
              <HelpTooltip term="percentil_territorial" />
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "percentile"}
              onChange={() => setActiveRasterLayer("percentile")}
              className="accent-cyan-400 cursor-pointer"
            />
          </label>
        </div>

        {/* Grupo 4: Referencia Metodológica & Visibilidad */}
        <div className="flex items-center justify-between mb-1.5 pt-2 border-t border-slate-800/80">
          <label className="text-[10px] uppercase font-mono tracking-wider text-slate-500 font-bold">
            Referencia Histórica & Control
          </label>
        </div>
        <div className="space-y-1.5">
          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "score" ? "bg-slate-800 border-slate-600 text-slate-200 shadow-sm" : "bg-slate-900/40 border-slate-800/80 hover:border-slate-700 text-slate-400"}`}>
            <span className="flex items-center gap-2 font-medium text-xs">
              <span className="w-2 h-2 rounded-full bg-slate-500 shadow-sm"></span>
              <span>Línea Base v1.0 (Regresión Logística 2024)</span>
              <HelpTooltip term="linea_base_v1" />
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "score"}
              onChange={() => setActiveRasterLayer("score")}
              className="accent-slate-400 cursor-pointer"
            />
          </label>

          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "none" ? "bg-slate-800 border-slate-600 text-slate-300" : "bg-slate-900/50 border-slate-800 text-slate-400"}`}>
            <span className="font-medium text-slate-400 text-xs">Ocultar Ráster</span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "none"}
              onChange={() => setActiveRasterLayer("none")}
              className="accent-cyan-400 cursor-pointer"
            />
          </label>
        </div>

        {/* Botón de Comparativa Rápida A/B */}
        {onToggleAB && (
          <button
            type="button"
            onClick={onToggleAB}
            className="w-full mt-2 py-1.5 px-2.5 rounded-lg bg-slate-900/90 hover:bg-amber-950/60 text-slate-300 hover:text-amber-300 border border-slate-800 hover:border-amber-600/50 transition-all text-[11px] font-mono flex items-center justify-center gap-1.5 cursor-pointer shadow"
            title="Alternar comparativa rápida de modelos A/B (Roca ↔ Aluvial o v1 ↔ v2)"
          >
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>Alternar Modelo A/B Rápido</span>
          </button>
        )}

        {/* Control de Opacidad del Ráster */}
        {activeRasterLayer !== "none" && (
          <div className="mt-3 p-2 rounded-lg bg-slate-900/70 border border-slate-800/80">
            <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono mb-1">
              <span className="flex items-center gap-1">
                <Sliders className="w-3 h-3 text-cyan-400" /> Opacidad
              </span>
              <span className="text-cyan-300 font-bold">{Math.round(rasterOpacity * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={rasterOpacity}
              onChange={(e) => setRasterOpacity(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
            />
          </div>
        )}
      </div>

      {/* 2. Capas Vectoriales e Inteligencia Minera */}
      <div className="mb-4 pt-3 border-t border-slate-800/80">
        <label className="text-[10px] uppercase font-mono tracking-wider text-cyan-400 font-bold block mb-2">
          Inteligencia Minera (Vectorial)
        </label>
        <div className="space-y-2">
          {/* Indicios BDMIN 787 */}
          <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="flex items-center gap-2 font-medium">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>Indicios BDMIN ({indicioFilter === "roca" ? "294" : indicioFilter === "aluvial" ? "299" : "787"})</span>
                <HelpTooltip term="indicios_bdmin" />
              </span>
              <input
                type="checkbox"
                checked={showIndicios}
                onChange={(e) => setShowIndicios?.(e.target.checked)}
                className="accent-amber-400 w-3.5 h-3.5 cursor-pointer rounded"
              />
            </label>

            {showIndicios && setIndicioFilter && (
              <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setIndicioFilter("todos")}
                  className={`flex-1 py-1 px-1.5 rounded text-[10px] font-mono transition-all ${
                    indicioFilter === "todos"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold"
                      : "text-slate-400 hover:text-slate-200 bg-slate-800/40"
                  }`}
                >
                  Todos (787)
                </button>
                <button
                  type="button"
                  onClick={() => setIndicioFilter("roca")}
                  className={`flex items-center justify-center gap-1 py-1 px-1.5 rounded text-[10px] font-mono transition-all ${
                    indicioFilter === "roca"
                      ? "bg-amber-500/30 text-amber-200 border border-amber-500/60 font-bold"
                      : "text-slate-400 hover:text-slate-200 bg-slate-800/40"
                  }`}
                  title="Oro primario en roca / filones"
                >
                  <Flame className="w-2.5 h-2.5 text-amber-400" /> Roca
                </button>
                <button
                  type="button"
                  onClick={() => setIndicioFilter("aluvial")}
                  className={`flex items-center justify-center gap-1 py-1 px-1.5 rounded text-[10px] font-mono transition-all ${
                    indicioFilter === "aluvial"
                      ? "bg-cyan-500/30 text-cyan-200 border border-cyan-500/60 font-bold"
                      : "text-slate-400 hover:text-slate-200 bg-slate-800/40"
                  }`}
                  title="Oro secundario aluvial / placeres"
                >
                  <Waves className="w-2.5 h-2.5 text-cyan-400" /> Aluvial
                </button>
              </div>
            )}
          </div>

          {/* Distritos Metalogénicos (32) */}
          <label className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800 hover:border-slate-700 cursor-pointer">
            <span className="flex items-center gap-2">
              <Compass className="w-3.5 h-3.5 text-cyan-400" />
              <span>Distritos Metalogénicos (32)</span>
              <HelpTooltip term="distritos_metalogenicos" />
            </span>
            <input
              type="checkbox"
              checked={showDistricts}
              onChange={(e) => setShowDistricts?.(e.target.checked)}
              className="accent-cyan-400 w-3.5 h-3.5 cursor-pointer rounded"
            />
          </label>

          {/* Zonas de Prospectividad (1.529) */}
          <label className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800 hover:border-slate-700 cursor-pointer">
            <span className="flex items-center gap-2">
              <Target className="w-3.5 h-3.5 text-emerald-400" />
              <span>Zonas de Prospectividad (1.529)</span>
              <HelpTooltip term="zonas_prospectividad" />
            </span>
            <input
              type="checkbox"
              checked={showZones}
              onChange={(e) => setShowZones(e.target.checked)}
              className="accent-emerald-400 w-3.5 h-3.5 cursor-pointer rounded"
            />
          </label>

          {/* Depósitos Auditados (46) */}
          <label className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800 hover:border-slate-700 cursor-pointer">
            <span className="flex items-center gap-2">
              <MapPin className="w-3.5 h-3.5 text-yellow-400" />
              <span>Yacimientos Mayores (46)</span>
              <HelpTooltip term="yacimientos_mayores" />
            </span>
            <input
              type="checkbox"
              checked={showDeposits}
              onChange={(e) => setShowDeposits(e.target.checked)}
              className="accent-yellow-400 w-3.5 h-3.5 cursor-pointer rounded"
            />
          </label>
        </div>
      </div>

      {/* 2.5. Herramienta Espacial: Buffer de Prospección */}
      <div className="mb-4 pt-3 border-t border-slate-800/80">
        <div className="flex items-center justify-between mb-2">
          <label className="text-[10px] uppercase font-mono tracking-wider text-cyan-400 font-bold flex items-center gap-1.5">
            <Crosshair className="w-3.5 h-3.5 text-cyan-400" /> Buffer Espacial GIS
            <HelpTooltip term="buffer_espacial" />
          </label>
          {bufferToolActive && (
            <span className="text-[8px] bg-cyan-500/20 text-cyan-300 font-mono px-1 py-0.2 rounded border border-cyan-500/40 animate-pulse">
              EN VIVO
            </span>
          )}
        </div>

        <div className={`p-2.5 rounded-lg border transition-all ${
          bufferToolActive
            ? "bg-cyan-950/40 border-cyan-500/60 shadow-lg shadow-cyan-950/50"
            : "bg-slate-900/50 border-slate-800"
        }`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-medium text-slate-200">Herramienta de Radio</span>
            <button
              type="button"
              onClick={() => setBufferToolActive?.(!bufferToolActive)}
              className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold transition-all cursor-pointer ${
                bufferToolActive
                  ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/40"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              {bufferToolActive ? "Activada" : "Activar"}
            </button>
          </div>

          <p className="text-[10px] text-slate-400 mb-2 leading-tight">
            {bufferToolActive
              ? "🎯 Haz clic en cualquier punto del mapa para lanzar el buffer geodésico y calcular el potencial mineral."
              : "Calcula en <1 ms indicios en radio, distrito metalogénico más cercano y favorabilidad máxima."}
          </p>

          {bufferToolActive && setBufferRadiusKm && (
            <div className="flex items-center gap-1 pt-1.5 border-t border-cyan-900/40">
              <span className="text-[10px] font-mono text-cyan-300">Radio:</span>
              {[5, 10, 20].map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setBufferRadiusKm(r)}
                  className={`flex-1 py-0.5 rounded text-[10px] font-mono font-semibold transition-all ${
                    bufferRadiusKm === r
                      ? "bg-cyan-500/30 text-cyan-200 border border-cyan-400"
                      : "bg-slate-800/60 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {r} km
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 3. Selector de Mapa Base */}
      <div className="mb-4 pt-3 border-t border-slate-800/80">
        <label className="text-[10px] uppercase font-mono tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
          <MapIcon className="w-3 h-3 text-cyan-400" /> Mapa Base
        </label>
        <div className="grid grid-cols-3 gap-1.5">
          <button
            onClick={() => setBaseMap("dark")}
            className={`py-1.5 px-2 rounded-lg border font-mono text-[10px] font-semibold transition-all ${baseMap === "dark" ? "bg-cyan-950/80 border-cyan-400 text-cyan-300 shadow-sm" : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"}`}
          >
            Oscuro
          </button>
          <button
            onClick={() => setBaseMap("street")}
            className={`py-1.5 px-2 rounded-lg border font-mono text-[10px] font-semibold transition-all ${baseMap === "street" ? "bg-cyan-950/80 border-cyan-400 text-cyan-300 shadow-sm" : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"}`}
          >
            Callejero
          </button>
          <button
            onClick={() => setBaseMap("satellite")}
            className={`py-1.5 px-2 rounded-lg border font-mono text-[10px] font-semibold transition-all ${baseMap === "satellite" ? "bg-cyan-950/80 border-cyan-400 text-cyan-300 shadow-sm" : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"}`}
          >
            Satélite
          </button>
        </div>
      </div>

      {/* 4. Leyenda Cartográfica Dinámica */}
      {activeRasterLayer !== "none" && (
        <div className="pt-3 border-t border-slate-800/80">
          <label className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-2">
            Leyenda: {
              activeRasterLayer === "score" || activeRasterLayer === "global_v2_score" ? "Favorabilidad (0 - 1)" :
              activeRasterLayer === "rock_score" ? "Oro en Roca (0 - 1)" :
              activeRasterLayer === "alluvial_score" ? "Oro Aluvial (0 - 1)" :
              activeRasterLayer === "v3_pu_score" ? "Score PU Calibrado v3.0 (0 - 1)" :
              activeRasterLayer === "v3_uncertainty" ? "Incertidumbre Epistémica σ (0.00 - 0.20+)" :
              activeRasterLayer === "percentile" ? "Percentil (0 - 100)" :
              "Bandas de Prioridad"
            }
          </label>

          {(activeRasterLayer === "score" || activeRasterLayer === "global_v2_score") && (
            <div>
              <div className="h-3 w-full rounded bg-gradient-to-r from-[#440154] via-[#21908d] to-[#fde725] border border-slate-700/60 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-1">
                <span>0.00 (Mín)</span>
                <span className="text-cyan-300 font-semibold">0.52 (p90)</span>
                <span className="text-amber-300 font-semibold">0.65 (p95)</span>
                <span className="text-emerald-300 font-bold">0.83 (p99)</span>
                <span>1.00</span>
              </div>
            </div>
          )}

          {activeRasterLayer === "v3_pu_score" && (
            <div>
              <div className="h-3 w-full rounded bg-gradient-to-r from-[#440154] via-[#21908d] to-[#fde725] border border-slate-700/60 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-1">
                <span>0.00 (Fondo)</span>
                <span className="text-cyan-300 font-semibold">0.30 (Moderado)</span>
                <span className="text-amber-300 font-semibold">0.60 (Alto)</span>
                <span className="text-emerald-300 font-bold">1.00 (Máx PU)</span>
              </div>
              <div className="text-[9px] text-purple-300/80 font-mono mt-1 text-center">
                Calibrado con factor Elkan-Noto (c = 0.72)
              </div>
            </div>
          )}

          {activeRasterLayer === "v3_uncertainty" && (
            <div>
              <div className="h-3 w-full rounded bg-gradient-to-r from-[#0d0887] via-[#cc4778] to-[#f0f921] border border-slate-700/60 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-1">
                <span className="text-emerald-300">0.00 (Certeza Alta)</span>
                <span className="text-amber-300">0.05 (Media)</span>
                <span className="text-rose-400 font-bold">&gt;0.15 (Alta σ)</span>
              </div>
              <div className="text-[9px] text-purple-300/80 font-mono mt-1 text-center">
                Desviación estándar inter-modelos en ensamble Bagging
              </div>
            </div>
          )}

          {activeRasterLayer === "rock_score" && (
            <div>
              <div className="h-3 w-full rounded bg-gradient-to-r from-[#000004] via-[#b63679] to-[#fcfdbf] border border-slate-700/60 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-1">
                <span>0.00</span>
                <span className="text-rose-300">Primario</span>
                <span>1.00</span>
              </div>
            </div>
          )}

          {activeRasterLayer === "alluvial_score" && (
            <div>
              <div className="h-3 w-full rounded bg-gradient-to-r from-[#00204d] via-[#7c7b78] to-[#ffea46] border border-slate-700/60 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-1">
                <span>0.00</span>
                <span className="text-blue-300">Placer</span>
                <span>1.00</span>
              </div>
            </div>
          )}

          {activeRasterLayer === "percentile" && (
            <div>
              <div className="h-3 w-full rounded bg-gradient-to-r from-[#0d0887] via-[#cc4778] to-[#f0f921] border border-slate-700/60 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-1">
                <span>0% (Inferior)</span>
                <span>50% (Mediana)</span>
                <span className="text-amber-300 font-bold">Top 1%</span>
              </div>
            </div>
          )}

          {activeRasterLayer === "priority" && (
            <div className="space-y-1 text-[11px]">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#E63946] border border-white/20"></span>
                <span>Top 1% (≥ 0.8333) — Muy Alta</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#F4A261] border border-white/20"></span>
                <span>Top 1-5% (≥ 0.6526) — Alta</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-[#2A9D8F] border border-white/20"></span>
                <span>Top 5-10% (≥ 0.5179) — Moderada</span>
              </div>
              <div className="flex items-center gap-2 text-slate-500">
                <span className="w-3 h-3 rounded bg-slate-700 border border-slate-600"></span>
                <span>Resto (&lt; 0.5179) — Fondo</span>
              </div>
            </div>
          )}
        </div>
      )}
    </aside>
  );
};
