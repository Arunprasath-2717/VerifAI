import React, { useState, useEffect } from 'react';
import { Trophy, ArrowUpDown, CheckSquare, Square, BarChart2, Eye, RefreshCw, Sparkles } from 'lucide-react';
import type { LeaderboardModel } from '../../types/api';
import { fetchLeaderboard } from '../../services/api';
import { ModelDetailView } from './ModelDetailView';
import { ModelComparisonView } from './ModelComparisonView';

export const LeaderboardView: React.FC = () => {
  const [models, setModels] = useState<LeaderboardModel[]>([]);
  const [sortBy, setSortBy] = useState<string>('verification_accuracy');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [comparisonModels, setComparisonModels] = useState<string[]>([]);
  const [showComparison, setShowComparison] = useState<boolean>(false);

  useEffect(() => {
    loadLeaderboardData();
  }, [sortBy, sortOrder]);

  const loadLeaderboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const lbRes = await fetchLeaderboard(sortBy, sortOrder);
      setModels(lbRes.models);
    } catch (err: any) {
      setError(err.message || 'Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (metricId: string) => {
    if (sortBy === metricId) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(metricId);
      setSortOrder('desc');
    }
  };

  const toggleSelectForComparison = (modelId: string) => {
    if (comparisonModels.includes(modelId)) {
      setComparisonModels(comparisonModels.filter(id => id !== modelId));
    } else {
      if (comparisonModels.length >= 4) {
        alert('You can compare a maximum of 4 models simultaneously.');
        return;
      }
      setComparisonModels([...comparisonModels, modelId]);
    }
  };

  return (
    <div className="space-y-8">
      
      {/* Leaderboard Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/80 border border-amber-500/30 rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-gradient-to-tr from-amber-500 to-yellow-600 rounded-2xl shadow-lg shadow-amber-500/20 text-slate-950">
            <Trophy className="h-7 w-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-2xl font-extrabold text-slate-100">Model Leaderboard</h2>
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-700">
                Empirical Evaluation
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-medium">
              Models ranked dynamically across stored verification accuracy, trust score, hallucination rate, and signal strength.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {comparisonModels.length > 0 && (
            <button
              onClick={() => setShowComparison(true)}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all duration-300 hover:scale-[1.02]"
            >
              <BarChart2 className="h-4 w-4" />
              <span>Compare Selected ({comparisonModels.length})</span>
            </button>
          )}

          <button
            onClick={loadLeaderboardData}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all duration-200"
            title="Refresh Leaderboard"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Sortable Leaderboard Table */}
      <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl shadow-2xl backdrop-blur-xl overflow-hidden">
        {loading ? (
          <div className="p-16 text-center text-slate-400 text-sm animate-pulse flex flex-col items-center justify-center space-y-3">
            <Sparkles className="h-6 w-6 text-indigo-400 animate-spin" />
            <span>Evaluating and ranking AI models across verification telemetry...</span>
          </div>
        ) : error ? (
          <div className="p-6 bg-rose-950/60 text-rose-300 text-sm">
            {error}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/90 text-slate-400 font-bold border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-4 w-12 text-center">Select</th>
                  <th className="px-5 py-4 w-20 text-center">Rank</th>
                  <th className="px-5 py-4 font-extrabold text-slate-100">Model</th>
                  
                  <th
                    onClick={() => handleSort('verification_accuracy')}
                    className="px-5 py-4 cursor-pointer hover:text-indigo-400 transition-colors"
                  >
                    <div className="flex items-center space-x-1.5">
                      <span>Accuracy</span>
                      <ArrowUpDown className="h-3.5 w-3.5 text-indigo-400" />
                    </div>
                  </th>

                  <th
                    onClick={() => handleSort('trust_score')}
                    className="px-5 py-4 cursor-pointer hover:text-emerald-400 transition-colors"
                  >
                    <div className="flex items-center space-x-1.5">
                      <span>Trust Score</span>
                      <ArrowUpDown className="h-3.5 w-3.5 text-emerald-400" />
                    </div>
                  </th>

                  <th
                    onClick={() => handleSort('hallucination_rate')}
                    className="px-5 py-4 cursor-pointer hover:text-rose-400 transition-colors"
                  >
                    <div className="flex items-center space-x-1.5">
                      <span>Hallucination</span>
                      <ArrowUpDown className="h-3.5 w-3.5 text-rose-400" />
                    </div>
                  </th>

                  <th
                    onClick={() => handleSort('consistency')}
                    className="px-5 py-4 cursor-pointer hover:text-violet-400 transition-colors"
                  >
                    <div className="flex items-center space-x-1.5">
                      <span>Consistency</span>
                      <ArrowUpDown className="h-3.5 w-3.5 text-violet-400" />
                    </div>
                  </th>

                  <th
                    onClick={() => handleSort('evidence_supported_rate')}
                    className="px-5 py-4 cursor-pointer hover:text-teal-400 transition-colors"
                  >
                    <div className="flex items-center space-x-1.5">
                      <span>Evidence Sup.</span>
                      <ArrowUpDown className="h-3.5 w-3.5 text-teal-400" />
                    </div>
                  </th>

                  <th
                    onClick={() => handleSort('inconclusive_rate')}
                    className="px-5 py-4 cursor-pointer hover:text-amber-400 transition-colors"
                  >
                    <div className="flex items-center space-x-1.5">
                      <span>Inconclusive</span>
                      <ArrowUpDown className="h-3.5 w-3.5 text-amber-400" />
                    </div>
                  </th>

                  <th className="px-5 py-4 text-right">Action</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800/60 font-mono">
                {models.map((m) => {
                  const isSelected = comparisonModels.includes(m.model_id);
                  return (
                    <tr
                      key={m.model_id}
                      className={`hover:bg-indigo-950/20 transition-colors ${
                        isSelected ? 'bg-indigo-950/40 border-l-4 border-l-indigo-500' : ''
                      }`}
                    >
                      <td className="px-5 py-4 text-center">
                        <button
                          onClick={() => toggleSelectForComparison(m.model_id)}
                          className="text-slate-400 hover:text-indigo-400 transition-colors"
                        >
                          {isSelected ? (
                            <CheckSquare className="h-5 w-5 text-indigo-400" />
                          ) : (
                            <Square className="h-5 w-5" />
                          )}
                        </button>
                      </td>

                      <td className="px-5 py-4 text-center font-sans font-extrabold">
                        {m.rank === 1 ? (
                          <span className="px-3 py-1 rounded-full bg-gradient-to-r from-amber-500 to-yellow-600 text-slate-950 font-black shadow-lg shadow-amber-500/30">
                            #1
                          </span>
                        ) : m.rank === 2 ? (
                          <span className="px-3 py-1 rounded-full bg-gradient-to-r from-slate-300 to-slate-400 text-slate-950 font-black shadow-lg shadow-slate-300/20">
                            #2
                          </span>
                        ) : m.rank === 3 ? (
                          <span className="px-3 py-1 rounded-full bg-gradient-to-r from-amber-700 to-amber-800 text-amber-100 font-black shadow-lg shadow-amber-700/20">
                            #3
                          </span>
                        ) : (
                          <span className="text-slate-400">#{m.rank}</span>
                        )}
                      </td>

                      <td className="px-5 py-4 font-sans font-bold text-slate-100">
                        <span className="text-sm">{m.model_id}</span>
                      </td>

                      <td className="px-5 py-4 font-bold text-emerald-400 text-sm">
                        {(m.verification_accuracy * 100).toFixed(1)}%
                      </td>

                      <td className="px-5 py-4 text-indigo-300">
                        {(m.trust_score * 100).toFixed(1)}%
                      </td>

                      <td className="px-5 py-4 text-rose-400 font-bold">
                        {(m.hallucination_rate * 100).toFixed(1)}%
                      </td>

                      <td className="px-5 py-4 text-violet-400">
                        {(m.consistency * 100).toFixed(1)}%
                      </td>

                      <td className="px-5 py-4 text-teal-400">
                        {(m.evidence_supported_rate * 100).toFixed(1)}%
                      </td>

                      <td className="px-5 py-4 text-amber-400">
                        {(m.inconclusive_rate * 100).toFixed(1)}%
                      </td>

                      <td className="px-5 py-4 text-right font-sans">
                        <button
                          onClick={() => setSelectedModelId(m.model_id)}
                          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 ml-auto transition-all duration-200"
                        >
                          <Eye className="h-3.5 w-3.5 text-indigo-400" />
                          <span>Detail</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Model Detail Drawer */}
      {selectedModelId && (
        <ModelDetailView
          modelId={selectedModelId}
          onClose={() => setSelectedModelId(null)}
        />
      )}

      {/* Model Comparison Modal */}
      {showComparison && (
        <ModelComparisonView
          modelIds={comparisonModels}
          onClose={() => setShowComparison(false)}
        />
      )}

    </div>
  );
};
