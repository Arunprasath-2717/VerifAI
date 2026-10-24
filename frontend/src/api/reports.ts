/**
 * VerifAI Analytics & Reports API Client
 * Connects to /api/v1/reports/analytics
 */

import { apiClient } from './client';

export interface AnalyticsSummary {
  total_verifications: number;
  supported_claims: number;
  contradicted_claims: number;
  unknown_claims: number;
  overall_accuracy_rate: number;
  avg_latency_ms: number;
}

export interface AnalyticsTimelinePoint {
  date: string;
  verifications: number;
  supported: number;
  contradicted: number;
  unknown: number;
}

export interface AnalyticsModelBreakdown {
  model_name: string;
  provider: string;
  total_runs: number;
  avg_latency_ms: number;
  pass_rate: number;
}

export interface AnalyticsEvidenceSource {
  source: string;
  count: number;
  reliability_score: number;
}

export interface AnalyticsReportResponse {
  period?: string;
  timeframe?: string;
  summary?: AnalyticsSummary;
  timeline?: AnalyticsTimelinePoint[];
  chart_data?: any[];
  model_breakdown?: AnalyticsModelBreakdown[];
  model_usage?: { model: string; usage: number }[];
  evidence_sources?: any[];
  total_verifications?: number;
  total_claims?: number;
  average_trust_score?: number;
  supported_rate?: number;
  contradicted_rate?: number;
  unknown_rate?: number;
}

export const reportsApi = {
  async getAnalytics(timeframe: '7D' | '30D' | '90D' | '1Y' = '30D'): Promise<AnalyticsReportResponse> {
    return apiClient<AnalyticsReportResponse>('/reports/analytics', {
      method: 'GET',
      params: { timeframe },
    });
  },
};
