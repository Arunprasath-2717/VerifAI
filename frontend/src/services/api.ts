import type {
  DashboardOverview,
  VerificationStats,
  ConfidenceData,
  SignalQualityData,
  EvidenceQualityData,
  TrendPoint,
  DomainStat,
  ModelStat,
  FilterOptions,
  ActiveFilters,
  LeaderboardModel,
  LeaderboardMetricInfo,
  ModelDetail,
  BenchmarkMetrics,
  BenchmarkModelResult,
  BenchmarkClaimResult
} from "../types/api";

const DELAY = 300;
const simulateNetworkDelay = () => new Promise(resolve => setTimeout(resolve, DELAY));

export async function fetchOverview(filters?: ActiveFilters): Promise<DashboardOverview> {
  await simulateNetworkDelay();
  return {
    overall_trust_score: 92,
    total_verifications: 14205,
    total_claims: 24500,
    supported_claims: 18000,
    contradicted_claims: 4500,
    inconclusive_claims: 2000,
    hallucination_rate: 0.04,
    average_confidence: 0.88,
    signal_quality: 0.91,
    evidence_quality: 0.89
  };
}

export async function fetchTrustScore(filters?: ActiveFilters) {
  await simulateNetworkDelay();
  return { score: 92, trend: "+2.4%" };
}

export async function fetchVerificationStats(filters?: ActiveFilters): Promise<VerificationStats> {
  await simulateNetworkDelay();
  return {
    total_claims: 24500,
    supported: { count: 18000, percentage: 73.4 },
    contradicted: { count: 4500, percentage: 18.3 },
    inconclusive: { count: 2000, percentage: 8.3 }
  };
}

export async function fetchHallucinationRate(filters?: ActiveFilters) {
  await simulateNetworkDelay();
  return { rate: 0.04, trend: "-0.5%" };
}

export async function fetchConfidence(filters?: ActiveFilters): Promise<ConfidenceData> {
  await simulateNetworkDelay();
  return {
    average_confidence: 0.88,
    total_claims: 24500,
    valid_signal_count: 23000,
    no_verification_signal_count: 1500,
    distribution: [
      { range: "0-20%", count: 120 },
      { range: "20-40%", count: 450 },
      { range: "40-60%", count: 1200 },
      { range: "60-80%", count: 4500 },
      { range: "80-100%", count: 18230 }
    ]
  };
}

export async function fetchSignalQuality(filters?: ActiveFilters): Promise<SignalQualityData> {
  await simulateNetworkDelay();
  return {
    average_signal_quality: 0.91,
    total_signals: 24500,
    breakdown: {
      entailment: 18000,
      contradiction: 4500,
      absent: 1000,
      refused: 500,
      failed_judgment: 500
    }
  };
}

export async function fetchEvidenceQuality(filters?: ActiveFilters): Promise<EvidenceQualityData> {
  await simulateNetworkDelay();
  return {
    average_strength: 0.89,
    total_evidence: 45000,
    strong_evidence_count: 38000,
    distribution: {
      SUPPORT: 30000,
      CONTRADICT: 10000,
      UNKNOWN: 5000
    }
  };
}

export async function fetchTrends(filters?: ActiveFilters): Promise<{ trends: TrendPoint[] }> {
  await simulateNetworkDelay();
  return {
    trends: [
      { date: "2026-09-01", verifications: 450, trust_score: 91, supported: 300, contradicted: 100, inconclusive: 50, hallucination_rate: 0.04, confidence: 0.87 },
      { date: "2026-09-02", verifications: 480, trust_score: 92, supported: 320, contradicted: 110, inconclusive: 50, hallucination_rate: 0.03, confidence: 0.88 },
      { date: "2026-09-03", verifications: 520, trust_score: 93, supported: 350, contradicted: 120, inconclusive: 50, hallucination_rate: 0.03, confidence: 0.89 },
      { date: "2026-09-04", verifications: 490, trust_score: 91, supported: 340, contradicted: 105, inconclusive: 45, hallucination_rate: 0.05, confidence: 0.86 },
      { date: "2026-09-05", verifications: 600, trust_score: 94, supported: 400, contradicted: 150, inconclusive: 50, hallucination_rate: 0.02, confidence: 0.91 },
      { date: "2026-09-06", verifications: 650, trust_score: 95, supported: 450, contradicted: 130, inconclusive: 70, hallucination_rate: 0.02, confidence: 0.92 },
      { date: "2026-09-07", verifications: 700, trust_score: 96, supported: 480, contradicted: 160, inconclusive: 60, hallucination_rate: 0.01, confidence: 0.94 }
    ]
  };
}

export async function fetchDomains(filters?: ActiveFilters): Promise<{ domains: DomainStat[] }> {
  await simulateNetworkDelay();
  return {
    domains: [
      { domain: "Science", verification_count: 4500, trust_score: 95, supported: 3500, contradicted: 800, inconclusive: 200, hallucination_rate: 0.01, confidence: 0.94 },
      { domain: "Politics", verification_count: 3200, trust_score: 82, supported: 1500, contradicted: 1200, inconclusive: 500, hallucination_rate: 0.06, confidence: 0.82 },
      { domain: "Technology", verification_count: 2800, trust_score: 97, supported: 2400, contradicted: 300, inconclusive: 100, hallucination_rate: 0.01, confidence: 0.96 },
      { domain: "Health", verification_count: 3705, trust_score: 89, supported: 2500, contradicted: 900, inconclusive: 305, hallucination_rate: 0.03, confidence: 0.89 }
    ]
  };
}

export async function fetchModels(filters?: ActiveFilters): Promise<{ models: ModelStat[] }> {
  await simulateNetworkDelay();
  return {
    models: [
      { model_id: "gemini-1.5-pro", verification_count: 5000, trust_score: 96, supported_rate: 0.75, contradiction_rate: 0.20, inconclusive_rate: 0.05, hallucination_rate: 0.02, average_confidence: 0.94 },
      { model_id: "gpt-4o", verification_count: 4205, trust_score: 94, supported_rate: 0.72, contradiction_rate: 0.22, inconclusive_rate: 0.06, hallucination_rate: 0.03, average_confidence: 0.93 },
      { model_id: "claude-3-opus", verification_count: 5000, trust_score: 92, supported_rate: 0.70, contradiction_rate: 0.25, inconclusive_rate: 0.05, hallucination_rate: 0.04, average_confidence: 0.91 }
    ]
  };
}

export async function fetchFilters(): Promise<FilterOptions> {
  await simulateNetworkDelay();
  return {
    models: ["gemini-1.5-pro", "gpt-4o", "claude-3-opus"],
    domains: ["Science", "Politics", "Technology", "Health"],
    verdicts: ["SUPPORTED", "CONTRADICTED", "NEUTRAL"],
    date_range: { min: "2026-09-01", max: "2026-09-30" }
  };
}

export async function fetchLeaderboard(sortBy: string = "verification_accuracy", order: string = "desc"): Promise<{ models: LeaderboardModel[]; sort_by: string; order: string }> {
  await simulateNetworkDelay();
  return {
    sort_by: sortBy,
    order,
    models: [
      { rank: 1, model_id: "gemini-1.5-pro", verification_count: 5000, verification_accuracy: 0.96, trust_score: 96, hallucination_rate: 0.02, consistency: 0.98, support_rate: 0.75, contradiction_rate: 0.20, inconclusive_rate: 0.05, average_confidence: 0.94, evidence_supported_rate: 0.95 },
      { rank: 2, model_id: "gpt-4o", verification_count: 4205, verification_accuracy: 0.95, trust_score: 94, hallucination_rate: 0.03, consistency: 0.96, support_rate: 0.72, contradiction_rate: 0.22, inconclusive_rate: 0.06, average_confidence: 0.93, evidence_supported_rate: 0.93 },
      { rank: 3, model_id: "claude-3-opus", verification_count: 5000, verification_accuracy: 0.94, trust_score: 92, hallucination_rate: 0.04, consistency: 0.95, support_rate: 0.70, contradiction_rate: 0.25, inconclusive_rate: 0.05, average_confidence: 0.91, evidence_supported_rate: 0.90 }
    ]
  };
}

export async function fetchLeaderboardMetrics(): Promise<{ metrics: LeaderboardMetricInfo[] }> {
  await simulateNetworkDelay();
  return {
    metrics: [
      { id: "verification_accuracy", label: "Accuracy", description: "Overall accuracy of verification" },
      { id: "trust_score", label: "Trust Score", description: "Aggregated metric of reliability" }
    ]
  };
}

export async function fetchModelDetail(modelId: string): Promise<ModelDetail> {
  await simulateNetworkDelay();
  return {
    model_id: modelId,
    verification_count: 5000,
    trust_score: 96,
    accuracy: 0.96,
    hallucination_rate: 0.02,
    consistency: 0.98,
    confidence: 0.94,
    evidence_support: 0.95,
    contradiction_rate: 0.20,
    inconclusive_rate: 0.05,
    total_claims: 12000,
    historical_performance: [
      { date: "2026-09-01", trust_score: 94, hallucination_rate: 0.03 },
      { date: "2026-09-07", trust_score: 96, hallucination_rate: 0.02 }
    ]
  };
}

export async function compareModels(modelIds: string[]): Promise<{ models: ModelDetail[]; comparison_matrix: Record<string, Record<string, any>> }> {
  await simulateNetworkDelay();
  return {
    models: [
      {
        model_id: "gemini-1.5-pro",
        verification_count: 5000,
        trust_score: 96,
        accuracy: 0.96,
        hallucination_rate: 0.02,
        consistency: 0.98,
        confidence: 0.94,
        evidence_support: 0.95,
        contradiction_rate: 0.20,
        inconclusive_rate: 0.05,
        total_claims: 12000,
        historical_performance: []
      }
    ],
    comparison_matrix: {}
  };
}

export async function fetchBenchmarks(): Promise<{ benchmarks: any[] }> {
  await simulateNetworkDelay();
  return { benchmarks: [{ id: "b1", name: "TruthfulQA", description: "Fact-checking benchmark" }] };
}

export async function fetchBenchmarkMetrics(benchmarkId: string): Promise<BenchmarkMetrics> {
  await simulateNetworkDelay();
  return {
    benchmark_id: benchmarkId,
    sampling_basis: "prompt_generation",
    total_items: 1000,
    claim_level: { precision: 0.95, recall: 0.94, f1: 0.945, accuracy: 0.95 },
    system_level: { hallucination_rate: 0.02, verification_accuracy: 0.96, false_positive_rate: 0.01, false_negative_rate: 0.01 },
    calibration: { ece: 0.03 },
    operational: { avg_latency_ms: 250, avg_llm_calls: 1.5, avg_search_calls: 3.2, total_token_usage: 150000, failure_rate: 0.001 }
  };
}

export async function fetchBenchmarkModels(benchmarkId: string): Promise<{ benchmark_id: string; models: BenchmarkModelResult[] }> {
  await simulateNetworkDelay();
  return {
    benchmark_id: benchmarkId,
    models: [
      { model_id: "gemini-1.5-pro", sampling_basis: "prompt_generation", item_count: 1000, precision: 0.96, recall: 0.95, f1: 0.955, accuracy: 0.96, ece: 0.02, latency_ms: 240, token_usage: 120000, failure_rate: 0.001 }
    ]
  };
}

export async function fetchBenchmarkClaims(benchmarkId: string, modelId?: string): Promise<{ benchmark_id: string; model_id?: string; total_claims: number; claims: BenchmarkClaimResult[] }> {
  await simulateNetworkDelay();
  return {
    benchmark_id: benchmarkId,
    model_id: modelId,
    total_claims: 2,
    claims: [
      { claim_id: "c1", item_id: "i1", claim_text: "Water boils at 100C", model_id: "gemini-1.5-pro", sampling_basis: "prompt_generation", ground_truth: "SUPPORTED", predicted_verdict: "SUPPORTED", precision: 0.99, recall: 0.99, f1: 0.99, accuracy: 1.0, ece: 0.01, is_correct: true, status: "SUCCESS" }
    ]
  };
}

export async function fetchBenchmarkComparison(benchmarkIds?: string[]): Promise<{ comparison: BenchmarkMetrics[] }> {
  await simulateNetworkDelay();
  return { comparison: [] };
}
