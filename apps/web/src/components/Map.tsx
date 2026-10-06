"use client";

import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { RasterLayerType, BufferAnalysisResult } from "../types";
import {
  Search,
  Compass,
  MapPin,
  Layers,
  Sparkles,
  Flame,
  Waves,
  Eye,
  Crosshair,
  RotateCcw,
  X,
  Target,
  ChevronRight,
  TrendingUp,
  Award,
  Maximize2,
  CheckCircle2,
  Copy,
  Zap
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MapProps {
  activeRasterLayer: RasterLayerType;
  rasterOpacity: number;
  showZones: boolean;
  showDeposits: boolean;
  showIndicios?: boolean;
  indicioFilter?: "todos" | "roca" | "aluvial";
  showDistricts?: boolean;
  baseMap: "dark" | "street" | "satellite";
  onSelectCoordinate: (lat: number, lon: number) => void;
  selectedCoordinates?: { lat: number; lon: number } | null;
  targetToZoom?: { lon: number; lat: number; zoom?: number } | null;
  bufferToolActive?: boolean;
  setBufferToolActive?: (val: boolean) => void;
  bufferRadiusKm?: number;
  setBufferRadiusKm?: (val: number) => void;
  bufferResult?: BufferAnalysisResult | null;
  onRunBufferAnalysis?: (lat: number, lon: number, radiusKm: number) => void;
  onCloseBufferResult?: () => void;
  onToggleAB?: () => void;
  is3DActive?: boolean;
  onToggle3D?: () => void;
}

// Directorio de búsqueda rápida integrado de distritos y yacimientos
const SEARCHABLE_LANDMARKS = [
  { name: "El Valle-Boinás (Belmonte, Asturias)", type: "Mina Primaria", lon: -6.25, lat: 43.32, zoom: 11, desc: "Skarn Au-Cu cámbrico · Mayor productor moderno" },
  { name: "Rodalquilar - El Cinto (Cabo de Gata, Almería)", type: "Mina Epitermal", lon: -2.04, lat: 36.85, zoom: 11.5, desc: "Epitermal alta sulfuración · Caldera volcánica" },
  { name: "Las Médulas (El Bierzo, León)", type: "Paleoplacer Aluvial", lon: -6.76, lat: 42.46, zoom: 11, desc: "Mayor explotación aurífera del Imperio Romano" },
  { name: "Salave (Tapia de Casariego, Asturias)", type: "IRGS Intrusivo", lon: -6.90, lat: 43.56, zoom: 11.5, desc: "Granodiorita Au-As-Sb · ~1.5 Moz Au" },
  { name: "Corcoesto (Costa da Morte, Galicia)", type: "Cizalla Dúctil", lon: -8.76, lat: 43.19, zoom: 11, desc: "Vetas cuarzo-arsenopirita en cizalla hercínica" },
  { name: "La Oriental (La Jara, Montes de Toledo)", type: "Filones Paleozoicos", lon: -5.05, lat: 39.60, zoom: 10.5, desc: "Metasedimentos del Domo Extremeño / Cámbrico" },
  { name: "Aguablanca (Monesterio, Badajoz)", type: "Brecha Magmática", lon: -6.21, lat: 38.05, zoom: 11, desc: "Sulfuros masivos Ni-Cu-(PGE-Au) en gabros" },
  { name: "California Granadina (Río Darro, Granada)", type: "Placer Aluvial", lon: -3.52, lat: 37.24, zoom: 11, desc: "Abanicos aluviales miocenos del Río Darro" },
  { name: "Cinturón del Narcea (Asturias)", type: "Distrito Metalogénico", lon: -6.27, lat: 43.31, zoom: 10, desc: "Cizalla tectónica del Narcea y calizas de Láncara" },
  { name: "Cuenca del Sil - El Bierzo (León)", type: "Distrito Metalogénico", lon: -6.70, lat: 42.48, zoom: 9.8, desc: "Cuenca aluvial terciaria y zócalo cantábrico" },
  { name: "Cabo de Gata (Almería)", type: "Distrito Metalogénico", lon: -2.06, lat: 36.86, zoom: 10.5, desc: "Complejo volcánico neógeno calcoalcalino" },
  { name: "Montes de Toledo (Toledo / C. Real)", type: "Distrito Metalogénico", lon: -4.50, lat: 39.55, zoom: 9.5, desc: "Anticlinales hercínicos y series del Alcudiense" },
  { name: "Zona de Ossa-Morena (Badajoz / Huelva)", type: "Distrito Metalogénico", lon: -6.50, lat: 38.20, zoom: 9.5, desc: "Plutonismo y suturas orogénicas hercínicas" },
  { name: "Costa da Morte / Ordes (Galicia)", type: "Distrito Metalogénico", lon: -8.70, lat: 43.15, zoom: 9.8, desc: "Complejo esquisto-metamórfico de Galicia Occidental" }
];

type MapLibreModule = typeof import("maplibre-gl");

// Fórmula matemática para generar polígonos circulares geodésicos en WGS84
function createGeoJSONCircle(center: [number, number], radiusInKm: number, points: number = 64) {
  const coords: [number, number][] = [];
  const distanceX = radiusInKm / (111.32 * Math.cos((center[1] * Math.PI) / 180));
  const distanceY = radiusInKm / 110.574;

  for (let i = 0; i < points; i++) {
    const theta = (i / points) * (2 * Math.PI);
    const x = distanceX * Math.cos(theta);
    const y = distanceY * Math.sin(theta);
    coords.push([center[0] + x, center[1] + y]);
  }
  coords.push(coords[0]);

  return {
    type: "Feature",
    geometry: {
      type: "Polygon",
      coordinates: [coords]
    },
    properties: {}
  };
}

export const Map: React.FC<MapProps> = ({
  activeRasterLayer,
  rasterOpacity,
  showZones,
  showDeposits,
  showIndicios = true,
  indicioFilter = "todos",
  showDistricts = true,
  baseMap,
  onSelectCoordinate,
  selectedCoordinates,
  targetToZoom,
  bufferToolActive = false,
  setBufferToolActive,
  bufferRadiusKm = 10,
  setBufferRadiusKm,
  bufferResult,
  onRunBufferAnalysis,
  onCloseBufferResult,
  onToggleAB,
  is3DActive,
  onToggle3D
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const clickMarker = useRef<any>(null);
  const bufferCenterMarker = useRef<any>(null);
  const mlRef = useRef<MapLibreModule | null>(null);

  // Estados interactivos del HUD y buscador
  const [cursorCoords, setCursorCoords] = useState<{ lon: number; lat: number } | null>(null);
  const [currentZoom, setCurrentZoom] = useState<number>(5.7);
  const [currentPitch, setCurrentPitch] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [hudCopied, setHudCopied] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Atajo de teclado: pulsar "/" para activar buscador rápidamente
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "TEXTAREA") {
        e.preventDefault();
        searchInputRef.current?.focus();
        setSearchOpen(true);
      } else if (e.key === "Escape") {
        setSearchOpen(false);
        searchInputRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Callbacks estables
  const onSelectRef = useRef(onSelectCoordinate);
  onSelectRef.current = onSelectCoordinate;

  const onBufferRunRef = useRef(onRunBufferAnalysis);
  onBufferRunRef.current = onRunBufferAnalysis;

  // Filtrar resultados de búsqueda
  const filteredSearchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase().trim();
    return SEARCHABLE_LANDMARKS.filter(
      (item) => item.name.toLowerCase().includes(q) || item.desc.toLowerCase().includes(q)
    );
  }, [searchQuery]);

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

    // B. Fuente y capa vectorial de Zonas de Prospectividad (1.529 Polígonos)
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
            "prioridad_muy_alta_top01", "#ef4444",
            "prioridad_alta_top05", "#f59e0b",
            "#10b981"
          ],
          "fill-opacity": 0.28
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
            "prioridad_muy_alta_top01", "#fca5a5",
            "prioridad_alta_top05", "#fde68a",
            "#6ee7b7"
          ],
          "line-width": 1.5,
          "line-opacity": 0.85
        }
      });

      // Hover y click en zona de prospectividad
      m.on("mouseenter", "zones_fill", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "zones_fill", () => {
        m.getCanvas().style.cursor = "";
      });

      m.on("click", "zones_fill", (e: any) => {
        if (!e.features || !e.features[0] || !mlRef.current) return;
        const props = e.features[0].properties;
        new mlRef.current.Popup({ offset: 12, className: "geoai-popup" })
          .setLngLat(e.lngLat)
          .setHTML(
            `<div class="p-2.5 font-sans text-xs bg-slate-950/95 text-slate-100 rounded-xl border border-slate-700 shadow-2xl backdrop-blur-xl">
              <div class="flex items-center justify-between gap-2 border-b border-slate-800 pb-1.5 mb-1.5">
                <span class="font-black text-amber-400 font-mono text-xs uppercase">${props.zona_id || "Zona"}</span>
                <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">Rank #${props.ranking_nacional || "N/A"}</span>
              </div>
              <p class="text-slate-200 font-semibold">${props.denominacion || "Zona de Prospectividad"}</p>
              <div class="grid grid-cols-2 gap-1.5 my-1.5 text-[11px] font-mono">
                <div class="bg-slate-900 p-1.5 rounded border border-slate-800">
                  <span class="text-[9px] text-slate-400 block">Área</span>
                  <span class="font-bold text-slate-100">${props.area_km2 || 1} km²</span>
                </div>
                <div class="bg-slate-900 p-1.5 rounded border border-slate-800">
                  <span class="text-[9px] text-slate-400 block">Score Máx</span>
                  <span class="font-bold text-emerald-400">${Number(props.score_maximo || 0).toFixed(4)}</span>
                </div>
              </div>
              <p class="text-[10px] text-slate-400">Distrito: <span class="text-cyan-300">${props.distrito_conocido_proximo || "N/A"}</span></p>
            </div>`
          )
          .addTo(m);
      });
    }

    // C. Fuente y capa de 787 Indicios BDMIN Nacional con clustering
    if (!m.getSource("indicios_source")) {
      m.addSource("indicios_source", {
        type: "geojson",
        data: `${API_BASE_URL}/api/indicios`,
        cluster: true,
        clusterMaxZoom: 10,
        clusterRadius: 35
      });

      // C1. Círculo de Clusters
      m.addLayer({
        id: "indicios_clusters",
        type: "circle",
        source: "indicios_source",
        filter: ["has", "point_count"],
        layout: {
          visibility: showIndicios ? "visible" : "none"
        },
        paint: {
          "circle-color": [
            "step",
            ["get", "point_count"],
            "#f59e0b",
            10, "#d97706",
            30, "#b45309"
          ],
          "circle-radius": [
            "step",
            ["get", "point_count"],
            14,
            10, 18,
            30, 24
          ],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
          "circle-opacity": 0.85
        }
      });

      // C2. Conteo del Cluster
      m.addLayer({
        id: "indicios_cluster_count",
        type: "symbol",
        source: "indicios_source",
        filter: ["has", "point_count"],
        layout: {
          visibility: showIndicios ? "visible" : "none",
          "text-field": "{point_count_abbreviated}",
          "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
          "text-size": 11
        },
        paint: {
          "text-color": "#ffffff"
        }
      });

      // C3. Puntos individuales no agrupados (Color según tipo_au)
      m.addLayer({
        id: "indicios_unclustered",
        type: "circle",
        source: "indicios_source",
        filter: ["!", ["has", "point_count"]],
        layout: {
          visibility: showIndicios ? "visible" : "none"
        },
        paint: {
          "circle-color": [
            "match",
            ["get", "tipo_au"],
            "roca", "#f59e0b",
            "aluvial", "#06b6d4",
            "#a855f7"
          ],
          "circle-radius": [
            "interpolate", ["linear"], ["zoom"],
            7, 3.5,
            11, 6,
            14, 9
          ],
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "#020617",
          "circle-opacity": 0.95
        }
      });

      // Click en Cluster: Zoom adentro
      m.on("click", "indicios_clusters", (e: any) => {
        const features = m.queryRenderedFeatures(e.point, { layers: ["indicios_clusters"] });
        const clusterId = features[0].properties.cluster_id;
        m.getSource("indicios_source").getClusterExpansionZoom(clusterId, (err: any, zoom: number) => {
          if (err) return;
          m.easeTo({
            center: features[0].geometry.coordinates,
            zoom: zoom
          });
        });
      });

      // Click en Indicio Individual: Popup geocientífico completo
      m.on("click", "indicios_unclustered", (e: any) => {
        if (!e.features || !e.features[0] || !mlRef.current) return;
        const props = e.features[0].properties;
        const geom = e.features[0].geometry;
        const isRoca = props.tipo_au === "roca";
        const isAluvial = props.tipo_au === "aluvial";

        // Exponer acción para el botón de buffer embebido en el popup HTML
        if (typeof window !== "undefined") {
          (window as any).geoaiRunBuffer = (lat: number, lon: number) => {
            if (onRunBufferAnalysis) {
              onRunBufferAnalysis(lat, lon, bufferRadiusKm || 10);
            }
          };
        }

        new mlRef.current.Popup({ offset: 12, className: "geoai-popup" })
          .setLngLat(geom.coordinates)
          .setHTML(
            `<div class="p-3.5 font-sans text-xs bg-slate-950/98 text-slate-100 rounded-2xl border border-slate-700/80 shadow-2xl backdrop-blur-2xl max-w-xs ring-1 ring-white/10">
              <div class="flex items-center justify-between gap-2 border-b border-slate-800/80 pb-2 mb-2">
                <span class="font-black text-amber-300 uppercase text-xs truncate tracking-wide">${props.nombre_mina || "Indicio Aurífero"}</span>
                <span class="text-[9px] font-mono px-2 py-0.5 rounded font-black tracking-wider uppercase ${
                  isRoca ? "bg-amber-500/20 text-amber-300 border border-amber-500/40" : isAluvial ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40" : "bg-purple-500/20 text-purple-300"
                }">
                  ${isRoca ? "ROCA PRIMARIO" : isAluvial ? "ALUVIAL PLACER" : "INDURADO"}
                </span>
              </div>
              <div class="space-y-1.5 text-slate-300 text-[11px]">
                <p class="flex items-center gap-1.5">
                  <span class="text-cyan-400">📍</span>
                  <span class="text-slate-100 font-semibold">${props.municipio || "N/A"} (${props.provincia || "España"})</span>
                </p>
                <p class="flex items-center gap-1.5">
                  <span class="text-amber-400">⛏️</span>
                  <span>Morfología: <strong class="text-slate-200">${props.morfologia || "Vetas / Placeres"}</strong></span>
                </p>
                <p class="flex items-center gap-1.5 text-slate-400 font-mono text-[10px]">
                  <span>🏷️ BDMIN: ${props.codigo_indicio || props.record_id || "IGME"}</span>
                </p>
                ${props.district_id ? `<p class="flex items-center gap-1.5 text-amber-300 font-mono text-[10px]"><span>🌐</span><span>Distrito: ${props.district_id}</span></p>` : ""}
              </div>
              
              <button
                onclick="if(window.geoaiRunBuffer){window.geoaiRunBuffer(${geom.coordinates[1]}, ${geom.coordinates[0]})}"
                class="w-full mt-3 py-1.5 px-2.5 rounded-xl bg-gradient-to-r from-cyan-950 via-slate-900 to-cyan-950 hover:bg-cyan-900 border border-cyan-500/60 hover:border-cyan-400 text-cyan-300 hover:text-white font-bold text-[10px] font-mono flex items-center justify-center gap-1.5 cursor-pointer transition-all shadow-md shadow-cyan-950/80"
              >
                <span>🎯</span>
                <span>Analizar Buffer de Prospección</span>
              </button>

              <div class="mt-2 pt-2 border-t border-slate-800/80 flex justify-between items-center text-[9px] font-mono text-slate-500">
                <span>${geom.coordinates[1].toFixed(3)}°N, ${geom.coordinates[0].toFixed(3)}°W</span>
                <span class="text-emerald-400 font-bold">BDMIN Auditado</span>
              </div>
            </div>`
          )
          .addTo(m);
      });

      m.on("mouseenter", "indicios_unclustered", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "indicios_unclustered", () => {
        m.getCanvas().style.cursor = "";
      });
      m.on("mouseenter", "indicios_clusters", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "indicios_clusters", () => {
        m.getCanvas().style.cursor = "";
      });
    }

    // D. Fuente y capa de 32 Distritos Metalogénicos
    if (!m.getSource("districts_source")) {
      m.addSource("districts_source", {
        type: "geojson",
        data: `${API_BASE_URL}/api/districts`
      });

      m.addLayer({
        id: "districts_labels",
        type: "symbol",
        source: "districts_source",
        minzoom: 6.5,
        layout: {
          visibility: showDistricts ? "visible" : "none",
          "text-field": ["get", "nombre"],
          "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
          "text-size": 11,
          "text-offset": [0, 1.2],
          "text-anchor": "top"
        },
        paint: {
          "text-color": "#38bdf8",
          "text-halo-color": "#020617",
          "text-halo-width": 2
        }
      });

      m.addLayer({
        id: "districts_points",
        type: "circle",
        source: "districts_source",
        minzoom: 6.5,
        layout: {
          visibility: showDistricts ? "visible" : "none"
        },
        paint: {
          "circle-color": "#38bdf8",
          "circle-radius": 4,
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1.5
        }
      });

      m.on("click", "districts_points", (e: any) => {
        if (!e.features || !e.features[0] || !mlRef.current) return;
        const p = e.features[0].properties;
        const geom = e.features[0].geometry;
        m.flyTo({ center: geom.coordinates, zoom: 10, duration: 1200 });
      });

      m.on("mouseenter", "districts_points", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "districts_points", () => {
        m.getCanvas().style.cursor = "";
      });
    }

    // E. Fuente y capa de Depósitos Confirmados Canónicos (46)
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
          "circle-color": "#FBBF24",
          "circle-radius": [
            "interpolate", ["linear"], ["zoom"],
            5, 4,
            8, 6,
            12, 8.5
          ],
          "circle-stroke-color": "#020617",
          "circle-stroke-width": 1.8,
          "circle-opacity": 0.95
        }
      });

      m.on("click", "deposits_circle", (e: any) => {
        if (!e.features || !e.features[0] || !mlRef.current) return;
        const props = e.features[0].properties;
        const geom = e.features[0].geometry as any;
        new mlRef.current.Popup({ offset: 10, className: "geoai-popup" })
          .setLngLat(geom.coordinates)
          .setHTML(
            `<div class="p-2.5 font-sans text-xs bg-slate-950 text-slate-100 rounded-xl border border-amber-500/50 shadow-2xl">
              <p class="font-black text-amber-400 uppercase text-xs">${props.nombre_mina || props.deposit_id || "Depósito"}</p>
              <p class="text-slate-300 text-[11px] mt-0.5">Distrito: <span class="text-cyan-300 font-mono">${props.district_id || "N/A"}</span></p>
              <p class="text-slate-300 text-[11px]">Tipo Au: <span class="text-emerald-400 capitalize font-bold">${props.tipo_au || "N/A"}</span></p>
              <p class="text-slate-400 text-[10px] mt-1">Indicios auditados en grupo: ${props.records_count || 1}</p>
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

    // F. Fuente y capa para el Círculo de Análisis por Radio (Buffer Tool)
    if (!m.getSource("buffer_circle_source")) {
      m.addSource("buffer_circle_source", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] }
      });

      m.addLayer({
        id: "buffer_circle_fill",
        type: "fill",
        source: "buffer_circle_source",
        paint: {
          "fill-color": "#06b6d4",
          "fill-opacity": 0.18
        }
      });

      m.addLayer({
        id: "buffer_circle_outline",
        type: "line",
        source: "buffer_circle_source",
        paint: {
          "line-color": "#22d3ee",
          "line-width": 2.2,
          "line-dasharray": [3, 2]
        }
      });
    }
  }, []);

  // 3. Inicializar mapa (carga dinámica de MapLibre para evitar SSR)
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    let cancelled = false;

    async function initMap() {
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
        zoom: 5.8,
        minZoom: 4.5,
        maxZoom: 15,
        pitch: 0,
        bearing: 0,
        attributionControl: false
      });

      // Controles de navegación y escala métrica
      m.addControl(new maplibregl.NavigationControl({ showCompass: true, showZoom: true }), "bottom-right");
      m.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }), "bottom-left");

      m.on("load", () => {
        if (cancelled) return;
        map.current = m;
        setMapLoaded(true);
        setupLayers(m, activeRasterLayer);
      });

      // Tracking de coordenadas bajo el cursor en tiempo real (throttled a ~25fps para máximo rendimiento WebGL)
      let lastMoveTime = 0;
      m.on("mousemove", (e: any) => {
        const now = performance.now();
        if (now - lastMoveTime > 40) {
          lastMoveTime = now;
          setCursorCoords({ lon: e.lngLat.lng, lat: e.lngLat.lat });
        }
      });

      // Tracking de zoom y pitch
      m.on("zoom", () => {
        setCurrentZoom(m.getZoom());
      });

      m.on("pitch", () => {
        setCurrentPitch(m.getPitch());
      });

      // Manejador de clic general sobre el mapa
      m.on("click", (e: any) => {
        const { lng, lat } = e.lngLat;
        if (bufferToolActive && onBufferRunRef.current) {
          onBufferRunRef.current(lat, lng, bufferRadiusKm);
        } else {
          onSelectRef.current(lat, lng);
        }
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

    if (m.getLayer("indicios_clusters")) {
      m.setLayoutProperty("indicios_clusters", "visibility", showIndicios ? "visible" : "none");
      m.setLayoutProperty("indicios_cluster_count", "visibility", showIndicios ? "visible" : "none");
      m.setLayoutProperty("indicios_unclustered", "visibility", showIndicios ? "visible" : "none");
    }

    if (m.getLayer("districts_labels")) {
      m.setLayoutProperty("districts_labels", "visibility", showDistricts ? "visible" : "none");
      m.setLayoutProperty("districts_points", "visibility", showDistricts ? "visible" : "none");
    }
  }, [showZones, showDeposits, showIndicios, showDistricts, mapLoaded]);

  // 7. Filtro de tipo en los indicios (Roca / Aluvial)
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    const m = map.current;
    const source = m.getSource("indicios_source") as any;
    if (source) {
      const url = indicioFilter && indicioFilter !== "todos"
        ? `${API_BASE_URL}/api/indicios?tipo_au=${encodeURIComponent(indicioFilter)}`
        : `${API_BASE_URL}/api/indicios`;
      source.setData(url);
    }
  }, [indicioFilter, mapLoaded]);

  // 8. Actualizar Círculo del Buffer cuando hay resultado de análisis espacial
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    const m = map.current;
    const source = m.getSource("buffer_circle_source") as any;

    if (bufferResult && bufferResult.center) {
      const circleGeoJSON = createGeoJSONCircle(
        [bufferResult.center.lon, bufferResult.center.lat],
        bufferResult.radius_km
      );
      if (source) source.setData(circleGeoJSON);
    } else if (source) {
      source.setData({ type: "FeatureCollection", features: [] });
    }
  }, [bufferResult, mapLoaded]);

  // 9. Marcador interactivo de celda seleccionada (preciso, estático e instantáneo sin transiciones deslizantes)
  useEffect(() => {
    if (!map.current || !mapLoaded || !mlRef.current) return;

    // Eliminar siempre el marcador anterior para que NUNCA se deslice de un punto a otro
    if (clickMarker.current) {
      clickMarker.current.remove();
      clickMarker.current = null;
    }

    if (selectedCoordinates) {
      const el = document.createElement("div");
      el.className = "geoai-reticle-marker pointer-events-none";
      el.innerHTML = `
        <div style="position: relative; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; pointer-events: none;">
          <span style="position: absolute; width: 26px; height: 26px; border-radius: 50%; border: 2px solid #22d3ee; background-color: rgba(6, 182, 212, 0.15); box-shadow: 0 0 10px rgba(6, 182, 212, 0.7);"></span>
          <span style="position: absolute; width: 32px; height: 1.5px; background-color: rgba(34, 211, 238, 0.8);"></span>
          <span style="position: absolute; width: 1.5px; height: 32px; background-color: rgba(34, 211, 238, 0.8);"></span>
          <span style="width: 6px; height: 6px; border-radius: 50%; background-color: #ffffff; box-shadow: 0 0 6px #ffffff; z-index: 2;"></span>
        </div>
      `;

      clickMarker.current = new mlRef.current.Marker({ element: el, anchor: "center" })
        .setLngLat([selectedCoordinates.lon, selectedCoordinates.lat])
        .addTo(map.current);
    }
  }, [selectedCoordinates, mapLoaded]);

  // 10. Zoom suave a target específico
  useEffect(() => {
    if (!map.current || !mapLoaded || !targetToZoom) return;
    map.current.flyTo({
      center: [targetToZoom.lon, targetToZoom.lat],
      zoom: targetToZoom.zoom || 10,
      duration: 1500,
      essential: true
    });
  }, [targetToZoom, mapLoaded]);

  // Sincronizar estado 3D externo
  useEffect(() => {
    if (!map.current || !mapLoaded || is3DActive === undefined) return;
    const pitch = map.current.getPitch();
    if (is3DActive && pitch < 10) {
      map.current.easeTo({ pitch: 60, bearing: -20, duration: 1000 });
    } else if (!is3DActive && pitch > 10) {
      map.current.easeTo({ pitch: 0, bearing: 0, duration: 1000 });
    }
  }, [is3DActive, mapLoaded]);

  // Función para alternar vista 3D / 2D
  const toggle3D = () => {
    if (!map.current) return;
    const pitch = map.current.getPitch();
    if (pitch > 10) {
      map.current.easeTo({ pitch: 0, bearing: 0, duration: 1000 });
    } else {
      map.current.easeTo({ pitch: 60, bearing: -20, duration: 1000 });
    }
    onToggle3D?.();
  };

  return (
    <div className="relative w-full h-full select-none overflow-hidden font-sans">
      {/* Contenedor MapLibre GL */}
      <div
        ref={mapContainer}
        className={`w-full h-full relative transition-colors ${
          bufferToolActive ? "cursor-crosshair" : ""
        }`}
      />

      {/* ================================================================= */}
      {/* BARRA SUPERIOR FLOTANTE: BUSCADOR & ACCESOS DIRECTOS A FAJAS */}
      {/* ================================================================= */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 lg:left-[calc(50%-7rem)] xl:left-[calc(50%-8.5rem)] z-20 flex flex-col items-center gap-2 max-w-xl xl:max-w-2xl w-[92vw]">
        <div className="flex items-center gap-1.5 w-full bg-slate-950/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-1.5 shadow-2xl">
          {/* Campo de Búsqueda Rápida */}
          <div className="relative flex-1 flex items-center">
            <Search className="w-4 h-4 text-cyan-400 absolute left-3 pointer-events-none" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setSearchOpen(true);
              }}
              onFocus={() => setSearchOpen(true)}
              placeholder="Buscar mina o cinturón (ej: Boinás, Médulas, Rodalquilar, Salave...)"
              className="w-full pl-9 pr-14 py-1.5 rounded-xl bg-slate-900/90 text-xs text-slate-100 placeholder-slate-500 border border-slate-800 focus:outline-none focus:border-cyan-400 transition-all font-sans"
            />
            <div className="absolute right-3 flex items-center gap-1.5 pointer-events-none">
              <span className="hidden sm:inline-block text-[9px] font-mono text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded border border-slate-700/60">
                /
              </span>
            </div>
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery("");
                  setSearchOpen(false);
                }}
                className="absolute right-9 text-slate-400 hover:text-white"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}

            {/* Dropdown de Resultados de Búsqueda */}
            {searchOpen && filteredSearchResults.length > 0 && (
              <div
                className="absolute top-11 left-0 w-full bg-slate-900/98 backdrop-blur-2xl border border-slate-700 rounded-xl shadow-2xl max-h-72 overflow-y-auto py-1 z-50 text-xs animate-in fade-in duration-150"
                onMouseLeave={() => setSearchOpen(false)}
              >
                <div className="px-3 py-1 text-[10px] font-mono text-slate-400 uppercase border-b border-slate-800">
                  Resultados Encontrados ({filteredSearchResults.length})
                </div>
                {filteredSearchResults.map((item) => (
                  <button
                    key={item.name}
                    onClick={() => {
                      if (map.current) {
                        map.current.flyTo({ center: [item.lon, item.lat], zoom: item.zoom, duration: 1500 });
                      }
                      setSearchOpen(false);
                      setSearchQuery("");
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-cyan-950/70 hover:text-cyan-200 transition-colors flex items-start justify-between gap-2 border-b border-slate-800/40 last:border-none cursor-pointer"
                  >
                    <div>
                      <span className="font-bold text-slate-100 block text-xs">{item.name}</span>
                      <span className="text-[10px] text-slate-400">{item.desc}</span>
                    </div>
                    <span className="text-[9px] font-mono bg-cyan-950 text-cyan-400 px-1.5 py-0.5 rounded border border-cyan-800/60 shrink-0">
                      {item.type}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Botón de Perspectiva 3D */}
          <button
            onClick={toggle3D}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold font-mono flex items-center gap-1.5 transition-all cursor-pointer shrink-0 ${
              currentPitch > 10
                ? "bg-amber-500 text-slate-950 border-amber-400 shadow-lg shadow-amber-500/20 font-black"
                : "bg-slate-900 text-slate-300 border-slate-800 hover:text-amber-400 hover:border-slate-700"
            }`}
            title="Alternar vista topográfica 3D / 2D con relieve e inclinación de cámara"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>{currentPitch > 10 ? "3D Activo" : "Vista 3D"}</span>
          </button>

          {/* Botón Herramienta de Radio (Buffer Tool) */}
          {setBufferToolActive && (
            <button
              onClick={() => setBufferToolActive(!bufferToolActive)}
              className={`px-3 py-1.5 rounded-xl border text-xs font-bold font-mono flex items-center gap-1.5 transition-all cursor-pointer shrink-0 ${
                bufferToolActive
                  ? "bg-cyan-500 text-slate-950 border-cyan-400 shadow-lg shadow-cyan-500/30 font-black animate-pulse"
                  : "bg-slate-900 text-slate-300 border-slate-800 hover:text-cyan-400 hover:border-slate-700"
              }`}
              title="Activar herramienta de análisis en radio de 10 km alrededor de cualquier clic"
            >
              <Target className="w-3.5 h-3.5" />
              <span>{bufferToolActive ? "Radio ON" : "Buffer"}</span>
            </button>
          )}
        </div>

        {/* Fajas y Distritos Rápidos (Pills Flotantes) */}
        <div className="flex items-center gap-1.5 overflow-x-auto max-w-full py-0.5 scrollbar-none">
          {[
            { label: "🇪🇸 Península", lon: -3.7, lat: 40.0, zoom: 5.8 },
            { label: "⛰️ Narcea", lon: -6.25, lat: 43.32, zoom: 11 },
            { label: "🌲 Galicia", lon: -8.76, lat: 43.19, zoom: 10.5 },
            { label: "⛏️ El Bierzo", lon: -6.76, lat: 42.46, zoom: 10.8 },
            { label: "🌋 Cabo de Gata", lon: -2.04, lat: 36.85, zoom: 11.2 },
            { label: "🏞️ Toledo", lon: -5.05, lat: 39.60, zoom: 10 },
            { label: "🏜️ Ossa-Morena", lon: -6.21, lat: 38.05, zoom: 10.5 }
          ].map((d) => (
            <button
              key={d.label}
              onClick={() => {
                if (map.current) {
                  map.current.flyTo({ center: [d.lon, d.lat], zoom: d.zoom, duration: 1200 });
                }
              }}
              className="px-2.5 py-1 rounded-full bg-slate-950/80 hover:bg-slate-900 text-slate-300 hover:text-amber-300 border border-slate-800/90 hover:border-amber-400/40 text-[10px] font-mono whitespace-nowrap shadow-md transition-all cursor-pointer backdrop-blur-md"
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>

      {/* ================================================================= */}
      {/* TARJETA FLOTANTE DE RESULTADOS DEL BUFFER ESPACIAL */}
      {/* ================================================================= */}
      {bufferResult && (
        <div className="absolute top-20 right-4 z-30 w-80 max-h-[75vh] overflow-y-auto bg-slate-950/95 backdrop-blur-2xl border border-cyan-500/50 rounded-2xl p-4 shadow-2xl text-xs text-slate-200 animate-in fade-in slide-in-from-right-4 duration-200">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800 mb-2.5">
            <div className="flex items-center gap-1.5 text-cyan-400 font-bold text-xs uppercase tracking-wider">
              <Target className="w-4 h-4 animate-spin text-cyan-400" />
              <span>Análisis por Radio ({bufferResult.radius_km} km)</span>
            </div>
            {onCloseBufferResult && (
              <button
                onClick={onCloseBufferResult}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="space-y-3 font-sans">
            {/* Cabecera de Categoría */}
            <div className="p-2.5 rounded-xl bg-cyan-950/50 border border-cyan-800/60">
              <span className="text-[10px] text-cyan-300 uppercase font-mono block">Categoría de Favorabilidad</span>
              <span className="text-sm font-black text-white">{bufferResult.prospectivity_tier}</span>
              {bufferResult.nearest_district && (
                <span className="text-[11px] text-slate-300 block mt-1">
                  Distrito: <strong className="text-amber-300">{bufferResult.nearest_district.nombre}</strong> ({bufferResult.nearest_district.distance_km} km)
                </span>
              )}
            </div>

            {/* 3 Métricas Cuantitativas */}
            <div className="grid grid-cols-3 gap-1.5 text-center font-mono">
              <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[9px] text-slate-400 block">Indicios</span>
                <span className="text-base font-black text-amber-400">{bufferResult.indicios_count}</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[9px] text-slate-400 block">Score Máx</span>
                <span className="text-base font-black text-emerald-400">{bufferResult.max_score.toFixed(3)}</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[9px] text-slate-400 block">Score Med.</span>
                <span className="text-base font-black text-cyan-400">{bufferResult.mean_score.toFixed(3)}</span>
              </div>
            </div>

            {/* Desglose Roca vs Aluvial */}
            <div className="flex items-center justify-between text-[11px] font-mono bg-slate-900/80 p-2 rounded-lg border border-slate-800">
              <span className="text-amber-300 flex items-center gap-1">
                <Flame className="w-3 h-3 text-amber-400" /> {bufferResult.indicios_roca} en Roca
              </span>
              <span className="text-cyan-300 flex items-center gap-1">
                <Waves className="w-3 h-3 text-cyan-400" /> {bufferResult.indicios_aluvial} Aluviales
              </span>
            </div>

            {/* Lista de Minas dentro del Radio */}
            {bufferResult.indicios && bufferResult.indicios.length > 0 && (
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-mono block mb-1 font-bold">
                  Yacimientos en el Radio ({bufferResult.indicios.length})
                </span>
                <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                  {bufferResult.indicios.map((ind, idx) => (
                    <div
                      key={idx}
                      onClick={() => {
                        if (map.current) {
                          map.current.flyTo({ center: [ind.lon, ind.lat], zoom: 12, duration: 1000 });
                        }
                      }}
                      className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800/80 hover:border-cyan-500/50 flex items-center justify-between text-[11px] transition-colors cursor-pointer"
                    >
                      <span className="font-semibold text-slate-200 truncate pr-2" title={ind.nombre_mina}>
                        {ind.nombre_mina}
                      </span>
                      <span className="text-[10px] font-mono text-cyan-400 shrink-0">
                        {ind.distance_km} km
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================================================================= */}
      {/* HUD INFERIOR: COORDENADAS WGS84 / EPSG:25830 + ZOOM + ESCALA */}
      {/* ================================================================= */}
      <div 
        onClick={() => {
          if (cursorCoords) {
            navigator.clipboard.writeText(`${cursorCoords.lat.toFixed(6)}, ${cursorCoords.lon.toFixed(6)}`);
            setHudCopied(true);
            setTimeout(() => setHudCopied(false), 2000);
          }
        }}
        className="absolute bottom-2 left-1/2 -translate-x-1/2 z-20 hidden md:flex items-center gap-3 px-3.5 py-1.5 rounded-full bg-slate-950/90 backdrop-blur-md border border-slate-800 hover:border-cyan-500/50 text-[10px] font-mono text-slate-400 shadow-2xl select-none cursor-pointer transition-all hover:bg-slate-900 group"
        title="Clic para copiar coordenadas WGS84 al portapapeles"
      >
        {hudCopied ? (
          <span className="text-emerald-400 font-bold flex items-center gap-1.5 animate-pulse">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>¡Coordenadas copiadas! ({cursorCoords?.lat.toFixed(4)}°, {cursorCoords?.lon.toFixed(4)}°)</span>
          </span>
        ) : cursorCoords ? (
          <>
            <span className="text-slate-300 flex items-center gap-1">
              WGS84: <strong className="text-cyan-300">{cursorCoords.lat.toFixed(4)}°N</strong>,{" "}
              <strong className="text-cyan-300">{Math.abs(cursorCoords.lon).toFixed(4)}°W</strong>
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">
              Zoom: <strong className="text-slate-200">{currentZoom.toFixed(1)}</strong>
            </span>
            {currentPitch > 0 && (
              <>
                <span className="text-slate-600">|</span>
                <span className="text-amber-400 font-bold">Pitch 3D: {Math.round(currentPitch)}°</span>
              </>
            )}
            <span className="text-[9px] text-slate-500 group-hover:text-cyan-300 flex items-center gap-0.5 ml-1 transition-colors">
              <Copy className="w-3 h-3" /> Copiar
            </span>
          </>
        ) : (
          <span>Mueve el cursor para rastrear coordenadas UTM ETRS89 y WGS84</span>
        )}
      </div>
    </div>
  );
};
