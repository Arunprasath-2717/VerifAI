import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { SignalQualityData } from '../../types/api';

interface SignalQualityChartProps {
  data: SignalQualityData | null;
  loading: boolean;
}

const SIGNAL_COLORS: Record<string, string> = {
  entailment: '#10b981',      // Emerald 500
  contradiction: '#f43f5e',   // Rose 500
  absent: '#64748b',          // Slate 500
  refused: '#a855f7',         // Purple 500
  failed_judgment: '#ef4444'  // Red 500 (Crucial distinction!)
};

export const SignalQualityChart: React.FC<SignalQualityChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="h-72 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex items-center justify-center animate-pulse">
        <div className="text-slate-500 text-sm">Loading Consistency Signal Quality...</div>
      </div>
    );
  }

  if (!data || data.total_signals === 0) {
    return (
      <div className="h-72 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center justify-center text-center">
        <span className="text-slate-400 font-semibold text-sm">No Signal Data</span>
        <span className="text-slate-500 text-xs mt-1">No consistency signals were logged for this selection</span>
      </div>
    );
  }

  const chartData = [
    { name: 'entailment', label: 'Entailment', count: data.breakdown.entailment },
    { name: 'contradiction', label: 'Contradiction', count: data.breakdown.contradiction },
    { name: 'absent', label: 'Absent', count: data.breakdown.absent },
    { name: 'refused', label: 'Refused', count: data.breakdown.refused },
    { name: 'failed_judgment', label: 'Failed Judgment', count: data.breakdown.failed_judgment }
  ];

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-md backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100">Consistency Signal Quality</h3>
          <p className="text-xs text-slate-400">Explicit tracking of Judge Failures, Refusals, and Absent Signals</p>
        </div>
        <div className="text-right">
          <span className="text-xs font-mono text-indigo-400 font-bold">
            {(data.average_signal_quality * 100).toFixed(1)}% Avg Score
          </span>
        </div>
      </div>

      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
              formatter={(val: any) => [`${val} signals`, 'Count']}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={SIGNAL_COLORS[entry.name] || '#6366f1'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
