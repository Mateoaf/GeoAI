"use client";

import { useState, useRef, useEffect, useCallback } from "react";

interface UseDraggableOptions {
  defaultOffset?: { x: number; y: number };
  minY?: number; // margen superior (ej. altura del header = 56px)
}

export function useDraggable(options: UseDraggableOptions = {}) {
  const { defaultOffset = { x: 0, y: 0 }, minY = 56 } = options;
  const [offset, setOffset] = useState<{ x: number; y: number }>(defaultOffset);
  const [isDragging, setIsDragging] = useState(false);

  const dragStartRef = useRef<{
    startX: number;
    startY: number;
    initialOffsetX: number;
    initialOffsetY: number;
  }>({ startX: 0, startY: 0, initialOffsetX: 0, initialOffsetY: 0 });

  const elementRef = useRef<HTMLDivElement | null>(null);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    // Solo responder al botón principal (izquierdo o toque)
    if (e.button !== 0) return;

    // Evitar que inputs o botones dentro del header disparen drag
    const target = e.target as HTMLElement;
    if (
      target.tagName === "BUTTON" ||
      target.tagName === "INPUT" ||
      target.tagName === "SELECT" ||
      target.closest("button") ||
      target.closest("input")
    ) {
      return;
    }

    e.preventDefault();
    setIsDragging(true);

    dragStartRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      initialOffsetX: offset.x,
      initialOffsetY: offset.y
    };

    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }, [offset]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging) return;

    const dx = e.clientX - dragStartRef.current.startX;
    const dy = e.clientY - dragStartRef.current.startY;

    let newX = dragStartRef.current.initialOffsetX + dx;
    let newY = dragStartRef.current.initialOffsetY + dy;

    // Clamping con respecto a los bordes de la ventana
    if (elementRef.current && typeof window !== "undefined") {
      const rect = elementRef.current.getBoundingClientRect();
      const currentTop = rect.top;
      const currentBottom = rect.bottom;
      const currentLeft = rect.left;
      const currentRight = rect.right;

      // Si se pasa del header arriba
      if (currentTop + dy < minY) {
        newY = dragStartRef.current.initialOffsetY + (minY - (currentTop - dy));
      }
      // Si se pasa del fondo abajo
      if (currentBottom + dy > window.innerHeight - 10) {
        newY = dragStartRef.current.initialOffsetY + (window.innerHeight - 10 - (currentBottom - dy));
      }
      // Bordes laterales
      if (currentLeft + dx < 10) {
        newX = dragStartRef.current.initialOffsetX + (10 - (currentLeft - dx));
      }
      if (currentRight + dx > window.innerWidth - 10) {
        newX = dragStartRef.current.initialOffsetX + (window.innerWidth - 10 - (currentRight - dx));
      }
    }

    setOffset({ x: newX, y: newY });
  }, [isDragging, minY]);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (!isDragging) return;
    setIsDragging(false);
    try {
      (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      // Ignorar si el puntero ya fue liberado
    }
  }, [isDragging]);

  const resetPosition = useCallback(() => {
    setOffset(defaultOffset);
  }, [defaultOffset]);

  return {
    offset,
    isDragging,
    elementRef,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    resetPosition,
    dragProps: {
      onPointerDown: handlePointerDown,
      onPointerMove: handlePointerMove,
      onPointerUp: handlePointerUp,
      style: {
        touchAction: "none" as const,
        cursor: isDragging ? "grabbing" : "grab"
      }
    }
  };
}
