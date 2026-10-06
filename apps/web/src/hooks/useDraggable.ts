"use client";

import { useState, useRef, useCallback, useEffect } from "react";

interface UseDraggableOptions {
  defaultOffset?: { x: number; y: number };
  minY?: number;
}

export function useDraggable(options: UseDraggableOptions = {}) {
  const { defaultOffset = { x: 0, y: 0 }, minY = 56 } = options;
  const [offset, setOffset] = useState<{ x: number; y: number }>(defaultOffset);
  const [isDragging, setIsDragging] = useState(false);

  const elementRef = useRef<HTMLDivElement | null>(null);
  const isDraggingRef = useRef(false);
  const offsetRef = useRef<{ x: number; y: number }>(defaultOffset);
  const rafIdRef = useRef<number | null>(null);

  const dragInfoRef = useRef<{
    startX: number;
    startY: number;
    originX: number;
    originY: number;
    windowWidth: number;
    windowHeight: number;
    isCentered: boolean;
  }>({
    startX: 0,
    startY: 0,
    originX: 0,
    originY: 0,
    windowWidth: 0,
    windowHeight: 0,
    isCentered: false,
  });

  useEffect(() => {
    offsetRef.current = offset;
  }, [offset]);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    if (e.button !== 0) return;

    // Ignorar si se hace clic en botones, inputs o enlaces interactivos
    const target = e.target as HTMLElement;
    if (
      target.tagName === "BUTTON" ||
      target.tagName === "INPUT" ||
      target.tagName === "SELECT" ||
      target.closest("button") ||
      target.closest("input") ||
      target.closest("select")
    ) {
      return;
    }

    e.preventDefault();
    isDraggingRef.current = true;
    setIsDragging(true);

    const elem = elementRef.current;
    const isCentered = elem ? elem.style.transform.includes("calc(-50%") : false;

    dragInfoRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      originX: offsetRef.current.x,
      originY: offsetRef.current.y,
      windowWidth: typeof window !== "undefined" ? window.innerWidth : 1200,
      windowHeight: typeof window !== "undefined" ? window.innerHeight : 800,
      isCentered,
    };

    if (elem) {
      elem.style.willChange = "transform";
      elem.style.transition = "none";
    }

    try {
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    } catch {
      // Ignorar si el navegador no soporta pointer capture
    }
  }, []);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDraggingRef.current || !elementRef.current) return;

    const info = dragInfoRef.current;
    const dx = e.clientX - info.startX;
    const dy = e.clientY - info.startY;

    let newX = info.originX + dx;
    let newY = info.originY + dy;

    // Limites de pantalla de alta velocidad (sin disparar reflow / getBoundingClientRect)
    const maxBoundX = info.windowWidth * 0.48;
    const minBoundX = -info.windowWidth * 0.48;
    const maxBoundY = info.windowHeight - 80;
    const minBoundY = -info.windowHeight * 0.4;

    newX = Math.max(minBoundX, Math.min(maxBoundX, newX));
    newY = Math.max(minBoundY, Math.min(maxBoundY, newY));

    offsetRef.current = { x: newX, y: newY };

    // Actualización directa al hardware GPU con requestAnimationFrame
    if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    rafIdRef.current = requestAnimationFrame(() => {
      if (elementRef.current) {
        if (info.isCentered) {
          elementRef.current.style.transform = `translate3d(calc(-50% + ${newX}px), ${newY}px, 0)`;
        } else {
          elementRef.current.style.transform = `translate3d(${newX}px, ${newY}px, 0)`;
        }
      }
    });
  }, []);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (!isDraggingRef.current) return;
    isDraggingRef.current = false;
    setIsDragging(false);

    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }

    if (elementRef.current) {
      elementRef.current.style.willChange = "auto";
      elementRef.current.style.transition = "";
    }

    // Sincronizar estado React final
    setOffset({ ...offsetRef.current });

    try {
      (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      // Ignorar si el puntero ya fue liberado
    }
  }, []);

  const resetPosition = useCallback(() => {
    offsetRef.current = defaultOffset;
    if (elementRef.current) {
      const isCentered = elementRef.current.style.transform.includes("calc(-50%");
      if (isCentered) {
        elementRef.current.style.transform = `translate3d(calc(-50% + ${defaultOffset.x}px), ${defaultOffset.y}px, 0)`;
      } else {
        elementRef.current.style.transform = `translate3d(${defaultOffset.x}px, ${defaultOffset.y}px, 0)`;
      }
    }
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
      onPointerCancel: handlePointerUp,
      style: {
        touchAction: "none" as const,
        cursor: isDragging ? "grabbing" : "grab"
      }
    }
  };
}
