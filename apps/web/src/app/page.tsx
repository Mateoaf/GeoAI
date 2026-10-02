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
import { ProjectSummary, CellInfo, CellExplanation, RasterLayerType } from "../types";
import { api } from "../lib/api";

export default function Home() {
  // Vista activa principal: "dashboard" (estilo foto) vs "map" (mapa GIS)
  const [currentView, setCurrentView] = useState<"map" | "dashboard">("dashboard");

  // Estado global del proyecto
  const [summary, setSummary] = useState<ProjectSummary | null>(null);

  // Estados de visualización cartográfica - Por defecto: Oro en Roca (v2) con mapa satelital/oscuro
  const [activeRasterLayer, setActiveRasterLayer] = useState<RasterLayerType>("rock_score");
  const [rasterOpacity, setRasterOpacity] = useState<number>(0.90);
  const [showZones, setShowZones] = useState<boolean>(true);
  const [showDeposits, setShowDeposits] = useState<boolean>(true);
  const [baseMap, setBaseMap] = useState<"dark" | "street" | "satellite">("dark");

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
        setCurrentView={setCurrentView}
        summary={summary}
        onOpenMethodology={() => setIsMethodologyOpen(true)}
        activeRasterLayer={activeRasterLayer}
        setActiveRasterLayer={setActiveRasterLayer}
        onOpenTab={handleOpenTab}
        activeTab={activeTab}
        isRightOpen={!isRightCollapsed}
        baseMap={baseMap}
        setBaseMap={setBaseMap}
        onZoomToZone={(target) => {
          setCurrentView("map");
          setTargetToZoom(target);
        }}
      />

      {/* 2. PESTAÑA A: DASHBOARD EJECUTIVO V3.0 (Estilo foto de referencia) */}
      <div className={currentView === "dashboard" ? "flex-1 w-full h-[calc(100vh-3.5rem)] overflow-y-auto" : "hidden"}>
        <ExecutiveDashboard
          onNavigateToMapTarget={(target) => {
            setCurrentView("map");
            setTargetToZoom(target);
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
          baseMap={baseMap}
          onSelectCoordinate={handleSelectCoordinate}
          selectedCoordinates={selectedCoordinates}
          targetToZoom={targetToZoom}
        />

        {/* Leyenda Dinámica de la Capa Activa */}
        <MapLegend activeRasterLayer={activeRasterLayer} />

        {/* Panel Izquierdo de Control de Capas (Arrastrable) */}
        <LeftLayerPanel
          activeRasterLayer={activeRasterLayer}
          setActiveRasterLayer={setActiveRasterLayer}
          rasterOpacity={rasterOpacity}
          setRasterOpacity={setRasterOpacity}
          showZones={showZones}
          setShowZones={setShowZones}
          showDeposits={showDeposits}
          setShowDeposits={setShowDeposits}
          baseMap={baseMap}
          setBaseMap={setBaseMap}
          isCollapsed={isLeftCollapsed}
          setIsCollapsed={setIsLeftCollapsed}
        />

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
        />

        {/* Panel Derecho Multitarea (Arrastrable) */}
        <RightPanel
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          isCollapsed={isRightCollapsed}
          setIsCollapsed={setIsRightCollapsed}
          activeCellExplanation={activeCellExplanation}
          onZoomToZone={(target) => setTargetToZoom(target)}
          activeCellId={selectedCell?.cell_id}
        />
      </main>

      {/* 4. Modal de Metodología y Limitaciones */}
      <MethodologyModal
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
      />
    </div>
  );
}
