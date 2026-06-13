"use client";

import { playDemo, reportPirStatus } from "@/lib/api";
import { CameraOff, Radio } from "lucide-react";
import { useState } from "react";

export function DemoControls() {
  const [busy, setBusy] = useState(false);
  const [pirBusy, setPirBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function fire(scenario: "all" | "red" | "yellow" | "green") {
    setBusy(true);
    setError(null);
    try {
      await playDemo(scenario);
    } catch (e: any) {
      setError(e?.message ?? "Bilinmeyen hata");
    } finally {
      setBusy(false);
    }
  }

  async function setPir(motion: boolean) {
    setPirBusy(true);
    setError(null);
    try {
      await reportPirStatus(motion);
    } catch (e: any) {
      setError(e?.message ?? "Bilinmeyen hata");
    } finally {
      setPirBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="text-xs uppercase tracking-wider text-slate-500 mb-3">
          Triaj senaryoları
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => fire("all")}
            disabled={busy}
            className="px-3 py-1.5 rounded-lg bg-slate-900 text-white text-sm font-medium hover:bg-slate-700 disabled:opacity-50"
          >
            Üçünü sırayla oynat
          </button>
          <button
            onClick={() => fire("red")}
            disabled={busy}
            className="px-3 py-1.5 rounded-lg bg-triage-red text-white text-sm font-medium hover:opacity-90 disabled:opacity-50"
          >
            Kritik
          </button>
          <button
            onClick={() => fire("yellow")}
            disabled={busy}
            className="px-3 py-1.5 rounded-lg bg-triage-yellow text-white text-sm font-medium hover:opacity-90 disabled:opacity-50"
          >
            Belirsiz
          </button>
          <button
            onClick={() => fire("green")}
            disabled={busy}
            className="px-3 py-1.5 rounded-lg bg-triage-green text-white text-sm font-medium hover:opacity-90 disabled:opacity-50"
          >
            Stabil
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="text-xs uppercase tracking-wider text-slate-500 mb-3">
          PIR sensörü simülasyonu
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setPir(false)}
            disabled={pirBusy}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm font-medium hover:bg-amber-100 disabled:opacity-50"
          >
            <CameraOff className="w-3.5 h-3.5" strokeWidth={2} />
            Hareket yok — kamera kapat
          </button>
          <button
            onClick={() => setPir(true)}
            disabled={pirBusy}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-medium hover:bg-emerald-100 disabled:opacity-50"
          >
            <Radio className="w-3.5 h-3.5" strokeWidth={2} />
            Hareket algılandı — kamera aç
          </button>
        </div>
      </div>

      {error && <div className="text-xs text-triage-red">Hata: {error}</div>}
    </div>
  );
}
