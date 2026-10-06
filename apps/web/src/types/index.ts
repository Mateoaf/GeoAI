/**
 * apps/web/src/types/index.ts
 * Definición de tipos TypeScript para GeoAI-Au Explorer.
 */

export interface Thresholds {
  top_01: number;
  top_05: number;
  top_10: number;
}

export type RasterLayerType =
  | "score"
  | "percentile"
  | "priority"
  | "global_v2_score"
  | "rock_score"
  | "alluvial_score"
  | "v3_pu_score"
  | "v3_uncertainty"
  | "none";

export interface ProjectSummary {
  project_name: string;
  tagline: string;
  release_version: string;
  is_scientific_release: boolean;
  model_name: string;
  model_family: string;
  resolution: string;
  crs: string;
  region: string;
  eligible_cells_count: number;
  features_count: number;
  prioritized_zones_count: number;
  thresholds: Thresholds;
  run_ids: Record<string, string>;
}

export interface CellInfo {
  cell_id: string;
  row: number;
  col: number;
  score: number;
  percentile_favorabilidad: number;
  prioridad_banda: string;
  land_area_m2: number;
  x_epsg25830: number;
  y_epsg25830: number;
  lon_wgs84: number;
  lat_wgs84: number;
  deposit_id: string | null;
  district_id: string | null;
  favorabilidad_pu_media?: number | null;
  incertidumbre_std?: number | null;
  categoria_fiabilidad?: string | null;
  es_extrapolacion?: boolean | null;
  distancia_dominio_z?: number | null;
}

export interface CellResponse {
  disclaimer: string;
  eligible: boolean;
  cell: CellInfo | null;
  query_coordinates?: { lat: number; lon: number } | null;
}

export interface FeatureContribution {
  variable: string;
  familia: string;
  raw_value: number;
  standardized_z: number;
  coefficient: number;
  contribution: number;
  odds_ratio: number;
  significado_geologico: string;
}

export interface CellExplanation {
  cell_id: string;
  prospectivity_score: number;
  intercept: number;
  logit_calculated: number;
  logit_decision_function: number;
  consistency_error: number;
  consistency_test_passed: boolean;
  sigmoid_score: number;
  top_positive_contributions: FeatureContribution[];
  top_negative_contributions: FeatureContribution[];
  all_contributions: FeatureContribution[];
}

export interface CellExplainResponse {
  disclaimer: string;
  explanation: CellExplanation;
}

export interface TargetZone {
  zona_id: string;
  denominacion: string;
  categoria_prioridad: string;
  ranking_nacional: number;
  score_maximo: number;
  score_medio: number;
  area_km2: number;
  celdas_count: number;
  centroide_x: number;
  centroide_y: number;
  deposito_conocido_proximo: string;
  distrito_conocido_proximo: string;
  distancia_deposito_proximo_km: number;
  anotacion_post_hoc: string;
}

export interface TargetsResponse {
  disclaimer: string;
  total_count: number;
  zones: TargetZone[];
}

export interface HoldoutMetricsSummary {
  holdout_cells: number;
  observed_P_cells: number;
  observed_deposits: number;
  districts_count: number;
  deposit_recovery_at_01: number;
  deposit_recovery_at_05: number;
  deposit_recovery_at_10: number;
  cell_recovery_at_01: number;
  cell_recovery_at_05: number;
  cell_recovery_at_10: number;
  roc_auc_PU: number;
  average_precision_PU: number;
  transfer_gap_note: string;
  bootstrap_uncertainty_ci95: Record<string, any>;
}

export interface HoldoutDepositItem {
  deposit_id: string;
  district_id: string;
  p_cells_count: number;
  max_score: number;
  mean_score: number;
  best_rank_in_holdout: number;
  best_area_fraction: number;
  best_percentile_favorability: number;
  recovered_at_01: boolean;
  recovered_at_05: boolean;
  recovered_at_10: boolean;
}

export interface HoldoutDistrictItem {
  district_id: string;
  unit_id: string;
  total_cells: number;
  p_cells: number;
  n_deposits: number;
  deposits_list: string;
  score_mean: number;
  score_median: number;
  score_max: number;
  deposits_recovered_at_01: number;
  deposit_recovery_rate_at_01: number;
  deposits_recovered_at_05: number;
  deposit_recovery_rate_at_05: number;
  deposits_recovered_at_10: number;
  deposit_recovery_rate_at_10: number;
  cells_recovered_at_01: number;
  cells_recovered_at_05: number;
  cells_recovered_at_10: number;
}

export interface ValidationSummaryResponse {
  summary: HoldoutMetricsSummary;
}

export interface ValidationDepositsResponse {
  deposits: HoldoutDepositItem[];
}

export interface ValidationDistrictsResponse {
  districts: HoldoutDistrictItem[];
}

export interface ModelCoefficient {
  variable: string;
  familia: string;
  coeficiente_estandarizado: number;
  abs_coeficiente: number;
  odds_ratio: number;
  impacto_modelo: string;
  significado_geologico: string;
}

export interface CopilotQuery {
  query: string;
  context?: Record<string, any>;
}

export interface CopilotAction {
  action_type: string;
  payload: Record<string, any>;
}

export interface CopilotResponse {
  disclaimer: string;
  query: string;
  answer_markdown: string;
  sources: string[];
  suggested_queries: string[];
  action?: CopilotAction | null;
}

export interface IndicioFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
  properties: {
    record_id: string;
    codigo_indicio: string;
    nombre_mina: string;
    provincia: string;
    municipio: string;
    morfologia: string;
    tipo_au: "roca" | "aluvial" | "desconocido";
    deposit_id: string;
    district_id: string;
    estado_presencia: string;
  };
}

export interface DistrictFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
  properties: {
    district_id: string;
    nombre: string;
    n_depositos: number;
    celdas_confirmadas: number;
    celdas_totales: number;
    area_km2: number;
    recintos_documentados: string;
  };
}

export interface BufferAnalysisResult {
  center: {
    lat: number;
    lon: number;
    x_epsg25830: number;
    y_epsg25830: number;
  };
  radius_km: number;
  indicios_count: number;
  indicios_roca: number;
  indicios_aluvial: number;
  indicios: Array<{
    record_id: string;
    nombre_mina: string;
    provincia: string;
    municipio: string;
    tipo_au: string;
    morfologia: string;
    distance_km: number;
    lon: number;
    lat: number;
  }>;
  nearest_district: {
    district_id: string;
    nombre: string;
    distance_km: number;
  } | null;
  max_score: number;
  mean_score: number;
  cells_analyzed: number;
  prospectivity_tier: string;
}
