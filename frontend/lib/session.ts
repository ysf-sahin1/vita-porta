"use client";

const STORAGE_KEY = "vita_porta_session";

export interface NurseSession {
  firstName: string;
  lastName: string;
  hospital: string;
  savedAt: string;
  /** Backend `/api/sessions/start` 'ten dönen oturum id'si — çıkışta kapatmak için. */
  sessionId?: string;
}

export function getSession(): NurseSession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<NurseSession>;
    if (!parsed.firstName || !parsed.lastName || !parsed.hospital) return null;
    return {
      firstName: String(parsed.firstName),
      lastName: String(parsed.lastName),
      hospital: String(parsed.hospital),
      savedAt: String(parsed.savedAt ?? new Date().toISOString()),
      sessionId: parsed.sessionId ? String(parsed.sessionId) : undefined,
    };
  } catch {
    return null;
  }
}

export function setSession(s: Omit<NurseSession, "savedAt">): NurseSession {
  const session: NurseSession = { ...s, savedAt: new Date().toISOString() };
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  }
  return session;
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
}

export function displayName(s: NurseSession): string {
  return `${s.firstName} ${s.lastName}`.trim();
}
