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

const API_BASE_URL = "http://localhost:8000/api/v1";

function buildQueryParams(filters?: ActiveFilters, extraParams?: Record<string, string>): string {
  const params = new URLSearchParams();
  if (filters) {
    if (filters.dateFrom) params.append("date_from", filters.dateFrom);
    if (filters.dateTo) params.append("date_to", filters.dateTo);
    if (filters.modelId) params.append("model_id", filters.modelId);
    if (filters.verdict) params.append("verdict", filters.verdict);
    if (filters.domain) params.append("domain", filters.domain);
  }
  if (extraParams) {
    Object.entries(extraParams).forEach(([k, v]) => {
      if (v) params.append(k, v);
    });
  }
  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

export async function fetchOverview(filters?: ActiveFilters): Promise<DashboardOverview> {
  const res = await fetch(`${API_BASE_URL}/dashboard/overview${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch dashboard overview");
  return res.json();
}

export async function fetchTrustScore(filters?: ActiveFilters) {
  const res = await fetch(`${API_BASE_URL}/dashboard/trust-score${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch trust score");
  return res.json();
}

export async function fetchVerificationStats(filters?: ActiveFilters): Promise<VerificationStats> {
  const res = await fetch(`${API_BASE_URL}/dashboard/verification-stats${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch verification stats");
  return res.json();
}

export async function fetchHallucinationRate(filters?: ActiveFilters) {
  const res = await fetch(`${API_BASE_URL}/dashboard/hallucination-rate${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch hallucination rate");
  return res.json();
}

export async function fetchConfidence(filters?: ActiveFilters): Promise<ConfidenceData> {
  const res = await fetch(`${API_BASE_URL}/dashboard/confidence${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch confidence analytics");
  return res.json();
}

export async function fetchSignalQuality(filters?: ActiveFilters): Promise<SignalQualityData> {
  const res = await fetch(`${API_BASE_URL}/dashboard/signal-quality${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch signal quality");
  return res.json();
}

export async function fetchEvidenceQuality(filters?: ActiveFilters): Promise<EvidenceQualityData> {
  const res = await fetch(`${API_BASE_URL}/dashboard/evidence-quality${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch evidence quality");
  return res.json();
}

export async function fetchTrends(filters?: ActiveFilters): Promise<{ trends: TrendPoint[] }> {
  const res = await fetch(`${API_BASE_URL}/dashboard/trends${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch trends");
  return res.json();
}

export async function fetchDomains(filters?: ActiveFilters): Promise<{ domains: DomainStat[] }> {
  const res = await fetch(`${API_BASE_URL}/dashboard/domains${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch domain analytics");
  return res.json();
}

export async function fetchModels(filters?: ActiveFilters): Promise<{ models: ModelStat[] }> {
  const res = await fetch(`${API_BASE_URL}/dashboard/models${buildQueryParams(filters)}`);
  if (!res.ok) throw new Error("Failed to fetch model analytics");
  return res.json();
}

export async function fetchFilters(): Promise<FilterOptions> {
  const res = await fetch(`${API_BASE_URL}/dashboard/filters`);
  if (!res.ok) throw new Error("Failed to fetch available filters");
  return res.json();
}

export async function fetchLeaderboard(sortBy: string = "verification_accuracy", order: string = "desc"): Promise<{ models: LeaderboardModel[]; sort_by: string; order: string }> {
  const res = await fetch(`${API_BASE_URL}/leaderboard?sort_by=${sortBy}&order=${order}`);
  if (!res.ok) throw new Error("Failed to fetch leaderboard");
  return res.json();
}

export async function fetchLeaderboardMetrics(): Promise<{ metrics: LeaderboardMetricInfo[] }> {
  const res = await fetch(`${API_BASE_URL}/leaderboard/metrics`);
  if (!res.ok) throw new Error("Failed to fetch leaderboard metrics");
  return res.json();
}

export async function fetchModelDetail(modelId: string): Promise<ModelDetail> {
  const res = await fetch(`${API_BASE_URL}/leaderboard/${encodeURIComponent(modelId)}`);
  if (!res.ok) throw new Error(`Failed to fetch model detail for ${modelId}`);
  return res.json();
}

export async function compareModels(modelIds: string[]): Promise<{ models: ModelDetail[]; comparison_matrix: Record<string, Record<string, any>> }> {
  const res = await fetch(`${API_BASE_URL}/leaderboard/compare?models=${encodeURIComponent(modelIds.join(","))}`);
  if (!res.ok) throw new Error("Failed to compare models");
  return res.json();
}

export async function fetchBenchmarks(): Promise<{ benchmarks: any[] }> {
  const res = await fetch(`${API_BASE_URL}/benchmark`);
  if (!res.ok) throw new Error("Failed to fetch benchmarks");
  return res.json();
}

export async function fetchBenchmarkMetrics(benchmarkId: string): Promise<BenchmarkMetrics> {
  const res = await fetch(`${API_BASE_URL}/benchmark/${encodeURIComponent(benchmarkId)}/metrics`);
  if (!res.ok) throw new Error("Failed to fetch benchmark metrics");
  return res.json();
}

export async function fetchBenchmarkModels(benchmarkId: string): Promise<{ benchmark_id: string; models: BenchmarkModelResult[] }> {
  const res = await fetch(`${API_BASE_URL}/benchmark/${encodeURIComponent(benchmarkId)}/models`);
  if (!res.ok) throw new Error("Failed to fetch benchmark model results");
  return res.json();
}

export async function fetchBenchmarkClaims(benchmarkId: string, modelId?: string): Promise<{ benchmark_id: string; model_id?: string; total_claims: number; claims: BenchmarkClaimResult[] }> {
  const q = modelId ? `?model_id=${encodeURIComponent(modelId)}` : "";
  const res = await fetch(`${API_BASE_URL}/benchmark/${encodeURIComponent(benchmarkId)}/claims${q}`);
  if (!res.ok) throw new Error("Failed to fetch benchmark claims");
  return res.json();
}

export async function fetchBenchmarkComparison(benchmarkIds?: string[]): Promise<{ comparison: BenchmarkMetrics[] }> {
  const q = benchmarkIds && benchmarkIds.length > 0 ? `?benchmark_ids=${encodeURIComponent(benchmarkIds.join(","))}` : "";
  const res = await fetch(`${API_BASE_URL}/benchmark/compare${q}`);
  if (!res.ok) throw new Error("Failed to fetch benchmark comparisons");
  return res.json();
}
