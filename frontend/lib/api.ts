const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function playDemo(scenario: "all" | "red" | "yellow" | "green" = "all") {
  const res = await fetch(`${API_BASE}/api/triage/demo?scenario=${scenario}`, { method: "POST" });
  if (!res.ok) throw new Error(`demo başlatılamadı (${res.status})`);
  return res.json();
}

export function streamUrl() {
  return `${API_BASE}/api/triage/stream`;
}
