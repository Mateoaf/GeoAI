"use client";

import React, { useState, useEffect } from "react";
import { Header } from "../components/Header";
import { Map } from "../components/Map";
import { LeftLayerPanel } from "../components/LeftLayerPanel";
import { CellInspector } from "../components/CellInspector";
import { RightPanel } from "../components/RightPanel";
import { MethodologyModal } from "../components/MethodologyModal";
import { ProjectSummary, CellInfo, CellExplanation, RasterLayerType } from "../types";
import { api } from "../lib/api";

export default function Home() {
  // Estado global del proyecto
  const [summary, setSummary] = useState<ProjectSummary | null>(null);

  // Estados de visualización cartográfica
  const [activeRasterLayer, setActiveRasterLayer] = useState<RasterLayerType>("score");
  const [rasterOpacity, setRasterOpacity] = useState<number>(0.85);
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

  // Paneles de control y tabs
  const [activeTab, setActiveTab] = useState<"explain" | "targets" | "validation" | "copilot">("explain");
  const [isLeftCollapsed, setIsLeftCollapsed] = useState<boolean>(false);
  const [isRightCollapsed, setIsRightCollapsed] = useState<boolean>(false);
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
        // Cargar inmediatamente la explicación aditiva exacta
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

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 font-sans">
      {/* 1. Barra de Navegación Superior */}
      <Header
        summary={summary}
        onOpenMethodology={() => setIsMethodologyOpen(true)}
      />

      {/* 2. Área Central del Mapa y Paneles Flotantes */}
      <main className="relative flex-1 w-full h-[calc(100vh-3.5rem)] overflow-hidden">
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

        {/* Panel Izquierdo de Control de Capas */}
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

        {/* Inspector de Celda Inferior */}
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

        {/* Panel Derecho Multitarea (Explicabilidad, Targets, Validación, Copiloto) */}
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

      {/* 3. Modal de Metodología y Limitaciones */}
      <MethodologyModal
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
      />
    </div>
  );
}
