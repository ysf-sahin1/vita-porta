"use client";

import { fetchHistory, postFeedback, streamUrl } from "@/lib/api";
import type { AgentObservation, NurseFeedback, TriageCategory, TriageDecision } from "@/lib/types";
import { useCallback, useEffect, useRef, useState } from "react";
import { type Verdict } from "./NurseVerdict";
import { useNurseSession } from "./SessionGate";

type AgentKey = "gait" | "skin" | "respiration" | "thermal" | "expression";
type Observations = Partial<Record<AgentKey, AgentObservation>>;

export interface PatientState {
  patientId: string;
  observations: Observations;
  decision?: TriageDecision;
  updatedAt: number;
}

export interface NurseMeta {
  firstName: string;
  lastName: string;
  hospital: string;
  feedbackAt: string;
}

export interface HistoryEntry {
  key: string;
  patientId: string;
  decision: TriageDecision;
  observations: Observations;
  /** Restore'dan geliyorsa true — backend'de feedback var, SSE'den canlı görmedik. */
  restored?: boolean;
}

export type ConnectionStatus = "connecting" | "live" | "offline";

export interface StreamSnapshot {
  status: ConnectionStatus;
  current: PatientState | null;
  history: HistoryEntry[];
  verdicts: Record<string, Verdict>;
  verdictNurses: Record<string, NurseMeta>;
  setVerdict: (key: string, verdict: Verdict) => void;
  lastObservationAt: number | null;
  lastDecisionLatencyMs: number | null;
}

export function entryKey(patientId: string, decidedAt: string): string {
  return `${patientId}__${decidedAt}`;
}

export function useTriageStream(): StreamSnapshot {
  const { session } = useNurseSession();
  const sessionRef = useRef(session);
  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [current, setCurrent] = useState<PatientState | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [verdicts, setVerdicts] = useState<Record<string, Verdict>>({});
  const [verdictNurses, setVerdictNurses] = useState<Record<string, NurseMeta>>({});
  const [lastObservationAt, setLastObservationAt] = useState<number | null>(null);
  const [lastDecisionLatencyMs, setLastDecisionLatencyMs] = useState<number | null>(null);

  const sourceRef = useRef<EventSource | null>(null);
  const patientObsRef = useRef<{ id: string | null; obs: Observations }>({ id: null, obs: {} });
  // Restore + canlı akış sırasında aynı kararın iki kere history'e girmesini önleyen set.
  const seenKeysRef = useRef<Set<string>>(new Set());
  // Son verdict'in kararı için snapshot — Auto-POST aramasında kullanılır.
  const decisionByKeyRef = useRef<Record<string, { decision: TriageDecision; obs: Observations }>>({});

  // ---- Mount: backend'den geçmiş feedback'leri restore et -------------------
  useEffect(() => {
    let cancelled = false;
    fetchHistory()
      .then((records) => {
        if (cancelled) return;
        const restoredEntries: HistoryEntry[] = [];
        const restoredVerdicts: Record<string, Verdict> = {};
        const restoredNurses: Record<string, NurseMeta> = {};

        for (const fb of records) {
          const verdict = feedbackToVerdict(fb);
          restoredVerdicts[fb.decision_id] = verdict;
          restoredNurses[fb.decision_id] = {
            firstName: fb.nurse_first_name,
            lastName: fb.nurse_last_name,
            hospital: fb.hospital,
            feedbackAt: fb.feedback_at,
          };

          if (!seenKeysRef.current.has(fb.decision_id)) {
            seenKeysRef.current.add(fb.decision_id);
            restoredEntries.push({
              key: fb.decision_id,
              patientId: fb.patient_id,
              decision: reconstructDecisionFromFeedback(fb),
              observations: (fb.observations_snapshot ?? {}) as Observations,
              restored: true,
            });
          }
        }

        restoredEntries.sort(
          (a, b) =>
            new Date(b.decision.decided_at).getTime() - new Date(a.decision.decided_at).getTime(),
        );

        setHistory((prev) => [...prev, ...restoredEntries]);
        setVerdicts((prev) => ({ ...restoredVerdicts, ...prev }));
        setVerdictNurses((prev) => ({ ...restoredNurses, ...prev }));
      })
      .catch((err) => {
        console.warn("[useTriageStream] history restore başarısız:", err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // ---- SSE kanalı -----------------------------------------------------------
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
      decisionByKeyRef.current[key] = { decision: data.decision, obs: obsSnapshot };

      // Aynı decision iki kere gelmesin (örn. restore + SSE replay).
      if (!seenKeysRef.current.has(key)) {
        seenKeysRef.current.add(key);
        setHistory((prev) => [
          { key, patientId: data.patient_id, decision: data.decision, observations: obsSnapshot },
          ...prev,
        ]);
      }

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

  // ---- setVerdict: state güncelle + backend'e POST --------------------------
  const setVerdict = useCallback((key: string, verdict: Verdict) => {
    const sess = sessionRef.current;
    setVerdicts((prev) => ({ ...prev, [key]: verdict }));
    setVerdictNurses((prev) => ({
      ...prev,
      [key]: {
        firstName: sess.firstName,
        lastName: sess.lastName,
        hospital: sess.hospital,
        feedbackAt: new Date().toISOString(),
      },
    }));

    // Karar snapshot'ı SSE'den geldiyse ya da history'de varsa onu kullan.
    const snap =
      decisionByKeyRef.current[key] ??
      findDecisionInHistoryByKey(key);
    if (!snap) {
      console.warn("[useTriageStream] verdict atıldı ama karar snapshot'ı yok:", key);
      return;
    }

    const verdictCategory: TriageCategory =
      verdict.action === "modified" && verdict.category
        ? verdict.category
        : snap.decision.category;

    const verdictKind: NurseFeedback["verdict_kind"] =
      verdict.action === "approved"
        ? "approve"
        : verdict.action === "rejected"
          ? "reject"
          : "override";

    const feedback: NurseFeedback = {
      decision_id: key,
      patient_id: snap.decision.patient_id,
      original_category: snap.decision.category,
      nurse_verdict: verdictCategory,
      verdict_kind: verdictKind,
      rationale_tr: snap.decision.rationale_tr ?? "",
      nurse_first_name: sess.firstName,
      nurse_last_name: sess.lastName,
      hospital: sess.hospital,
      signals_summary: buildSignalsSummary(snap.obs, snap.decision),
      observations_snapshot: snap.obs as Record<string, AgentObservation>,
      decided_at: snap.decision.decided_at,
      feedback_at: new Date().toISOString(),
    };

    postFeedback(feedback).catch((err) => {
      console.warn("[useTriageStream] postFeedback başarısız:", err);
    });
  }, []);

  // History'den decision snapshot bulma helper'ı — closure içinde state'i takip eder.
  const historyRef = useRef(history);
  useEffect(() => {
    historyRef.current = history;
  }, [history]);
  function findDecisionInHistoryByKey(
    key: string,
  ): { decision: TriageDecision; obs: Observations } | null {
    const entry = historyRef.current.find((e) => e.key === key);
    return entry ? { decision: entry.decision, obs: entry.observations } : null;
  }

  return {
    status,
    current,
    history,
    verdicts,
    verdictNurses,
    setVerdict,
    lastObservationAt,
    lastDecisionLatencyMs,
  };
}

// ----------------------------------------------------------------- helpers

function feedbackToVerdict(fb: NurseFeedback): Verdict {
  const at = formatVerdictTimeFromIso(fb.feedback_at);
  if (fb.verdict_kind === "approve") return { action: "approved", at };
  if (fb.verdict_kind === "reject") return { action: "rejected", at };
  return { action: "modified", category: fb.nurse_verdict, at };
}

function formatVerdictTimeFromIso(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

function reconstructDecisionFromFeedback(fb: NurseFeedback): TriageDecision {
  const label =
    fb.original_category === "red"
      ? "Kırmızı — Acil"
      : fb.original_category === "yellow"
        ? "Sarı — Kısa süre içinde"
        : fb.original_category === "green"
          ? "Yeşil — Düşük öncelik"
          : "Veri yetersiz";
  return {
    patient_id: fb.patient_id,
    category: fb.original_category,
    label_tr: label,
    rationale_tr: fb.rationale_tr || "(geçmiş kayıttan yüklendi)",
    confidence: 0,
    per_agent_weights: {},
    rag_references: [],
    historical_feedback: [],
    decided_at: fb.decided_at,
    latency_ms: null,
  };
}

function buildSignalsSummary(obs: Observations, decision: TriageDecision): string {
  const parts: string[] = [decision.rationale_tr ?? ""];
  for (const ob of Object.values(obs)) {
    if (!ob) continue;
    parts.push(ob.summary_tr);
    for (const [k, v] of Object.entries(ob.signals ?? {})) {
      if (typeof v === "string") parts.push(`${k}:${v}`);
      else if (typeof v === "boolean" && v) parts.push(k);
      else if (typeof v === "number") parts.push(`${k}:${v.toFixed(2)}`);
    }
  }
  return parts.filter(Boolean).join(" ");
}
