"use client";

import React, { useState } from "react";
import { CellInfo } from "../types";
import {
  Compass,
  X,
  AlertTriangle,
  Sparkles,
  MapPin,
  Database,
  ArrowUpRight,
  GripHorizontal,
  ChevronDown,
  ChevronUp,
  RotateCcw
} from "lucide-react";
import { useDraggable } from "../hooks/useDraggable";

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
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const { offset, isDragging, elementRef, dragProps, resetPosition } = useDraggable();

  if (!cell && !queryCoordinates) return null;

  return (
    <div
      ref={elementRef}
      style={{
        transform: `translate3d(calc(-50% + ${offset.x}px), ${offset.y}px, 0)`
      }}
      className={`absolute bottom-20 left-1/2 z-40 w-[94vw] max-w-xl bg-slate-900/95 backdrop-blur-2xl border rounded-2xl shadow-2xl transition-shadow select-none ${
        isDragging
          ? "border-cyan-400/80 shadow-cyan-500/20 shadow-2xl ring-2 ring-cyan-400/30"
          : "border-slate-700/80 shadow-black/90"
      }`}
    >
      {/* 1. Barra Superior con Tirador de Arrastre (Grip Handle) */}
      <div
        {...dragProps}
        onDoubleClick={resetPosition}
        className="flex items-center justify-between border-b border-slate-800/80 px-4 py-2 bg-slate-950/60 rounded-t-2xl cursor-grab active:cursor-grabbing hover:bg-slate-800/40 transition-colors"
        title="Arrastra para mover libremente por la pantalla · Doble clic para centrar"
      >
        <div className="flex items-center gap-2">
          <GripHorizontal className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
          <div className="flex items-center gap-1.5">
            <div className="w-5 h-5 rounded-md bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
              <Compass className="w-3 h-3 text-amber-400" />
            </div>
            <span className="text-[11px] font-bold text-slate-200">
              Inspección Celda 1 km²
            </span>
          </div>
          {cell?.deposit_id && (
            <span className="text-[9px] bg-yellow-500/20 text-yellow-300 border border-yellow-500/40 px-1.5 py-0.2 rounded-full font-mono">
              Yacimiento
            </span>
          )}
        </div>

        {/* Botones de Control de la Ventana */}
        <div className="flex items-center gap-1">
          {(offset.x !== 0 || offset.y !== 0) && (
            <button
              onClick={resetPosition}
              className="p-1 rounded text-slate-400 hover:text-cyan-300 hover:bg-slate-800/80 transition-colors cursor-pointer"
              title="Restablecer posición al centro inferior"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800/80 transition-colors cursor-pointer"
            title={isMinimized ? "Maximizar inspector" : "Minimizar inspector"}
          >
            {isMinimized ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800/80 transition-colors cursor-pointer"
            title="Cerrar inspector"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. Modo Minimizado (Pill compacta informativa) */}
      {isMinimized && cell && (
        <div className="p-3 flex items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-mono text-cyan-300 font-bold">R{cell.row} C{cell.col}</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-300">Score: <strong className="text-cyan-400 font-mono">{cell.score.toFixed(3)}</strong></span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400 font-mono">Percentil: {cell.percentile_favorabilidad.toFixed(1)}%</span>
          </div>

          <button
            onClick={onExplainClick}
            className="py-1 px-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-[10px] flex items-center gap-1 cursor-pointer transition-colors"
          >
            <Sparkles className="w-3 h-3 text-slate-950" />
            <span>Explicar Factores</span>
          </button>
        </div>
      )}

      {/* 3. Modo Completo Expandido */}
      {!isMinimized && (
        <div className="p-4 text-slate-100 space-y-3">
          {queryCoordinates && (
            <p className="text-[10px] text-slate-400 font-mono">
              Coordenadas: {queryCoordinates.lat.toFixed(4)}°N, {queryCoordinates.lon.toFixed(4)}°E (EPSG:25830 UTM30N)
            </p>
          )}

          {!eligible ? (
            <div className="py-2.5 px-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-slate-200">Celda Fuera de Dominio Peninsular o NoData</p>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                  Las coordenadas seleccionadas caen en aguas marinas o en sectores con cobertura insuficiente (&lt;80%) de los 56 predictores aprobados.
                </p>
              </div>
            </div>
          ) : cell ? (
            <div className="space-y-3">
              {/* Métricas Clave */}
              <div className="grid grid-cols-3 gap-2.5">
                <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-400 font-medium block mb-0.5">Favorabilidad</span>
                  <span className="text-lg font-black font-mono text-cyan-400">
                    {cell.score.toFixed(3)}
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-400 font-medium block mb-0.5">Percentil</span>
                  <span className="text-lg font-black font-mono text-purple-400">
                    {cell.percentile_favorabilidad.toFixed(1)}%
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center flex flex-col justify-center items-center">
                  <span className="text-[10px] text-slate-400 font-medium block mb-0.5">Banda</span>
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md ${
                    cell.prioridad_banda === "top_01"
                      ? "bg-red-500/20 text-red-400 border border-red-500/40"
                      : cell.prioridad_banda === "top_05"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                      : cell.prioridad_banda === "top_10"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                      : "bg-slate-800 text-slate-400"
                  }`}>
                    {cell.prioridad_banda === "top_01" ? "Top 1%" : cell.prioridad_banda === "top_05" ? "Top 5%" : cell.prioridad_banda === "top_10" ? "Top 10%" : "Fondo"}
                  </span>
                </div>
              </div>

              {/* Atributos geológicos y de ubicación */}
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] font-mono grid grid-cols-2 gap-2 text-slate-300">
                <div>
                  <span className="text-slate-500">Malla:</span> R{cell.row} C{cell.col}
                </div>
                <div>
                  <span className="text-slate-500">Superficie:</span> {(cell.land_area_m2 / 1e6).toFixed(2)} km²
                </div>
                {cell.district_id && (
                  <div className="col-span-2 text-cyan-300 flex items-center gap-1.5 truncate">
                    <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                    <span>Distrito: <strong>{cell.district_id}</strong></span>
                  </div>
                )}
                {cell.deposit_id && (
                  <div className="col-span-2 text-amber-300 flex items-center gap-1.5 truncate">
                    <Database className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <span>Yacimiento: <strong>{cell.deposit_id}</strong></span>
                  </div>
                )}
              </div>

              {/* Botón de Explicabilidad */}
              <button
                onClick={onExplainClick}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 via-teal-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 transition-all cursor-pointer"
              >
                <Sparkles className="w-4 h-4 text-slate-950" />
                <span>Explicar Factores Geológicos de esta Celda</span>
                <ArrowUpRight className="w-4 h-4 text-slate-950" />
              </button>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
