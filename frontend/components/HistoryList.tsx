"use client";

import { cn } from "@/lib/cn";
import { useNurseSession } from "./SessionGate";
import { verdictColorClass, verdictIcon, type Verdict } from "./NurseVerdict";
import type { HistoryEntry, NurseMeta } from "./useTriageStream";
import { Trash2, UserCog } from "lucide-react";
import { useState } from "react";
import { ResetConfirmDialog } from "./ResetConfirmDialog";

const DOT: Record<HistoryEntry["decision"]["category"], string> = {
  red: "bg-triage-red",
  yellow: "bg-triage-yellow",
  green: "bg-triage-green",
  insufficient: "bg-triage-gray",
};

export interface HistoryListProps {
  history: HistoryEntry[];
  verdicts: Record<string, Verdict>;
  verdictNurses: Record<string, NurseMeta>;
  selectedKey: string | null;
  onSelect: (key: string) => void;
  onReset: () => Promise<void> | void;
}

export function HistoryList({
  history,
  verdicts,
  verdictNurses,
  selectedKey,
  onSelect,
  onReset,
}: HistoryListProps) {
  const { session } = useNurseSession();
  const currentNurseKey = `${session.firstName.toLowerCase()}|${session.lastName.toLowerCase()}|${session.hospital.toLowerCase()}`;
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleConfirm = async () => {
    try {
      await onReset();
    } finally {
      setConfirmOpen(false);
    }
  };

  if (history.length === 0) {
    return (
      <>
        <div className="rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-glass p-5 text-sm text-slate-400">
          Henüz triaj kararı yok.
        </div>
        <ResetConfirmDialog
          open={confirmOpen}
          onCancel={() => setConfirmOpen(false)}
          onConfirm={handleConfirm}
        />
      </>
    );
  }

  // Mesai değişikliği marker'ları: history zamana göre azalan; bir entry'nin
  // verdict'i şu anki hemşireden farklıysa "farklı hemşire" sayılır. Önceki
  // entry (üstte, daha yeni) farklı hemşireyse, aralarına divider düşeriz.
  const items: ({ kind: "entry"; entry: HistoryEntry } | { kind: "shift"; nurse: NurseMeta })[] = [];
  let lastNurseKey: string | null = null;
  for (const entry of history) {
    const nurse = verdictNurses[entry.key];
    const nurseKey = nurse
      ? `${nurse.firstName.toLowerCase()}|${nurse.lastName.toLowerCase()}|${nurse.hospital.toLowerCase()}`
      : null;
    if (nurseKey && lastNurseKey && nurseKey !== lastNurseKey) {
      // Hemşire önceki entry'den farklı → mesai değişikliği
      items.push({ kind: "shift", nurse });
    }
    items.push({ kind: "entry", entry });
    if (nurseKey) lastNurseKey = nurseKey;
  }

  return (
    <div className="rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-glass overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-200/60 flex items-center justify-between gap-2">
        <span className="text-xs uppercase tracking-wider text-slate-500 font-medium">
          Son kararlar
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400 tabular-nums">{history.length}</span>
          <button
            type="button"
            onClick={() => setConfirmOpen(true)}
            aria-label="Geçmişi sıfırla"
            title="Tüm geçmiş kararları ve verdict'leri kalıcı olarak sil"
            className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] uppercase tracking-wider text-slate-500 hover:bg-rose-50 hover:text-rose-600 transition-colors"
          >
            <Trash2 className="w-3 h-3" strokeWidth={2.2} />
            Sıfırla
          </button>
        </div>
      </div>
      <ResetConfirmDialog
        open={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleConfirm}
      />
      <ul className="divide-y divide-slate-200/40 max-h-[480px] overflow-y-auto">
        {items.map((item, idx) => {
          if (item.kind === "shift") {
            return <ShiftMarker key={`shift-${idx}`} nurse={item.nurse} />;
          }
          const entry = item.entry;
          const v = verdicts[entry.key];
          const VIcon = v ? verdictIcon(v.action) : null;
          const isSelected = selectedKey === entry.key;
          const nurse = verdictNurses[entry.key];
          const nurseKey = nurse
            ? `${nurse.firstName.toLowerCase()}|${nurse.lastName.toLowerCase()}|${nurse.hospital.toLowerCase()}`
            : null;
          const isOtherNurse = nurseKey !== null && nurseKey !== currentNurseKey;

          return (
            <li key={entry.key}>
              <button
                type="button"
                onClick={() => onSelect(entry.key)}
                className={cn(
                  "w-full px-5 py-3 text-sm text-left transition-colors",
                  isSelected ? "bg-sky-50/70" : "hover:bg-white/60",
                )}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={cn(
                      "inline-block w-2.5 h-2.5 rounded-full flex-shrink-0",
                      DOT[entry.decision.category],
                    )}
                  />
                  <span className="text-xs text-slate-500 tabular-nums w-[68px] flex-shrink-0">
                    {formatTime(entry.decision.decided_at)}
                  </span>
                  <span
                    className={cn(
                      "truncate min-w-0 flex-1",
                      isOtherNurse
                        ? "italic font-normal text-slate-600"
                        : "font-medium text-slate-700",
                    )}
                  >
                    {entry.patientId}
                    {entry.restored && (
                      <span className="ml-2 text-[10px] uppercase tracking-wider text-slate-400">
                        · geçmiş
                      </span>
                    )}
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
                </div>
                {nurse && (
                  <div
                    className={cn(
                      "mt-1 ml-[80px] text-[11px] truncate",
                      isOtherNurse ? "italic text-slate-500" : "text-slate-400",
                    )}
                  >
                    {nurse.firstName} {nurse.lastName} · {formatTime(nurse.feedbackAt)}
                  </div>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function ShiftMarker({ nurse }: { nurse: NurseMeta }) {
  return (
    <li
      className="px-5 py-2 bg-slate-50/60 border-y border-slate-200/40 text-[10px] uppercase tracking-wider text-slate-500 flex items-center gap-2"
      aria-label="Mesai değişikliği"
    >
      <UserCog className="w-3.5 h-3.5 text-slate-400" strokeWidth={2.2} />
      <span className="font-medium">Mesai değişikliği</span>
      <span className="font-normal italic">
        {nurse.firstName} {nurse.lastName}
      </span>
      <span className="ml-auto tabular-nums text-slate-400">{formatTime(nurse.feedbackAt)}</span>
    </li>
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
