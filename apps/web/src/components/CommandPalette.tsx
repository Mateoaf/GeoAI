"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Search,
  Sparkles,
  Flame,
  Waves,
  Globe2,
  Layers,
  MapPin,
  Compass,
  Target,
  Bot,
  BarChart3,
  ShieldCheck,
  Command,
  ArrowRight,
  Maximize2,
  X,
  Satellite,
  Moon,
  Sun,
  ChevronRight
} from "lucide-react";
import { RasterLayerType } from "../types";

export interface CommandItem {
  id: string;
  title: string;
  subtitle: string;
  category: "Modelos" | "Distritos" | "Minas" | "Herramientas" | "Vistas";
  icon: React.ReactNode;
  badge?: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRasterLayer: (layer: RasterLayerType) => void;
  onZoomTo: (target: { lon: number; lat: number; zoom?: number }) => void;
  onOpenTab: (tab: "explain" | "targets" | "validation" | "copilot") => void;
  onOpenMethodology: () => void;
  onToggle3D: () => void;
  onToggleBuffer: () => void;
  onSetBaseMap: (map: "dark" | "street" | "satellite") => void;
  onSwitchView: (view: "map" | "dashboard") => void;
  onShowToast?: (msg: string) => void;
  theme?: "dark" | "light";
  onToggleTheme?: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectRasterLayer,
  onZoomTo,
  onOpenTab,
  onOpenMethodology,
  onToggle3D,
  onToggleBuffer,
  onSetBaseMap,
  onSwitchView,
  onShowToast,
  theme = "dark",
  onToggleTheme
}) => {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Lista completa de comandos disponibles
  const commands: CommandItem[] = [
    // Modelos
    {
      id: "mod_v3_pu",
      title: "Cargar Motor GeoAI v3.0 (Producción)",
      subtitle: "Positive-Unlabeled bagging calibrado · Susceptibilidad Minera Oficial",
      category: "Modelos",
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
      badge: "v3.0 Oficial",
      action: () => {
        onSelectRasterLayer("v3_pu_score");
        onSwitchView("map");
        onShowToast?.("🎯 Capa activa: Motor Oficial GeoAI v3.0 (Producción)");
        onClose();
      }
    },
    {
      id: "mod_v3_uncertainty",
      title: "Cargar Fiabilidad e Incertidumbre v3.0",
      subtitle: "Desviación estándar y detección de extrapolación fuera de dominio",
      category: "Modelos",
      icon: <Sparkles className="w-4 h-4 text-amber-400" />,
      badge: "Incertidumbre",
      action: () => {
        onSelectRasterLayer("v3_uncertainty");
        onSwitchView("map");
        onShowToast?.("🛡️ Capa activa: Incertidumbre y Fiabilidad v3.0");
        onClose();
      }
    },
    {
      id: "mod_rock",
      title: "Cargar Modelo Oro en Roca v2",
      subtitle: "Vetas primarias hercínicas y skarns · LightGBM (ROC 0.976)",
      category: "Modelos",
      icon: <Flame className="w-4 h-4 text-amber-400" />,
      badge: "ROC 0.976",
      action: () => {
        onSelectRasterLayer("rock_score");
        onSwitchView("map");
        onShowToast?.("🔥 Capa activa: Oro en Roca v2 (LightGBM)");
        onClose();
      }
    },
    {
      id: "mod_alluvial",
      title: "Cargar Modelo Oro Aluvial v2",
      subtitle: "Placeres fluviales, abanicos y terrazas cenozoicas (ROC 0.951)",
      category: "Modelos",
      icon: <Waves className="w-4 h-4 text-cyan-400" />,
      badge: "ROC 0.951",
      action: () => {
        onSelectRasterLayer("alluvial_score");
        onSwitchView("map");
        onShowToast?.("🌊 Capa activa: Oro Aluvial v2 (LightGBM)");
        onClose();
      }
    },
    {
      id: "mod_global",
      title: "Cargar Modelo Ensamble Global v2",
      subtitle: "Integración de 787 indicios y 56 covariables (ROC 0.966)",
      category: "Modelos",
      icon: <Globe2 className="w-4 h-4 text-emerald-400" />,
      badge: "ROC 0.966",
      action: () => {
        onSelectRasterLayer("global_v2_score");
        onSwitchView("map");
        onShowToast?.("🌐 Capa activa: Ensamble Global v2");
        onClose();
      }
    },
    {
      id: "mod_priority",
      title: "Cargar Bandas Prioritarias Top 1%, 5%, 10%",
      subtitle: "Clasificación territorial en macro-clusters conexos (Fase H)",
      category: "Modelos",
      icon: <Layers className="w-4 h-4 text-rose-400" />,
      badge: "754 Clusters",
      action: () => {
        onSelectRasterLayer("priority");
        onSwitchView("map");
        onShowToast?.("🎯 Capa activa: Bandas Prioritarias Top 1%, 5%, 10%");
        onClose();
      }
    },
    {
      id: "mod_v1",
      title: "Cargar Línea Base Histórica v1.0",
      subtitle: "Regresión Logística L2 de referencia científica y benchmark (190 confirmados)",
      category: "Modelos",
      icon: <BarChart3 className="w-4 h-4 text-slate-300" />,
      badge: "v1.0 Base",
      action: () => {
        onSelectRasterLayer("score");
        onSwitchView("map");
        onShowToast?.("📐 Capa activa: Línea Base Histórica v1.0 (Auditado)");
        onClose();
      }
    },

    // Distritos
    {
      id: "dist_narcea",
      title: "Volar a Cinturón del Narcea (Asturias)",
      subtitle: "Calizas de Láncara y Cizalla del Narcea · Mayor distrito moderno",
      category: "Distritos",
      icon: <Compass className="w-4 h-4 text-cyan-400" />,
      badge: "Asturias",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -6.25, lat: 43.32, zoom: 11 });
        onShowToast?.("✈️ Navegando al Cinturón del Narcea");
        onClose();
      }
    },
    {
      id: "dist_bierzo",
      title: "Volar a Cuenca del Sil / El Bierzo (León)",
      subtitle: "Placeres aluviales gigantes e infraestructura histórica romana",
      category: "Distritos",
      icon: <Compass className="w-4 h-4 text-cyan-400" />,
      badge: "León",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -6.76, lat: 42.46, zoom: 10.8 });
        onShowToast?.("✈️ Navegando a El Bierzo");
        onClose();
      }
    },
    {
      id: "dist_gata",
      title: "Volar a Cabo de Gata (Almería)",
      subtitle: "Caldera volcánica neógena calcoalcalina · Yacimiento de Rodalquilar",
      category: "Distritos",
      icon: <Compass className="w-4 h-4 text-cyan-400" />,
      badge: "Almería",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -2.04, lat: 36.85, zoom: 11.2 });
        onShowToast?.("✈️ Navegando a Cabo de Gata");
        onClose();
      }
    },
    {
      id: "dist_galicia",
      title: "Volar a Costa da Morte / Carballo (Galicia)",
      subtitle: "Vetas de cuarzo-arsenopirita en cizalla hercínica",
      category: "Distritos",
      icon: <Compass className="w-4 h-4 text-cyan-400" />,
      badge: "A Coruña",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -8.76, lat: 43.19, zoom: 10.5 });
        onShowToast?.("✈️ Navegando a Galicia");
        onClose();
      }
    },
    {
      id: "dist_toledo",
      title: "Volar a Montes de Toledo / La Jara",
      subtitle: "Metasedimentos del Domo Extremeño y zócalo paleozoico",
      category: "Distritos",
      icon: <Compass className="w-4 h-4 text-cyan-400" />,
      badge: "Toledo",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -5.05, lat: 39.60, zoom: 10 });
        onShowToast?.("✈️ Navegando a Montes de Toledo");
        onClose();
      }
    },
    {
      id: "dist_ossa",
      title: "Volar a Ossa-Morena / Monesterio (Badajoz)",
      subtitle: "Brechas magmáticas y sulfuros masivos Ni-Cu-(PGE-Au)",
      category: "Distritos",
      icon: <Compass className="w-4 h-4 text-cyan-400" />,
      badge: "Badajoz",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -6.21, lat: 38.05, zoom: 10.5 });
        onShowToast?.("✈️ Navegando a Ossa-Morena");
        onClose();
      }
    },

    // Minas Emblemáticas
    {
      id: "mina_boinas",
      title: "Mina El Valle-Boinás (Belmonte de Miranda)",
      subtitle: "Skarn Au-Cu orogénico cámbrico · Producción moderna",
      category: "Minas",
      icon: <MapPin className="w-4 h-4 text-amber-400" />,
      badge: "Mina Activa",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -6.25, lat: 43.32, zoom: 12 });
        onShowToast?.("📍 Centrando en Mina El Valle-Boinás");
        onClose();
      }
    },
    {
      id: "mina_medulas",
      title: "Las Médulas (Carucedo, León)",
      subtitle: "Mayor paleoplacer aurífero del Imperio Romano",
      category: "Minas",
      icon: <MapPin className="w-4 h-4 text-amber-400" />,
      badge: "Histórico",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -6.76, lat: 42.46, zoom: 12 });
        onShowToast?.("📍 Centrando en Las Médulas");
        onClose();
      }
    },
    {
      id: "mina_rodalquilar",
      title: "Rodalquilar - El Cinto (Cabo de Gata)",
      subtitle: "Epitermal de alta sulfuración con adularia y alunita",
      category: "Minas",
      icon: <MapPin className="w-4 h-4 text-amber-400" />,
      badge: "Holdout Ciego",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -2.04, lat: 36.85, zoom: 12 });
        onShowToast?.("📍 Centrando en Rodalquilar");
        onClose();
      }
    },
    {
      id: "mina_salave",
      title: "Yacimiento de Salave (Tapia de Casariego)",
      subtitle: "Depósito intrusivo de granodiorita Au-As-Sb (~1.5 Moz Au)",
      category: "Minas",
      icon: <MapPin className="w-4 h-4 text-amber-400" />,
      badge: "Asturias",
      action: () => {
        onSwitchView("map");
        onZoomTo({ lon: -6.90, lat: 43.56, zoom: 12 });
        onShowToast?.("📍 Centrando en Salave");
        onClose();
      }
    },

    // Herramientas
    {
      id: "tool_buffer",
      title: "Activar Herramienta de Buffer Espacial",
      subtitle: "Cálculo geodésico y densidad de indicios en radio de 5, 10 o 20 km",
      category: "Herramientas",
      icon: <Target className="w-4 h-4 text-cyan-400" />,
      badge: "GIS Tool",
      action: () => {
        onSwitchView("map");
        onToggleBuffer();
        onShowToast?.("🎯 Herramienta de Buffer activada. Haz clic en el mapa.");
        onClose();
      }
    },
    {
      id: "tool_3d",
      title: "Alternar Perspectiva Topográfica 3D",
      subtitle: "Inclinación de relieve a 60° con orientación de cámara azimutal",
      category: "Herramientas",
      icon: <Compass className="w-4 h-4 text-amber-400" />,
      badge: "Pitch 60°",
      action: () => {
        onSwitchView("map");
        onToggle3D();
        onShowToast?.("🏔️ Alternando perspectiva topográfica 3D");
        onClose();
      }
    },
    {
      id: "tool_sat",
      title: "Activar Mapa Base Satélite Alta Resolución",
      subtitle: "Imágenes satelitales globales de Esri World Imagery",
      category: "Herramientas",
      icon: <Satellite className="w-4 h-4 text-cyan-400" />,
      badge: "Esri",
      action: () => {
        onSetBaseMap("satellite");
        onShowToast?.("🛰️ Mapa base cambiado a Satélite");
        onClose();
      }
    },
    {
      id: "tool_dark",
      title: "Activar Mapa Base Oscuro Carto Dark",
      subtitle: "Modo nocturno de alto contraste ideal para anomalías ráster",
      category: "Herramientas",
      icon: <Moon className="w-4 h-4 text-slate-300" />,
      badge: "Carto",
      action: () => {
        onSetBaseMap("dark");
        onShowToast?.("🌙 Mapa base cambiado a Carto Dark");
        onClose();
      }
    },
    {
      id: "tool_theme",
      title: theme === "light" ? "Cambiar a Modo Oscuro" : "Cambiar a Modo Claro",
      subtitle: theme === "light" ? "Lienzo de alto contraste oscuro con cartografía Dark Matter" : "Lienzo luminoso con cartografía Carto Voyager",
      category: "Herramientas",
      icon: theme === "light" ? <Moon className="w-4 h-4 text-cyan-400" /> : <Sun className="w-4 h-4 text-amber-500" />,
      badge: "Tema",
      action: () => {
        onToggleTheme?.();
        onClose();
      }
    },

    // Vistas y Paneles
    {
      id: "view_dash",
      title: "Abrir Dashboard Ejecutivo v3.0",
      subtitle: "Métricas de Lift, simulador de distritos y trazabilidad de cuadernos",
      category: "Vistas",
      icon: <BarChart3 className="w-4 h-4 text-amber-400" />,
      badge: "Dashboard",
      action: () => {
        onSwitchView("dashboard");
        onClose();
      }
    },
    {
      id: "view_map",
      title: "Abrir Mapa GIS Interactivo",
      subtitle: "Lienzo cartográfico nacional con 478.443 celdas y 787 indicios",
      category: "Vistas",
      icon: <Compass className="w-4 h-4 text-cyan-400" />,
      badge: "Mapa",
      action: () => {
        onSwitchView("map");
        onClose();
      }
    },
    {
      id: "view_targets",
      title: "Consultar 1.529 Targets Priorizados",
      subtitle: "Listado clasificado de zonas prioritarias con ranking y filtrado",
      category: "Vistas",
      icon: <Target className="w-4 h-4 text-amber-400" />,
      badge: "Panel Derecho",
      action: () => {
        onSwitchView("map");
        onOpenTab("targets");
        onClose();
      }
    },
    {
      id: "view_copilot",
      title: "Consultar Copiloto IA Geológico",
      subtitle: "Asistente inteligente con respuestas fundamentadas en datos auditados",
      category: "Vistas",
      icon: <Bot className="w-4 h-4 text-purple-400" />,
      badge: "Copilot",
      action: () => {
        onSwitchView("map");
        onOpenTab("copilot");
        onClose();
      }
    },
    {
      id: "view_validation",
      title: "Ver Validación y Test Ciego",
      subtitle: "Métricas de holdout espacial, curvas ROC-AUC y balance de positivos",
      category: "Vistas",
      icon: <BarChart3 className="w-4 h-4 text-emerald-400" />,
      badge: "Validación",
      action: () => {
        onSwitchView("map");
        onOpenTab("validation");
        onClose();
      }
    },
    {
      id: "view_methodology",
      title: "Consultar Metodología y Limitaciones",
      subtitle: "Auditoría científica, mitigación de sesgos y protocolo geocientífico",
      category: "Vistas",
      icon: <ShieldCheck className="w-4 h-4 text-cyan-400" />,
      badge: "Documentación",
      action: () => {
        onOpenMethodology();
        onClose();
      }
    }
  ];

  // Filtrar según query
  const filtered = query.trim()
    ? commands.filter(
        (c) =>
          c.title.toLowerCase().includes(query.toLowerCase()) ||
          c.subtitle.toLowerCase().includes(query.toLowerCase()) ||
          c.category.toLowerCase().includes(query.toLowerCase())
      )
    : commands;

  // Manejo de teclado: Flechas arriba/abajo y Enter
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % filtered.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % filtered.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].action();
      }
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  // Scroll automático para mantener seleccionado en vista
  useEffect(() => {
    const list = listRef.current;
    if (!list) return;
    const item = list.children[selectedIndex] as HTMLElement;
    if (item) {
      item.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-start justify-center pt-16 sm:pt-24 p-4 animate-in fade-in duration-150 select-none"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-slate-950/95 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden ring-1 ring-white/10 flex flex-col max-h-[75vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Input de Búsqueda de Comandos */}
        <div className="flex items-center px-4 py-3.5 border-b border-slate-800 bg-slate-900/60 gap-3">
          <Search className="w-5 h-5 text-cyan-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Escribe un comando o busca minas, distritos, modelos... (ej: roca, narcea, buffer)"
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none font-sans"
          />
          {query ? (
            <button
              onClick={() => {
                setQuery("");
                setSelectedIndex(0);
              }}
              className="text-slate-400 hover:text-white p-1 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          ) : (
            <kbd className="hidden sm:inline-block text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
              ESC
            </kbd>
          )}
        </div>

        {/* Lista de Comandos */}
        <div ref={listRef} className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin">
          {filtered.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No se encontraron comandos o localizaciones para &ldquo;{query}&rdquo;
            </div>
          ) : (
            filtered.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => item.action()}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`px-3 py-2.5 rounded-xl flex items-center justify-between gap-3 cursor-pointer transition-all ${
                    isSelected
                      ? "bg-cyan-950/70 border border-cyan-500/50 text-cyan-200 shadow-md shadow-cyan-950/40"
                      : "hover:bg-slate-900/60 border border-transparent text-slate-300"
                  }`}
                >
                  <div className="flex items-center gap-3 truncate">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                        isSelected
                          ? "bg-cyan-500/20 border border-cyan-400/40"
                          : "bg-slate-900 border border-slate-800"
                      }`}
                    >
                      {item.icon}
                    </div>
                    <div className="truncate">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-slate-100 truncate">
                          {item.title}
                        </span>
                        <span className="text-[9px] font-mono text-slate-500 uppercase">
                          {item.category}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 truncate mt-0.5">
                        {item.subtitle}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {item.badge && (
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-slate-900 text-slate-400 border border-slate-800">
                        {item.badge}
                      </span>
                    )}
                    {isSelected && (
                      <ChevronRight className="w-4 h-4 text-cyan-400 animate-in fade-in" />
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer del Command Palette */}
        <div className="px-4 py-2 border-t border-slate-800/80 bg-slate-900/40 flex items-center justify-between text-[10px] font-mono text-slate-500">
          <div className="flex items-center gap-3">
            <span>↑↓ Navegar</span>
            <span>↵ Ejecutar</span>
            <span>ESC Salir</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400">
            <Command className="w-3 h-3 text-cyan-400" />
            <span>GeoAI Spotlight v3.0</span>
          </div>
        </div>
      </div>
    </div>
  );
};
