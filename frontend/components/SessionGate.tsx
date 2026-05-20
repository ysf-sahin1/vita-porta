"use client";

import { LoginScreen } from "@/components/LoginScreen";
import { endSessionApi } from "@/lib/api";
import { clearSession, getSession, type NurseSession } from "@/lib/session";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

interface SessionContextValue {
  session: NurseSession;
  logout: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function useNurseSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useNurseSession must be used inside SessionGate");
  return ctx;
}

export function SessionGate({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const [session, setLocalSession] = useState<NurseSession | null>(null);

  useEffect(() => {
    setMounted(true);
    setLocalSession(getSession());
  }, []);

  const logout = useCallback(() => {
    const current = getSession();
    if (current?.sessionId) {
      // Best-effort — endSessionApi fail-silent.
      void endSessionApi(current.sessionId);
    }
    clearSession();
    setLocalSession(null);
  }, []);

  if (!mounted) {
    return <div className="min-h-screen" aria-hidden="true" />;
  }

  if (!session) {
    return <LoginScreen onReady={(s) => setLocalSession(s)} />;
  }

  return (
    <SessionContext.Provider value={{ session, logout }}>{children}</SessionContext.Provider>
  );
}
