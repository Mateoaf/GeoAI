"use client";

import React, { useState } from "react";
import { RasterLayerType } from "../types";
import { Info, ChevronDown, ChevronUp, Layers } from "lucide-react";

interface MapLegendProps {
  activeRasterLayer: RasterLayerType;
}

export const MapLegend: React.FC<MapLegendProps> = ({ activeRasterLayer }) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  if (activeRasterLayer === "none") return null;

  return (
    <div className="absolute bottom-6 right-14 z-20 select-none">
      {isCollapsed ? (
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-cyan-400 border border-slate-700/80 shadow-xl backdrop-blur-md flex items-center gap-1.5 text-xs font-mono transition-all cursor-pointer"
          title="Mostrar Leyenda Cartográfica"
        >
          <Layers className="w-4 h-4" />
          <span className="hidden sm:inline text-[11px]">Leyenda</span>
        </button>
      ) : (
        <div className="w-64 bg-slate-950/90 backdrop-blur-xl border border-slate-800/80 rounded-xl shadow-2xl p-3 text-slate-200 text-xs animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="flex items-center justify-between pb-1.5 mb-2 border-b border-slate-800">
            <span className="text-[10px] font-bold uppercase font-mono tracking-wider text-slate-300 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              Leyenda de Capa
            </span>
            <button
              onClick={() => setIsCollapsed(true)}
              className="p-0.5 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors cursor-pointer"
              title="Colapsar leyenda"
            >
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* 1. Leyenda de Bandas Prioritarias */}
          {activeRasterLayer === "priority" && (
            <div className="space-y-1.5 text-[11px] font-mono">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-red-500 shadow-sm shadow-red-500/50"></span>
                  <span className="text-slate-200 font-bold">Top 1%</span>
                </span>
                <span className="text-red-400 font-semibold">Muy Alta</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-amber-400 shadow-sm shadow-amber-400/50"></span>
                  <span className="text-slate-300">Top 5%</span>
                </span>
                <span className="text-amber-300">Alta</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-emerald-400 shadow-sm shadow-emerald-400/50"></span>
                  <span className="text-slate-300">Top 10%</span>
                </span>
                <span className="text-emerald-300">Moderada-Alta</span>
              </div>
              <p className="text-[9px] text-slate-500 pt-1 border-t border-slate-800/80">
                Fondo territorial transparente (&gt;90% restante)
              </p>
            </div>
          )}

          {/* 2. Leyenda Oro en Roca (Magma) */}
          {activeRasterLayer === "rock_score" && (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span>Vetas Primarias</span>
                <span className="text-amber-400 font-bold">ROC 0.976</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-purple-950 via-rose-600 via-amber-500 to-yellow-200 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span>0.10 (Anomalía)</span>
                <span>0.50</span>
                <span className="text-amber-300 font-bold">0.99 (Veta)</span>
              </div>
            </div>
          )}

          {/* 3. Leyenda Oro Aluvial (Cividis) */}
          {activeRasterLayer === "alluvial_score" && (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span>Placeres y Terrazas</span>
                <span className="text-cyan-400 font-bold">ROC 0.951</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-blue-950 via-teal-700 via-yellow-600 to-yellow-300 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span>0.08 (Fondo)</span>
                <span>0.40</span>
                <span className="text-cyan-300 font-bold">0.95 (Placer)</span>
              </div>
            </div>
          )}

          {/* 4. Leyenda Global v2 o v1.0 (Viridis) */}
          {(activeRasterLayer === "score" || activeRasterLayer === "global_v2_score") && (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span>Score Favorabilidad</span>
                <span className="text-emerald-400 font-bold">{activeRasterLayer === "global_v2_score" ? "v2.0" : "v1.0 LR"}</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-indigo-950 via-teal-600 via-emerald-500 to-yellow-300 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span>0.08 (Umbral)</span>
                <span>0.50</span>
                <span className="text-emerald-300 font-bold">1.00 (Máx)</span>
              </div>
            </div>
          )}

          {/* 4b. Leyenda Motor Oficial v3.0 (Viridis) */}
          {activeRasterLayer === "v3_pu_score" && (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span className="text-purple-300 font-bold">Motor Oficial v3.0 (PU Learning)</span>
                <span className="text-emerald-400 font-bold">c = 0.72</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-indigo-950 via-teal-600 via-emerald-500 to-yellow-300 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span>0.06 (Umbral)</span>
                <span>0.50</span>
                <span className="text-yellow-300 font-bold">1.00 (Máx)</span>
              </div>
              <p className="text-[9px] text-slate-400 pt-1 border-t border-slate-800/80">
                Amarillo = Máxima favorabilidad calibrada v3.0
              </p>
            </div>
          )}

          {/* 4c. Leyenda Incertidumbre Epistémica v3.0 (Plasma) */}
          {activeRasterLayer === "v3_uncertainty" && (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span className="text-purple-300 font-bold">Incertidumbre Epistémica (σ)</span>
                <span className="text-amber-400 font-bold">Desv. Estándar</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-purple-950 via-pink-600 to-yellow-300 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span className="text-purple-400 font-semibold">0.01 (Certeza)</span>
                <span>0.08</span>
                <span className="text-yellow-300 font-bold">0.20+ (Alta Duda)</span>
              </div>
              <p className="text-[9px] text-amber-300/90 pt-1 border-t border-slate-800/80 leading-tight">
                ⚠️ Amarillo = Máxima dispersión/duda del modelo (no es potencial de oro).
              </p>
            </div>
          )}

          {/* 5. Leyenda Percentil (Plasma) */}
          {activeRasterLayer === "percentile" && (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span>Percentil Territorial</span>
                <span className="text-purple-400 font-bold">50% - 100%</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-purple-950 via-pink-600 to-yellow-300 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span>P50</span>
                <span>P80</span>
                <span className="text-purple-300 font-bold">P99.9</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
