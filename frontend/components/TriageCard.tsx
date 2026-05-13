"use client";

import { cn } from "@/lib/cn";
import type { TriageCategory, TriageDecision } from "@/lib/types";
import { AlertTriangle, CheckCircle2, Clock3, HelpCircle } from "lucide-react";

const STYLE: Record<
  TriageCategory,
  { ring: string; bg: string; fg: string; Icon: typeof AlertTriangle; pulse: boolean }
> = {
  red: { ring: "ring-triage-red", bg: "bg-triage-redBg", fg: "text-triage-red", Icon: AlertTriangle, pulse: true },
  yellow: { ring: "ring-triage-yellow", bg: "bg-triage-yellowBg", fg: "text-triage-yellow", Icon: Clock3, pulse: false },
  green: { ring: "ring-triage-green", bg: "bg-triage-greenBg", fg: "text-triage-green", Icon: CheckCircle2, pulse: false },
  insufficient: { ring: "ring-triage-gray", bg: "bg-triage-grayBg", fg: "text-triage-gray", Icon: HelpCircle, pulse: false },
};

export function TriageCard({ decision }: { decision: TriageDecision }) {
  const style = STYLE[decision.category];
  const { Icon } = style;

  return (
    <div
      className={cn(
        "relative rounded-2xl border bg-white shadow-sm p-6 ring-2",
        style.ring,
        style.pulse && "animate-pulseRing",
      )}
    >
      <div className="flex items-center gap-4">
        <div className={cn("rounded-xl p-3", style.bg)}>
          <Icon className={cn("w-10 h-10", style.fg)} />
        </div>
        <div>
          <div className="text-xs uppercase tracking-wider text-slate-500">
            Önerilen Triaj · Hasta {decision.patient_id}
          </div>
          <div className={cn("text-3xl font-bold mt-1", style.fg)}>{decision.label_tr}</div>
        </div>
        <div className="ml-auto text-right">
          <div className="text-xs text-slate-500">Güven</div>
          <div className="text-2xl font-semibold text-slate-800">
            %{Math.round(decision.confidence * 100)}
          </div>
          {decision.latency_ms !== null && (
            <div className="text-[11px] text-slate-400 mt-1">
              {decision.latency_ms} ms
            </div>
          )}
        </div>
      </div>
      <p className="mt-5 text-slate-700 leading-relaxed">{decision.rationale_tr}</p>
      <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        {(["gait", "skin", "respiration", "thermal"] as const).map((name) => {
          const w = decision.per_agent_weights[name] ?? 0;
          const label =
            name === "gait"
              ? "Yürüyüş"
              : name === "skin"
                ? "Ten Rengi"
                : name === "respiration"
                  ? "Solunum"
                  : "Termal";
          return (
            <div key={name} className="rounded-lg border border-slate-200 p-3 bg-slate-50/50">
              <div className="text-[11px] uppercase text-slate-500 tracking-wide">{label}</div>
              <div className="mt-2 h-1.5 rounded bg-slate-200 overflow-hidden">
                <div
                  className={cn("h-full", style.fg.replace("text-", "bg-"))}
                  style={{ width: `${Math.max(4, w * 100)}%` }}
                />
              </div>
              <div className="mt-1 text-xs text-slate-500">%{Math.round(w * 100)} ağırlık</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
