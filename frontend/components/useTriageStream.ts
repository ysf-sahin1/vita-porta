"use client";

import { streamUrl } from "@/lib/api";
import type { AgentObservation, TriageDecision } from "@/lib/types";
import { useEffect, useRef, useState } from "react";

export interface PatientState {
  patientId: string;
  observations: Partial<Record<"gait" | "skin" | "respiration", AgentObservation>>;
  decision?: TriageDecision;
  updatedAt: number;
}

export type ConnectionStatus = "connecting" | "live" | "offline";

export function useTriageStream() {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [current, setCurrent] = useState<PatientState | null>(null);
  const [history, setHistory] = useState<TriageDecision[]>([]);
  const sourceRef = useRef<EventSource | null>(null);

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
      setCurrent((prev) => {
        if (!prev || prev.patientId !== data.patient_id) {
          return {
            patientId: data.patient_id,
            observations: { [data.observation.agent]: data.observation },
            updatedAt: Date.now(),
          };
        }
        return {
          ...prev,
          observations: { ...prev.observations, [data.observation.agent]: data.observation },
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
      setCurrent((prev) => ({
        patientId: data.patient_id,
        observations: prev?.patientId === data.patient_id ? prev.observations : {},
        decision: data.decision,
        updatedAt: Date.now(),
      }));
      setHistory((prev) => [data.decision, ...prev].slice(0, 5));
    });

    es.onerror = () => setStatus("offline");

    return () => {
      es.close();
      sourceRef.current = null;
    };
  }, []);

  return { status, current, history };
}
