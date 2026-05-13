"use client";

import { cn } from "@/lib/cn";
import type { AgentObservation } from "@/lib/types";
import { Activity, Droplets, Footprints, Thermometer } from "lucide-react";

type Agent = "gait" | "skin" | "respiration" | "thermal";

const AGENT_META: Record<
  Agent,
  { label: string; Icon: typeof Activity; color: string; bg: string }
> = {
  gait: { label: "Yürüyüş Ajanı", Icon: Footprints, color: "text-indigo-600", bg: "bg-indigo-50" },
  skin: { label: "Ten Rengi Ajanı", Icon: Droplets, color: "text-rose-600", bg: "bg-rose-50" },
  respiration: { label: "Solunum Ajanı", Icon: Activity, color: "text-sky-600", bg: "bg-sky-50" },
  thermal: { label: "Termal Ajan", Icon: Thermometer, color: "text-orange-600", bg: "bg-orange-50" },
};

export function AgentPanel({
  observations,
}: {
  observations: Partial<Record<Agent, AgentObservation>>;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {(Object.keys(AGENT_META) as Agent[]).map((agent) => (
        <AgentCard key={agent} agent={agent} obs={observations[agent]} />
      ))}
    </div>
  );
}

function AgentCard({ agent, obs }: { agent: Agent; obs: AgentObservation | undefined }) {
  const meta = AGENT_META[agent];
  const { Icon } = meta;
  return (
    <div
      className={cn(
        "rounded-xl border bg-white p-4 shadow-sm transition-all",
        obs ? "border-slate-300" : "border-dashed border-slate-200",
      )}
    >
      <div className="flex items-center gap-3">
        <div className={cn("rounded-lg p-2", meta.bg)}>
          <Icon className={cn("w-5 h-5", meta.color)} />
        </div>
        <div className="flex-1">
          <div className={cn("text-sm font-semibold", meta.color)}>{meta.label}</div>
          {obs && (
            <div className="text-[11px] text-slate-500">
              Güven: %{Math.round(obs.confidence * 100)}
            </div>
          )}
        </div>
      </div>
      {obs ? (
        <p className="mt-3 text-sm text-slate-700 leading-relaxed">{obs.summary_tr}</p>
      ) : (
        <p className="mt-3 text-sm text-slate-400">Veri bekleniyor…</p>
      )}
      {obs && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {Object.entries(obs.signals)
            .slice(0, 4)
            .map(([k, v]) => (
              <span
                key={k}
                className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-600"
              >
                {k}: {String(v)}
              </span>
            ))}
        </div>
      )}
    </div>
  );
}
