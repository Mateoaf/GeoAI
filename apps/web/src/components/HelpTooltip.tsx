"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { HelpCircle, X, Sparkles, Lightbulb } from "lucide-react";
import { GLOSSARY, GlossaryEntry } from "../lib/glossary";

interface HelpTooltipProps {
  term?: keyof typeof GLOSSARY | string;
  title?: string;
  summary?: string;
  example?: string;
  category?: string;
  className?: string;
  iconSize?: "sm" | "md" | "xs";
}

export const HelpTooltip: React.FC<HelpTooltipProps> = ({
  term,
  title: customTitle,
  summary: customSummary,
  example: customExample,
  category: customCategory,
  className = "",
  iconSize = "sm"
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [coords, setCoords] = useState<{ top: number; left: number; placement: "right" | "left" | "bottom" }>({
    top: 0,
    left: 0,
    placement: "right"
  });

  const buttonRef = useRef<HTMLButtonElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const data: GlossaryEntry = (term && GLOSSARY[term])
    ? GLOSSARY[term]
    : {
        title: customTitle || "Información",
        category: (customCategory as any) || "Concepto Geológico",
        summary: customSummary || "",
        example: customExample,
        badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
      };

  const updatePosition = useCallback(() => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    const tooltipWidth = 320;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let left = rect.right + 10;
    let top = rect.top - 10;
    let placement: "right" | "left" | "bottom" = "right";

    // Si no cabe a la derecha, colocar a la izquierda
    if (left + tooltipWidth > viewportWidth - 20) {
      left = rect.left - tooltipWidth - 10;
      placement = "left";
    }

    // En pantallas pequeñas (móviles), centrar horizontalmente abajo
    if (viewportWidth < 640 || left < 10) {
      left = Math.max(10, Math.min(viewportWidth - tooltipWidth - 10, rect.left - tooltipWidth / 2));
      top = rect.bottom + 8;
      placement = "bottom";
    }

    // Asegurar que no se salga por abajo
    if (top + 220 > viewportHeight) {
      top = Math.max(10, viewportHeight - 240);
    }

    setCoords({ top, left, placement });
  }, []);

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    updatePosition();
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setIsOpen(false);
    }, 200);
  };

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    updatePosition();
    setIsOpen((prev) => !prev);
  };

  // Cerrar al hacer clic fuera o pulsar Escape
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        tooltipRef.current &&
        !tooltipRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const sizeClasses = {
    xs: "w-3 h-3",
    sm: "w-3.5 h-3.5",
    md: "w-4 h-4"
  }[iconSize];

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        onClick={handleClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        aria-label={`Explicación: ${data.title}`}
        className={`inline-flex items-center justify-center p-0.5 rounded-full text-slate-400 hover:text-cyan-300 hover:bg-cyan-950/40 transition-all cursor-pointer focus:outline-none focus:ring-1 focus:ring-cyan-400 shrink-0 ${className}`}
        title="Haz clic o pasa el cursor para ver qué significa en cristiano"
      >
        <HelpCircle className={`${sizeClasses} hover:scale-110 transition-transform`} />
      </button>

      {mounted &&
        isOpen &&
        createPortal(
          <div
            ref={tooltipRef}
            onMouseEnter={() => {
              if (timeoutRef.current) clearTimeout(timeoutRef.current);
            }}
            onMouseLeave={handleMouseLeave}
            style={{
              position: "fixed",
              top: `${coords.top}px`,
              left: `${coords.left}px`,
              zIndex: 9999
            }}
            className="w-80 max-w-[92vw] bg-slate-950/98 backdrop-blur-2xl border border-cyan-800/70 rounded-2xl shadow-2xl p-3.5 text-slate-200 text-xs animate-in fade-in zoom-in-95 duration-150 select-text"
          >
            {/* Cabecera */}
            <div className="flex items-start justify-between gap-2 pb-2 mb-2 border-b border-slate-800/80">
              <div className="space-y-1">
                <span className="font-bold text-slate-100 text-[12px] block leading-snug">
                  {data.title}
                </span>
                {data.category && (
                  <span
                    className={`inline-block text-[9px] font-mono px-2 py-0.5 rounded-full border font-bold uppercase tracking-wider ${
                      data.badgeColor || "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
                    }`}
                  >
                    {data.category}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsOpen(false);
                }}
                className="p-1 rounded text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
                title="Cerrar explicación"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Explicación en lenguaje para todos los públicos */}
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans mb-2.5">
              {data.summary}
            </p>

            {/* Ejemplo o dato curioso */}
            {data.example && (
              <div className="p-2 rounded-xl bg-slate-900/90 border border-slate-800 text-[10px] text-slate-400 font-sans flex items-start gap-2">
                <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                <span className="leading-snug text-slate-300 font-medium">{data.example}</span>
              </div>
            )}
          </div>,
          document.body
        )}
    </>
  );
};
