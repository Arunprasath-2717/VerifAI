import { apiClient } from './client';
import { ChartPoint, VerificationRecord, ModelLeaderboardEntry } from '../types';

export interface DashboardStatsData {
  verifications_count: number;
  claims_count: number;
  evidence_sources_count: number;
  conversations_count: number;
  weekly_chart_data: ChartPoint[];
  monthly_chart_data: ChartPoint[];
  recent_verifications: any[];
  stat_cards: {
    title: string;
    value: string;
    trend: string;
    sub: string;
    sparkline: number[];
  }[];
  leaderboard_preview: {
    rank: number;
    model: string;
    provider: string;
    accuracy: number;
    hallucination_rate: number;
    latency_ms: number;
    certified: boolean;
  }[];
  sparklines?: {
    verifications?: number[];
    claims?: number[];
    evidence?: number[];
    conversations?: number[];
  };
}

export type BackendDashboardStats = DashboardStatsData;

export const dashboardApi = {
  async getStats(): Promise<DashboardStatsData> {
    return apiClient<DashboardStatsData>('/dashboard/stats', {
      method: 'GET',
    });
  },
};
