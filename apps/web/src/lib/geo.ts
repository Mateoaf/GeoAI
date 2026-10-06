/**
 * Funciones geodésicas y de conversión de coordenadas para el proyecto GeoAI España.
 * Sistema de referencia proyectado: ETRS89 / UTM Huso 30N (EPSG:25830).
 * Sistema de referencia geográfico: WGS84 / ETRS89 (EPSG:4326).
 */

/**
 * Convierte coordenadas proyectadas UTM Huso 30N (EPSG:25830) a coordenadas geográficas WGS84 (lon, lat).
 * Algoritmo Snyder con precisión sub-milimétrica.
 */
export function utm30ToWgs84(x: number, y: number): { lon: number; lat: number } {
  const a = 6378137.0; // Semieje mayor WGS84
  const f = 1 / 298.257223563;
  const e2 = 2 * f - f * f;
  const ePrime2 = e2 / (1 - e2);
  const k0 = 0.9996;
  const lon0 = (-3.0 * Math.PI) / 180.0; // Meridiano central de UTM Huso 30N: 3° W

  const xAdj = x - 500000.0;
  const yAdj = y;

  const M = yAdj / k0;
  const mu = M / (a * (1 - e2 / 4 - (3 * e2 * e2) / 64 - (5 * Math.pow(e2, 3)) / 256));

  const e1 = (1 - Math.sqrt(1 - e2)) / (1 + Math.sqrt(1 - e2));
  const J1 = (3 * e1) / 2 - (27 * Math.pow(e1, 3)) / 32;
  const J2 = (21 * Math.pow(e1, 2)) / 16 - (55 * Math.pow(e1, 4)) / 32;
  const J3 = (151 * Math.pow(e1, 3)) / 96;
  const J4 = (1097 * Math.pow(e1, 4)) / 512;

  const fp =
    mu +
    J1 * Math.sin(2 * mu) +
    J2 * Math.sin(4 * mu) +
    J3 * Math.sin(6 * mu) +
    J4 * Math.sin(8 * mu);

  const C1 = ePrime2 * Math.pow(Math.cos(fp), 2);
  const T1 = Math.pow(Math.tan(fp), 2);
  const R1 = (a * (1 - e2)) / Math.pow(1 - e2 * Math.pow(Math.sin(fp), 2), 1.5);
  const N1 = a / Math.sqrt(1 - e2 * Math.pow(Math.sin(fp), 2));
  const D = xAdj / (N1 * k0);

  const latRad =
    fp -
    ((N1 * Math.tan(fp)) / R1) *
      (Math.pow(D, 2) / 2 -
        ((5 + 3 * T1 + 10 * C1 - 4 * Math.pow(C1, 2) - 9 * ePrime2) * Math.pow(D, 4)) / 24 +
        ((61 + 90 * T1 + 298 * C1 + 45 * Math.pow(T1, 2) - 252 * ePrime2 - 3 * Math.pow(C1, 2)) *
          Math.pow(D, 6)) /
          720);

  const lonRad =
    lon0 +
    (D -
      ((1 + 2 * T1 + C1) * Math.pow(D, 3)) / 6 +
      ((5 - 2 * C1 + 28 * T1 - 3 * Math.pow(C1, 2) + 8 * ePrime2 + 24 * Math.pow(T1, 2)) *
        Math.pow(D, 5)) /
        120) /
      Math.cos(fp);

  return {
    lon: (lonRad * 180.0) / Math.PI,
    lat: (latRad * 180.0) / Math.PI
  };
}

/**
 * Formatea un par de coordenadas WGS84 en notación legible.
 */
export function formatWgs84(lat: number, lon: number, decimals: number = 4): string {
  const ns = lat >= 0 ? "N" : "S";
  const ew = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(decimals)}° ${ns}, ${Math.abs(lon).toFixed(decimals)}° ${ew}`;
}

/**
 * Formatea coordenadas UTM30 ETRS89 en metros.
 */
export function formatUtm30(x: number, y: number): string {
  return `X=${Math.round(x).toLocaleString()} m, Y=${Math.round(y).toLocaleString()} m (UTM30N)`;
}
