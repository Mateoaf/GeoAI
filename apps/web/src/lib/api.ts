/**
 * apps/web/src/lib/api.ts
 * Cliente API para conectar con el backend de GeoAI-Au Explorer.
 */

import {
  ProjectSummary,
  CellResponse,
  CellExplainResponse,
  TargetsResponse,
  TargetZone,
  ValidationSummaryResponse,
  ValidationDepositsResponse,
  ValidationDistrictsResponse,
  ModelCoefficient,
  CopilotQuery,
  CopilotResponse
} from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, options);
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errJson = await res.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // Ignorar fallback
    }
    throw new Error(`Error en API (${res.status}): ${errorDetail}`);
  }
  return res.json();
}

export const api = {
  getProjectSummary: async (): Promise<ProjectSummary> => {
    const data = await fetchJson<{ summary: ProjectSummary }>("/api/project/summary");
    return data.summary;
  },

  getCellByCoordinate: async (lat: number, lon: number): Promise<CellResponse> => {
    return fetchJson<CellResponse>(`/api/cell/by-coordinate?lat=${lat}&lon=${lon}`);
  },

  getCellById: async (cellId: string): Promise<CellResponse> => {
    return fetchJson<CellResponse>(`/api/cell/${cellId}`);
  },

  explainCell: async (cellId: string): Promise<CellExplainResponse> => {
    return fetchJson<CellExplainResponse>(`/api/cell/${cellId}/explain`);
  },

  getTargets: async (params?: {
    categoria?: string;
    distrito?: string;
    min_score?: number;
    sin_deposito_cercano?: boolean;
    limit?: number;
  }): Promise<TargetsResponse> => {
    const query = new URLSearchParams();
    if (params?.categoria) query.set("categoria", params.categoria);
    if (params?.distrito) query.set("distrito", params.distrito);
    if (params?.min_score !== undefined) query.set("min_score", params.min_score.toString());
    if (params?.sin_deposito_cercano) query.set("sin_deposito_cercano", "true");
    if (params?.limit) query.set("limit", params.limit.toString());

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchJson<TargetsResponse>(`/api/targets${qs}`);
  },

  getTargetById: async (zonaId: string): Promise<TargetZone> => {
    return fetchJson<TargetZone>(`/api/targets/${zonaId}`);
  },

  getTargetsGeoJSON: async (): Promise<any> => {
    return fetchJson<any>("/api/targets/geojson");
  },

  getDepositsGeoJSON: async (): Promise<any> => {
    return fetchJson<any>("/api/deposits");
  },

  getValidationSummary: async (): Promise<ValidationSummaryResponse> => {
    return fetchJson<ValidationSummaryResponse>("/api/validation/summary");
  },

  getValidationDeposits: async (): Promise<ValidationDepositsResponse> => {
    return fetchJson<ValidationDepositsResponse>("/api/validation/deposits");
  },

  getValidationDistricts: async (): Promise<ValidationDistrictsResponse> => {
    return fetchJson<ValidationDistrictsResponse>("/api/validation/districts");
  },

  getValidationComparison: async (): Promise<any> => {
    return fetchJson<any>("/api/validation/comparison");
  },

  getModelCoefficients: async (): Promise<{ coefficients: ModelCoefficient[]; intercept: number }> => {
    return fetchJson<{ coefficients: ModelCoefficient[]; intercept: number }>("/api/model/coefficients");
  },

  queryCopilot: async (query: CopilotQuery): Promise<CopilotResponse> => {
    return fetchJson<CopilotResponse>("/api/copilot/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(query)
    });
  },

  getIndiciosGeoJSON: async (tipo_au?: string): Promise<any> => {
    const qs = tipo_au && tipo_au !== "todos" ? `?tipo_au=${encodeURIComponent(tipo_au)}` : "";
    return fetchJson<any>(`/api/indicios${qs}`);
  },

  getDistrictsGeoJSON: async (): Promise<any> => {
    return fetchJson<any>("/api/districts");
  },

  getBufferAnalysis: async (lat: number, lon: number, radiusKm: number = 10): Promise<any> => {
    return fetchJson<any>(`/api/spatial/buffer-analysis?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`);
  }
};
