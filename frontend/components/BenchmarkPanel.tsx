"use client";

import { fetchLatestBenchmark, runBenchmark } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { BenchmarkReport, TriageCategory } from "@/lib/types";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Play,
  ShieldAlert,
  Timer,
} from "lucide-react";
import { useEffect, useState } from "react";

const CATEGORIES: TriageCategory[] = ["red", "yellow", "green", "insufficient"];
const LABELS: Record<TriageCategory, string> = {
  red: "Kırmızı",
  yellow: "Sarı",
  green: "Yeşil",
  insufficient: "Yetersiz",
};
const CATEGORY_CLASS: Record<TriageCategory, string> = {
  red: "text-rose-700 bg-rose-50",
  yellow: "text-amber-700 bg-amber-50",
  green: "text-emerald-700 bg-emerald-50",
  insufficient: "text-slate-600 bg-slate-100",
};

export function BenchmarkPanel() {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLatestBenchmark().then(setReport).catch(() => setReport(null));
  }, []);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setReport(await runBenchmark("mock"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark çalıştırılamadı");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-glass p-5 md:p-7 space-y-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-slate-900 p-2.5 text-white">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Benchmark ve güvenlik ölçümleri</h2>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              Etiketli vakalarda sistem önerisini beklenen kategoriyle karşılaştırır. Kritik vaka
              yakalama ve kaçırma oranları temel güvenlik göstergeleridir.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={run}
          disabled={busy}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          <Play className="w-4 h-4" />
          {busy ? "Çalıştırılıyor..." : "Sentetik baseline çalıştır"}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {!report ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 p-8 text-center text-sm text-slate-500">
          Henüz benchmark raporu yok. Başlangıç veri setini çalıştırarak ölçüm oluşturun.
        </div>
      ) : (
        <BenchmarkReportView report={report} />
      )}
    </section>
  );
}

function BenchmarkReportView({ report }: { report: BenchmarkReport }) {
  const metrics = report.metrics;
  const failures = report.results.filter((result) => !result.correct);

  return (
    <div className="space-y-5">
      <div
        className={cn(
          "rounded-xl border px-4 py-3 text-sm",
          report.synthetic
            ? "border-amber-200 bg-amber-50 text-amber-800"
            : "border-emerald-200 bg-emerald-50 text-emerald-800",
        )}
      >
        <div className="font-semibold">
          {report.synthetic ? "Sentetik baseline" : "Uzman etiketli veri seti"} ·{" "}
          {report.dataset_name} v{report.dataset_version}
        </div>
        <div className="mt-0.5 text-xs opacity-80">
          {report.synthetic
            ? "Bu sonuçlar benchmark altyapısını doğrular; klinik performans kanıtı değildir."
            : report.dataset_description}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <MetricCard
          label="Kırmızı yakalama"
          value={percent(metrics.red_sensitivity)}
          tone={metrics.red_sensitivity !== null && metrics.red_sensitivity >= 0.95 ? "good" : "warn"}
          icon={<ShieldAlert className="w-4 h-4" />}
        />
        <MetricCard
          label="Kritik kaçırma"
          value={percent(metrics.critical_miss_rate)}
          tone={metrics.critical_miss_rate === 0 ? "good" : "danger"}
          icon={<AlertTriangle className="w-4 h-4" />}
        />
        <MetricCard
          label="Genel doğruluk"
          value={percent(metrics.accuracy)}
          tone="neutral"
          icon={<CheckCircle2 className="w-4 h-4" />}
        />
        <MetricCard
          label="Veri yetersiz"
          value={percent(metrics.insufficient_rate)}
          tone="neutral"
          icon={<BarChart3 className="w-4 h-4" />}
        />
        <MetricCard
          label="Ort. karar süresi"
          value={`${Math.round(metrics.mean_latency_ms)} ms`}
          tone="neutral"
          icon={<Timer className="w-4 h-4" />}
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
        <ConfusionMatrix report={report} />
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Koşu özeti
          </div>
          <dl className="mt-3 space-y-2 text-sm">
            <SummaryRow label="Toplam vaka" value={String(metrics.total_cases)} />
            <SummaryRow label="Doğru vaka" value={String(metrics.correct_cases)} />
            <SummaryRow label="Düşük öncelik verme" value={percent(metrics.under_triage_rate)} />
            <SummaryRow label="Aşırı öncelik verme" value={percent(metrics.over_triage_rate)} />
            <SummaryRow label="P95 karar süresi" value={`${Math.round(metrics.p95_latency_ms)} ms`} />
            <SummaryRow label="Karar motoru" value={report.engine} />
            <SummaryRow label="Hatalı vaka" value={String(failures.length)} />
          </dl>
        </div>
      </div>

      {failures.length > 0 && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/70 p-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-rose-700">
            İncelenmesi gereken vakalar
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {failures.map((failure) => (
              <span
                key={failure.case_id}
                className="rounded-lg border border-rose-200 bg-white px-2.5 py-1.5 text-xs text-rose-700"
              >
                {failure.case_id}: {LABELS[failure.expected_category]} →{" "}
                {LABELS[failure.predicted_category]}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  tone,
  icon,
}: {
  label: string;
  value: string;
  tone: "good" | "warn" | "danger" | "neutral";
  icon: React.ReactNode;
}) {
  const toneClass = {
    good: "border-emerald-200 bg-emerald-50 text-emerald-800",
    warn: "border-amber-200 bg-amber-50 text-amber-800",
    danger: "border-rose-200 bg-rose-50 text-rose-800",
    neutral: "border-slate-200 bg-white text-slate-800",
  }[tone];
  return (
    <div className={cn("rounded-2xl border p-4", toneClass)}>
      <div className="flex items-center gap-1.5 text-xs font-medium opacity-70">
        {icon}
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold tabular-nums">{value}</div>
    </div>
  );
}

function ConfusionMatrix({ report }: { report: BenchmarkReport }) {
  const matrix = report.metrics.confusion_matrix;
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        Confusion matrix · Gerçek / Sistem
      </div>
      <table className="mt-3 w-full min-w-[480px] border-separate border-spacing-1 text-center text-xs">
        <thead>
          <tr>
            <th className="px-2 py-2 text-left text-slate-400">Gerçek ↓</th>
            {CATEGORIES.map((category) => (
              <th key={category} className="px-2 py-2 font-medium text-slate-500">
                {LABELS[category]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {CATEGORIES.map((expected) => (
            <tr key={expected}>
              <th className="px-2 py-2 text-left font-medium text-slate-600">{LABELS[expected]}</th>
              {CATEGORIES.map((predicted) => (
                <td
                  key={predicted}
                  className={cn(
                    "rounded-lg px-3 py-2.5 tabular-nums",
                    expected === predicted ? CATEGORY_CLASS[expected] : "bg-slate-50 text-slate-500",
                  )}
                >
                  {matrix[expected]?.[predicted] ?? 0}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-2 last:border-0">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium text-slate-800 tabular-nums">{value}</dd>
    </div>
  );
}

function percent(value: number | null): string {
  return value === null ? "N/A" : `%${Math.round(value * 100)}`;
}
