"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";

import { RasterLayerType } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MapProps {
  activeRasterLayer: RasterLayerType;
  rasterOpacity: number;
  showZones: boolean;
  showDeposits: boolean;
  baseMap: "dark" | "street" | "satellite";
  onSelectCoordinate: (lat: number, lon: number) => void;
  selectedCoordinates?: { lat: number; lon: number } | null;
  targetToZoom?: { lon: number; lat: number; zoom?: number } | null;
}

// Tipos para almacenar la referencia al módulo cargado dinámicamente
type MapLibreModule = typeof import("maplibre-gl");

export const Map: React.FC<MapProps> = ({
  activeRasterLayer,
  rasterOpacity,
  showZones,
  showDeposits,
  baseMap,
  onSelectCoordinate,
  selectedCoordinates,
  targetToZoom
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const clickMarker = useRef<any>(null);
  const mlRef = useRef<MapLibreModule | null>(null);

  // Callback estable para el handler de clic
  const onSelectRef = useRef(onSelectCoordinate);
  onSelectRef.current = onSelectCoordinate;

  // 1. Obtener estilo base
  const getBaseStyle = (type: "dark" | "street" | "satellite"): any => {
    if (type === "satellite") {
      return {
        version: 8,
        sources: {
          esri_satellite: {
            type: "raster",
            tiles: [
              "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ],
            tileSize: 256,
            attribution: "Esri, Maxar, Earthstar Geographics"
          }
        },
        layers: [
          {
            id: "esri_satellite_layer",
            type: "raster",
            source: "esri_satellite",
            minzoom: 0,
            maxzoom: 19
          }
        ]
      };
    } else if (type === "street") {
      return "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";
    } else {
      return "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
    }
  };

  // 2. Configurar capas geoespaciales sobre el mapa
  const setupLayers = useCallback((m: any, currentRasterLayer: string) => {
    // A. Fuente y capa Raster COG dinámica
    if (!m.getSource("geoai_raster_source")) {
      m.addSource("geoai_raster_source", {
        type: "raster",
        tiles: [`${API_BASE_URL}/api/tiles/${currentRasterLayer === "none" ? "score" : currentRasterLayer}/{z}/{x}/{y}.png`],
        tileSize: 256
      });

      m.addLayer({
        id: "geoai_raster_layer",
        type: "raster",
        source: "geoai_raster_source",
        paint: {
          "raster-opacity": currentRasterLayer === "none" ? 0 : rasterOpacity
        }
      });
    }

    // B. Fuente y capa vectorial de Zonas de Prospectividad (Polígonos)
    if (!m.getSource("zones_source")) {
      m.addSource("zones_source", {
        type: "geojson",
        data: `${API_BASE_URL}/api/targets/geojson`
      });

      m.addLayer({
        id: "zones_fill",
        type: "fill",
        source: "zones_source",
        layout: {
          visibility: showZones ? "visible" : "none"
        },
        paint: {
          "fill-color": [
            "match",
            ["get", "categoria_prioridad"],
            "prioridad_muy_alta_top01", "#E63946",
            "#F4A261"
          ],
          "fill-opacity": 0.25
        }
      });

      m.addLayer({
        id: "zones_outline",
        type: "line",
        source: "zones_source",
        layout: {
          visibility: showZones ? "visible" : "none"
        },
        paint: {
          "line-color": [
            "match",
            ["get", "categoria_prioridad"],
            "prioridad_muy_alta_top01", "#E63946",
            "#F4A261"
          ],
          "line-width": 1.5,
          "line-opacity": 0.8
        }
      });

      // Hover en zona
      m.on("mouseenter", "zones_fill", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "zones_fill", () => {
        m.getCanvas().style.cursor = "";
      });
    }

    // C. Fuente y capa de Depósitos Confirmados (Puntos)
    if (!m.getSource("deposits_source")) {
      m.addSource("deposits_source", {
        type: "geojson",
        data: `${API_BASE_URL}/api/deposits`
      });

      m.addLayer({
        id: "deposits_circle",
        type: "circle",
        source: "deposits_source",
        layout: {
          visibility: showDeposits ? "visible" : "none"
        },
        paint: {
          "circle-color": "#FFD700",
          "circle-radius": 5,
          "circle-stroke-color": "#0F172A",
          "circle-stroke-width": 1.5,
          "circle-opacity": 0.95
        }
      });

      // Popup en depósitos
      m.on("click", "deposits_circle", (e: any) => {
        if (!e.features || !e.features[0] || !mlRef.current) return;
        const props = e.features[0].properties;
        const geom = e.features[0].geometry as any;
        new mlRef.current.Popup({ offset: 10, className: "geoai-popup" })
          .setLngLat(geom.coordinates)
          .setHTML(
            `<div class="p-2 font-sans text-xs bg-slate-900 text-slate-100 rounded border border-slate-700">
              <p class="font-bold text-amber-400 uppercase text-[11px]">${props.deposit_id || "Depósito"}</p>
              <p class="text-slate-300">Distrito: <span class="text-cyan-300">${props.district_id || "N/A"}</span></p>
              <p class="text-slate-300">Tipo Au: <span class="text-emerald-400 capitalize">${props.tipo_au || "N/A"}</span></p>
              <p class="text-slate-400 text-[10px] mt-1">Indicios auditados: ${props.records_count || 1}</p>
            </div>`
          )
          .addTo(m);
      });

      m.on("mouseenter", "deposits_circle", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "deposits_circle", () => {
        m.getCanvas().style.cursor = "";
      });
    }
  }, []);

  // 3. Inicializar mapa (carga dinámica de MapLibre para evitar SSR)
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    let cancelled = false;

    async function initMap() {
      // Importación dinámica — evita SSR y window/self errors
      const maplibregl = await import("maplibre-gl");
      if (typeof window !== "undefined") {
        maplibregl.setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");
      }
      await import("maplibre-gl/dist/maplibre-gl.css");
      mlRef.current = maplibregl;

      if (cancelled || !mapContainer.current) return;

      const m = new maplibregl.Map({
        container: mapContainer.current,
        style: getBaseStyle(baseMap),
        center: [-3.7, 40.0],
        zoom: 5.7,
        minZoom: 4.5,
        maxZoom: 14,
        attributionControl: false
      });

      m.addControl(new maplibregl.NavigationControl({ showCompass: true, showZoom: true }), "top-right");

      m.on("load", () => {
        if (cancelled) return;
        map.current = m;
        setMapLoaded(true);
        setupLayers(m, activeRasterLayer);
      });

      m.on("click", (e: any) => {
        const { lng, lat } = e.lngLat;
        onSelectRef.current(lat, lng);
      });
    }

    initMap();

    return () => {
      cancelled = true;
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // 4. Cambiar mapa base si se modifica
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    map.current.setStyle(getBaseStyle(baseMap));
    map.current.once("style.load", () => {
      if (map.current) setupLayers(map.current, activeRasterLayer);
    });
  }, [baseMap]);

  // 5. Actualizar capa raster cuando cambia layer o opacidad
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    const m = map.current;

    const source = m.getSource("geoai_raster_source") as any;
    if (source && activeRasterLayer !== "none") {
      source.setTiles([`${API_BASE_URL}/api/tiles/${activeRasterLayer}/{z}/{x}/{y}.png`]);
    }

    if (m.getLayer("geoai_raster_layer")) {
      m.setPaintProperty(
        "geoai_raster_layer",
        "raster-opacity",
        activeRasterLayer === "none" ? 0 : rasterOpacity
      );
    }
  }, [activeRasterLayer, rasterOpacity, mapLoaded]);

  // 6. Toggles de capas vectoriales
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    const m = map.current;

    if (m.getLayer("zones_fill")) {
      m.setLayoutProperty("zones_fill", "visibility", showZones ? "visible" : "none");
      m.setLayoutProperty("zones_outline", "visibility", showZones ? "visible" : "none");
    }

    if (m.getLayer("deposits_circle")) {
      m.setLayoutProperty("deposits_circle", "visibility", showDeposits ? "visible" : "none");
    }
  }, [showZones, showDeposits, mapLoaded]);

  // 7. Marcador interactivo de celda seleccionada
  useEffect(() => {
    if (!map.current || !mapLoaded || !mlRef.current) return;

    if (selectedCoordinates) {
      if (!clickMarker.current) {
        const el = document.createElement("div");
        el.className = "w-4 h-4 rounded-full border-2 border-cyan-400 bg-cyan-400/40 animate-ping";
        clickMarker.current = new mlRef.current.Marker({ element: el })
          .setLngLat([selectedCoordinates.lon, selectedCoordinates.lat])
          .addTo(map.current);
      } else {
        clickMarker.current.setLngLat([selectedCoordinates.lon, selectedCoordinates.lat]);
      }
    } else if (clickMarker.current) {
      clickMarker.current.remove();
      clickMarker.current = null;
    }
  }, [selectedCoordinates, mapLoaded]);

  // 8. Zoom suave a target específico
  useEffect(() => {
    if (!map.current || !mapLoaded || !targetToZoom) return;
    map.current.flyTo({
      center: [targetToZoom.lon, targetToZoom.lat],
      zoom: targetToZoom.zoom || 9,
      duration: 1500,
      essential: true
    });
  }, [targetToZoom, mapLoaded]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
};
