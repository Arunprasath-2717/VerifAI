import React, { useState, useEffect } from 'react';
import { LineChart, CheckCircle2, AlertTriangle, Cpu, Database, Activity, Gauge, Clock } from 'lucide-react';
import type { BenchmarkMetrics, BenchmarkModelResult, BenchmarkClaimResult } from '../../types/api';
import { fetchBenchmarks, fetchBenchmarkMetrics, fetchBenchmarkModels, fetchBenchmarkClaims } from '../../services/api';

export const BenchmarkAnalyticsView: React.FC = () => {
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [selectedBenchmarkId, setSelectedBenchmarkId] = useState<string>('bm-factuality-v1');
  const [metrics, setMetrics] = useState<BenchmarkMetrics | null>(null);
  const [models, setModels] = useState<BenchmarkModelResult[]>([]);
  const [claims, setClaims] = useState<BenchmarkClaimResult[]>([]);
  const [selectedModelFilter, setSelectedModelFilter] = useState<string>('');
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBenchmarkList();
  }, []);

  useEffect(() => {
    if (selectedBenchmarkId) {
      loadBenchmarkData(selectedBenchmarkId);
    }
  }, [selectedBenchmarkId, selectedModelFilter]);

  const loadBenchmarkList = async () => {
    try {
      const res = await fetchBenchmarks();
      setBenchmarks(res.benchmarks);
      if (res.benchmarks.length > 0 && !selectedBenchmarkId) {
        setSelectedBenchmarkId(res.benchmarks[0].benchmark_id);
      }
    } catch (err: any) {
      console.error('Failed to load benchmark list:', err);
    }
  };

  const loadBenchmarkData = async (bmId: string) => {
    setLoading(true);
    setError(null);
    try {
      const [mRes, modRes, cRes] = await Promise.all([
        fetchBenchmarkMetrics(bmId),
        fetchBenchmarkModels(bmId),
        fetchBenchmarkClaims(bmId, selectedModelFilter || undefined)
      ]);
      setMetrics(mRes);
      setModels(modRes.models);
      setClaims(cRes.claims);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch benchmark analytics');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Selector & Sampling Basis Header */}
      <div className="bg-white/30 backdrop-blur-md border border-white/50 rounded-xl p-5 shadow-lg backdrop-blur-md flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <LineChart className="h-6 w-6 text-sky-400" />
            <h2 className="text-xl font-bold text-slate-900">Benchmark Analytics Engine</h2>
          </div>
          <p className="text-xs text-slate-600 mt-1">
            Empirical evaluation layer built over raw benchmark results (Arun's runner integration)
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Benchmark Selection */}
          <div className="flex items-center space-x-2 bg-white/60 px-3.5 py-2 rounded-lg border border-white/50 text-xs">
            <Database className="h-4 w-4 text-sky-400" />
            <select
              value={selectedBenchmarkId}
              onChange={(e) => setSelectedBenchmarkId(e.target.value)}
              className="bg-transparent text-slate-800 font-bold focus:outline-none cursor-pointer"
            >
              {benchmarks.map((b) => (
                <option key={b.benchmark_id} value={b.benchmark_id} className="bg-white/50 text-slate-800">
                  {b.benchmark_id} ({b.total_items} items)
                </option>
              ))}
            </select>
          </div>

          {/* Sampling Basis Metadata Badge */}
          {metrics && (
            <div className={`px-3 py-1.5 rounded-lg border text-xs font-mono font-bold flex items-center space-x-1.5 ${
              metrics.sampling_basis === 'prompt_generation'
                ? 'bg-emerald-100 text-emerald-700 border-emerald-300'
                : 'bg-amber-100 text-amber-700 border-amber-300'
            }`}>
              <span>Sampling Basis:</span>
              <span className="underline decoration-indigo-400">{metrics.sampling_basis}</span>
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <div className="h-64 bg-white/30 rounded-xl border border-white/50 flex items-center justify-center text-slate-500 text-sm animate-pulse">
          Computing claim-level, system-level, calibration & operational benchmark metrics...
        </div>
      ) : error ? (
        <div className="p-4 bg-rose-100 text-rose-700 text-sm rounded-xl">
          {error}
        </div>
      ) : metrics ? (
        <div className="space-y-6">
          
          {/* Metrics Categorized Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            
            {/* Claim-Level Metrics */}
            <div className="bg-white/30 border border-white/50 rounded-xl p-4 shadow-md backdrop-blur-sm">
              <div className="flex items-center space-x-2 text-xs font-bold text-sky-700 mb-3 uppercase tracking-wider">
                <CheckCircle2 className="h-4 w-4" />
                <span>Claim-Level Evaluation</span>
              </div>
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-600">Precision:</span>
                  <span className="text-emerald-700 font-bold">{(metrics.claim_level.precision * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Recall:</span>
                  <span className="text-sky-700 font-bold">{(metrics.claim_level.recall * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">F1 Score:</span>
                  <span className="text-purple-400 font-bold">{(metrics.claim_level.f1 * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between border-t border-white/50 pt-1.5">
                  <span className="text-slate-600">Accuracy:</span>
                  <span className="text-slate-900 font-bold">{(metrics.claim_level.accuracy * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* System-Level Metrics */}
            <div className="bg-white/30 border border-white/50 rounded-xl p-4 shadow-md backdrop-blur-sm">
              <div className="flex items-center space-x-2 text-xs font-bold text-rose-700 mb-3 uppercase tracking-wider">
                <Activity className="h-4 w-4" />
                <span>System-Level Metrics</span>
              </div>
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-600">Hallucination Rate:</span>
                  <span className="text-rose-700 font-bold">{(metrics.system_level.hallucination_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">False Positive (FPR):</span>
                  <span className="text-amber-700 font-bold">{(metrics.system_level.false_positive_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">False Negative (FNR):</span>
                  <span className="text-sky-400 font-bold">{(metrics.system_level.false_negative_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between border-t border-white/50 pt-1.5">
                  <span className="text-slate-600">Verification Acc:</span>
                  <span className="text-emerald-700 font-bold">{(metrics.system_level.verification_accuracy * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* Calibration Metrics */}
            <div className="bg-white/30 border border-white/50 rounded-xl p-4 shadow-md backdrop-blur-sm">
              <div className="flex items-center space-x-2 text-xs font-bold text-blue-700 mb-3 uppercase tracking-wider">
                <Gauge className="h-4 w-4" />
                <span>Calibration Metric</span>
              </div>
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between items-center py-2">
                  <span className="text-slate-600">ECE Error:</span>
                  <span className="text-2xl font-bold text-violet-700">{(metrics.calibration.ece * 100).toFixed(2)}%</span>
                </div>
                <p className="text-[10px] text-slate-500 font-sans leading-tight">
                  Expected Calibration Error (ECE) measures confidence alignment with true verdict accuracy.
                </p>
              </div>
            </div>

            {/* Operational Metrics */}
            <div className="bg-white/30 border border-white/50 rounded-xl p-4 shadow-md backdrop-blur-sm">
              <div className="flex items-center space-x-2 text-xs font-bold text-teal-700 mb-3 uppercase tracking-wider">
                <Clock className="h-4 w-4" />
                <span>Operational Telemetry</span>
              </div>
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-600">Avg Latency:</span>
                  <span className="text-slate-800 font-bold">{metrics.operational.avg_latency_ms} ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">LLM / Search Calls:</span>
                  <span className="text-teal-700 font-bold">{metrics.operational.avg_llm_calls} / {metrics.operational.avg_search_calls}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Token Usage:</span>
                  <span className="text-slate-700">{metrics.operational.total_token_usage.toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-t border-white/50 pt-1.5">
                  <span className="text-slate-600">Failure Rate:</span>
                  <span className="text-rose-700 font-bold">{(metrics.operational.failure_rate * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>

          </div>

          {/* Model-Wise Benchmark Table */}
          <div className="bg-white/30 border border-white/50 rounded-xl p-5 shadow-md backdrop-blur-sm">
            <h3 className="text-base font-semibold text-slate-900 mb-3">Model Benchmark Breakdown</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-white/40 text-slate-600 font-semibold border-b border-white/50">
                  <tr>
                    <th className="px-4 py-3">Model</th>
                    <th className="px-4 py-3">Sampling Basis</th>
                    <th className="px-4 py-3">Items</th>
                    <th className="px-4 py-3">Precision</th>
                    <th className="px-4 py-3">Recall</th>
                    <th className="px-4 py-3">F1</th>
                    <th className="px-4 py-3">Accuracy</th>
                    <th className="px-4 py-3">ECE</th>
                    <th className="px-4 py-3">Avg Latency</th>
                    <th className="px-4 py-3">Tokens</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/50 font-mono">
                  {models.map((m) => (
                    <tr key={m.model_id} className="hover:bg-white/60 transition-colors">
                      <td className="px-4 py-3 font-sans font-bold text-slate-900">{m.model_id}</td>
                      <td className="px-4 py-3 text-slate-600">{m.sampling_basis}</td>
                      <td className="px-4 py-3 text-slate-700">{m.item_count}</td>
                      <td className="px-4 py-3 text-emerald-700 font-bold">{(m.precision * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-sky-700 font-bold">{(m.recall * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-purple-400 font-bold">{(m.f1 * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-slate-900 font-bold">{(m.accuracy * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-blue-700">{(m.ece * 100).toFixed(2)}%</td>
                      <td className="px-4 py-3 text-slate-700">{m.latency_ms} ms</td>
                      <td className="px-4 py-3 text-slate-600">{m.token_usage.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Claim-Level Traceability Table */}
          <div className="bg-white/30 border border-white/50 rounded-xl p-5 shadow-md backdrop-blur-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
              <div>
                <h3 className="text-base font-semibold text-slate-900">Claim-Level Traceability Log</h3>
                <p className="text-xs text-slate-600">Individual evaluated claims, ground-truth labels vs predictions</p>
              </div>

              {/* Model Filter for Claims */}
              <div className="flex items-center space-x-2 bg-white/60 px-3 py-1.5 rounded-lg border border-white/50 text-xs">
                <Cpu className="h-3.5 w-3.5 text-sky-700" />
                <select
                  value={selectedModelFilter}
                  onChange={(e) => setSelectedModelFilter(e.target.value)}
                  className="bg-transparent text-slate-800 focus:outline-none cursor-pointer"
                >
                  <option value="" className="bg-white/50">Filter by Model (All)</option>
                  {models.map(m => (
                    <option key={m.model_id} value={m.model_id} className="bg-white/50">
                      {m.model_id}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-white/40 text-slate-600 font-semibold border-b border-white/50">
                  <tr>
                    <th className="px-4 py-3">Claim ID</th>
                    <th className="px-4 py-3">Claim Text</th>
                    <th className="px-4 py-3">Model</th>
                    <th className="px-4 py-3">Ground Truth</th>
                    <th className="px-4 py-3">Predicted Verdict</th>
                    <th className="px-4 py-3">Correctness</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/50 font-mono">
                  {claims.slice(0, 15).map((c) => (
                    <tr key={c.claim_id} className="hover:bg-white/60 transition-colors">
                      <td className="px-4 py-3 text-slate-600">{c.item_id}</td>
                      <td className="px-4 py-3 font-sans text-slate-800">{c.claim_text}</td>
                      <td className="px-4 py-3 text-sky-700">{c.model_id}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          c.ground_truth === 'SUPPORTED' ? 'bg-emerald-100 text-emerald-700 border border-emerald-300' :
                          c.ground_truth === 'CONTRADICTED' ? 'bg-rose-100 text-rose-700 border border-rose-300' :
                          'bg-amber-100 text-amber-700 border border-amber-300'
                        }`}>
                          {c.ground_truth}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          c.predicted_verdict === 'SUPPORTED' ? 'bg-emerald-100 text-emerald-700 border border-emerald-300' :
                          c.predicted_verdict === 'CONTRADICTED' ? 'bg-rose-100 text-rose-700 border border-rose-300' :
                          'bg-amber-100 text-amber-700 border border-amber-300'
                        }`}>
                          {c.predicted_verdict}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {c.is_correct ? (
                          <span className="text-emerald-700 font-bold font-sans flex items-center space-x-1">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            <span>Correct</span>
                          </span>
                        ) : (
                          <span className="text-rose-700 font-bold font-sans flex items-center space-x-1">
                            <AlertTriangle className="h-3.5 w-3.5" />
                            <span>Mismatch</span>
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{c.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {claims.length > 15 && (
                <div className="p-3 text-center text-slate-500 text-xs border-t border-white/50 font-sans">
                  Showing first 15 of {claims.length} claim logs.
                </div>
              )}
            </div>
          </div>

        </div>
      ) : null}

    </div>
  );
};
