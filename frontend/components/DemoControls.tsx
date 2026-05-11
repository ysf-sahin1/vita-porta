"use client";

import { playDemo } from "@/lib/api";
import { useState } from "react";

export function DemoControls() {
  const [busy, setBusy] = useState(false);
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

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-xs uppercase tracking-wider text-slate-500 mb-3">
        Demo senaryoları
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
      {error && <div className="mt-2 text-xs text-triage-red">Hata: {error}</div>}
    </div>
  );
}
