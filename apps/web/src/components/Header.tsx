"use client";

import React, { useState } from "react";
import { ProjectSummary, RasterLayerType } from "../types";
import {
  ShieldCheck,
  Sparkles,
  Flame,
  Waves,
  Globe2,
  Target,
  Bot,
  BarChart3,
  Layers,
  MapPin,
  ChevronDown,
  Sun,
  Moon,
  Satellite,
  Map as MapIcon
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
}

const DISTRICT_PRESETS = [
  { name: "🇪🇸 Vista Peninsular", lon: -3.70, lat: 40.00, zoom: 5.8 },
  { name: "⛰️ Asturias (El Valle-Boinás)", lon: -6.25, lat: 43.32, zoom: 10 },
  { name: "🌲 Galicia (Corcoesto)", lon: -8.76, lat: 43.19, zoom: 10 },
  { name: "⛏️ León (Las Médulas / Sil)", lon: -6.76, lat: 42.46, zoom: 10.5 },
  { name: "🏜️ Ossa Morena (Alconchel)", lon: -6.71, lat: 38.52, zoom: 10 },
  { name: "🌋 Almería (Rodalquilar)", lon: -2.04, lat: 36.85, zoom: 11 },
  { name: "🏞️ Montes de Toledo", lon: -4.50, lat: 39.55, zoom: 9 }
];

export const Header: React.FC<HeaderProps> = ({
  currentView,
  setCurrentView,
  summary,
  onOpenMethodology,
  activeRasterLayer,
  setActiveRasterLayer,
  onOpenTab,
  activeTab,
  isRightOpen,
  baseMap,
  setBaseMap,
  onZoomToZone
}) => {
  const [districtDropdownOpen, setDistrictDropdownOpen] = useState(false);

  return (
    <header className="h-14 bg-slate-950/95 backdrop-blur-xl border-b border-slate-800/80 px-4 flex items-center justify-between text-slate-100 z-30 relative select-none">
      {/* 1. Logo y Branding + Selector de Pestaña Principal */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 via-yellow-400 to-cyan-400 flex items-center justify-center shadow-lg shadow-amber-500/20 border border-amber-300/40">
            <Sparkles className="w-4 h-4 text-slate-950 font-black" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold tracking-tight text-base bg-gradient-to-r from-amber-300 via-yellow-200 to-cyan-300 bg-clip-text text-transparent">
                GEOAI-AU
              </span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30">
                PROSPECTIVITY v3.0
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium tracking-tight hidden sm:block">
              Inteligencia Aurífera Peninsular · 787 Yacimientos e Indicios
            </p>
          </div>
        </div>

        {/* PESTAÑAS PRINCIPALES: MAPA GIS vs DASHBOARD V3.0 */}
        <div className="hidden sm:flex items-center p-1 bg-slate-900/90 rounded-xl border border-slate-800 gap-1 ml-2">
          <button
            onClick={() => setCurrentView("map")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              currentView === "map"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <MapIcon className="w-3.5 h-3.5" />
            <span>Mapa GIS</span>
          </button>
          <button
            onClick={() => setCurrentView("dashboard")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              currentView === "dashboard"
                ? "bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Dashboard v3.0</span>
            <span className="text-[9px] bg-amber-950/80 text-amber-300 px-1.5 py-0.2 rounded font-mono">Foto</span>
          </button>
        </div>
      </div>

      {/* 2. Selector Rápido de Modelo / Capa (Pills segmentadas en el centro cuando está en vista de mapa) */}
      {currentView === "map" ? (
        <div className="hidden lg:flex items-center p-1 bg-slate-900/90 rounded-xl border border-slate-800 shadow-inner gap-1">
          <button
            onClick={() => setActiveRasterLayer("rock_score")}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              activeRasterLayer === "rock_score"
                ? "bg-gradient-to-r from-amber-500 to-rose-600 text-slate-950 font-bold shadow-md shadow-amber-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
            title="Oro en Roca / Vetas Primarias (LightGBM - ROC 0.976)"
          >
            <Flame className="w-3.5 h-3.5" />
            <span>Oro en Roca</span>
          </button>

        <button
          onClick={() => setActiveRasterLayer("alluvial_score")}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            activeRasterLayer === "alluvial_score"
              ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 font-bold shadow-md shadow-cyan-500/20"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
          title="Oro Aluvial / Terrazas y Placeres (LightGBM - ROC 0.951)"
        >
          <Waves className="w-3.5 h-3.5" />
          <span>Oro Aluvial</span>
        </button>

        <button
          onClick={() => setActiveRasterLayer("global_v2_score")}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            activeRasterLayer === "global_v2_score"
              ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
          title="Oro Global v2 (LightGBM - ROC 0.962)"
        >
          <Globe2 className="w-3.5 h-3.5" />
          <span>Global v2</span>
        </button>

        <button
          onClick={() => setActiveRasterLayer("priority")}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            activeRasterLayer === "priority"
              ? "bg-amber-400 text-slate-950 font-bold shadow-md shadow-amber-400/20"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
          title="Bandas Prioritarias Top 1%, 5%, 10%"
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Bandas Top</span>
        </button>

        <button
          onClick={() => setActiveRasterLayer("score")}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            activeRasterLayer === "score"
              ? "bg-slate-200 text-slate-950 font-bold shadow-md"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
          title="Modelo Oficial v1.0 (Regresión Logística Auditada)"
        >
          <span>v1.0 Base</span>
        </button>
      </div>
      ) : (
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-xl bg-slate-900/90 border border-slate-800 text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
          <span className="text-slate-300">Executive MPM Benchmark ·</span>
          <span className="text-amber-400 font-bold">27 Capas Geocientíficas</span>
        </div>
      )}

      {/* 3. Acciones, Hotspots y Paneles Rápidos */}
      <div className="flex items-center gap-2">
        {/* Selector de Distritos Mineros Clave */}
        {onZoomToZone && (
          <div className="relative hidden md:block">
            <button
              onClick={() => setDistrictDropdownOpen(!districtDropdownOpen)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800 transition-all text-xs font-medium cursor-pointer"
              title="Volar a un distrito aurífero emblemático"
            >
              <MapPin className="w-3.5 h-3.5 text-cyan-400" />
              <span>Distritos</span>
              <ChevronDown className="w-3 h-3 text-slate-500" />
            </button>

            {districtDropdownOpen && (
              <div
                className="absolute top-10 right-0 w-64 bg-slate-900/95 backdrop-blur-2xl border border-slate-700/80 rounded-xl shadow-2xl py-1.5 z-50 text-xs animate-in fade-in zoom-in-95 duration-150"
                onMouseLeave={() => setDistrictDropdownOpen(false)}
              >
                <div className="px-3 py-1 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                  Navegación Rápida a Focos Auríferos
                </div>
                {DISTRICT_PRESETS.map((d) => (
                  <button
                    key={d.name}
                    onClick={() => {
                      onZoomToZone({ lon: d.lon, lat: d.lat, zoom: d.zoom });
                      setDistrictDropdownOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-cyan-950/60 hover:text-cyan-300 transition-colors flex items-center justify-between text-slate-200 cursor-pointer"
                  >
                    <span>{d.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Toggle Rápido Mapa Base (Oscuro vs Satélite) */}
        <div className="flex items-center p-0.5 bg-slate-900 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setBaseMap("dark")}
            className={`p-1.5 rounded-md transition-colors cursor-pointer ${
              baseMap === "dark" ? "bg-slate-800 text-cyan-400 shadow-sm" : "text-slate-400 hover:text-slate-200"
            }`}
            title="Mapa Base Oscuro (Carto Dark Matter)"
          >
            <Moon className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setBaseMap("satellite")}
            className={`p-1.5 rounded-md transition-colors cursor-pointer ${
              baseMap === "satellite" ? "bg-slate-800 text-amber-400 shadow-sm" : "text-slate-400 hover:text-slate-200"
            }`}
            title="Mapa Base Satélite Alta Resolución (Esri World Imagery)"
          >
            <Satellite className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Targets (1.529) */}
        <button
          onClick={() => onOpenTab("targets")}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all cursor-pointer ${
            isRightOpen && activeTab === "targets"
              ? "bg-amber-500/20 border-amber-500/60 text-amber-300 shadow-sm"
              : "bg-slate-900/80 border-slate-800 text-slate-300 hover:text-amber-300 hover:border-slate-700"
          }`}
        >
          <Target className="w-3.5 h-3.5 text-amber-400" />
          <span className="hidden sm:inline">Targets</span>
          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-950/80 text-amber-400 border border-amber-800/50">
            1.529
          </span>
        </button>

        {/* Copiloto IA */}
        <button
          onClick={() => onOpenTab("copilot")}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all cursor-pointer ${
            isRightOpen && activeTab === "copilot"
              ? "bg-purple-500/20 border-purple-500/60 text-purple-300 shadow-sm"
              : "bg-slate-900/80 border-slate-800 text-slate-300 hover:text-purple-300 hover:border-slate-700"
          }`}
        >
          <Bot className="w-3.5 h-3.5 text-purple-400" />
          <span className="hidden sm:inline">Copiloto</span>
        </button>

        {/* Validación / Auditoría */}
        <button
          onClick={() => onOpenTab("validation")}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all cursor-pointer ${
            isRightOpen && activeTab === "validation"
              ? "bg-emerald-500/20 border-emerald-500/60 text-emerald-300 shadow-sm"
              : "bg-slate-900/80 border-slate-800 text-slate-300 hover:text-emerald-300 hover:border-slate-700"
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5 text-emerald-400" />
          <span className="hidden sm:inline">Validación</span>
        </button>

        {/* Metodología */}
        <button
          onClick={onOpenMethodology}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800 transition-all text-xs font-medium cursor-pointer"
          title="Metodología y Limitaciones del Estudio"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden md:inline">Metodología</span>
        </button>
      </div>
    </header>
  );
};
