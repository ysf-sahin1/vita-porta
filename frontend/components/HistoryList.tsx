"use client";

import { cn } from "@/lib/cn";
import type { TriageDecision } from "@/lib/types";

const DOT: Record<TriageDecision["category"], string> = {
  red: "bg-triage-red",
  yellow: "bg-triage-yellow",
  green: "bg-triage-green",
  insufficient: "bg-triage-gray",
};

export function HistoryList({ history }: { history: TriageDecision[] }) {
  if (history.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-4 text-sm text-slate-400">
        Henüz triaj kararı yok.
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-100 text-xs uppercase tracking-wider text-slate-500">
        Son kararlar
      </div>
      <ul className="divide-y divide-slate-100">
        {history.map((d, i) => (
          <li key={`${d.patient_id}-${i}`} className="px-4 py-3 flex items-center gap-3 text-sm">
            <span className={cn("inline-block w-2.5 h-2.5 rounded-full", DOT[d.category])} />
            <span className="font-medium text-slate-700 w-24">{d.patient_id}</span>
            <span className="text-slate-600 flex-1 truncate">{d.rationale_tr}</span>
            <span className="text-xs text-slate-400">%{Math.round(d.confidence * 100)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
