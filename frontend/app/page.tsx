"use client";

import { AgentPanel } from "@/components/AgentPanel";
import { DemoControls } from "@/components/DemoControls";
import { Header } from "@/components/Header";
import { HistoryList } from "@/components/HistoryList";
import { TriageCard } from "@/components/TriageCard";
import { useTriageStream } from "@/components/useTriageStream";

export default function Page() {
  const { status, current, history } = useTriageStream();
  const observations = current?.observations ?? {};

  return (
    <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <Header status={status} />
      <DemoControls />

      {current?.decision ? (
        <TriageCard decision={current.decision} />
      ) : (
        <div className="rounded-2xl border-2 border-dashed border-slate-200 p-10 text-center bg-white/50">
          <div className="text-slate-500 text-sm">
            Kapı kamerasından henüz hasta bildirimi alınmadı. Demo senaryolarından birini başlatın.
          </div>
        </div>
      )}

      <section>
        <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">Ajan gözlemleri</div>
        <AgentPanel observations={observations} />
      </section>

      <HistoryList history={history} />

      <footer className="text-center text-xs text-slate-400 pt-6 border-t border-slate-100">
        Vita Porta · CODEX AI Hackathon 2026 · Bu sistem tanı koymaz, son karar her zaman triaj
        hemşiresine aittir.
      </footer>
    </main>
  );
}
