import React, { useState, useEffect } from 'react';
import { X, Cpu } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ModelDetail } from '../../types/api';
import { fetchModelDetail } from '../../services/api';

interface ModelDetailViewProps {
  modelId: string;
  onClose: () => void;
}

export const ModelDetailView: React.FC<ModelDetailViewProps> = ({ modelId, onClose }) => {
  const [detail, setDetail] = useState<ModelDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDetail() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchModelDetail(modelId);
        setDetail(data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch model details');
      } finally {
        setLoading(false);
      }
    }
    loadDetail();
  }, [modelId]);

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-950 rounded-xl border border-indigo-800">
              <Cpu className="h-6 w-6 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">{modelId} Analytics Deep Dive</h2>
              <p className="text-xs text-slate-400">Detailed metric breakdown derived from stored verification logs</p>
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
            Loading model telemetry metrics...
          </div>
        ) : error ? (
          <div className="p-4 bg-rose-950/40 text-rose-300 text-sm rounded-xl">
            {error}
          </div>
        ) : detail ? (
          <div className="space-y-6">
            
            {/* KPI Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 font-semibold block mb-1">Verification Accuracy</span>
                <span className="text-2xl font-bold text-emerald-400">{(detail.accuracy * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 font-semibold block mb-1">Trust Score</span>
                <span className="text-2xl font-bold text-indigo-400">{(detail.trust_score * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 font-semibold block mb-1">Hallucination Rate</span>
                <span className="text-2xl font-bold text-rose-400">{(detail.hallucination_rate * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 font-semibold block mb-1">Consistency Signal</span>
                <span className="text-2xl font-bold text-violet-400">{(detail.consistency * 100).toFixed(1)}%</span>
              </div>
            </div>

            {/* Additional Telemetry */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400 block mb-1">Average Confidence</span>
                <span className="text-lg font-bold text-sky-400">
                  {detail.confidence !== null ? `${(detail.confidence * 100).toFixed(1)}%` : 'No signal'}
                </span>
              </div>
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400 block mb-1">Evidence Support</span>
                <span className="text-lg font-bold text-teal-400">{(detail.evidence_support * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400 block mb-1">Inconclusive Rate</span>
                <span className="text-lg font-bold text-amber-400">{(detail.inconclusive_rate * 100).toFixed(1)}%</span>
              </div>
            </div>

            {/* Historical Trend Chart */}
            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
              <h3 className="text-sm font-bold text-slate-200 mb-3">Model Historical Trajectory</h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={detail.historical_performance} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" domain={[0, 1]} tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
                      formatter={(val: any) => [`${(val * 100).toFixed(1)}%`, 'Score']}
                    />
                    <Area type="monotone" dataKey="trust_score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} name="Trust Score" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        ) : null}

      </div>
    </div>
  );
};
