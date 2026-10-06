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
  RotateCcw,
  Crosshair,
  Target
} from "lucide-react";
import { useDraggable } from "../hooks/useDraggable";
import { formatWgs84, formatUtm30 } from "../lib/geo";

interface CellInspectorProps {
  cell: CellInfo | null;
  eligible: boolean;
  queryCoordinates?: { lat: number; lon: number } | null;
  onClose: () => void;
  onExplainClick: () => void;
  onRunBuffer?: (lat: number, lon: number) => void;
}

export const CellInspector: React.FC<CellInspectorProps> = ({
  cell,
  eligible,
  queryCoordinates,
  onClose,
  onExplainClick,
  onRunBuffer
}) => {
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const { offset, isDragging, elementRef, dragProps, resetPosition } = useDraggable();

  if (!cell && !queryCoordinates) return null;

  const handleCopyCoords = () => {
    if (queryCoordinates && typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(`${queryCoordinates.lat.toFixed(6)}, ${queryCoordinates.lon.toFixed(6)}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      ref={elementRef}
      style={{
        transform: `translate3d(calc(-50% + ${offset.x}px), ${offset.y}px, 0)`
      }}
      className={`absolute bottom-20 left-1/2 z-40 w-[94vw] max-w-xl bg-slate-950/95 backdrop-blur-2xl border rounded-2xl shadow-2xl transition-shadow select-none ${
        isDragging
          ? "border-cyan-400/80 shadow-cyan-500/20 shadow-2xl ring-2 ring-cyan-400/30"
          : "border-slate-800 shadow-black/90 hover:border-slate-700"
      }`}
    >
      {/* 1. Barra Superior con Tirador de Arrastre (Grip Handle) */}
      <div
        {...dragProps}
        onDoubleClick={resetPosition}
        className="flex items-center justify-between border-b border-slate-800/80 px-4 py-2.5 bg-slate-900/60 rounded-t-2xl cursor-grab active:cursor-grabbing hover:bg-slate-800/40 transition-colors"
        title="Arrastra para mover libremente por la pantalla · Doble clic para centrar"
      >
        <div className="flex items-center gap-2">
          <GripHorizontal className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
          <div className="flex items-center gap-1.5">
            <div className="w-5 h-5 rounded-md bg-gradient-to-br from-amber-500/30 to-amber-600/10 border border-amber-500/40 flex items-center justify-center">
              <Compass className="w-3 h-3 text-amber-400" />
            </div>
            <span className="text-[11px] font-bold tracking-wide uppercase text-slate-200">
              Sonda Territorial · Celda 1 km²
            </span>
          </div>
          {cell?.deposit_id && (
            <span className="text-[9px] bg-yellow-500/20 text-yellow-300 border border-yellow-500/40 px-2 py-0.5 rounded-full font-mono font-bold animate-pulse">
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
          <div className="flex items-center gap-2 font-mono">
            <span className="text-cyan-300 font-bold">R{cell.row} C{cell.col}</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-300">Score: <strong className="text-cyan-400 font-bold">{cell.score.toFixed(3)}</strong></span>
            <span className="text-slate-600">|</span>
            <span className="text-purple-300">p{cell.percentile_favorabilidad.toFixed(1)}</span>
          </div>

          <div className="flex items-center gap-1.5">
            {onRunBuffer && (
              <button
                onClick={() => onRunBuffer(cell.lat_wgs84, cell.lon_wgs84)}
                className="py-1 px-2 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-700/60 text-cyan-300 text-[10px] font-mono cursor-pointer transition-all"
                title="Lanzar buffer de prospección en esta celda"
              >
                Buffer
              </button>
            )}
            <button
              onClick={onExplainClick}
              className="py-1 px-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-teal-400 hover:from-cyan-400 hover:to-teal-300 text-slate-950 font-bold text-[10px] flex items-center gap-1 cursor-pointer transition-all shadow-sm shadow-cyan-500/30"
            >
              <Sparkles className="w-3 h-3 text-slate-950" />
              <span>Explicar</span>
            </button>
          </div>
        </div>
      )}

      {/* 3. Modo Completo Expandido */}
      {!isMinimized && (
        <div className="p-4 text-slate-100 space-y-3.5">
          {queryCoordinates && (
            <div
              onClick={handleCopyCoords}
              className="flex items-center justify-between text-[10px] font-mono bg-slate-900/60 hover:bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800/80 hover:border-cyan-500/50 cursor-pointer transition-colors group"
              title="Haz clic para copiar coordenadas WGS84 al portapapeles"
            >
              <span className="text-slate-300">
                WGS84: <strong className="text-cyan-300">{formatWgs84(queryCoordinates.lat, queryCoordinates.lon)}</strong>
                {cell && <span className="text-slate-500 hidden sm:inline ml-2">({formatUtm30(cell.x_epsg25830, cell.y_epsg25830)})</span>}
              </span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold transition-all ${
                copied
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  : "text-slate-500 group-hover:text-cyan-300"
              }`}>
                {copied ? "¡Copiado! ✓" : "Copiar WGS84"}
              </span>
            </div>
          )}

          {!eligible ? (
            <div className="py-3 px-3.5 rounded-xl bg-slate-900/60 border border-amber-900/40 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-slate-200">Celda Fuera de Dominio Peninsular o Enmascarada</p>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                  Las coordenadas seleccionadas corresponden a aguas marítimas, cuencas sedimentarias profundas sin basamento accesible o zonas con cobertura heterogénea de predictores.
                </p>
              </div>
            </div>
          ) : cell ? (
            <div className="space-y-3">
              {/* Métricas Clave */}
              <div className="grid grid-cols-3 gap-2.5">
                <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800/80 text-center relative overflow-hidden">
                  <span className="text-[10px] text-slate-400 font-medium block mb-0.5 uppercase tracking-wider">Favorabilidad</span>
                  <span className="text-xl font-black font-mono text-cyan-300">
                    {cell.score.toFixed(3)}
                  </span>
                  <div className="w-full bg-slate-800 h-1 rounded-full mt-1.5 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-500 via-teal-400 to-yellow-300 transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(5, cell.score * 100))}%` }}
                    />
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800/80 text-center relative overflow-hidden">
                  <span className="text-[10px] text-slate-400 font-medium block mb-0.5 uppercase tracking-wider">Percentil</span>
                  <span className="text-xl font-black font-mono text-purple-300">
                    {cell.percentile_favorabilidad.toFixed(1)}%
                  </span>
                  <div className="w-full bg-slate-800 h-1 rounded-full mt-1.5 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 via-purple-400 to-pink-400 transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(5, cell.percentile_favorabilidad))}%` }}
                    />
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800/80 text-center flex flex-col justify-center items-center">
                  <span className="text-[10px] text-slate-400 font-medium block mb-1 uppercase tracking-wider">Banda Territorial</span>
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md font-mono ${
                    cell.prioridad_banda === "top_01"
                      ? "bg-red-500/20 text-red-300 border border-red-500/50 shadow-sm shadow-red-500/20"
                      : cell.prioridad_banda === "top_05"
                      ? "bg-amber-500/20 text-amber-200 border border-amber-500/50 shadow-sm shadow-amber-500/20"
                      : cell.prioridad_banda === "top_10"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/50"
                      : "bg-slate-800/80 text-slate-400 border border-slate-700"
                  }`}>
                    {cell.prioridad_banda === "top_01" ? "Top 1% (Crítico)" : cell.prioridad_banda === "top_05" ? "Top 5% (Alto)" : cell.prioridad_banda === "top_10" ? "Top 10% (Medio)" : "Fondo (>10%)"}
                  </span>
                </div>
              </div>

              {/* Métricas Avanzadas v3.0 (PU Learning, Incertidumbre y Fiabilidad) */}
              {cell.favorabilidad_pu_media !== undefined && cell.favorabilidad_pu_media !== null && (
                <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-800/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-purple-300 font-bold flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-purple-400" />
                      Evaluación v3.0 (PU Learning & Incertidumbre)
                    </span>
                    <span className="text-[9px] font-mono bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded border border-purple-500/30">
                      c = 0.72
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-center font-mono">
                    <div className="p-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
                      <span className="text-[9px] text-slate-400 block uppercase">Score PU Calibrado</span>
                      <span className="text-base font-black text-purple-300">
                        {cell.favorabilidad_pu_media.toFixed(3)}
                      </span>
                    </div>

                    <div className="p-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
                      <span className="text-[9px] text-slate-400 block uppercase">Incertidumbre (σ)</span>
                      <span className={`text-base font-black ${
                        (cell.incertidumbre_std ?? 0) > 0.08
                          ? "text-rose-400"
                          : (cell.incertidumbre_std ?? 0) > 0.04
                          ? "text-amber-300"
                          : "text-emerald-300"
                      }`}>
                        ±{((cell.incertidumbre_std ?? 0) * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="col-span-2 sm:col-span-1 p-1.5 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-col justify-center">
                      <span className="text-[9px] text-slate-400 block uppercase">Distancia Z</span>
                      <span className="text-sm font-bold text-slate-300">
                        {cell.distancia_dominio_z !== undefined && cell.distancia_dominio_z !== null
                          ? `${cell.distancia_dominio_z.toFixed(1)}σ`
                          : "N/A"}
                      </span>
                    </div>
                  </div>

                  {cell.categoria_fiabilidad && (
                    <div className="flex items-center justify-between pt-1 border-t border-purple-900/40 text-[10px]">
                      <span className="text-slate-400">Matriz de Fiabilidad 2D:</span>
                      <span className={`font-mono font-bold px-2 py-0.5 rounded border text-[10px] ${
                        cell.categoria_fiabilidad.includes("Prioridad A")
                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                          : cell.categoria_fiabilidad.includes("Frontera")
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                          : cell.categoria_fiabilidad.includes("Esterilidad")
                          ? "bg-slate-800 text-slate-300 border-slate-700"
                          : cell.categoria_fiabilidad.includes("Extrapolación")
                          ? "bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse"
                          : "bg-cyan-950/60 text-cyan-300 border-cyan-800/60"
                      }`}>
                        {cell.categoria_fiabilidad}
                      </span>
                    </div>
                  )}

                  {cell.es_extrapolacion && (
                    <div className="flex items-center gap-1.5 text-[10px] text-rose-300 bg-rose-950/40 p-1.5 rounded border border-rose-900/50">
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                      <span>Alerta OOD: Celda en extrapolación geológica (&gt; 3σ respecto al dominio conocido).</span>
                    </div>
                  )}
                </div>
              )}

              {/* Atributos geológicos y de ubicación */}
              <div className="p-2.5 rounded-xl bg-slate-900/50 border border-slate-800/80 text-[11px] font-mono grid grid-cols-2 gap-2 text-slate-300">
                <div>
                  <span className="text-slate-500">Malla:</span> R{cell.row} C{cell.col}
                </div>
                <div>
                  <span className="text-slate-500">Área Terrestre:</span> {(cell.land_area_m2 / 1e6).toFixed(2)} km²
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
                    <span>Yacimiento Histórico: <strong>{cell.deposit_id}</strong></span>
                  </div>
                )}
              </div>

              {/* Botonera de Acciones Rápidas */}
              <div className="flex items-center gap-2 pt-1">
                {onRunBuffer && (
                  <button
                    onClick={() => onRunBuffer(cell.lat_wgs84, cell.lon_wgs84)}
                    className="flex-1 py-2.5 px-3 rounded-xl bg-slate-900 hover:bg-cyan-950/60 border border-cyan-800/60 hover:border-cyan-500/80 text-cyan-300 font-semibold text-xs flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-sm"
                    title="Calcular buffer geodésico y densidad de indicios alrededor de esta celda"
                  >
                    <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Analizar Buffer Espacial</span>
                  </button>
                )}

                <button
                  onClick={onExplainClick}
                  className="flex-1 py-2.5 px-3 rounded-xl bg-gradient-to-r from-cyan-500 via-teal-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 transition-all cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5 text-slate-950" />
                  <span>Explicar Celda (XAI)</span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-950" />
                </button>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
