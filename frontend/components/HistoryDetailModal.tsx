"use client";

import { cn } from "@/lib/cn";
import { formatSignal } from "@/lib/signalLabels";
import type { AgentObservation, TriageCategory } from "@/lib/types";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Droplets,
  Footprints,
  HelpCircle,
  Thermometer,
  X,
} from "lucide-react";
import { useEffect } from "react";
import {
  formatVerdictTime,
  NurseVerdict,
  type Verdict,
} from "./NurseVerdict";
import type { HistoryEntry } from "./useTriageStream";

type AgentKey = "gait" | "skin" | "respiration" | "thermal";

const CATEGORY_STYLE: Record<
  TriageCategory,
  { ring: string; bg: string; fg: string; Icon: typeof AlertTriangle }
> = {
  red: { ring: "ring-triage-red", bg: "bg-triage-redBg", fg: "text-triage-red", Icon: AlertTriangle },
  yellow: {
    ring: "ring-triage-yellow",
    bg: "bg-triage-yellowBg",
    fg: "text-triage-yellow",
    Icon: Clock3,
  },
  green: {
    ring: "ring-triage-green",
    bg: "bg-triage-greenBg",
    fg: "text-triage-green",
    Icon: CheckCircle2,
  },
  insufficient: {
    ring: "ring-triage-gray",
    bg: "bg-triage-grayBg",
    fg: "text-triage-gray",
    Icon: HelpCircle,
  },
};

const AGENT_META: Record<
  AgentKey,
  { label: string; Icon: typeof Activity; color: string; bg: string }
> = {
  gait: { label: "Yürüyüş", Icon: Footprints, color: "text-indigo-600", bg: "bg-indigo-50" },
  skin: { label: "Ten Rengi", Icon: Droplets, color: "text-rose-600", bg: "bg-rose-50" },
  respiration: { label: "Solunum", Icon: Activity, color: "text-sky-600", bg: "bg-sky-50" },
  thermal: { label: "Termal", Icon: Thermometer, color: "text-orange-600", bg: "bg-orange-50" },
};

export interface HistoryDetailModalProps {
  entry: HistoryEntry | null;
  verdict: Verdict | null;
  onVerdictChange: (v: Omit<Verdict, "at">) => void;
  onClose: () => void;
}

export function HistoryDetailModal({
  entry,
  verdict,
  onVerdictChange,
  onClose,
}: HistoryDetailModalProps) {
  useEffect(() => {
    if (!entry) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [entry, onClose]);

  if (!entry) return null;

  const { decision, observations, patientId } = entry;
  const style = CATEGORY_STYLE[decision.category];
  const { Icon } = style;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-40 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-w-3xl w-full max-h-[90vh] overflow-y-auto rounded-3xl bg-white/95 backdrop-blur-xl border border-white/70 shadow-glassLg p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Kapat"
          className="absolute top-4 right-4 rounded-full p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" strokeWidth={2.2} />
        </button>

        <div className="flex items-start gap-4 pr-8">
          <div className={cn("rounded-2xl p-3", style.bg)}>
            <Icon className={cn("w-10 h-10", style.fg)} strokeWidth={2} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase tracking-wider text-slate-500">
              Geçmiş karar · Hasta {patientId}
            </div>
            <div className={cn("text-3xl font-bold mt-1", style.fg)}>
              {decision.label_tr}
            </div>
            <div className="text-xs text-slate-500 mt-1 tabular-nums">
              {formatTime(decision.decided_at)}
              {decision.latency_ms !== null && ` · ${decision.latency_ms} ms`}
              {" · "}
              %{Math.round(decision.confidence * 100)} güven
            </div>
          </div>
        </div>

        <p className="mt-5 text-slate-700 leading-relaxed text-sm">
          {decision.rationale_tr}
        </p>

        <div className="mt-5">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
            O anki ajan gözlemleri
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(Object.keys(AGENT_META) as AgentKey[]).map((agent) => (
              <AgentSummary key={agent} agent={agent} obs={observations[agent]} />
            ))}
          </div>
        </div>

        <NurseVerdict verdict={verdict} onChange={onVerdictChange} />
      </div>
    </div>
  );
}

function AgentSummary({ agent, obs }: { agent: AgentKey; obs: AgentObservation | undefined }) {
  const meta = AGENT_META[agent];
  const { Icon } = meta;
  if (!obs) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/40 p-3">
        <div className="flex items-center gap-2">
          <div className={cn("rounded-lg p-1.5", meta.bg)}>
            <Icon className={cn("w-4 h-4", meta.color)} strokeWidth={2.2} />
          </div>
          <span className="text-xs font-semibold text-slate-500">{meta.label}</span>
        </div>
        <p className="text-xs text-slate-400 mt-2">Veri yok</p>
      </div>
    );
  }
  const labeledSignals = Object.entries(obs.signals)
    .map(([k, v]) => formatSignal(k, v))
    .filter((s): s is NonNullable<typeof s> => s !== null)
    .slice(0, 5);
  return (
    <div className="rounded-xl border border-slate-200/70 bg-white/70 p-3">
      <div className="flex items-center gap-2">
        <div className={cn("rounded-lg p-1.5", meta.bg)}>
          <Icon className={cn("w-4 h-4", meta.color)} strokeWidth={2.2} />
        </div>
        <span className={cn("text-xs font-semibold", meta.color)}>{meta.label}</span>
        <span className="ml-auto text-[11px] text-slate-500 tabular-nums">
          %{Math.round(obs.confidence * 100)}
        </span>
      </div>
      <p className="text-xs text-slate-700 mt-2 leading-relaxed">{obs.summary_tr}</p>
      {labeledSignals.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {labeledSignals.map((s, i) => (
            <span
              key={i}
              className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-600"
            >
              {s.label}: {s.display}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return formatVerdictTime(d);
}
