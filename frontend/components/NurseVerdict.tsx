"use client";

import { cn } from "@/lib/cn";
import type { TriageCategory } from "@/lib/types";
import { Check, PencilLine, X } from "lucide-react";
import { useState } from "react";

export type Verdict = {
  action: "approved" | "rejected" | "modified";
  category?: TriageCategory;
  at: string;
};

export interface NurseVerdictProps {
  verdict: Verdict | null;
  onChange: (v: Omit<Verdict, "at">) => void;
  compact?: boolean;
}

export function NurseVerdict({ verdict, onChange, compact = false }: NurseVerdictProps) {
  const [modifying, setModifying] = useState(false);

  if (verdict) {
    return (
      <div className={cn(compact ? "mt-3" : "mt-5 pt-4 border-t border-slate-200/60")}>
        <VerdictBanner verdict={verdict} />
        <ChromaNotice />
      </div>
    );
  }

  return (
    <div className={cn(compact ? "mt-3" : "mt-5 pt-4 border-t border-slate-200/60")}>
      <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-2">Hemşire kararı</div>
      {modifying ? (
        <CategoryPicker
          onPick={(cat) => {
            onChange({ action: "modified", category: cat });
            setModifying(false);
          }}
          onCancel={() => setModifying(false)}
        />
      ) : (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onChange({ action: "approved" })}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 shadow-sm transition-colors"
          >
            <Check className="w-4 h-4" strokeWidth={2.4} /> Onayla
          </button>
          <button
            onClick={() => onChange({ action: "rejected" })}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-600 text-white text-sm font-medium hover:bg-rose-700 shadow-sm transition-colors"
          >
            <X className="w-4 h-4" strokeWidth={2.4} /> Reddet
          </button>
          <button
            onClick={() => setModifying(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white text-slate-700 text-sm font-medium border border-slate-200 hover:bg-slate-50 shadow-sm transition-colors"
          >
            <PencilLine className="w-4 h-4" strokeWidth={2.2} /> Değiştir
          </button>
        </div>
      )}
      <ChromaNotice />
    </div>
  );
}

export function verdictIcon(action: Verdict["action"]) {
  if (action === "approved") return Check;
  if (action === "rejected") return X;
  return PencilLine;
}

export function verdictColorClass(action: Verdict["action"]): string {
  if (action === "approved") return "text-emerald-600";
  if (action === "rejected") return "text-rose-600";
  return "text-amber-600";
}

function VerdictBanner({ verdict }: { verdict: Verdict }) {
  const map: Record<Verdict["action"], { label: string; cls: string; Icon: typeof Check }> = {
    approved: {
      label: "Hemşire kararı onayladı",
      cls: "bg-emerald-50 text-emerald-800 border-emerald-200",
      Icon: Check,
    },
    rejected: {
      label: "Hemşire kararı reddetti",
      cls: "bg-rose-50 text-rose-800 border-rose-200",
      Icon: X,
    },
    modified: {
      label: "Hemşire kararı değiştirdi",
      cls: "bg-amber-50 text-amber-800 border-amber-200",
      Icon: PencilLine,
    },
  };
  const m = map[verdict.action];
  const I = m.Icon;
  const catLabel = verdict.category
    ? verdict.category === "red"
      ? "Kırmızı"
      : verdict.category === "yellow"
        ? "Sarı"
        : verdict.category === "green"
          ? "Yeşil"
          : "Yetersiz"
    : null;
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium",
        m.cls,
      )}
    >
      <I className="w-4 h-4" strokeWidth={2.4} />
      <span>{m.label}</span>
      {catLabel && (
        <span className="px-2 py-0.5 rounded-full bg-white/70 text-xs font-semibold">
          → {catLabel}
        </span>
      )}
      <span className="text-xs opacity-70 tabular-nums">· {verdict.at}</span>
    </div>
  );
}

function CategoryPicker({
  onPick,
  onCancel,
}: {
  onPick: (cat: TriageCategory) => void;
  onCancel: () => void;
}) {
  const options: { cat: TriageCategory; label: string; cls: string }[] = [
    { cat: "red", label: "Kırmızı", cls: "bg-triage-red hover:bg-red-700" },
    { cat: "yellow", label: "Sarı", cls: "bg-triage-yellow hover:bg-yellow-600" },
    { cat: "green", label: "Yeşil", cls: "bg-triage-green hover:bg-green-700" },
  ];
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs text-slate-500">Yeni kategori:</span>
      {options.map((o) => (
        <button
          key={o.cat}
          onClick={() => onPick(o.cat)}
          className={cn(
            "px-3 py-1.5 rounded-lg text-white text-sm font-medium shadow-sm transition-colors",
            o.cls,
          )}
        >
          {o.label}
        </button>
      ))}
      <button
        onClick={onCancel}
        className="px-3 py-1.5 rounded-lg text-slate-500 text-sm hover:text-slate-700"
      >
        İptal
      </button>
    </div>
  );
}

function ChromaNotice() {
  return (
    <p className="mt-3 text-[11px] italic text-slate-400 leading-relaxed">
      Hemşire kararı kalıcı olarak kaydedilir; benzer sinyallere sahip bir sonraki hastada
      sistem bu kararı "geçmiş deneyim" olarak referans alır.
    </p>
  );
}

export function formatVerdictTime(d: Date = new Date()): string {
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}
