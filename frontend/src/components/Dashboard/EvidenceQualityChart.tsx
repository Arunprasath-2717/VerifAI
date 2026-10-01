import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { EvidenceQualityData } from '../../types/api';

interface EvidenceQualityChartProps {
  data: EvidenceQualityData | null;
  loading: boolean;
}

const EVIDENCE_COLORS = {
  SUPPORT: '#10b981',    // Emerald 500
  CONTRADICT: '#f43f5e', // Rose 500
  UNKNOWN: '#64748b'     // Slate 500 (Crucial distinction!)
};

export const EvidenceQualityChart: React.FC<EvidenceQualityChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="h-72 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex items-center justify-center animate-pulse">
        <div className="text-slate-500 text-sm">Loading Evidence Quality Distribution...</div>
      </div>
    );
  }

  if (!data || data.total_evidence === 0) {
    return (
      <div className="h-72 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center justify-center text-center">
        <span className="text-slate-400 font-semibold text-sm">No Evidence Data</span>
        <span className="text-slate-500 text-xs mt-1">No evidence items were found for current selection</span>
      </div>
    );
  }

  const chartData = [
    { name: 'SUPPORT', label: 'SUPPORT', count: data.distribution.SUPPORT },
    { name: 'CONTRADICT', label: 'CONTRADICT', count: data.distribution.CONTRADICT },
    { name: 'UNKNOWN', label: 'UNKNOWN', count: data.distribution.UNKNOWN }
  ];

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-md backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100">Evidence Quality Breakdown</h3>
          <p className="text-xs text-slate-400">SUPPORT vs CONTRADICT vs Preserved UNKNOWN</p>
        </div>
        <div className="text-right">
          <span className="text-xs font-mono text-teal-400 font-bold">
            {(data.average_strength * 100).toFixed(1)}% Strength
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
              formatter={(val: any) => [`${val} evidence items`, 'Count']}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={EVIDENCE_COLORS[entry.name as keyof typeof EVIDENCE_COLORS]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
