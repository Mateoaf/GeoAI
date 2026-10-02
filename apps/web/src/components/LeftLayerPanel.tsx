"use client";

import React from "react";
import { Layers, MapPin, Target, Eye, Sliders, Map as MapIcon, ChevronLeft, ChevronRight, GripHorizontal, RotateCcw } from "lucide-react";
import { useDraggable } from "../hooks/useDraggable";
import { RasterLayerType } from "../types";

interface LeftLayerPanelProps {
  activeRasterLayer: RasterLayerType;
  setActiveRasterLayer: (layer: RasterLayerType) => void;
  rasterOpacity: number;
  setRasterOpacity: (val: number) => void;
  showZones: boolean;
  setShowZones: (val: boolean) => void;
  showDeposits: boolean;
  setShowDeposits: (val: boolean) => void;
  baseMap: "dark" | "street" | "satellite";
  setBaseMap: (val: "dark" | "street" | "satellite") => void;
  isCollapsed: boolean;
  setIsCollapsed: (val: boolean) => void;
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
  baseMap,
  setBaseMap,
  isCollapsed,
  setIsCollapsed
}) => {
  const { offset, isDragging, elementRef, dragProps, resetPosition } = useDraggable();

  if (isCollapsed) {
    return (
      <button
        onClick={() => setIsCollapsed(false)}
        className="absolute top-16 left-3 z-20 p-2.5 rounded-lg bg-slate-900/90 text-cyan-400 hover:text-cyan-200 border border-cyan-800/60 shadow-xl backdrop-blur-md transition-all cursor-pointer"
        title="Mostrar Capas"
      >
        <Layers className="w-5 h-5" />
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
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-[10px] uppercase font-mono tracking-wider text-cyan-400 font-bold">
            Modelo Oficial v1.0 (Auditado)
          </label>
        </div>
        <div className="space-y-1.5 mb-3">
          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "score" ? "bg-cyan-950/50 border-cyan-500/50 text-cyan-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm"></span>
              Score Oficial v1.0 (LR)
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "score"}
              onChange={() => setActiveRasterLayer("score")}
              className="accent-cyan-400 cursor-pointer"
            />
          </label>

          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "percentile" ? "bg-cyan-950/50 border-cyan-500/50 text-cyan-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-400 shadow-sm"></span>
              Percentil Territorial
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "percentile"}
              onChange={() => setActiveRasterLayer("percentile")}
              className="accent-cyan-400 cursor-pointer"
            />
          </label>

          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "priority" ? "bg-cyan-950/50 border-cyan-500/50 text-cyan-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-sm"></span>
              Bandas Top 1 / 5 / 10%
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "priority"}
              onChange={() => setActiveRasterLayer("priority")}
              className="accent-cyan-400 cursor-pointer"
            />
          </label>
        </div>

        {/* Modelos Especializados v2 (787 Indicios) */}
        <div className="flex items-center justify-between mb-1.5 pt-2 border-t border-slate-800/80">
          <label className="text-[10px] uppercase font-mono tracking-wider text-amber-400 font-bold">
            Modelos Avanzados v2 (787 Indicios)
          </label>
          <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-mono">ROC 0.96+</span>
        </div>
        <div className="space-y-1.5">
          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "global_v2_score" ? "bg-amber-950/50 border-amber-500/50 text-amber-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-sm"></span>
              Oro Global v2 (LightGBM)
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "global_v2_score"}
              onChange={() => setActiveRasterLayer("global_v2_score")}
              className="accent-amber-400 cursor-pointer"
            />
          </label>

          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "rock_score" ? "bg-amber-950/50 border-amber-500/50 text-amber-200 shadow-sm" : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"}`}>
            <span className="flex items-center gap-2 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm"></span>
              Oro en Roca (Primario)
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
              Oro Aluvial (Placeres)
            </span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "alluvial_score"}
              onChange={() => setActiveRasterLayer("alluvial_score")}
              className="accent-amber-400 cursor-pointer"
            />
          </label>

          <label className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${activeRasterLayer === "none" ? "bg-slate-800 border-slate-600 text-slate-300" : "bg-slate-900/50 border-slate-800 text-slate-400"}`}>
            <span className="font-medium text-slate-400">Ocultar Ráster</span>
            <input
              type="radio"
              name="raster_layer"
              checked={activeRasterLayer === "none"}
              onChange={() => setActiveRasterLayer("none")}
              className="accent-cyan-400 cursor-pointer"
            />
          </label>
        </div>

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

      {/* 2. Capas Vectoriales de Contexto */}
      <div className="mb-4 pt-3 border-t border-slate-800/80">
        <label className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-2">
          Elementos Vectoriales
        </label>
        <div className="space-y-1.5">
          <label className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800 hover:border-slate-700 cursor-pointer">
            <span className="flex items-center gap-2">
              <Target className="w-3.5 h-3.5 text-amber-400" />
              <span>Zonas de Prospectividad (1.529)</span>
            </span>
            <input
              type="checkbox"
              checked={showZones}
              onChange={(e) => setShowZones(e.target.checked)}
              className="accent-amber-400 w-3.5 h-3.5 cursor-pointer rounded"
            />
          </label>

          <label className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800 hover:border-slate-700 cursor-pointer">
            <span className="flex items-center gap-2">
              <MapPin className="w-3.5 h-3.5 text-yellow-400" />
              <span>Depósitos Auditados (46)</span>
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
            Leyenda: {activeRasterLayer === "score" ? "Favorabilidad (0 - 1)" : activeRasterLayer === "percentile" ? "Percentil (0 - 100)" : "Bandas de Prioridad"}
          </label>

          {activeRasterLayer === "score" && (
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
