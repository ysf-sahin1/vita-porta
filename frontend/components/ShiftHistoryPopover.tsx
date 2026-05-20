"use client";

import { fetchSessions } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { NurseSessionRecord } from "@/lib/types";
import { Clock3, History, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

const POLL_MS = 15_000;

export interface ShiftHistoryPopoverProps {
  /** Aktif hemşirenin session_id'si — listede "(siz)" rozeti için */
  currentSessionId: string | undefined;
}

export function ShiftHistoryPopover({ currentSessionId }: ShiftHistoryPopoverProps) {
  const [open, setOpen] = useState(false);
  const [records, setRecords] = useState<NurseSessionRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const sessions = await fetchSessions(20);
      setRecords(sessions);
      setErr(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "mesai geçmişi alınamadı");
    } finally {
      setLoading(false);
    }
  }, []);

  // İlk yüklemede ve popover her açıldığında tazele; açıkken 15sn'de bir poll et.
  useEffect(() => {
    if (!open) return;
    void refresh();
    const id = window.setInterval(refresh, POLL_MS);
    return () => window.clearInterval(id);
  }, [open, refresh]);

  // Dışına tıklayınca kapat
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!containerRef.current) return;
      if (!containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("mousedown", onDown);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const activeCount = records.filter((r) => r.logout_at === null).length;

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="dialog"
        aria-expanded={open}
        title="Hemşire mesai geçmişi"
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border shadow-sm text-xs font-medium uppercase tracking-wider transition-colors",
          open
            ? "bg-slate-900 text-white border-slate-900"
            : "bg-white/80 text-slate-600 border-slate-200/70 hover:bg-slate-100",
        )}
      >
        <History className="w-3.5 h-3.5" strokeWidth={2.2} />
        Mesai
        {activeCount > 0 && (
          <span
            className={cn(
              "ml-0.5 inline-flex items-center justify-center min-w-[18px] h-[18px] rounded-full text-[10px] font-semibold tabular-nums px-1",
              open ? "bg-emerald-400 text-slate-900" : "bg-emerald-500 text-white",
            )}
            aria-label={`${activeCount} aktif oturum`}
          >
            {activeCount}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Mesai geçmişi"
          className="absolute right-0 mt-2 w-[360px] max-w-[calc(100vw-2rem)] z-30 rounded-2xl bg-white/95 backdrop-blur-xl border border-white/70 shadow-glassLg p-4"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs uppercase tracking-wider text-slate-500 font-medium">
              Mesai geçmişi
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Kapat"
              className="rounded-full p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            >
              <X className="w-3.5 h-3.5" strokeWidth={2.2} />
            </button>
          </div>

          {loading && records.length === 0 && (
            <div className="text-xs text-slate-400 py-4 text-center">Yükleniyor…</div>
          )}

          {err && (
            <div className="text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2">
              {err}
            </div>
          )}

          {!loading && !err && records.length === 0 && (
            <div className="text-xs text-slate-400 py-4 text-center">
              Henüz mesai kaydı yok.
            </div>
          )}

          {records.length > 0 && (
            <ul className="space-y-2 max-h-[420px] overflow-y-auto pr-1 -mr-1">
              {records.map((r) => (
                <SessionRow
                  key={r.session_id}
                  record={r}
                  isCurrent={r.session_id === currentSessionId}
                />
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function SessionRow({
  record,
  isCurrent,
}: {
  record: NurseSessionRecord;
  isCurrent: boolean;
}) {
  const active = record.logout_at === null;
  const fullName = `${record.nurse_first_name} ${record.nurse_last_name}`.trim();
  const loginStr = formatDateTime(record.login_at);
  const logoutStr = record.logout_at ? formatTimeShort(record.logout_at) : null;
  const duration = computeDuration(record.login_at, record.logout_at);

  return (
    <li
      className={cn(
        "rounded-xl border px-3 py-2.5 text-xs",
        active
          ? "border-emerald-200 bg-emerald-50/60"
          : "border-slate-200/70 bg-white/70",
        isCurrent && "ring-1 ring-slate-900/30",
      )}
    >
      <div className="flex items-center gap-2">
        <span className="font-semibold text-slate-800 truncate">{fullName}</span>
        {isCurrent && (
          <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded-full bg-slate-900 text-white">
            Siz
          </span>
        )}
        <span
          className={cn(
            "ml-auto inline-flex items-center gap-1 text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full",
            active
              ? "bg-emerald-500/15 text-emerald-700"
              : "bg-slate-100 text-slate-500",
          )}
        >
          <span
            className={cn(
              "inline-block w-1.5 h-1.5 rounded-full",
              active ? "bg-emerald-500 animate-statusGlow" : "bg-slate-400",
            )}
          />
          {active ? "Aktif" : "Kapandı"}
        </span>
      </div>
      <div className="text-slate-500 mt-1 truncate">{record.hospital}</div>
      <div className="flex items-center gap-1.5 mt-1.5 text-slate-600 tabular-nums">
        <Clock3 className="w-3 h-3 text-slate-400" strokeWidth={2.2} />
        <span>{loginStr}</span>
        <span className="text-slate-300">→</span>
        <span>{logoutStr ?? "—"}</span>
        {duration && (
          <span className="ml-auto text-slate-400 text-[10px]">{duration}</span>
        )}
      </div>
    </li>
  );
}

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${dd}.${mm} ${hh}:${mi}`;
}

function formatTimeShort(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mi}`;
}

function computeDuration(loginAt: string, logoutAt: string | null): string | null {
  const start = new Date(loginAt).getTime();
  const end = logoutAt ? new Date(logoutAt).getTime() : Date.now();
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return null;
  const mins = Math.floor((end - start) / 60_000);
  if (mins < 60) return `${mins} dk`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m === 0 ? `${h} sa` : `${h} sa ${m} dk`;
}
