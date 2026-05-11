export type TriageCategory = "red" | "yellow" | "green" | "insufficient";

export interface AgentObservation {
  agent: "gait" | "skin" | "respiration";
  confidence: number;
  summary_tr: string;
  signals: Record<string, number | string | boolean>;
  captured_at: string;
}

export interface TriageDecision {
  patient_id: string;
  category: TriageCategory;
  label_tr: string;
  rationale_tr: string;
  confidence: number;
  per_agent_weights: Record<string, number>;
  rag_references: string[];
  decided_at: string;
  latency_ms: number | null;
}

export type TriageEvent =
  | { type: "agent_observation"; patient_id: string; observation: AgentObservation; emitted_at: string }
  | { type: "decision"; patient_id: string; decision: TriageDecision; emitted_at: string }
  | { type: "heartbeat"; emitted_at: string; message?: string }
  | { type: "error"; emitted_at: string; message: string };
