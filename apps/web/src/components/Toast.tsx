"use client";

import React, { useEffect } from "react";
import { Sparkles, CheckCircle2, AlertCircle, Info, X } from "lucide-react";

export interface ToastMessage {
  id: string;
  message: string;
  type?: "success" | "info" | "warning";
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none select-none">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  );
};

const ToastItem: React.FC<{ toast: ToastMessage; onDismiss: (id: string) => void }> = ({
  toast,
  onDismiss
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, 3200);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  return (
    <div
      onClick={() => onDismiss(toast.id)}
      className="pointer-events-auto flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-slate-950/95 backdrop-blur-2xl border border-cyan-500/50 text-slate-100 text-xs font-sans shadow-2xl shadow-cyan-950/50 cursor-pointer animate-in fade-in slide-in-from-bottom-3 duration-200 hover:border-cyan-400 ring-1 ring-white/10"
    >
      <div className="w-5 h-5 rounded-md bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center shrink-0">
        <Sparkles className="w-3 h-3 text-cyan-300" />
      </div>
      <span className="font-medium text-slate-200">{toast.message}</span>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDismiss(toast.id);
        }}
        className="ml-2 text-slate-400 hover:text-white p-0.5 rounded"
      >
        <X className="w-3 h-3" />
      </button>
    </div>
  );
};
