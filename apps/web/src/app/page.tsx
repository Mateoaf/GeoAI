"use client";

import React, { useState, useEffect } from "react";
import { Header } from "../components/Header";
import { Map } from "../components/Map";
import { LeftLayerPanel } from "../components/LeftLayerPanel";
import { CellInspector } from "../components/CellInspector";
import { RightPanel } from "../components/RightPanel";
import { MethodologyModal } from "../components/MethodologyModal";
import { MapLegend } from "../components/MapLegend";
import { ExecutiveDashboard } from "../components/ExecutiveDashboard";
import { ProjectSummary, CellInfo, CellExplanation, RasterLayerType, BufferAnalysisResult } from "../types";
import { api } from "../lib/api";
import { CommandPalette } from "../components/CommandPalette";
import { ToastContainer, ToastMessage } from "../components/Toast";

export default function Home() {
  // Vista activa principal: "dashboard" (estilo foto) vs "map" (mapa GIS)
  const [currentView, setCurrentView] = useState<"map" | "dashboard">("dashboard");

  // Estado global del proyecto
  const [summary, setSummary] = useState<ProjectSummary | null>(null);

  // Estados de visualización cartográfica - Por defecto: Motor Oficial v3.0 (PU Calibrado c=0.72)
  const [activeRasterLayer, setActiveRasterLayer] = useState<RasterLayerType>("v3_pu_score");
  const [rasterOpacity, setRasterOpacity] = useState<number>(0.90);
  const [showZones, setShowZones] = useState<boolean>(true);
  const [showDeposits, setShowDeposits] = useState<boolean>(true);
  const [showIndicios, setShowIndicios] = useState<boolean>(true);
  const [indicioFilter, setIndicioFilter] = useState<"todos" | "roca" | "aluvial">("todos");
  const [showDistricts, setShowDistricts] = useState<boolean>(true);
  const [baseMap, setBaseMap] = useState<"dark" | "street" | "satellite">("dark");

  // Tema de interfaz: "dark" vs "light"
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    try {
      const savedTheme = localStorage.getItem("geoai-theme") as "dark" | "light" | null;
      if (savedTheme === "light") {
        setTheme("light");
        document.documentElement.classList.remove("dark");
        document.documentElement.classList.add("light");
        setBaseMap("street");
      } else {
        setTheme("dark");
        document.documentElement.classList.add("dark");
        document.documentElement.classList.remove("light");
      }
    } catch (e) {
      console.warn("localStorage not available", e);
    }
  }, []);

  const handleToggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    try {
      localStorage.setItem("geoai-theme", next);
    } catch (e) {}

    if (next === "light") {
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
      if (baseMap === "dark") {
        setBaseMap("street");
      }
      showToast("☀️ Modo claro activado", "info");
    } else {
      document.documentElement.classList.remove("light");
      document.documentElement.classList.add("dark");
      if (baseMap === "street") {
        setBaseMap("dark");
      }
      showToast("🌙 Modo oscuro activado", "info");
    }
  };

  // Herramienta de Buffer Espacial GIS
  const [bufferToolActive, setBufferToolActive] = useState<boolean>(false);
  const [bufferRadiusKm, setBufferRadiusKm] = useState<number>(10);
  const [bufferResult, setBufferResult] = useState<BufferAnalysisResult | null>(null);

  // Spotlight Command Palette & Toasts & Zen Mode
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState<boolean>(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [isZenMode, setIsZenMode] = useState<boolean>(false);

  // Estados de inspección territorial
  const [selectedCoordinates, setSelectedCoordinates] = useState<{ lat: number; lon: number } | null>(null);
  const [selectedCell, setSelectedCell] = useState<CellInfo | null>(null);
  const [cellEligible, setCellEligible] = useState<boolean>(true);
  const [cellLoading, setCellLoading] = useState<boolean>(false);
  const [activeCellExplanation, setActiveCellExplanation] = useState<CellExplanation | null>(null);

  // Navegación en el mapa
  const [targetToZoom, setTargetToZoom] = useState<{ lon: number; lat: number; zoom?: number } | null>(null);

  // Paneles de control y tabs - Panel derecho COLAPSADO por defecto para lienzo limpio
  const [activeTab, setActiveTab] = useState<"explain" | "targets" | "validation" | "copilot">("targets");
  const [isLeftCollapsed, setIsLeftCollapsed] = useState<boolean>(false);
  const [isRightCollapsed, setIsRightCollapsed] = useState<boolean>(true);
  const [isMethodologyOpen, setIsMethodologyOpen] = useState<boolean>(false);

  // Sistema de notificación toast
  const showToast = (message: string, type: "success" | "info" | "warning" = "info") => {
    const id = Date.now().toString() + Math.random().toString(36).slice(2, 5);
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  // Estado de perspectiva 3D (Pitch 60°)
  const [is3DActive, setIs3DActive] = useState<boolean>(false);

  const handleToggle3D = () => {
    setIs3DActive((prev) => {
      const next = !prev;
      showToast(next ? "🏔️ Perspectiva 3D activada (Relieve y topografía)" : "🗺️ Vista 2D plana activada", "info");
      return next;
    });
  };

  // Comparativa A/B rápida de modelos de favorabilidad
  const handleToggleAB = () => {
    if (activeRasterLayer === "rock_score") {
      setActiveRasterLayer("alluvial_score");
      showToast("⚡ Comparativa A/B: Oro Aluvial v2 activado (Placeres secundarios)", "info");
    } else if (activeRasterLayer === "alluvial_score") {
      setActiveRasterLayer("rock_score");
      showToast("⚡ Comparativa A/B: Oro en Roca v2 activado (Filones primarios)", "info");
    } else if (activeRasterLayer === "score") {
      setActiveRasterLayer("global_v2_score");
      showToast("⚡ Comparativa A/B: Oro Global v2 activado (ROC 0.966)", "info");
    } else {
      setActiveRasterLayer("rock_score");
      showToast("⚡ Comparativa A/B: Oro en Roca v2 activado", "info");
    }
  };

  // Atajo de teclado global Ctrl+K / Cmd+K para abrir Command Palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Carga inicial del resumen del proyecto
  useEffect(() => {
    async function loadInitial() {
      try {
        const sum = await api.getProjectSummary();
        setSummary(sum);
      } catch (err) {
        console.error("Error conectando con backend FastAPI:", err);
      }
    }
    loadInitial();
  }, []);

  // Manejador de selección de celda al hacer clic en el mapa
  const handleSelectCoordinate = async (lat: number, lon: number) => {
    setSelectedCoordinates({ lat, lon });
    setCellLoading(true);

    try {
      const resp = await api.getCellByCoordinate(lat, lon);
      setCellEligible(resp.eligible);
      setSelectedCell(resp.cell);

      if (resp.eligible && resp.cell) {
        try {
          const expResp = await api.explainCell(resp.cell.cell_id);
          setActiveCellExplanation(expResp.explanation);
        } catch (e) {
          console.error("Error calculando explicabilidad:", e);
          setActiveCellExplanation(null);
        }
      } else {
        setActiveCellExplanation(null);
      }
    } catch (err) {
      console.error("Error consultando celda:", err);
      setCellEligible(false);
      setSelectedCell(null);
      setActiveCellExplanation(null);
    } finally {
      setCellLoading(false);
    }
  };

  // Ejecución de análisis de buffer espacial GIS (<1 ms)
  const handleRunBufferAnalysis = async (lat: number, lon: number, radiusKm: number) => {
    try {
      const res = await api.getBufferAnalysis(lat, lon, radiusKm);
      setBufferResult(res);
      showToast(`🎯 Buffer ${radiusKm} km: ${res.indicios_count} indicios detectados (${res.nearest_district.nombre})`);
    } catch (err) {
      console.error("Error ejecutando análisis de buffer:", err);
      showToast("⚠️ Error al calcular análisis de buffer", "warning");
    }
  };

  // Toggle o apertura de pestaña del panel derecho desde el Header
  const handleOpenTab = (tab: "explain" | "targets" | "validation" | "copilot") => {
    if (!isRightCollapsed && activeTab === tab) {
      setIsRightCollapsed(true);
    } else {
      setActiveTab(tab);
      setIsRightCollapsed(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 font-sans">
      {/* 1. Barra de Navegación Superior */}
      <Header
        currentView={currentView}
        setCurrentView={(v) => {
          setCurrentView(v);
          showToast(v === "map" ? "🗺️ Vista: Mapa GIS Interactivo" : "📊 Vista: Dashboard Ejecutivo v3.0");
        }}
        summary={summary}
        onOpenMethodology={() => setIsMethodologyOpen(true)}
        activeRasterLayer={activeRasterLayer}
        setActiveRasterLayer={(layer) => {
          setActiveRasterLayer(layer);
          showToast(`Capa activa: ${layer}`);
        }}
        onOpenTab={handleOpenTab}
        activeTab={activeTab}
        isRightOpen={!isRightCollapsed}
        baseMap={baseMap}
        setBaseMap={(b) => {
          setBaseMap(b);
          showToast(`Mapa base: ${b === "satellite" ? "Satélite" : b === "dark" ? "Oscuro" : "Callejero"}`);
        }}
        onZoomToZone={(target) => {
          setCurrentView("map");
          setTargetToZoom(target);
          showToast("Navegando a coordenadas seleccionadas");
        }}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        isZenMode={isZenMode}
        onToggleZenMode={() => {
          const next = !isZenMode;
          setIsZenMode(next);
          if (next) {
            setIsLeftCollapsed(true);
            setIsRightCollapsed(true);
            showToast("Modo Inmersivo (Zen) activado");
          } else {
            setIsLeftCollapsed(false);
            showToast("Modo Inmersivo desactivado");
          }
        }}
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />

      {/* 2. PESTAÑA A: DASHBOARD EJECUTIVO V3.0 (Estilo foto de referencia) */}
      <div className={currentView === "dashboard" ? "flex-1 w-full h-[calc(100vh-3.5rem)] overflow-y-auto" : "hidden"}>
        <ExecutiveDashboard
          onNavigateToMapTarget={(target) => {
            setCurrentView("map");
            setTargetToZoom(target);
            showToast("Navegando a blanco minero en el mapa");
          }}
        />
      </div>

      {/* 3. PESTAÑA B: ÁREA CENTRAL DEL MAPA GIS Y PANELES FLOTANTES */}
      <main className={currentView === "map" ? "relative flex-1 w-full h-[calc(100vh-3.5rem)] overflow-hidden" : "hidden"}>
        {/* Lienzo del Mapa a pantalla completa */}
        <Map
          activeRasterLayer={activeRasterLayer}
          rasterOpacity={rasterOpacity}
          showZones={showZones}
          showDeposits={showDeposits}
          showIndicios={showIndicios}
          indicioFilter={indicioFilter}
          showDistricts={showDistricts}
          baseMap={baseMap}
          onSelectCoordinate={handleSelectCoordinate}
          selectedCoordinates={selectedCoordinates}
          targetToZoom={targetToZoom}
          bufferToolActive={bufferToolActive}
          setBufferToolActive={setBufferToolActive}
          bufferRadiusKm={bufferRadiusKm}
          setBufferRadiusKm={setBufferRadiusKm}
          bufferResult={bufferResult}
          onRunBufferAnalysis={handleRunBufferAnalysis}
          onCloseBufferResult={() => setBufferResult(null)}
          is3DActive={is3DActive}
          onToggle3D={handleToggle3D}
        />

        {/* Leyenda Dinámica de la Capa Activa */}
        {!isZenMode && <MapLegend activeRasterLayer={activeRasterLayer} />}

        {/* Panel Izquierdo de Control de Capas (Arrastrable) */}
        {!isZenMode && (
          <LeftLayerPanel
            activeRasterLayer={activeRasterLayer}
            setActiveRasterLayer={setActiveRasterLayer}
            rasterOpacity={rasterOpacity}
            setRasterOpacity={setRasterOpacity}
            showZones={showZones}
            setShowZones={setShowZones}
            showDeposits={showDeposits}
            setShowDeposits={setShowDeposits}
            showIndicios={showIndicios}
            setShowIndicios={setShowIndicios}
            indicioFilter={indicioFilter}
            setIndicioFilter={setIndicioFilter}
            showDistricts={showDistricts}
            setShowDistricts={setShowDistricts}
            bufferToolActive={bufferToolActive}
            setBufferToolActive={setBufferToolActive}
            bufferRadiusKm={bufferRadiusKm}
            setBufferRadiusKm={setBufferRadiusKm}
            baseMap={baseMap}
            setBaseMap={setBaseMap}
            isCollapsed={isLeftCollapsed}
            setIsCollapsed={setIsLeftCollapsed}
            onToggleAB={handleToggleAB}
          />
        )}

        {/* Inspector de Celda Inferior Flotante (Arrastrable y Minimizable) */}
        <CellInspector
          cell={selectedCell}
          eligible={cellEligible}
          queryCoordinates={selectedCoordinates}
          onClose={() => {
            setSelectedCoordinates(null);
            setSelectedCell(null);
          }}
          onExplainClick={() => {
            setActiveTab("explain");
            setIsRightCollapsed(false);
          }}
          onRunBuffer={(lat, lon) => handleRunBufferAnalysis(lat, lon, bufferRadiusKm)}
        />

        {/* Panel Derecho Multitarea (Arrastrable) */}
        {!isZenMode && (
          <RightPanel
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            isCollapsed={isRightCollapsed}
            setIsCollapsed={setIsRightCollapsed}
            activeCellExplanation={activeCellExplanation}
            onZoomToZone={(target) => setTargetToZoom(target)}
            activeCellId={selectedCell?.cell_id}
            selectedCell={selectedCell}
            onSelectCoordinate={handleSelectCoordinate}
          />
        )}
      </main>

      {/* 4. Modal de Metodología y Limitaciones */}
      <MethodologyModal
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
      />

      {/* 5. Spotlight Command Palette (Ctrl+K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectRasterLayer={(l) => setActiveRasterLayer(l)}
        onZoomTo={(t) => setTargetToZoom(t)}
        onOpenTab={handleOpenTab}
        onOpenMethodology={() => setIsMethodologyOpen(true)}
        onToggle3D={handleToggle3D}
        onToggleBuffer={() => {
          const next = !bufferToolActive;
          setBufferToolActive(next);
          showToast(next ? "🎯 Herramienta de Buffer activada" : "Herramienta de Buffer desactivada");
        }}
        onSetBaseMap={(m) => setBaseMap(m)}
        onSwitchView={(v) => setCurrentView(v)}
        onShowToast={showToast}
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />

      {/* 6. Sistema de Notificaciones Toast */}
      <ToastContainer
        toasts={toasts}
        onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))}
      />
    </div>
  );
}
