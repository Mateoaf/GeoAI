"use client";

import React from "react";
import { CellInfo } from "../types";
import { Compass, X, AlertTriangle, Sparkles, MapPin, Database } from "lucide-react";

interface CellInspectorProps {
  cell: CellInfo | null;
  eligible: boolean;
  queryCoordinates?: { lat: number; lon: number } | null;
  onClose: () => void;
  onExplainClick: () => void;
}

export const CellInspector: React.FC<CellInspectorProps> = ({
  cell,
  eligible,
  queryCoordinates,
  onClose,
  onExplainClick
}) => {
  if (!cell && !queryCoordinates) return null;

  return (
    <div className="absolute bottom-5 left-3 sm:left-auto sm:right-auto sm:left-1/2 sm:-translate-x-1/2 z-20 w-[calc(100%-1.5rem)] sm:w-[32rem] bg-slate-950/95 backdrop-blur-md border border-cyan-500/40 rounded-xl shadow-2xl p-4 text-slate-100 select-none animate-in fade-in slide-in-from-bottom-3 duration-200">
      {/* Barra Superior del Inspector */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-cyan-400" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-cyan-300">
            Inspección Territorial 1 km²
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {!eligible ? (
        <div className="py-2 text-xs text-slate-400 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-slate-200">Celda No Elegible / NoData</p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Las coordenadas seleccionadas caen en aguas marinas o en territorio peninsular con cobertura insuficiente (&lt; 80%) de los 56 predictores aprobados.
            </p>
            {queryCoordinates && (
              <p className="text-[10px] font-mono text-slate-500 mt-2">
                Consulta: {queryCoordinates.lat.toFixed(5)}°N, {queryCoordinates.lon.toFixed(5)}°E
              </p>
            )}
          </div>
        </div>
      ) : cell ? (
        <div>
          {/* Métricas Principales de la Celda */}
          <div className="grid grid-cols-3 gap-2 text-center mb-3">
            <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-800">
              <span className="text-[9px] uppercase font-mono tracking-wider text-slate-400 block mb-0.5">
                Favorabilidad
              </span>
              <span className="text-lg font-black font-mono text-cyan-400">
                {cell.score.toFixed(3)}
              </span>
            </div>

            <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-800">
              <span className="text-[9px] uppercase font-mono tracking-wider text-slate-400 block mb-0.5">
                Percentil
              </span>
              <span className="text-lg font-black font-mono text-purple-400">
                {cell.percentile_favorabilidad.toFixed(1)}%
              </span>
            </div>

            <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-800">
              <span className="text-[9px] uppercase font-mono tracking-wider text-slate-400 block mb-0.5">
                Prioridad
              </span>
              <span className={`text-xs font-extrabold uppercase font-mono px-2 py-0.5 rounded inline-block mt-1 ${
                cell.prioridad_banda === "top_01"
                  ? "bg-red-950/80 text-red-400 border border-red-700/60"
                  : cell.prioridad_banda === "top_05"
                  ? "bg-amber-950/80 text-amber-400 border border-amber-700/60"
                  : cell.prioridad_banda === "top_10"
                  ? "bg-teal-950/80 text-teal-400 border border-teal-700/60"
                  : "bg-slate-800 text-slate-400"
              }`}>
                {cell.prioridad_banda.replace("_", " ")}
              </span>
            </div>
          </div>

          {/* Atributos Territoriales y Contextuales */}
          <div className="text-[11px] font-mono grid grid-cols-2 gap-x-4 gap-y-1 text-slate-300 mb-3 bg-slate-900/50 p-2 rounded-lg border border-slate-800/80">
            <div>
              <span className="text-slate-500">cell_id:</span>{" "}
              <span className="text-cyan-300 font-semibold">{cell.cell_id.split("_v1_")[1]}</span>
            </div>
            <div>
              <span className="text-slate-500">Malla:</span> R{cell.row} C{cell.col}
            </div>
            <div>
              <span className="text-slate-500">Coord:</span> {cell.lat_wgs84.toFixed(4)}°N, {cell.lon_wgs84.toFixed(4)}°E
            </div>
            <div>
              <span className="text-slate-500">Área:</span> {(cell.land_area_m2 / 1e6).toFixed(2)} km²
            </div>
            {cell.district_id && (
              <div className="col-span-2 text-amber-300 flex items-center gap-1 mt-1">
                <MapPin className="w-3 h-3 text-amber-400 shrink-0" />
                <span>Distrito: {cell.district_id}</span>
              </div>
            )}
            {cell.deposit_id && (
              <div className="col-span-2 text-yellow-300 flex items-center gap-1 font-bold">
                <Database className="w-3 h-3 text-yellow-400 shrink-0" />
                <span>Depósito Confirmado: {cell.deposit_id}</span>
              </div>
            )}
          </div>

          {/* Guardarraíl Científico Obligatorio */}
          <p className="text-[10px] text-slate-400 leading-tight italic border-l-2 border-cyan-500/60 pl-2 py-0.5 mb-3">
            Score relativo de prospectividad; no representa probabilidad calibrada de existencia de un depósito ni estimación económica de recursos.
          </p>

          {/* Botón de Explicabilidad Local */}
          <button
            onClick={onExplainClick}
            className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-cyan-600 via-teal-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/20 transition-all cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-slate-950" />
            <span>Explicar Factores Geológicos de esta Celda (β · z)</span>
          </button>
        </div>
      ) : null}
    </div>
  );
};
