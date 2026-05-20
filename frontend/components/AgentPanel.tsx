"use client";

import { cn } from "@/lib/cn";
import { inferAgentReason } from "@/lib/agentReasons";
import { formatSignal } from "@/lib/signalLabels";
import type { AgentObservation, TriageCategory } from "@/lib/types";
import {
  Activity,
  AlertTriangle,
  Footprints,
  Info,
  Smile,
  Thermometer,
} from "lucide-react";
import { AnatomicalRadial } from "./AnatomicalRadial";
import { PostureSilhouette } from "./PostureSilhouette";
import { Tooltip } from "./Tooltip";

export type Agent = "gait" | "thermal" | "expression";

export const AGENT_META: Record<
  Agent,
  { label: string; Icon: typeof Activity; color: string; bg: string }
> = {
  gait: { label: "Yürüyüş Ajanı", Icon: Footprints, color: "text-indigo-600", bg: "bg-indigo-50" },
  thermal: { label: "Termal Ajan", Icon: Thermometer, color: "text-orange-600", bg: "bg-orange-50" },
  expression: {
    label: "Yüz İfadesi Ajanı",
    Icon: Smile,
    color: "text-violet-600",
    bg: "bg-violet-50",
  },
};

export function AgentPanel({
  observations,
  category,
}: {
  observations: Partial<Record<Agent, AgentObservation>>;
  category: TriageCategory | null;
}) {
  return (
    <>
      {/* Wide ekranda anatomik radyal — silüet merkezde, ajanlar etrafında */}
      <div className="hidden xl:block">
        <AnatomicalRadial observations={observations} category={category} />
      </div>
      {/* Mobile / tablet fallback — düz grid */}
      <div className="xl:hidden grid grid-cols-1 md:grid-cols-3 gap-4">
        {(Object.keys(AGENT_META) as Agent[]).map((agent) => (
          <AgentCard key={agent} agent={agent} obs={observations[agent]} />
        ))}
      </div>
    </>
  );
}

export function AgentCard({ agent, obs }: { agent: Agent; obs: AgentObservation | undefined }) {
  const meta = AGENT_META[agent];
  const { Icon } = meta;
  const reason = obs ? inferAgentReason(obs) : null;

  return (
    <div
      className={cn(
        "rounded-2xl bg-white/70 backdrop-blur-xl border shadow-glass p-4 transition-all",
        obs ? "border-white/60" : "border-dashed border-slate-200/80",
      )}
    >
      <div className="flex items-center gap-3">
        <div className={cn("rounded-xl p-2", meta.bg)}>
          <Icon className={cn("w-5 h-5", meta.color)} strokeWidth={2.1} />
        </div>
        <div className="flex-1 min-w-0">
          <div className={cn("text-sm font-semibold truncate", meta.color)}>{meta.label}</div>
          {obs && (
            <div className="text-[11px] text-slate-500 flex items-center gap-1">
              <span>Güven: %{Math.round(obs.confidence * 100)}</span>
              <Tooltip
                content={
                  <>
                    <strong>Güven</strong>: Ajanın kendi gözleminin kalitesine emniyeti. Yüz tespit
                    edildi mi, ışık yeterli mi, sinyal kararlı mı — bu metrikten gelir.
                  </>
                }
                align="left"
              />
            </div>
          )}
        </div>
      </div>

      {agent === "gait" && <div className="mt-3"><PostureSilhouette obs={obs} /></div>}

      {obs ? (
        <p className="mt-3 text-sm text-slate-700 leading-relaxed">{obs.summary_tr}</p>
      ) : (
        <p className="mt-3 text-sm text-slate-400">Veri bekleniyor…</p>
      )}

      {reason && <ReasonHint reason={reason} />}

      {obs && <SignalPills signals={obs.signals} />}
    </div>
  );
}

function SignalPills({ signals }: { signals: AgentObservation["signals"] }) {
  const items = Object.entries(signals)
    .map(([k, v]) => formatSignal(k, v))
    .filter((s): s is NonNullable<typeof s> => s !== null)
    .slice(0, 4);
  if (items.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {items.map((s, i) => (
        <span
          key={i}
          className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-600"
        >
          {s.label}: {s.display}
        </span>
      ))}
    </div>
  );
}

function ReasonHint({ reason }: { reason: NonNullable<ReturnType<typeof inferAgentReason>> }) {
  const palette =
    reason.severity === "error"
      ? "bg-rose-50 text-rose-700 border-rose-200"
      : reason.severity === "warn"
        ? "bg-amber-50 text-amber-800 border-amber-200"
        : "bg-sky-50 text-sky-800 border-sky-200";
  const Icon = reason.severity === "info" ? Info : AlertTriangle;
  return (
    <div className={cn("mt-3 flex items-start gap-2 rounded-xl border px-3 py-2 text-xs leading-relaxed", palette)}>
      <Icon className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" strokeWidth={2.2} />
      <span>{reason.text}</span>
    </div>
  );
}
