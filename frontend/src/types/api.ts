export interface DashboardOverview {
  overall_trust_score: number | null;
  total_verifications: number;
  total_claims: number;
  supported_claims: number;
  contradicted_claims: number;
  inconclusive_claims: number;
  hallucination_rate: number;
  average_confidence: number | null;
  signal_quality: number;
  evidence_quality: number;
}

export interface VerificationStats {
  total_claims: number;
  supported: { count: number; percentage: number };
  contradicted: { count: number; percentage: number };
  inconclusive: { count: number; percentage: number };
}

export interface ConfidenceData {
  average_confidence: number | null;
  total_claims: number;
  valid_signal_count: number;
  no_verification_signal_count: number;
  distribution: Array<{ range: string; count: number }>;
  note?: string;
}

export interface SignalQualityData {
  average_signal_quality: number;
  total_signals: number;
  breakdown: {
    entailment: number;
    contradiction: number;
    absent: number;
    refused: number;
    failed_judgment: number;
  };
  note?: string;
}

export interface EvidenceQualityData {
  average_strength: number;
  total_evidence: number;
  strong_evidence_count: number;
  distribution: {
    SUPPORT: number;
    CONTRADICT: number;
    UNKNOWN: number;
  };
  note?: string;
}

export interface TrendPoint {
  date: string;
  verifications: number;
  trust_score: number | null;
  supported: number;
  contradicted: number;
  inconclusive: number;
  hallucination_rate: number;
  confidence: number | null;
}

export interface DomainStat {
  domain: string;
  verification_count: number;
  trust_score: number | null;
  supported: number;
  contradicted: number;
  inconclusive: number;
  hallucination_rate: number;
  confidence: number | null;
}

export interface ModelStat {
  model_id: string;
  verification_count: number;
  trust_score: number | null;
  supported_rate: number;
  contradiction_rate: number;
  inconclusive_rate: number;
  hallucination_rate: number;
  average_confidence: number | null;
}

export interface FilterOptions {
  models: string[];
  domains: string[];
  verdicts: string[];
  date_range: { min: string | null; max: string | null };
}

export interface ActiveFilters {
  dateFrom: string;
  dateTo: string;
  modelId: string;
  verdict: string;
  domain: string;
}

export interface LeaderboardModel {
  rank: number;
  model_id: string;
  verification_count: number;
  verification_accuracy: number;
  trust_score: number;
  hallucination_rate: number;
  consistency: number;
  support_rate: number;
  contradiction_rate: number;
  inconclusive_rate: number;
  average_confidence: number | null;
  evidence_supported_rate: number;
}

export interface LeaderboardMetricInfo {
  id: string;
  label: string;
  description: string;
}

export interface ModelDetail {
  model_id: string;
  verification_count: number;
  trust_score: number;
  accuracy: number;
  hallucination_rate: number;
  consistency: number;
  confidence: number | null;
  evidence_support: number;
  contradiction_rate: number;
  inconclusive_rate: number;
  total_claims: number;
  historical_performance: Array<{
    date: string;
    trust_score: number;
    hallucination_rate: number;
  }>;
}

export interface BenchmarkMetrics {
  benchmark_id: string;
  sampling_basis: "prompt_generation" | "response_rewrite";
  total_items: number;
  claim_level: {
    precision: number;
    recall: number;
    f1: number;
    accuracy: number;
  };
  system_level: {
    hallucination_rate: number;
    verification_accuracy: number;
    false_positive_rate: number;
    false_negative_rate: number;
  };
  calibration: {
    ece: number;
  };
  operational: {
    avg_latency_ms: number;
    avg_llm_calls: number;
    avg_search_calls: number;
    total_token_usage: number;
    failure_rate: number;
  };
}

export interface BenchmarkModelResult {
  model_id: string;
  sampling_basis: string;
  item_count: number;
  precision: number;
  recall: number;
  f1: number;
  accuracy: number;
  ece: number;
  latency_ms: number;
  token_usage: number;
  failure_rate: number;
}

export interface BenchmarkClaimResult {
  claim_id: string;
  item_id: string;
  claim_text: string;
  model_id: string;
  sampling_basis: string;
  ground_truth: string;
  predicted_verdict: string;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  accuracy: number | null;
  ece: number | null;
  is_correct: boolean;
  status: string;
}
