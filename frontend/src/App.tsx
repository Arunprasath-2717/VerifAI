import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { FilterBar } from './components/FilterBar';
import { OverviewCards } from './components/Dashboard/OverviewCards';
import { VerdictDistributionChart } from './components/Dashboard/VerdictDistributionChart';
import { TrendsChart } from './components/Dashboard/TrendsChart';
import { SignalQualityChart } from './components/Dashboard/SignalQualityChart';
import { EvidenceQualityChart } from './components/Dashboard/EvidenceQualityChart';
import { ConfidenceChart } from './components/Dashboard/ConfidenceChart';
import { DomainAnalyticsTable } from './components/Dashboard/DomainAnalyticsTable';
import { LeaderboardView } from './components/Leaderboard/LeaderboardView';
import { BenchmarkAnalyticsView } from './components/Benchmark/BenchmarkAnalyticsView';

import type {
  ActiveFilters,
  FilterOptions,
  DashboardOverview,
  VerificationStats,
  ConfidenceData,
  SignalQualityData,
  EvidenceQualityData,
  TrendPoint,
  DomainStat
} from './types/api';

import {
  fetchOverview,
  fetchVerificationStats,
  fetchConfidence,
  fetchSignalQuality,
  fetchEvidenceQuality,
  fetchTrends,
  fetchDomains,
  fetchFilters
} from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'leaderboard' | 'benchmark'>('dashboard');

  // Compositing filter state
  const [filters, setFilters] = useState<ActiveFilters>({
    dateFrom: '',
    dateTo: '',
    modelId: '',
    verdict: '',
    domain: ''
  });

  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);

  // Dashboard Data State
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [stats, setStats] = useState<VerificationStats | null>(null);
  const [confidence, setConfidence] = useState<ConfidenceData | null>(null);
  const [signalQuality, setSignalQuality] = useState<SignalQualityData | null>(null);
  const [evidenceQuality, setEvidenceQuality] = useState<EvidenceQualityData | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [domains, setDomains] = useState<DomainStat[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFilterOptions();
  }, []);

  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboardData();
    }
  }, [activeTab, filters]);

  const loadFilterOptions = async () => {
    try {
      const opts = await fetchFilters();
      setFilterOptions(opts);
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  };

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        ovRes,
        stRes,
        confRes,
        sigRes,
        evRes,
        trRes,
        domRes
      ] = await Promise.all([
        fetchOverview(filters),
        fetchVerificationStats(filters),
        fetchConfidence(filters),
        fetchSignalQuality(filters),
        fetchEvidenceQuality(filters),
        fetchTrends(filters),
        fetchDomains(filters)
      ]);

      setOverview(ovRes);
      setStats(stRes);
      setConfidence(confRes);
      setSignalQuality(sigRes);
      setEvidenceQuality(evRes);
      setTrends(trRes.trends);
      setDomains(domRes.domains);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to VerifAI Analytics Backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetFilters = () => {
    setFilters({
      dateFrom: '',
      dateTo: '',
      modelId: '',
      verdict: '',
      domain: ''
    });
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      
      {/* Top Navbar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Render Trust Dashboard */}
        {activeTab === 'dashboard' && (
          <div>
            {/* Filter Bar */}
            <FilterBar
              options={filterOptions}
              filters={filters}
              onFilterChange={setFilters}
              onReset={handleResetFilters}
            />

            {/* Error Notification */}
            {error && (
              <div className="p-4 bg-rose-950/80 border border-rose-800 rounded-xl text-rose-200 text-sm mb-6 flex items-center justify-between">
                <span>{error} (Ensure backend server is running on http://localhost:8000)</span>
                <button
                  onClick={loadDashboardData}
                  className="px-3 py-1 rounded bg-rose-900 hover:bg-rose-800 text-white font-semibold text-xs"
                >
                  Retry
                </button>
              </div>
            )}

            {/* KPI Cards */}
            <OverviewCards overview={overview} loading={loading} error={error} />

            {/* Visual Charts Grid 1: Verdict Distribution & Trends */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <VerdictDistributionChart stats={stats} loading={loading} />
              <TrendsChart trends={trends} loading={loading} />
            </div>

            {/* Visual Charts Grid 2: Signal Quality & Evidence Quality */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <SignalQualityChart data={signalQuality} loading={loading} />
              <EvidenceQualityChart data={evidenceQuality} loading={loading} />
            </div>

            {/* Visual Charts Grid 3: Confidence Distribution */}
            <div className="mb-6">
              <ConfidenceChart data={confidence} loading={loading} />
            </div>

            {/* Domain Analytics Matrix Table */}
            <DomainAnalyticsTable domains={domains} loading={loading} />
          </div>
        )}

        {/* Render Model Leaderboard */}
        {activeTab === 'leaderboard' && (
          <LeaderboardView />
        )}

        {/* Render Benchmark Analytics */}
        {activeTab === 'benchmark' && (
          <BenchmarkAnalyticsView />
        )}

      </main>

      {/* Footer */}
      <footer className="bg-slate-900/60 border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        VerifAI Read-Only Analytics Layer • Powered by FastAPI & React TypeScript Recharts • All metrics traceable to core verification tables
      </footer>

    </div>
  );
}
