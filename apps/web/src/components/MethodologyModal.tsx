"use client";

import React from "react";
import { X, ShieldAlert, FileText, CheckCircle2, AlertTriangle, Layers, Database } from "lucide-react";

interface MethodologyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MethodologyModal: React.FC<MethodologyModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-slate-900 border border-cyan-800/60 rounded-2xl shadow-2xl flex flex-col text-slate-200 overflow-hidden font-sans">
        {/* Header del Modal */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-950 border border-cyan-700/50 text-cyan-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 tracking-tight">
                Metodología, Model Card y Limitaciones Científicas
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                GeoAI-Au v1.0 — Cadena Metodológica Sellada B → H
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido con scroll */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs leading-relaxed text-slate-300 scrollbar-thin">
          {/* Aviso Fundamental */}
          <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-600/50 text-amber-200 flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-bold text-sm text-amber-300 mb-1">
                Guardarraíl Metodológico de Interpretación
              </h3>
              <p className="text-[11px] text-amber-200/90 leading-normal">
                GeoAI-Au es un sistema de priorización territorial a escala regional (1 km²).
                El índice predictivo representa <strong>favorabilidad geológica relativa</strong> (<em>prospectivity/favorability score</em>)
                derivada de un clasificador lineal entrenado con muestreo sintético P/U (ratio 3).
                <strong>Bajo ningún concepto debe interpretarse como probabilidad física o estadística calibrada de encontrar un yacimiento ni como estimación de leyes o reservas minerales.</strong>
              </p>
            </div>
          </div>

          {/* 1. Model Card */}
          <div className="space-y-2">
            <h3 className="font-bold text-sm text-cyan-400 uppercase tracking-wider flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-cyan-400" />
              <span>1. Resumen del Modelo (Model Card)</span>
            </h3>
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 font-mono text-[11px] space-y-1">
              <div><strong>Algoritmo:</strong> Regresión Logística L2 (<code className="text-cyan-300">C=0.1, solver='lbfgs', max_iter=3000</code>).</div>
              <div><strong>Pipeline:</strong> <code className="text-slate-300">FeatureGuard → SimpleImputer(median) → StandardScaler() → LogisticRegression()</code>.</div>
              <div><strong>Predictores:</strong> Exactamente 56 variables continuas aprobadas (19 litologías, 27 cronoestratigrafías, 3 distancias estructurales, 6 morfometrías y 1 hidrológica).</div>
              <div><strong>Anti-Fuga (Leakage):</strong> El vector X excluye distancias a minas conocidas, nombres o indicios minerales.</div>
              <div><strong>Odds Ratio:</strong> exp(β) refleja el cambio multiplicativo en odds por +1 desviación estándar (+1σ) tras StandardScaler.</div>
            </div>
          </div>

          {/* 2. Procedencia B -> H */}
          <div className="space-y-2">
            <h3 className="font-bold text-sm text-amber-400 uppercase tracking-wider flex items-center gap-2">
              <Database className="w-4 h-4 text-amber-400" />
              <span>2. Cadena de Datos y Soporte Territorial</span>
            </h3>
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1.5 text-[11px]">
              <p>
                <strong>Inventario Auditado (Fase B):</strong> 790 registros BDMIN evaluados formalmente: 190 ocurrencias confirmadas (46 depósitos, 32 distritos), 597 pendientes en cuarentena y 3 rechazadas.
              </p>
              <p>
                <strong>Soporte Canónico (Fase D):</strong> Máscara <code className="text-cyan-300 font-mono">eligible_approved_features</code> con 478.443 celdas terrestres de 1 km² (96,3% de España peninsular), cubriendo 45 depósitos (incluyendo Salave recuperado tras auditar cobertura).
              </p>
              <p>
                <strong>Protocolo de CV (Fases E y F):</strong> Nested spatial block CV sobre desarrollo (bloques de 50 km + gap de 5 km) con 15 particiones internas de ajuste para selección determinista del pipeline.
              </p>
            </div>
          </div>

          {/* 3. Validación y Brecha de Transferencia */}
          <div className="space-y-2">
            <h3 className="font-bold text-sm text-emerald-400 uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-emerald-400" />
              <span>3. Evaluación Ciega en Holdout y Brecha de Transferencia</span>
            </h3>
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1.5 text-[11px]">
              <p>
                <strong>Apertura de la Reserva Ciega (Fase G):</strong> 5 distritos completos aislados durante todo el diseño (13.541 celdas, 8 depósitos test).
              </p>
              <p>
                <strong>Rendimiento Observado:</strong> Deposit Recovery @5% = 12,50% (1/8: Rodalquilar Cinto), Recovery @10% = 25,00% (2/8: Rodalquilar Cinto y La Oriental). ROC-AUC = 0,5807.
              </p>
              <p>
                <strong>Brecha de Transferencia (N=8):</strong> La diferencia respecto a la validación de desarrollo (ROC-AUC 0,7402) refleja la heterogeneidad regional extrema entre los distritos de entrenamiento (orogénicos, placeres) y los de test (epitermales terciarios en Cabo de Gata, leucogranitos hercínicos en Costa da Morte).
              </p>
            </div>
          </div>

          {/* 4. Interpretación de Coeficientes y No Causalidad */}
          <div className="space-y-2">
            <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              <span>4. Interpretación de Coeficientes Específicos</span>
            </h3>
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1.5 text-[11px]">
              <p>
                <strong>Coeficiente de Distancia a Fallas (β = +0,2122):</strong> Formulado estrictamente como <em>hipótesis geológica de escala</em> (efecto de colinealidad con cabalgamientos en regresión regularizada y resolución cartográfica regional 1:1.000.000), no como mecanismo físico de que el oro 'evite' fallas.
              </p>
              <p>
                <strong>Anotación Post-Hoc en Targets:</strong> En el catálogo de las 1.529 zonas priorizadas, las distancias a depósitos conocidos son una mera anotación geográfica post-hoc y no intervinieron en la predicción.
              </p>
            </div>
          </div>
        </div>

        {/* Footer del Modal */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition-colors cursor-pointer"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
};
