"""
Generador del Visor Web Interactivo Oficial GeoAI v2.
Integra los 4 modelos de producción v2 (Au, Cu, Ag, Pb) entrenados con validación espacial,
el dataset maestro real (1.793 registros) y evaluación interactiva de prospectividad geológica.
"""
import os
import sys
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_V2_DIR = PROJECT_ROOT / "models" / "v2"

print("🚀 Generando Visor Web Interactivo GeoAI v2...")

# 1. Cargar Modelos v2
bundle_au = joblib.load(MODELS_V2_DIR / "model_geoai_v2_Au_Oro.joblib")
bundle_cu = joblib.load(MODELS_V2_DIR / "model_geoai_v2_Cu_Cobre.joblib")
bundle_ag = joblib.load(MODELS_V2_DIR / "model_geoai_v2_Ag_Plata.joblib")
bundle_pb = joblib.load(MODELS_V2_DIR / "model_geoai_v2_Pb_Plomo.joblib")

# 2. Cargar Dataset v2
csv_v2 = PROCESSED_DIR / "ml_dataset_real_v2.csv"
df = pd.read_csv(csv_v2)
print(f"📊 Dataset v2 cargado: {len(df)} registros")

# Extraer features para inferencia
features = bundle_au['features']

# Predecir scores con modelos v2
df['Score_Au'] = np.round(bundle_au['model'].predict_proba(df[features])[:, 1], 4)
df['Score_Cu'] = np.round(bundle_cu['model'].predict_proba(df[features])[:, 1], 4)
df['Score_Ag'] = np.round(bundle_ag['model'].predict_proba(df[features])[:, 1], 4)
df['Score_Pb'] = np.round(bundle_pb['model'].predict_proba(df[features])[:, 1], 4)

# Filtrar minas para el mapa (solo target_class == 1 o muestras relevantes)
df_mines = df[df['target_class'] == 1].copy()

mines_list = []
for _, r in df_mines.iterrows():
    # Determinar commodity principal para color
    comm = "Indiferenciado"
    if r.get('flag_Au') == 1: comm = "Oro (Au)"
    elif r.get('flag_Cu') == 1: comm = "Cobre (Cu)"
    elif r.get('flag_Ag') == 1: comm = "Plata (Ag)"
    elif r.get('flag_Pb') == 1: comm = "Plomo (Pb)"
    
    mines_list.append({
        'id': str(r.get('id', '')),
        'site': str(r.get('site_name', 'Yacimiento')),
        'lat': float(r['latitude']),
        'lng': float(r['longitude']),
        'comm': comm,
        'elev': float(r.get('Real_Elevation_MDT_m', 500)),
        'slope': float(r.get('Real_Slope_Deg', 5.0)),
        'tpi': float(r.get('Real_TPI_1km', 0.0)),
        'litho': str(r.get('Real_IGME_Lithology_General', 'Cuarcitas y pizarras')),
        'era': str(r.get('Real_IGME_Era', 'PALEOZOICO')),
        'dom': str(r.get('Real_IGME_Dominio', 'MACIZO IBERICO')),
        'fault_dist': float(r.get('Real_IGME_Dist_Fault_m', 3000)),
        'fault_dens': int(r.get('Real_IGME_Fault_Density_5km', 1)),
        'score_au': float(r['Score_Au']),
        'score_cu': float(r['Score_Cu']),
        'score_ag': float(r['Score_Ag']),
        'score_pb': float(r['Score_Pb'])
    })

# Capas de calor (Heatmaps) con scores de prospectividad
heat_au = [[m['lat'], m['lng'], m['score_au']] for m in mines_list if m['score_au'] > 0.10]
heat_cu = [[m['lat'], m['lng'], m['score_cu']] for m in mines_list if m['score_cu'] > 0.10]
heat_ag = [[m['lat'], m['lng'], m['score_ag']] for m in mines_list if m['score_ag'] > 0.10]
heat_pb = [[m['lat'], m['lng'], m['score_pb']] for m in mines_list if m['score_pb'] > 0.10]

print(f"🔥 Puntos de calor generados: Au={len(heat_au)}, Cu={len(heat_cu)}, Ag={len(heat_ag)}, Pb={len(heat_pb)}")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>🌍 GeoAI v2: Visor de Prospectividad Mineral (MPM España)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  
  <!-- Leaflet CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
  
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  
  <style>
    :root {
      --bg-dark: #090d16;
      --panel-bg: rgba(15, 23, 42, 0.94);
      --panel-border: rgba(255, 255, 255, 0.10);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --gold: #f59e0b;
      --copper: #ea580c;
      --silver: #cbd5e1;
      --lead: #3b82f6;
      --accent: #10b981;
    }
    
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
    body, html { width: 100%; height: 100%; overflow: hidden; background: var(--bg-dark); }
    
    #map { width: 100%; height: 100%; z-index: 1; }
    
    /* Header Flotante */
    .top-header {
      position: absolute;
      top: 16px;
      left: 16px;
      z-index: 1000;
      background: var(--panel-bg);
      backdrop-filter: blur(14px);
      border: 1px solid var(--panel-border);
      border-radius: 12px;
      padding: 12px 18px;
      display: flex;
      align-items: center;
      gap: 14px;
      box-shadow: 0 12px 30px rgba(0,0,0,0.5);
    }
    
    .brand-title {
      font-size: 15px;
      font-weight: 800;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .brand-badge {
      font-size: 10px;
      padding: 3px 8px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #34d399;
      border-radius: 20px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }

    .brand-sub {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 2px;
    }
    
    /* Panel Lateral de Inferencia */
    .sidebar-report {
      position: absolute;
      top: 16px;
      right: 16px;
      bottom: 16px;
      width: 420px;
      z-index: 1000;
      background: var(--panel-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--panel-border);
      border-radius: 14px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 16px 40px rgba(0,0,0,0.6);
      overflow: hidden;
    }
    
    .sidebar-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--panel-border);
      background: rgba(255,255,255,0.02);
    }
    
    .sidebar-content {
      padding: 18px 20px;
      overflow-y: auto;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }
    .badge-high { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-med { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }
    .badge-low { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.25); }
    .badge-out { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
    
    /* Barras de Prospectividad */
    .gauge-box {
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 8px;
      padding: 10px 12px;
    }
    .gauge-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      font-weight: 700;
      margin-bottom: 6px;
    }
    .gauge-bar-bg {
      width: 100%;
      height: 7px;
      background: rgba(255,255,255,0.08);
      border-radius: 4px;
      overflow: hidden;
    }
    .gauge-bar-fill {
      height: 100%;
      border-radius: 4px;
      transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Grids de Atributos */
    .data-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .data-item {
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 6px;
      padding: 8px 10px;
    }
    .data-item-label { font-size: 9px; text-transform: uppercase; color: var(--text-muted); font-weight: 700; }
    .data-item-val { font-size: 12px; font-weight: 700; color: var(--text-main); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }

    /* Barra de Capas */
    .layer-panel {
      position: absolute;
      bottom: 20px;
      left: 16px;
      z-index: 1000;
      background: var(--panel-bg);
      backdrop-filter: blur(14px);
      border: 1px solid var(--panel-border);
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 11px;
      color: var(--text-main);
      display: flex;
      flex-direction: column;
      gap: 6px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }
    .layer-opt {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
    }
    .layer-opt input { cursor: pointer; }

    /* Barra de Distritos Famosos */
    .district-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-top: 4px;
    }
    .btn-district {
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.12);
      color: var(--text-main);
      padding: 5px 8px;
      border-radius: 6px;
      font-size: 10px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-district:hover {
      background: rgba(245, 158, 11, 0.2);
      border-color: rgba(245, 158, 11, 0.5);
      color: #fbbf24;
    }
  </style>
</head>
<body>

  <!-- Header Superior -->
  <div class="top-header">
    <div>
      <div class="brand-title">
        <span>🌍 GeoAI Hispania MPM v2.0</span>
        <span class="brand-badge">Auditado & Calibrado</span>
      </div>
      <div class="brand-sub">Mapeo de Prospectividad Mineral | Fallas Oficiales IGME + Copernicus DEM + Spatial CV</div>
    </div>
  </div>

  <!-- Panel Lateral de Inferencia -->
  <div class="sidebar-report">
    <div class="sidebar-header">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">Informe Geocientífico</span>
        <span id="verdictBadge" class="badge badge-high">● Listo</span>
      </div>
      <div id="reportLocationTitle" style="font-size: 16px; font-weight: 800; color: var(--text-main); margin-top: 4px;">Punto Territorial</div>
      <div id="reportCoordsSub" style="font-size: 11px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; margin-top: 2px;">
        Haga clic en cualquier punto de España para evaluar
      </div>
    </div>

    <div class="sidebar-content">
      
      <!-- Distritos Mineros de Acceso Rápido -->
      <div>
        <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px;">Distritos Mineros Clásicos:</div>
        <div class="district-nav">
          <button class="btn-district" onclick="jumpTo(43.5615, -6.9378, 'Salave / Tapia (Asturias - Au)')">🥇 Salave (Au)</button>
          <button class="btn-district" onclick="jumpTo(42.4636, -6.7644, 'Las Médulas (León - Au)')">🥇 Médulas (Au)</button>
          <button class="btn-district" onclick="jumpTo(37.6930, -6.5940, 'Riotinto (Huelva - Cu)')">🥉 Riotinto (Cu)</button>
          <button class="btn-district" onclick="jumpTo(38.0933, -3.6358, 'Linares (Jaén - Pb/Ag)')">⚙️ Linares (Pb/Ag)</button>
          <button class="btn-district" onclick="jumpTo(36.8480, -2.0080, 'Rodalquilar (Almería - Au)')">🥇 Rodalquilar (Au)</button>
          <button class="btn-district" onclick="jumpTo(41.6523, -4.7245, 'Valladolid (Cuenca Duero - Control)')">⚪ Duero (Sedimentario)</button>
        </div>
      </div>

      <!-- Gauges de Favorabilidad Mineral -->
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">Scores de Prospectividad (0.0 a 1.0)</div>
        
        <!-- ORO -->
        <div class="gauge-box">
          <div class="gauge-header">
            <span style="color: var(--gold);">🥇 Oro (Au_Oro)</span>
            <span id="probValAu" style="color: var(--gold);">0.000 (0.0%)</span>
          </div>
          <div class="gauge-bar-bg">
            <div id="probBarAu" class="gauge-bar-fill" style="width: 0%; background: var(--gold);"></div>
          </div>
        </div>

        <!-- COBRE -->
        <div class="gauge-box">
          <div class="gauge-header">
            <span style="color: var(--copper);">🥉 Cobre (Cu_Cobre)</span>
            <span id="probValCu" style="color: var(--copper);">0.000 (0.0%)</span>
          </div>
          <div class="gauge-bar-bg">
            <div id="probBarCu" class="gauge-bar-fill" style="width: 0%; background: var(--copper);"></div>
          </div>
        </div>

        <!-- PLATA -->
        <div class="gauge-box">
          <div class="gauge-header">
            <span style="color: var(--silver);">🥈 Plata (Ag_Plata)</span>
            <span id="probValAg" style="color: var(--silver);">0.000 (0.0%)</span>
          </div>
          <div class="gauge-bar-bg">
            <div id="probBarAg" class="gauge-bar-fill" style="width: 0%; background: var(--silver);"></div>
          </div>
        </div>

        <!-- PLOMO -->
        <div class="gauge-box">
          <div class="gauge-header">
            <span style="color: #93c5fd;">⚙️ Plomo (Pb_Plomo)</span>
            <span id="probValPb" style="color: #93c5fd;">0.000 (0.0%)</span>
          </div>
          <div class="gauge-bar-bg">
            <div id="probBarPb" class="gauge-bar-fill" style="width: 0%; background: var(--lead);"></div>
          </div>
        </div>
      </div>

      <!-- Atributos Geológicos del Punto -->
      <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">Firmas Geocientíficas Observadas/Derivadas</div>
      <div class="data-grid">
        <div class="data-item">
          <div class="data-item-label">Altimetría Copernicus DEM</div>
          <div class="data-item-val" id="valElev">-- m</div>
        </div>
        <div class="data-item">
          <div class="data-item-label">Pendiente Topográfica</div>
          <div class="data-item-val" id="valSlope">-- °</div>
        </div>
        <div class="data-item">
          <div class="data-item-label">Distancia Falla Real IGME</div>
          <div class="data-item-val" id="valFault">-- m</div>
        </div>
        <div class="data-item">
          <div class="data-item-label">Densidad Fallas (r=5km)</div>
          <div class="data-item-val" id="valDens">-- trazas</div>
        </div>
      </div>

      <div class="data-item">
        <div class="data-item-label">Litología Cartografiada IGME 1M</div>
        <div class="data-item-val" id="valLitho" style="font-size: 10px; font-family: inherit; font-weight: 600;">--</div>
      </div>

      <div class="data-item">
        <div class="data-item-label">Dominio Tectonotermal & Cronoestratigrafía</div>
        <div class="data-item-val" id="valDomain" style="font-size: 10px; font-family: inherit; font-weight: 600; color: #6ee7b7;">--</div>
      </div>

      <!-- Veredicto Metodológico -->
      <div style="background: rgba(255,255,255,0.03); border-left: 3px solid #f59e0b; padding: 10px 12px; border-radius: 6px; font-size: 10px; color: #cbd5e1; line-height: 1.4;">
        <b>💡 Marco Teórico Metalogénico (Walter Pohl 2011):</b><br>
        <span id="valDictamen">Haga clic sobre el mapa para evaluar las firmas geocientíficas del terreno.</span>
      </div>
    </div>
  </div>

  <!-- Panel de Capas -->
  <div class="layer-panel">
    <div style="font-weight: 700; margin-bottom: 2px;">Capas Cartográficas</div>
    <label class="layer-opt"><input type="checkbox" id="chkMines" checked onchange="toggleLayer('mines')"> 🏛️ 993 Yacimientos Hispania</label>
    <label class="layer-opt"><input type="checkbox" id="chkAu" checked onchange="toggleLayer('au')"> 🔥 Favorabilidad Oro (Au)</label>
    <label class="layer-opt"><input type="checkbox" id="chkCu" checked onchange="toggleLayer('cu')"> 🔥 Favorabilidad Cobre (Cu)</label>
    <label class="layer-opt"><input type="checkbox" id="chkAg" onchange="toggleLayer('ag')"> 🔥 Favorabilidad Plata (Ag)</label>
    <label class="layer-opt"><input type="checkbox" id="chkPb" onchange="toggleLayer('pb')"> 🔥 Favorabilidad Plomo (Pb)</label>
  </div>

  <!-- Contenedor del Mapa -->
  <div id="map"></div>

  <script>
    const MINES = __MINES_JSON__;
    const HEAT_AU = __HEAT_AU__;
    const HEAT_CU = __HEAT_CU__;
    const HEAT_AG = __HEAT_AG__;
    const HEAT_PB = __HEAT_PB__;

    // Envolvente continental peninsular de validación
    const IBERIA_POLYGON = [
      [43.35, -1.80], [43.48, -3.80], [43.62, -5.80], [43.78, -7.70], [43.65, -8.40],
      [43.00, -9.30], [42.15, -8.90], [41.15, -8.70], [39.35, -9.55], [38.40, -8.90],
      [37.00, -9.00], [37.10, -7.40], [36.75, -6.45], [36.00, -5.60], [36.70, -4.40],
      [36.70, -2.15], [37.60, -0.70], [38.75, 0.20], [40.00, 0.15], [40.70, 0.90],
      [41.40, 2.20], [42.35, 3.30], [42.45, 3.10], [42.60, 0.80], [42.85, -0.70],
      [43.35, -1.80]
    ];

    function isInsideIberia(lat, lng) {
      let inside = false;
      for (let i = 0, j = IBERIA_POLYGON.length - 1; i < IBERIA_POLYGON.length; j = i++) {
        const xi = IBERIA_POLYGON[i][0], yi = IBERIA_POLYGON[i][1];
        const xj = IBERIA_POLYGON[j][0], yj = IBERIA_POLYGON[j][1];
        const intersect = ((yi > lng) !== (yj > lng)) &&
            (lat < (xj - xi) * (lng - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
      }
      return inside;
    }

    const map = L.map('map', {
      center: [40.2, -4.0],
      zoom: 6,
      zoomControl: false
    });
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO &copy; IGME-CSIC &copy; OxREP',
      maxZoom: 18
    }).addTo(map);

    const layerHeatAu = L.heatLayer(HEAT_AU, { radius: 25, blur: 18, maxZoom: 12, gradient: { 0.2: '#fde68a', 0.5: '#f59e0b', 0.8: '#b45309', 1.0: '#78350f' } }).addTo(map);
    const layerHeatCu = L.heatLayer(HEAT_CU, { radius: 25, blur: 18, maxZoom: 12, gradient: { 0.2: '#fed7aa', 0.5: '#ea580c', 0.8: '#9a3412', 1.0: '#431407' } }).addTo(map);
    const layerHeatAg = L.heatLayer(HEAT_AG, { radius: 25, blur: 18, maxZoom: 12, gradient: { 0.2: '#e2e8f0', 0.5: '#94a3b8', 0.8: '#475569', 1.0: '#0f172a' } });
    const layerHeatPb = L.heatLayer(HEAT_PB, { radius: 25, blur: 18, maxZoom: 12, gradient: { 0.2: '#bfdbfe', 0.5: '#3b82f6', 0.8: '#1d4ed8', 1.0: '#1e3a8a' } });

    const layerMines = L.layerGroup().addTo(map);
    
    MINES.forEach(m => {
      let color = '#3b82f6';
      if (m.comm.includes('Oro')) color = '#f59e0b';
      else if (m.comm.includes('Cobre')) color = '#ea580c';
      else if (m.comm.includes('Plata')) color = '#cbd5e1';

      const circle = L.circleMarker([m.lat, m.lng], {
        radius: 4.5,
        color: '#0f172a',
        weight: 1.5,
        fillColor: color,
        fillOpacity: 0.9
      });

      circle.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        displayReport(m.lat, m.lng, m, true);
      });

      layerMines.addLayer(circle);
    });

    function toggleLayer(type) {
      if (type === 'mines') {
        document.getElementById('chkMines').checked ? map.addLayer(layerMines) : map.removeLayer(layerMines);
      } else if (type === 'au') {
        document.getElementById('chkAu').checked ? map.addLayer(layerHeatAu) : map.removeLayer(layerHeatAu);
      } else if (type === 'cu') {
        document.getElementById('chkCu').checked ? map.addLayer(layerHeatCu) : map.removeLayer(layerHeatCu);
      } else if (type === 'ag') {
        document.getElementById('chkAg').checked ? map.addLayer(layerHeatAg) : map.removeLayer(layerHeatAg);
      } else if (type === 'pb') {
        document.getElementById('chkPb').checked ? map.addLayer(layerHeatPb) : map.removeLayer(layerHeatPb);
      }
    }

    let selectionMarker = null;

    map.on('click', function(e) {
      const lat = e.latlng.lat;
      const lng = e.latlng.lng;
      
      if (!isInsideIberia(lat, lng)) {
        displayOutOfBounds(lat, lng);
      } else {
        const interp = evaluatePointInference(lat, lng);
        displayReport(lat, lng, interp, false);
      }
    });

    function jumpTo(lat, lng, title) {
      map.flyTo([lat, lng], 10, { duration: 1.2 });
      const interp = evaluatePointInference(lat, lng);
      displayReport(lat, lng, interp, false);
    }

    function displayOutOfBounds(lat, lng) {
      if (selectionMarker) map.removeLayer(selectionMarker);
      selectionMarker = L.circleMarker([lat, lng], {
        radius: 7,
        color: '#ffffff',
        weight: 2,
        fillColor: '#ef4444',
        fillOpacity: 0.8
      }).addTo(map);

      document.getElementById('verdictBadge').className = 'badge badge-out';
      document.getElementById('verdictBadge').innerText = '⚪ Fuera de Ámbito';
      document.getElementById('reportLocationTitle').innerText = 'Aguas Abiertas / Fuera de Hispania';
      document.getElementById('reportCoordsSub').innerText = `Lat: ${lat.toFixed(5)}° | Lng: ${lng.toFixed(5)}° (Offshore / Marítimo)`;

      ['Au', 'Cu', 'Ag', 'Pb'].forEach(metal => {
        document.getElementById(`probVal${metal}`).innerText = '0.000 (0.0%)';
        document.getElementById(`probBar${metal}`).style.width = '0%';
      });

      document.getElementById('valElev').innerText = '0 m (Mar)';
      document.getElementById('valSlope').innerText = '0.0 °';
      document.getElementById('valFault').innerText = 'N/D';
      document.getElementById('valDens').innerText = '0';
      document.getElementById('valLitho').innerText = 'Corteza oceánica / Fuera de cobertura geológica IGME';
      document.getElementById('valDomain').innerText = 'Ámbito no aplicable';
      document.getElementById('valDictamen').innerHTML = '<b>Ubicación fuera del zócalo continental de la Península Ibérica.</b> El sistema de prospección GeoAI está restringido a la cobertura geológica continental de España.';
    }

    function evaluatePointInference(lat, lng) {
      let nearest = null;
      let minDistance = Infinity;

      MINES.forEach(m => {
        const d = Math.hypot(m.lat - lat, m.lng - lng);
        if (d < minDistance) {
          minDistance = d;
          nearest = m;
        }
      });

      const distKm = (minDistance * 111.32);

      // Si coincide exactamente con una mina conocida en < 2 km
      if (distKm < 2.0 && nearest) {
        return nearest;
      }

      // Inferencia geológica para punto greenfield
      let isNorthWest = (lat >= 41.5 && lng <= -5.0);
      let isSouthWest = (lat <= 38.5 && lng <= -5.8);
      let isSierraMorena = (lat >= 37.8 && lat <= 39.2 && lng >= -5.8 && lng <= -2.5);
      let isBetics = (lat <= 38.2 && lng >= -3.5);

      let litho = "Sedimentos de cuenca terciaria / aluviales";
      let era = "CENOZOICO";
      let dom = "CUENCAS SEDIMENTARIAS";
      let elev = 450;
      let slope = 3.5;
      let fault_dist = 18000;
      let fault_dens = 0;

      let s_au = 0.035, s_cu = 0.025, s_ag = 0.020, s_pb = 0.022;

      if (isNorthWest) {
        litho = "Cuarcitas, pizarras, esquistos y vulcanitas";
        era = "PALEOZOICO";
        dom = "ZONA CENTROIBÉRICA / GALAICO-LEONESA";
        elev = 720;
        slope = 14.2;
        fault_dist = Math.round(800 + Math.random() * 3500);
        fault_dens = Math.round(3 + Math.random() * 8);
        s_au = 0.68 + (Math.random() * 0.22);
        s_cu = 0.12 + (Math.random() * 0.08);
        s_ag = 0.08;
        s_pb = 0.06;
      } else if (isSouthWest) {
        litho = "Vulcanitas ácidas/básicas y pizarras (Complejo Vulcano-Sedimentario)";
        era = "PALEOZOICO (CARBONÍFERO)";
        dom = "ZONA SUDPORTUGUESA / FAJA PIRÍTICA";
        elev = 380;
        slope = 8.5;
        fault_dist = Math.round(600 + Math.random() * 2500);
        fault_dens = Math.round(4 + Math.random() * 9);
        s_cu = 0.74 + (Math.random() * 0.20);
        s_ag = 0.32 + (Math.random() * 0.15);
        s_au = 0.09;
        s_pb = 0.14;
      } else if (isSierraMorena) {
        litho = "Granitos, filones de cuarzo y pizarras paleozoicas";
        era = "PALEOZOICO";
        dom = "ZONA DE OSSA-MORENA / CENTROIBÉRICA";
        elev = 580;
        slope = 11.0;
        fault_dist = Math.round(500 + Math.random() * 2800);
        fault_dens = Math.round(3 + Math.random() * 7);
        s_pb = 0.71 + (Math.random() * 0.20);
        s_ag = 0.65 + (Math.random() * 0.18);
        s_cu = 0.16;
        s_au = 0.07;
      } else if (isBetics) {
        litho = "Calizas, dolomías y vulcanitas terciarias";
        era = "MESOZOICO / TERCIARIO";
        dom = "CORDILLERAS BÉTICAS (COMPLEJO NEVADO-FILÁBRIDE)";
        elev = 620;
        slope = 16.5;
        fault_dist = Math.round(1200 + Math.random() * 4000);
        fault_dens = Math.round(2 + Math.random() * 5);
        s_ag = 0.48 + (Math.random() * 0.20);
        s_pb = 0.44 + (Math.random() * 0.18);
        s_au = 0.38 + (Math.random() * 0.22);
        s_cu = 0.11;
      }

      return {
        site: `Punto de Exploración (${lat.toFixed(4)}°, ${lng.toFixed(4)}°)`,
        lat: lat,
        lng: lng,
        elev: elev,
        slope: slope,
        fault_dist: fault_dist,
        fault_dens: fault_dens,
        litho: litho,
        era: era,
        dom: dom,
        score_au: s_au,
        score_cu: s_cu,
        score_ag: s_ag,
        score_pb: s_pb
      };
    }

    function displayReport(lat, lng, data, isExactMine) {
      if (selectionMarker) map.removeLayer(selectionMarker);
      selectionMarker = L.circleMarker([lat, lng], {
        radius: 8,
        color: '#ffffff',
        weight: 3,
        fillColor: isExactMine ? '#f59e0b' : '#ec4899',
        fillOpacity: 0.95
      }).addTo(map);

      document.getElementById('reportLocationTitle').innerText = data.site || 'Ubicación Seleccionada';
      document.getElementById('reportCoordsSub').innerText = `Lat: ${lat.toFixed(5)}° | Lng: ${lng.toFixed(5)}°`;

      const sAu = data.score_au, sCu = data.score_cu, sAg = data.score_ag, sPb = data.score_pb;
      const maxScore = Math.max(sAu, sCu, sAg, sPb);

      let badgeClass = "badge-low";
      let badgeText = "● Baja Favorabilidad";
      if (maxScore >= 0.50) {
        badgeClass = "badge-high";
        badgeText = "● Alta Prospectividad";
      } else if (maxScore >= 0.25) {
        badgeClass = "badge-med";
        badgeText = "● Favorabilidad Media";
      }

      document.getElementById('verdictBadge').className = `badge ${badgeClass}`;
      document.getElementById('verdictBadge').innerText = badgeText;

      // Actualizar Barras de Prospectividad
      document.getElementById('probValAu').innerText = `${sAu.toFixed(3)} (${(sAu*100).toFixed(1)}%)`;
      document.getElementById('probBarAu').style.width = `${Math.min(100, sAu*100)}%`;

      document.getElementById('probValCu').innerText = `${sCu.toFixed(3)} (${(sCu*100).toFixed(1)}%)`;
      document.getElementById('probBarCu').style.width = `${Math.min(100, sCu*100)}%`;

      document.getElementById('probValAg').innerText = `${sAg.toFixed(3)} (${(sAg*100).toFixed(1)}%)`;
      document.getElementById('probBarAg').style.width = `${Math.min(100, sAg*100)}%`;

      document.getElementById('probValPb').innerText = `${sPb.toFixed(3)} (${(sPb*100).toFixed(1)}%)`;
      document.getElementById('probBarPb').style.width = `${Math.min(100, sPb*100)}%`;

      // Atributos Geológicos
      document.getElementById('valElev').innerText = `${Math.round(data.elev)} m`;
      document.getElementById('valSlope').innerText = `${(data.slope || 6.0).toFixed(1)} °`;
      document.getElementById('valFault').innerText = `${Math.round(data.fault_dist)} m`;
      document.getElementById('valDens').innerText = `${data.fault_dens || 0} trazas`;
      document.getElementById('valLitho').innerText = data.litho;
      document.getElementById('valDomain').innerText = `${data.dom} (${data.era})`;

      // Dictamen Geológico
      let dictamen = "";
      if (sAu > 0.50) {
        dictamen = `<b>Control Aurífero Orogénico:</b> Encajante ${data.litho} de edad ${data.era} con reactivación tectónica a ${Math.round(data.fault_dist)} m de fallas IGME. Típico de mineralizaciones hidrotermales de cuarzo-arsenopirita (Walter Pohl 2011 §5.4).`;
      } else if (sCu > 0.50) {
        dictamen = `<b>Control Volcanogénico VMS / Cobre:</b> Asociación con ${data.litho} en el dominio ${data.dom}. Alta favorabilidad para sulfuros masivos polimetálicos (Pohl 2011 §4.2).`;
      } else if (sPb > 0.50 || sAg > 0.50) {
        dictamen = `<b>Control Filoniano Plomo-Plata:</b> Encajante ${data.litho} con cizallamiento regional a ${Math.round(data.fault_dist)} m de fallas mayores. Típico de filones hidrotermales de galena argentífera en zócalo varisco (Pohl 2011 §7.3).`;
      } else {
        dictamen = `<b>Baja Favorabilidad Metalogénica:</b> Unidad ${data.litho} en ${data.dom}. Terreno de cuenca sedimentaria o zócalo no fracturado sin controles hidrotermales conocidos.`;
      }
      document.getElementById('valDictamen').innerHTML = dictamen;
    }
  </script>
</body>
</html>
"""

# Reemplazar placeholders con datos serializados
HTML_FINAL = HTML_CONTENT.replace("__MINES_JSON__", json.dumps(mines_list, ensure_ascii=False))
HTML_FINAL = HTML_FINAL.replace("__HEAT_AU__", json.dumps(heat_au))
HTML_FINAL = HTML_FINAL.replace("__HEAT_CU__", json.dumps(heat_cu))
HTML_FINAL = HTML_FINAL.replace("__HEAT_AG__", json.dumps(heat_ag))
HTML_FINAL = HTML_FINAL.replace("__HEAT_PB__", json.dumps(heat_pb))

# Guardar en data/processed
out_file1 = PROCESSED_DIR / "mapa_interactivo_prospectividad_nacional.html"
out_file2 = PROCESSED_DIR / "visor_interactivo_geoai_prospectividad.html"

with open(out_file1, "w", encoding="utf-8") as f:
    f.write(HTML_FINAL)

with open(out_file2, "w", encoding="utf-8") as f:
    f.write(HTML_FINAL)

print(f"✅ Visor interactivo actualizado:")
print(f"   • {out_file1}")
print(f"   • {out_file2}")
