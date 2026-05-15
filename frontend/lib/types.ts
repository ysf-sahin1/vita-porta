export type TriageCategory = "red" | "yellow" | "green" | "insufficient";

export interface AgentObservation {
  agent: "gait" | "skin" | "respiration" | "thermal" | "expression";
  confidence: number;
  summary_tr: string;
  signals: Record<string, number | string | boolean>;
  captured_at: string;
}

export interface HistoricalFeedback {
  nurse_name: string;
  hospital: string;
  original_category: TriageCategory;
  nurse_verdict: string;
  verdict_kind: "approve" | "reject" | "override";
  rationale_tr: string;
  feedback_at: string;
  similarity_score: number;
}

export interface TriageDecision {
  patient_id: string;
  category: TriageCategory;
  label_tr: string;
  rationale_tr: string;
  confidence: number;
  per_agent_weights: Record<string, number>;
  rag_references: string[];
  historical_feedback: HistoricalFeedback[];
  decided_at: string;
  latency_ms: number | null;
}

export interface NurseFeedback {
  decision_id: string;
  patient_id: string;
  original_category: TriageCategory;
  nurse_verdict: TriageCategory;
  verdict_kind: "approve" | "reject" | "override";
  rationale_tr: string;
  nurse_first_name: string;
  nurse_last_name: string;
  hospital: string;
  signals_summary: string;
  observations_snapshot: Record<string, AgentObservation>;
  decided_at: string;
  feedback_at: string;
}

export type TriageEvent =
  | { type: "agent_observation"; patient_id: string; observation: AgentObservation; emitted_at: string }
  | { type: "decision"; patient_id: string; decision: TriageDecision; emitted_at: string }
  | { type: "heartbeat"; emitted_at: string; message?: string }
  | { type: "error"; emitted_at: string; message: string };
