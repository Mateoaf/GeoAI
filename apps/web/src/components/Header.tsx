"use client";

import React from "react";
import { ProjectSummary, RasterLayerType } from "../types";
import {
  ShieldCheck,
  Sparkles,
  BarChart3,
  Map as MapIcon,
  Search,
  Maximize2,
  PanelRight,
  Layers,
  Sun,
  Moon
} from "lucide-react";

interface HeaderProps {
  currentView: "map" | "dashboard";
  setCurrentView: (view: "map" | "dashboard") => void;
  summary: ProjectSummary | null;
  onOpenMethodology: () => void;
  activeRasterLayer: RasterLayerType;
  setActiveRasterLayer: (layer: RasterLayerType) => void;
  onOpenTab: (tab: "explain" | "targets" | "validation" | "copilot") => void;
  activeTab: "explain" | "targets" | "validation" | "copilot";
  isRightOpen: boolean;
  baseMap: "dark" | "street" | "satellite";
  setBaseMap: (val: "dark" | "street" | "satellite") => void;
  onZoomToZone?: (target: { lon: number; lat: number; zoom?: number }) => void;
  onOpenCommandPalette?: () => void;
  isZenMode?: boolean;
  onToggleZenMode?: () => void;
  theme?: "dark" | "light";
  onToggleTheme?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  setCurrentView,
  onOpenMethodology,
  onOpenTab,
  activeTab,
  isRightOpen,
  onOpenCommandPalette,
  isZenMode,
  onToggleZenMode,
  theme = "dark",
  onToggleTheme
}) => {
  return (
    <header className="h-14 bg-slate-950/95 backdrop-blur-xl border-b border-slate-800/80 px-4 flex items-center justify-between text-slate-100 z-30 relative select-none">
      {/* 1. SECCIÓN IZQUIERDA: LOGO + SELECTOR DE VISTA (MAPA / DASHBOARD) */}
      <div className="flex items-center gap-4">
        {/* Branding */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 via-yellow-400 to-cyan-400 flex items-center justify-center shadow-lg shadow-amber-500/20 border border-amber-300/40 shrink-0">
            <Sparkles className="w-4 h-4 text-slate-950 font-black" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-black tracking-tight text-base bg-gradient-to-r from-amber-300 via-yellow-200 to-cyan-300 bg-clip-text text-transparent">
              GEOAI-AU
            </span>
            <span className="text-[9px] font-mono uppercase font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30">
              PROSPECTIVITY v3.0
            </span>
          </div>
        </div>

        {/* Selector de Vista: Mapa GIS vs Dashboard Ejecutivo */}
        <div className="flex items-center p-1 bg-slate-900/90 rounded-xl border border-slate-800/80 gap-1">
          <button
            onClick={() => setCurrentView("map")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              currentView === "map"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20 font-black"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <MapIcon className="w-3.5 h-3.5" />
            <span>Mapa GIS</span>
          </button>
          <button
            onClick={() => setCurrentView("dashboard")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              currentView === "dashboard"
                ? "bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20 font-black"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </button>
        </div>
      </div>

      {/* 2. SECCIÓN CENTRAL: BUSCADOR SPOTLIGHT GLOBAL (CTRL+K) */}
      {onOpenCommandPalette && (
        <button
          onClick={onOpenCommandPalette}
          className="hidden md:flex items-center justify-between w-64 lg:w-96 px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800/90 text-slate-400 hover:text-slate-200 border border-slate-800 hover:border-cyan-500/40 transition-all text-xs cursor-pointer group shadow-inner"
          title="Buscar yacimientos, distritos mineros, modelos y herramientas (Ctrl+K)"
        >
          <div className="flex items-center gap-2 truncate">
            <Search className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition-transform shrink-0" />
            <span className="truncate text-slate-400 group-hover:text-slate-300">
              Buscar minas, distritos, modelos...
            </span>
          </div>
          <kbd className="text-[10px] font-mono bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 text-slate-400 group-hover:border-slate-700 shrink-0 ml-2">
            Ctrl K
          </kbd>
        </button>
      )}

      {/* 3. SECCIÓN DERECHA: TELEMETRÍA + ACCIONES */}
      <div className="flex items-center gap-2.5">
        {/* Telemetría compacta del sistema auditado */}
        <div className="hidden xl:flex items-center gap-2 px-3 py-1 rounded-xl bg-slate-900/80 border border-slate-800/80 text-[11px] font-mono text-slate-400 shadow-inner">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>478k Celdas</span>
          <span className="text-slate-700">|</span>
          <span className="text-amber-300 font-semibold">787 Indicios</span>
          <span className="text-slate-700">|</span>
          <span className="text-cyan-300 font-semibold">56 Covariables</span>
        </div>

        {/* Botón Abrir / Cerrar Panel Lateral (solo en vista de mapa) */}
        {currentView === "map" && (
          <button
            onClick={() => onOpenTab(activeTab || "targets")}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-xs font-medium transition-all cursor-pointer ${
              isRightOpen
                ? "bg-amber-500/20 border-amber-500/50 text-amber-300 shadow-sm"
                : "bg-slate-900/80 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
            title={isRightOpen ? "Colapsar Panel Multitarea" : "Abrir Panel Multitarea (Targets, Copiloto, Explicabilidad)"}
          >
            <PanelRight className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline">Panel</span>
          </button>
        )}

        {/* Modal de Metodología */}
        <button
          onClick={onOpenMethodology}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800 transition-all text-xs font-medium cursor-pointer"
          title="Metodología y Limitaciones del Estudio"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden sm:inline">Metodología</span>
        </button>

        {/* Selector de Modo Oscuro / Modo Claro */}
        {onToggleTheme && (
          <button
            onClick={onToggleTheme}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer shadow-sm ${
              theme === "light"
                ? "bg-amber-100 hover:bg-amber-200/90 text-amber-900 border-amber-300 shadow-amber-500/10"
                : "bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-amber-300 border-slate-800"
            }`}
            title={theme === "light" ? "Cambiar a Modo Oscuro (🌙)" : "Cambiar a Modo Claro (☀️)"}
          >
            {theme === "light" ? (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-600 animate-spin-subtle" />
                <span className="hidden sm:inline">Modo Claro</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-cyan-400" />
                <span className="hidden sm:inline">Modo Oscuro</span>
              </>
            )}
          </button>
        )}

        {/* Toggle Modo Inmersivo / Zen */}
        {onToggleZenMode && currentView === "map" && (
          <button
            onClick={onToggleZenMode}
            className={`p-2 rounded-xl border text-xs transition-colors cursor-pointer ${
              isZenMode
                ? "bg-cyan-500 text-slate-950 border-cyan-400 font-bold shadow-md shadow-cyan-500/20"
                : "bg-slate-900/80 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800"
            }`}
            title={isZenMode ? "Salir de Modo Inmersivo" : "Modo Inmersivo (Lienzo Completo)"}
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </header>
  );
};
