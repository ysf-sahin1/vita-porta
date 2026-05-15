import type { NurseFeedback } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function playDemo(scenario: "all" | "red" | "yellow" | "green" = "all") {
  const res = await fetch(`${API_BASE}/api/triage/demo?scenario=${scenario}`, { method: "POST" });
  if (!res.ok) throw new Error(`demo başlatılamadı (${res.status})`);
  return res.json();
}

export function streamUrl() {
  return `${API_BASE}/api/triage/stream`;
}

export async function postFeedback(feedback: NurseFeedback): Promise<void> {
  const res = await fetch(`${API_BASE}/api/triage/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(feedback),
  });
  if (!res.ok) throw new Error(`feedback kaydedilemedi (${res.status})`);
}

export async function fetchHistory(): Promise<NurseFeedback[]> {
  const res = await fetch(`${API_BASE}/api/triage/history`);
  if (!res.ok) throw new Error(`history alınamadı (${res.status})`);
  return res.json();
}
