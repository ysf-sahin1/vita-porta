export type TriageCategory = "red" | "yellow" | "green" | "insufficient";

export interface AgentObservation {
  agent: "gait" | "thermal" | "expression";
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

export interface DecisionRecord {
  decision_id: string;
  patient_id: string;
  decision: TriageDecision;
  observations_snapshot: Record<string, AgentObservation>;
}

export interface HistoryResponse {
  decisions: DecisionRecord[];
  feedback: NurseFeedback[];
}

export interface NurseSessionRecord {
  session_id: string;
  nurse_first_name: string;
  nurse_last_name: string;
  hospital: string;
  login_at: string;
  logout_at: string | null;
}

export interface BenchmarkCaseResult {
  case_id: string;
  expected_category: TriageCategory;
  predicted_category: TriageCategory;
  correct: boolean;
  critical_miss: boolean;
  under_triage: boolean;
  over_triage: boolean;
  input_type: string;
  confidence: number;
  latency_ms: number;
  agent_confidences: Record<string, number>;
  notes: string;
  tags: string[];
  error: string | null;
}

export interface BenchmarkMetrics {
  total_cases: number;
  correct_cases: number;
  accuracy: number;
  red_sensitivity: number | null;
  critical_miss_rate: number | null;
  under_triage_rate: number;
  over_triage_rate: number;
  insufficient_rate: number;
  mean_latency_ms: number;
  p95_latency_ms: number;
  category_recall: Record<TriageCategory, number | null>;
  confusion_matrix: Record<TriageCategory, Record<TriageCategory, number>>;
}

export interface BenchmarkReport {
  dataset_name: string;
  dataset_version: string;
  dataset_description: string;
  synthetic: boolean;
  engine: string;
  created_at: string;
  metrics: BenchmarkMetrics;
  results: BenchmarkCaseResult[];
}

export type TriageEvent =
  | { type: "agent_observation"; patient_id: string; observation: AgentObservation; emitted_at: string }
  | { type: "decision"; patient_id: string; decision: TriageDecision; emitted_at: string }
  | { type: "heartbeat"; emitted_at: string; message?: string }
  | { type: "error"; emitted_at: string; message: string }
  | { type: "pir_status"; pir_motion: boolean; emitted_at: string };
