"use client";

import React from "react";
import { ProjectSummary } from "../types";
import { ShieldCheck, Info, Sparkles } from "lucide-react";

interface HeaderProps {
  summary: ProjectSummary | null;
  onOpenMethodology: () => void;
}

export const Header: React.FC<HeaderProps> = ({ summary, onOpenMethodology }) => {
  return (
    <header className="h-14 bg-slate-950/90 backdrop-blur-md border-b border-cyan-900/40 px-4 flex items-center justify-between text-slate-100 z-30 relative select-none">
      {/* Logo y Branding */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 via-teal-600 to-amber-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/40">
            <Sparkles className="w-4 h-4 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold tracking-wider text-base bg-gradient-to-r from-cyan-400 via-teal-300 to-amber-300 bg-clip-text text-transparent">
                GEOAI-AU
              </span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/50">
                Explorer
              </span>
            </div>
            <p className="text-[10px] text-slate-400 tracking-tight hidden sm:block">
              Mineral Prospectivity Intelligence — España Peninsular
            </p>
          </div>
        </div>

        {/* Badge de versión científica sellada */}
        <div className="hidden lg:flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-950/60 border border-emerald-600/40 text-[11px] text-emerald-400 font-mono shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Scientific Release v1.0</span>
        </div>
      </div>

      {/* Chips de Metadatos Canónicos */}
      <div className="hidden xl:flex items-center gap-2 text-xs font-mono">
        <div className="px-2.5 py-1 rounded bg-slate-900/80 border border-slate-800 text-slate-300 flex items-center gap-1.5">
          <span className="text-slate-500 uppercase">Model:</span>
          <span className="text-cyan-400 font-semibold">{summary?.model_name || "logistic_01"}</span>
        </div>
        <div className="px-2.5 py-1 rounded bg-slate-900/80 border border-slate-800 text-slate-300 flex items-center gap-1.5">
          <span className="text-slate-500 uppercase">Res:</span>
          <span className="text-cyan-400 font-semibold">{summary ? "1 km" : "1 km"}</span>
        </div>
        <div className="px-2.5 py-1 rounded bg-slate-900/80 border border-slate-800 text-slate-300 flex items-center gap-1.5">
          <span className="text-slate-500 uppercase">Region:</span>
          <span className="text-slate-200">España peninsular</span>
        </div>
        <div className="px-2.5 py-1 rounded bg-slate-900/80 border border-slate-800 text-slate-300 flex items-center gap-1.5">
          <span className="text-slate-500 uppercase">Cells:</span>
          <span className="text-amber-400 font-semibold">
            {summary ? summary.eligible_cells_count.toLocaleString("es-ES") : "478.443"}
          </span>
        </div>
        <div className="px-2.5 py-1 rounded bg-slate-900/80 border border-slate-800 text-slate-300 flex items-center gap-1.5">
          <span className="text-slate-500 uppercase">Features:</span>
          <span className="text-emerald-400 font-semibold">{summary?.features_count || 56}</span>
        </div>
      </div>

      {/* Botón de Metodología y Limitaciones */}
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenMethodology}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 hover:text-cyan-200 border border-cyan-800/60 transition-all text-xs font-medium shadow-sm hover:shadow-cyan-500/10 cursor-pointer"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden sm:inline">Metodología y Limitaciones</span>
          <span className="sm:hidden">Info</span>
        </button>
      </div>
    </header>
  );
};
