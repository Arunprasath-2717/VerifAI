import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { ConfidenceData } from '../../types/api';

interface ConfidenceChartProps {
  data: ConfidenceData | null;
  loading: boolean;
}

export const ConfidenceChart: React.FC<ConfidenceChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="h-72 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex items-center justify-center animate-pulse">
        <div className="text-slate-500 text-sm">Loading Confidence Distribution...</div>
      </div>
    );
  }

  if (!data || data.total_claims === 0) {
    return (
      <div className="h-72 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center justify-center text-center">
        <span className="text-slate-400 font-semibold text-sm">No Confidence Data</span>
        <span className="text-slate-500 text-xs mt-1">No claim confidences found for active filters</span>
      </div>
    );
  }

  const chartData = data.distribution.map((d) => ({
    range: d.range,
    count: d.count
  }));

  const avgFormatted = data.average_confidence !== null
    ? `${(data.average_confidence * 100).toFixed(1)}%`
    : 'No verification signal';

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-md backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100">Confidence Range Distribution</h3>
          <p className="text-xs text-slate-400">Histogram of numerical confidence across verified claims</p>
        </div>
        <div className="text-right">
          <span className="text-xs font-mono text-sky-400 font-bold block">
            Avg: {avgFormatted}
          </span>
          {data.no_verification_signal_count > 0 && (
            <span className="text-[10px] text-amber-400 font-medium">
              {data.no_verification_signal_count} with "No verification signal"
            </span>
          )}
        </div>
      </div>

      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="range" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
              formatter={(val: any) => [`${val} claims`, 'Count']}
            />
            <Bar dataKey="count" fill="#38bdf8" radius={[6, 6, 0, 0]}>
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={index >= 3 ? '#0ea5e9' : '#38bdf8'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {data.no_verification_signal_count > 0 && (
        <div className="mt-3 p-2 bg-amber-950/30 border border-amber-900/50 rounded-lg text-amber-300 text-[11px]">
          Note: {data.no_verification_signal_count} claim(s) had missing confidence and are explicitly tracked as "No verification signal" rather than mapped to 0.0.
        </div>
      )}
    </div>
  );
};
