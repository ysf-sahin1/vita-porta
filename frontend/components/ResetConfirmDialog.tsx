"use client";

import { cn } from "@/lib/cn";
import { AlertTriangle, X } from "lucide-react";
import { useEffect, useState } from "react";

export interface ResetConfirmDialogProps {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => Promise<void> | void;
}

export function ResetConfirmDialog({ open, onCancel, onConfirm }: ResetConfirmDialogProps) {
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onCancel]);

  if (!open) return null;

  const handleConfirm = async () => {
    setBusy(true);
    try {
      await onConfirm();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm"
      onClick={onCancel}
    >
      <div
        className="relative max-w-md w-full rounded-3xl bg-white/95 backdrop-blur-xl border border-white/70 shadow-glassLg p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onCancel}
          aria-label="Kapat"
          className="absolute top-4 right-4 rounded-full p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <X className="w-4 h-4" strokeWidth={2.2} />
        </button>

        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-rose-50 p-3 flex-shrink-0">
            <AlertTriangle className="w-6 h-6 text-rose-600" strokeWidth={2.2} />
          </div>
          <div className="flex-1 min-w-0 pr-6">
            <div className="text-lg font-semibold text-slate-900">Geçmişi sıfırla</div>
            <p className="mt-2 text-sm text-slate-600 leading-relaxed">
              Tüm geçmiş triaj kararları ve hemşire verdict kayıtları{" "}
              <strong className="text-slate-900">kalıcı olarak silinecek</strong>. Bu işlem geri
              alınamaz. Devam etmek istediğinizden emin misiniz?
            </p>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="px-4 py-2 rounded-xl bg-white text-slate-700 text-sm font-medium border border-slate-200 hover:bg-slate-50 disabled:opacity-50 transition-colors"
          >
            İptal
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={busy}
            className={cn(
              "px-4 py-2 rounded-xl text-white text-sm font-medium shadow-sm transition-colors",
              busy ? "bg-rose-400 cursor-wait" : "bg-rose-600 hover:bg-rose-700",
            )}
          >
            {busy ? "Siliniyor…" : "Evet, sıfırla"}
          </button>
        </div>
      </div>
    </div>
  );
}
