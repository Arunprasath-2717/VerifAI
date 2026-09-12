import React, { useState, useEffect } from 'react';
import { X, BarChart2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { ModelDetail } from '../../types/api';
import { compareModels } from '../../services/api';

interface ModelComparisonViewProps {
  modelIds: string[];
  onClose: () => void;
}

const MODEL_PALETTE = ['#6366f1', '#10b981', '#f43f5e', '#a855f7', '#38bdf8', '#f59e0b'];

export const ModelComparisonView: React.FC<ModelComparisonViewProps> = ({ modelIds, onClose }) => {
  const [data, setData] = useState<{ models: ModelDetail[]; comparison_matrix: Record<string, Record<string, any>> } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadComparison() {
      setLoading(true);
      setError(null);
      try {
        const res = await compareModels(modelIds);
        setData(res);
      } catch (err: any) {
        setError(err.message || 'Failed to compare selected models');
      } finally {
        setLoading(false);
      }
    }
    if (modelIds.length > 0) {
      loadComparison();
    }
  }, [modelIds]);

  if (!modelIds || modelIds.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-5xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-purple-950 rounded-xl border border-purple-800">
              <BarChart2 className="h-6 w-6 text-purple-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">Multi-Model Comparative Analytics</h2>
              <p className="text-xs text-slate-400">Side-by-side empirical metric comparison for selected models</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center text-slate-500 text-sm animate-pulse">
            Computing comparison matrices...
          </div>
        ) : error ? (
          <div className="p-4 bg-rose-950/40 text-rose-300 text-sm rounded-xl">
            {error}
          </div>
        ) : data ? (
          <div className="space-y-6">
            
            {/* Comparison Matrix Table */}
            <div className="overflow-x-auto bg-slate-950 rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3 font-bold text-slate-200">Metric</th>
                    {data.models.map((m, idx) => (
                      <th key={m.model_id} className="px-4 py-3 font-bold" style={{ color: MODEL_PALETTE[idx % MODEL_PALETTE.length] }}>
                        {m.model_id}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  <tr>
                    <td className="px-4 py-3 font-sans font-semibold text-slate-300">Verification Accuracy</td>
                    {data.models.map(m => (
                      <td key={m.model_id} className="px-4 py-3 text-emerald-400 font-bold">
                        {(m.accuracy * 100).toFixed(1)}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-sans font-semibold text-slate-300">Trust Score</td>
                    {data.models.map(m => (
                      <td key={m.model_id} className="px-4 py-3 text-indigo-400">
                        {(m.trust_score * 100).toFixed(1)}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-sans font-semibold text-slate-300">Hallucination Rate</td>
                    {data.models.map(m => (
                      <td key={m.model_id} className="px-4 py-3 text-rose-400 font-bold">
                        {(m.hallucination_rate * 100).toFixed(1)}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-sans font-semibold text-slate-300">Consistency Signal</td>
                    {data.models.map(m => (
                      <td key={m.model_id} className="px-4 py-3 text-violet-400">
                        {(m.consistency * 100).toFixed(1)}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-sans font-semibold text-slate-300">Evidence Support Rate</td>
                    {data.models.map(m => (
                      <td key={m.model_id} className="px-4 py-3 text-teal-400">
                        {(m.evidence_support * 100).toFixed(1)}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-sans font-semibold text-slate-300">Inconclusive Rate</td>
                    {data.models.map(m => (
                      <td key={m.model_id} className="px-4 py-3 text-amber-400">
                        {(m.inconclusive_rate * 100).toFixed(1)}%
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Side-by-Side Visual Chart */}
            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
              <h3 className="text-sm font-bold text-slate-200 mb-3">Comparative Metrics Chart</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { metric: 'Accuracy', ...Object.fromEntries(data.models.map(m => [m.model_id, Math.round(m.accuracy * 100)])) },
                      { metric: 'Trust Score', ...Object.fromEntries(data.models.map(m => [m.model_id, Math.round(m.trust_score * 100)])) },
                      { metric: 'Consistency', ...Object.fromEntries(data.models.map(m => [m.model_id, Math.round(m.consistency * 100)])) },
                      { metric: 'Evidence Support', ...Object.fromEntries(data.models.map(m => [m.model_id, Math.round(m.evidence_support * 100)])) }
                    ]}
                    margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="metric" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
                      formatter={(val: any) => [`${val}%`, 'Score']}
                    />
                    <Legend verticalAlign="top" height={36} />
                    {data.models.map((m, idx) => (
                      <Bar key={m.model_id} dataKey={m.model_id} fill={MODEL_PALETTE[idx % MODEL_PALETTE.length]} radius={[4, 4, 0, 0]} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        ) : null}

      </div>
    </div>
  );
};
