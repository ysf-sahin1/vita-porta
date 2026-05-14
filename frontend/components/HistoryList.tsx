"use client";

import { cn } from "@/lib/cn";
import { verdictColorClass, verdictIcon, type Verdict } from "./NurseVerdict";
import type { HistoryEntry } from "./useTriageStream";

const DOT: Record<HistoryEntry["decision"]["category"], string> = {
  red: "bg-triage-red",
  yellow: "bg-triage-yellow",
  green: "bg-triage-green",
  insufficient: "bg-triage-gray",
};

export interface HistoryListProps {
  history: HistoryEntry[];
  verdicts: Record<string, Verdict>;
  selectedKey: string | null;
  onSelect: (key: string) => void;
}

export function HistoryList({ history, verdicts, selectedKey, onSelect }: HistoryListProps) {
  if (history.length === 0) {
    return (
      <div className="rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-glass p-5 text-sm text-slate-400">
        Henüz triaj kararı yok.
      </div>
    );
  }
  return (
    <div className="rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-glass overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-200/60 flex items-baseline justify-between">
        <span className="text-xs uppercase tracking-wider text-slate-500 font-medium">
          Son kararlar
        </span>
        <span className="text-[11px] text-slate-400 tabular-nums">{history.length}</span>
      </div>
      <ul className="divide-y divide-slate-200/40 max-h-[480px] overflow-y-auto">
        {history.map((entry) => {
          const v = verdicts[entry.key];
          const VIcon = v ? verdictIcon(v.action) : null;
          const isSelected = selectedKey === entry.key;
          return (
            <li key={entry.key}>
              <button
                type="button"
                onClick={() => onSelect(entry.key)}
                className={cn(
                  "w-full px-5 py-3 flex items-center gap-3 text-sm text-left transition-colors",
                  isSelected ? "bg-sky-50/70" : "hover:bg-white/60",
                )}
              >
                <span
                  className={cn(
                    "inline-block w-2.5 h-2.5 rounded-full flex-shrink-0",
                    DOT[entry.decision.category],
                  )}
                />
                <span className="text-xs text-slate-500 tabular-nums w-[68px] flex-shrink-0">
                  {formatTime(entry.decision.decided_at)}
                </span>
                <span className="font-medium text-slate-700 truncate min-w-0 flex-1">
                  {entry.patientId}
                </span>
                {VIcon && (
                  <span
                    className={cn(
                      "inline-flex items-center justify-center w-5 h-5 rounded-full bg-white/80 border border-slate-200/70 flex-shrink-0",
                      verdictColorClass(v!.action),
                    )}
                    title={verdictLabel(v!)}
                  >
                    <VIcon className="w-3 h-3" strokeWidth={2.6} />
                  </span>
                )}
                <span className="text-xs text-slate-400 tabular-nums flex-shrink-0">
                  %{Math.round(entry.decision.confidence * 100)}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "--:--:--";
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

function verdictLabel(v: Verdict): string {
  if (v.action === "approved") return "Onaylandı";
  if (v.action === "rejected") return "Reddedildi";
  return "Değiştirildi";
}
