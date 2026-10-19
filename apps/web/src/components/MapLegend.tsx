"use client";

import React, { useState } from "react";
import { RasterLayerType } from "../types";
import { Info, ChevronDown, ChevronUp, Layers } from "lucide-react";
import { HelpTooltip } from "./HelpTooltip";

interface MapLegendProps {
  activeRasterLayer: RasterLayerType;
}

export const MapLegend: React.FC<MapLegendProps> = ({ activeRasterLayer }) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  if (activeRasterLayer === "none") return null;

  const getLegendTerm = (): string => {
    switch (activeRasterLayer) {
      case "v3_uncertainty":
        return "incertidumbre_epistemica";
      case "rock_score":
        return "oro_roca";
      case "alluvial_score":
        return "oro_aluvial";
      case "global_v2_score":
        return "ensamble_multitipologia";
      case "v3_pu_score":
      case "score":
      default:
        return "pu_learning";
    }
  };

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
              <span>Leyenda de Capa</span>
              <HelpTooltip term={getLegendTerm()} iconSize="xs" />
            </span>
            <button
              onClick={() => setIsCollapsed(true)}
              className="p-0.5 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors cursor-pointer"
              title="Colapsar leyenda"
            >
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Leyenda Incertidumbre Epistémica (Plasma) */}
          {activeRasterLayer === "v3_uncertainty" ? (
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
          ) : activeRasterLayer === "rock_score" ? (
            /* Leyenda Oro en Roca (Magma) */
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span className="text-rose-400 font-bold">Oro en Roca</span>
                <span className="text-amber-400 font-bold">Vetas & Skarns</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-[#000004] via-[#b63679] to-[#fcfdbf] shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span>0.00 (Fondo)</span>
                <span className="text-rose-300">Primario</span>
                <span className="text-amber-300 font-bold">1.00 (Máxima)</span>
              </div>
              <p className="text-[9px] text-slate-400 pt-1 border-t border-slate-800/80">
                Oro primario hidrotermal en roca madre
              </p>
            </div>
          ) : activeRasterLayer === "alluvial_score" ? (
            /* Leyenda Oro Aluvial (Cividis) */
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span className="text-blue-400 font-bold">Oro Aluvial</span>
                <span className="text-amber-400 font-bold">Placeres</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-[#00204d] via-[#7c7b78] to-[#ffea46] shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span>0.00 (Fondo)</span>
                <span className="text-blue-300">Sedimentos</span>
                <span className="text-amber-300 font-bold">1.00 (Máxima)</span>
              </div>
              <p className="text-[9px] text-slate-400 pt-1 border-t border-slate-800/80">
                Placeres aluviales en gravas y terrazas fluviales
              </p>
            </div>
          ) : activeRasterLayer === "global_v2_score" ? (
            /* Leyenda Ensamble Multitipología (Viridis) */
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span className="text-cyan-300 font-bold">Ensamble Multitipología</span>
                <span className="text-amber-400 font-bold">Roca + Placer</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-indigo-950 via-teal-600 via-emerald-500 to-yellow-300 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span>0.00 (Fondo)</span>
                <span>0.50</span>
                <span className="text-yellow-300 font-bold">1.00 (Máxima)</span>
              </div>
              <p className="text-[9px] text-slate-400 pt-1 border-t border-slate-800/80">
                Integración multivariable de yacimientos primarios y secundarios
              </p>
            </div>
          ) : (
            /* Leyenda Favorabilidad Aurífera (Viridis) */
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span className="text-purple-300 font-bold">Favorabilidad Aurífera</span>
                <span className="text-emerald-400 font-bold">Calibrada</span>
              </div>
              <div className="h-3 w-full rounded-md bg-gradient-to-r from-indigo-950 via-teal-600 via-emerald-500 to-yellow-300 shadow-inner"></div>
              <div className="flex justify-between text-[9px] font-mono text-slate-400">
                <span>0.16 (Fondo)</span>
                <span>0.60</span>
                <span className="text-yellow-300 font-bold">1.00 (Máxima)</span>
              </div>
              <p className="text-[9px] text-slate-400 pt-1 border-t border-slate-800/80 leading-tight">
                Amarillo = Máxima favorabilidad. Valor = tasa de acierto observada en validación espacial (buffer 15 km); no es la probabilidad de hallar oro. Para comparar territorios use el percentil.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
