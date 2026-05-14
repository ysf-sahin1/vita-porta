"use client";

import { cn } from "@/lib/cn";
import { ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import type { ConnectionStatus } from "./useTriageStream";

type PillState = "live" | "warn" | "off";

const PILL_CLASS: Record<PillState, { dot: string; text: string; glow: boolean }> = {
  live: { dot: "bg-status-live", text: "text-emerald-700", glow: true },
  warn: { dot: "bg-status-warn", text: "text-amber-700", glow: false },
  off: { dot: "bg-status-off", text: "text-slate-500", glow: false },
};

export interface HeaderProps {
  apiStatus: ConnectionStatus;
  lastObservationAt: number | null;
  lastDecisionLatencyMs: number | null;
}

export function Header({ apiStatus, lastObservationAt, lastDecisionLatencyMs }: HeaderProps) {
  const camState = useCameraState(lastObservationAt);
  const apiState = mapApiState(apiStatus);
  const llmState = mapLlmState(lastDecisionLatencyMs);
  const apiLabel =
    apiStatus === "live" ? "API" : apiStatus === "connecting" ? "API…" : "API";
  const llmLabel = describeLlm(lastDecisionLatencyMs);

  return (
    <header className="rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-glass px-6 py-5 md:px-8 md:py-6 flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-4">
        <div className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 p-3 text-white shadow-glass">
          <ShieldCheck className="w-7 h-7" strokeWidth={2.2} />
        </div>
        <div>
          <h1 className="text-3xl font-semibold text-slate-900 tracking-tight leading-none">
            Vita Porta
          </h1>
          <p className="text-sm text-slate-500 mt-1.5">
            Hemşire triaj asistanı · Sistem öneridir, son karar hemşireye aittir
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 md:gap-3">
        <StatusPill state={camState} label="Kamera" />
        <StatusPill state={apiState} label={apiLabel} />
        <StatusPill state={llmState} label={llmLabel} />
        <LiveClock />
      </div>
    </header>
  );
}

function StatusPill({ state, label }: { state: PillState; label: string }) {
  const cls = PILL_CLASS[state];
  return (
    <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/80 border border-slate-200/70 shadow-sm">
      <span
        className={cn(
          "inline-block w-2 h-2 rounded-full",
          cls.dot,
          cls.glow && "animate-statusGlow",
        )}
      />
      <span className={cn("text-xs font-medium uppercase tracking-wider", cls.text)}>
        {label}
      </span>
    </span>
  );
}

function LiveClock() {
  const [now, setNow] = useState<string>(() => formatClock(new Date()));
  useEffect(() => {
    const id = window.setInterval(() => setNow(formatClock(new Date())), 1000);
    return () => window.clearInterval(id);
  }, []);
  return (
    <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 text-white shadow-sm">
      <span className="text-xs font-medium uppercase tracking-wider opacity-70">Saat</span>
      <span className="text-sm font-semibold tabular-nums">{now}</span>
    </span>
  );
}

function formatClock(d: Date): string {
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

function mapApiState(s: ConnectionStatus): PillState {
  if (s === "live") return "live";
  if (s === "connecting") return "warn";
  return "off";
}

function useCameraState(lastObservationAt: number | null): PillState {
  const [now, setNow] = useState<number>(() => Date.now());
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);
  if (lastObservationAt === null) return "off";
  const age = now - lastObservationAt;
  if (age < 5000) return "live";
  if (age < 15000) return "warn";
  return "off";
}

function mapLlmState(latencyMs: number | null): PillState {
  if (latencyMs === null) return "off";
  if (latencyMs > 100) return "live";
  return "warn";
}

function describeLlm(latencyMs: number | null): string {
  if (latencyMs === null) return "LLM";
  return latencyMs > 100 ? "LLM" : "LLM·mock";
}
