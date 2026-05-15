"use client";

import { cn } from "@/lib/cn";
import type { TriageCategory, TriageDecision } from "@/lib/types";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  HelpCircle,
} from "lucide-react";
import { NurseVerdict, type Verdict } from "./NurseVerdict";
import { Tooltip } from "./Tooltip";

const STYLE: Record<
  TriageCategory,
  { ring: string; bg: string; fg: string; Icon: typeof AlertTriangle; pulse: boolean }
> = {
  red: { ring: "ring-triage-red", bg: "bg-triage-redBg", fg: "text-triage-red", Icon: AlertTriangle, pulse: true },
  yellow: { ring: "ring-triage-yellow", bg: "bg-triage-yellowBg", fg: "text-triage-yellow", Icon: Clock3, pulse: false },
  green: { ring: "ring-triage-green", bg: "bg-triage-greenBg", fg: "text-triage-green", Icon: CheckCircle2, pulse: false },
  insufficient: { ring: "ring-triage-gray", bg: "bg-triage-grayBg", fg: "text-triage-gray", Icon: HelpCircle, pulse: false },
};

function formatDecisionTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

export interface TriageCardProps {
  decision: TriageDecision;
  verdict: Verdict | null;
  onVerdictChange: (v: Omit<Verdict, "at">) => void;
}

export function TriageCard({ decision, verdict, onVerdictChange }: TriageCardProps) {
  const style = STYLE[decision.category];
  const { Icon } = style;

  return (
    <div
      className={cn(
        "relative rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-glass p-6 ring-2",
        style.ring,
        style.pulse && "animate-pulseRing",
      )}
    >
      <div className="flex items-center gap-4">
        <div className={cn("rounded-2xl p-3", style.bg)}>
          <Icon className={cn("w-10 h-10", style.fg)} strokeWidth={2} />
        </div>
        <div>
          <div className="text-xs uppercase tracking-wider text-slate-500">
            Önerilen Triaj · Hasta {decision.patient_id}
          </div>
          <div className={cn("text-3xl font-bold mt-1", style.fg)}>{decision.label_tr}</div>
        </div>
        <div className="ml-auto text-right">
          <div className="text-xs text-slate-500 flex items-center justify-end gap-1">
            <span>Güven</span>
            <Tooltip
              content={
                <>
                  <strong>Genel güven</strong>: Supervisor'ın bu karara olan toplam emniyeti. Ajan
                  güvenleri ve ağırlıklı toplamından hesaplanır.
                </>
              }
              align="right"
            />
          </div>
          <div className="text-2xl font-semibold text-slate-800">
            %{Math.round(decision.confidence * 100)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 tabular-nums">
            {formatDecisionTime(decision.decided_at)}
            {decision.latency_ms !== null && ` · ${decision.latency_ms} ms`}
          </div>
        </div>
      </div>

      <p className="mt-5 text-slate-700 leading-relaxed">{decision.rationale_tr}</p>

      <div className="mt-5">
        <div className="flex items-center gap-1 text-xs uppercase tracking-wider text-slate-500 mb-2">
          <span>Ajan ağırlıkları</span>
          <Tooltip
            content={
              <>
                <strong>Ağırlık</strong>: Supervisor'ın bu ajanı nihai karara ne kadar dahil ettiği.
                Düşük güvenli ajan otomatik düşük ağırlık alır.
                <br />
                <strong className="text-emerald-300">Güven ≠ Ağırlık</strong>: Güven ajanın kendi
                ölçümünden, ağırlık supervisor'ın değerlendirmesinden gelir.
              </>
            }
            align="left"
          />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3 text-sm">
          {(["gait", "skin", "respiration", "thermal", "expression"] as const).map((name) => {
            const w = decision.per_agent_weights[name] ?? 0;
            const label =
              name === "gait"
                ? "Yürüyüş"
                : name === "skin"
                  ? "Ten Rengi"
                  : name === "respiration"
                    ? "Solunum"
                    : name === "thermal"
                      ? "Termal"
                      : "İfade";
            return (
              <div key={name} className="rounded-xl border border-slate-200/60 p-3 bg-white/50">
                <div className="text-[11px] uppercase text-slate-500 tracking-wide">{label}</div>
                <div className="mt-2 h-1.5 rounded bg-slate-200/70 overflow-hidden">
                  <div
                    className={cn("h-full", style.fg.replace("text-", "bg-"))}
                    style={{ width: `${Math.max(4, w * 100)}%` }}
                  />
                </div>
                <div className="mt-1 text-xs text-slate-500 tabular-nums">%{Math.round(w * 100)}</div>
              </div>
            );
          })}
        </div>
      </div>

      <NurseVerdict verdict={verdict} onChange={onVerdictChange} />
    </div>
  );
}
