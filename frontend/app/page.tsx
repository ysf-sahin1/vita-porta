"use client";

import { AgentPanel } from "@/components/AgentPanel";
import { DemoControls } from "@/components/DemoControls";
import { Header } from "@/components/Header";
import { HistoryDetailModal } from "@/components/HistoryDetailModal";
import { HistoryList } from "@/components/HistoryList";
import {
  formatVerdictTime,
  type Verdict,
} from "@/components/NurseVerdict";
import { SessionGate } from "@/components/SessionGate";
import { TriageCard } from "@/components/TriageCard";
import { entryKey, useTriageStream } from "@/components/useTriageStream";
import { useState } from "react";

export default function Page() {
  return (
    <SessionGate>
      <Dashboard />
    </SessionGate>
  );
}

function Dashboard() {
  const {
    status,
    current,
    history,
    verdicts,
    setVerdict,
    lastObservationAt,
    lastDecisionLatencyMs,
  } = useTriageStream();

  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const observations = current?.observations ?? {};
  const isRealPatient = current?.patientId
    ? !current.patientId.startsWith("demo-")
    : false;
  const showDemoControls = !isRealPatient;

  const currentKey = current?.decision
    ? entryKey(current.patientId, current.decision.decided_at)
    : null;
  const currentVerdict = currentKey ? verdicts[currentKey] ?? null : null;

  const handleVerdict = (key: string) => (v: Omit<Verdict, "at">) => {
    setVerdict(key, { ...v, at: formatVerdictTime() });
  };

  const selectedEntry =
    selectedKey !== null ? history.find((h) => h.key === selectedKey) ?? null : null;
  const selectedVerdict = selectedKey !== null ? verdicts[selectedKey] ?? null : null;

  return (
    <main className="max-w-[1400px] mx-auto px-4 md:px-8 py-6 md:py-8 space-y-6">
      <Header
        apiStatus={status}
        lastObservationAt={lastObservationAt}
        lastDecisionLatencyMs={lastDecisionLatencyMs}
      />

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_380px] gap-6">
        <section className="space-y-6 min-w-0">
          {current?.decision && currentKey ? (
            <TriageCard
              decision={current.decision}
              verdict={currentVerdict}
              onVerdictChange={handleVerdict(currentKey)}
            />
          ) : (
            <EmptyTriage />
          )}

          <div>
            <div className="text-xs uppercase tracking-wider text-slate-500 mb-3 px-1">
              Ajan gözlemleri
            </div>
            <AgentPanel
              observations={observations}
              category={current?.decision?.category ?? null}
            />
          </div>
        </section>

        <aside className="space-y-6">
          <HistoryList
            history={history}
            verdicts={verdicts}
            selectedKey={selectedKey}
            onSelect={(k) => setSelectedKey(k)}
          />
        </aside>
      </div>

      {showDemoControls && (
        <details className="rounded-2xl bg-white/60 backdrop-blur-xl border border-white/60 shadow-glass">
          <summary className="cursor-pointer select-none px-5 py-3 text-xs uppercase tracking-wider text-slate-500 font-medium">
            Geliştirici · Demo senaryoları
          </summary>
          <div className="px-5 pb-5">
            <DemoControls />
          </div>
        </details>
      )}

      <footer className="text-center text-xs text-slate-400 pt-4">
        Vita Porta · CODEX AI Hackathon 2026 · Bu sistem tanı koymaz, son karar her zaman triaj
        hemşiresine aittir.
      </footer>

      <HistoryDetailModal
        entry={selectedEntry}
        verdict={selectedVerdict}
        onVerdictChange={selectedKey ? handleVerdict(selectedKey) : () => {}}
        onClose={() => setSelectedKey(null)}
      />
    </main>
  );
}

function EmptyTriage() {
  return (
    <div className="rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-glass p-10 text-center">
      <div className="mx-auto w-12 h-12 rounded-full bg-slate-100 mb-4" />
      <div className="text-slate-500 text-sm">
        Kapı kamerasından henüz hasta bildirimi alınmadı.
      </div>
      <div className="text-slate-400 text-xs mt-1">
        Geliştirici panelinden bir demo senaryosu başlatabilirsiniz.
      </div>
    </div>
  );
}
