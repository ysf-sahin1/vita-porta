"use client";

import { streamUrl } from "@/lib/api";
import type { AgentObservation, TriageDecision } from "@/lib/types";
import { useCallback, useEffect, useRef, useState } from "react";
import type { Verdict } from "./NurseVerdict";

type AgentKey = "gait" | "skin" | "respiration" | "thermal";
type Observations = Partial<Record<AgentKey, AgentObservation>>;

export interface PatientState {
  patientId: string;
  observations: Observations;
  decision?: TriageDecision;
  updatedAt: number;
}

export interface HistoryEntry {
  key: string;
  patientId: string;
  decision: TriageDecision;
  observations: Observations;
}

export type ConnectionStatus = "connecting" | "live" | "offline";

export interface StreamSnapshot {
  status: ConnectionStatus;
  current: PatientState | null;
  history: HistoryEntry[];
  verdicts: Record<string, Verdict>;
  setVerdict: (key: string, verdict: Verdict) => void;
  lastObservationAt: number | null;
  lastDecisionLatencyMs: number | null;
}

export function entryKey(patientId: string, decidedAt: string): string {
  return `${patientId}__${decidedAt}`;
}

export function useTriageStream(): StreamSnapshot {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [current, setCurrent] = useState<PatientState | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [verdicts, setVerdicts] = useState<Record<string, Verdict>>({});
  const [lastObservationAt, setLastObservationAt] = useState<number | null>(null);
  const [lastDecisionLatencyMs, setLastDecisionLatencyMs] = useState<number | null>(null);

  const sourceRef = useRef<EventSource | null>(null);
  const patientObsRef = useRef<{ id: string | null; obs: Observations }>({ id: null, obs: {} });

  useEffect(() => {
    const es = new EventSource(streamUrl());
    sourceRef.current = es;
    setStatus("connecting");

    es.addEventListener("heartbeat", () => setStatus("live"));

    es.addEventListener("agent_observation", (ev) => {
      const data = JSON.parse((ev as MessageEvent).data) as {
        patient_id: string;
        observation: AgentObservation;
      };
      setStatus("live");
      setLastObservationAt(Date.now());

      if (patientObsRef.current.id !== data.patient_id) {
        patientObsRef.current = { id: data.patient_id, obs: {} };
      }
      patientObsRef.current.obs = {
        ...patientObsRef.current.obs,
        [data.observation.agent]: data.observation,
      };

      setCurrent((prev) => {
        const sameAsPrev = prev && prev.patientId === data.patient_id;
        return {
          patientId: data.patient_id,
          observations: { ...patientObsRef.current.obs },
          decision: sameAsPrev ? prev.decision : undefined,
          updatedAt: Date.now(),
        };
      });
    });

    es.addEventListener("decision", (ev) => {
      const data = JSON.parse((ev as MessageEvent).data) as {
        patient_id: string;
        decision: TriageDecision;
      };
      setStatus("live");
      if (data.decision.latency_ms !== null) {
        setLastDecisionLatencyMs(data.decision.latency_ms);
      }

      const obsSnapshot: Observations =
        patientObsRef.current.id === data.patient_id
          ? { ...patientObsRef.current.obs }
          : {};

      const key = entryKey(data.patient_id, data.decision.decided_at);
      setHistory((prev) => [
        { key, patientId: data.patient_id, decision: data.decision, observations: obsSnapshot },
        ...prev,
      ]);

      setCurrent({
        patientId: data.patient_id,
        observations: obsSnapshot,
        decision: data.decision,
        updatedAt: Date.now(),
      });
    });

    es.onerror = () => setStatus("offline");

    return () => {
      es.close();
      sourceRef.current = null;
    };
  }, []);

  const setVerdict = useCallback((key: string, verdict: Verdict) => {
    setVerdicts((prev) => ({ ...prev, [key]: verdict }));
  }, []);

  return {
    status,
    current,
    history,
    verdicts,
    setVerdict,
    lastObservationAt,
    lastDecisionLatencyMs,
  };
}
