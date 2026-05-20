import type { HistoryResponse, NurseFeedback, NurseSessionRecord } from "./types";

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

export async function fetchHistory(): Promise<HistoryResponse> {
  const res = await fetch(`${API_BASE}/api/triage/history`);
  if (!res.ok) throw new Error(`history alınamadı (${res.status})`);
  return res.json();
}

export async function resetHistory(): Promise<void> {
  const res = await fetch(`${API_BASE}/api/triage/history`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    throw new Error(`geçmiş sıfırlanamadı (${res.status})`);
  }
}

export async function startSessionApi(input: {
  firstName: string;
  lastName: string;
  hospital: string;
}): Promise<NurseSessionRecord> {
  const res = await fetch(`${API_BASE}/api/sessions/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      first_name: input.firstName,
      last_name: input.lastName,
      hospital: input.hospital,
    }),
  });
  if (!res.ok) throw new Error(`mesai başlatılamadı (${res.status})`);
  return res.json();
}

export async function endSessionApi(sessionId: string): Promise<void> {
  // Çıkış best-effort — başarısızlık UI'yi engellemesin.
  try {
    await fetch(`${API_BASE}/api/sessions/end`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
  } catch {
    // sessizce yut — kullanıcı zaten çıkıyor.
  }
}

export async function fetchSessions(limit = 20): Promise<NurseSessionRecord[]> {
  const res = await fetch(`${API_BASE}/api/sessions?limit=${limit}`);
  if (!res.ok) throw new Error(`mesai geçmişi alınamadı (${res.status})`);
  const data = (await res.json()) as { sessions: NurseSessionRecord[] };
  return data.sessions ?? [];
}
