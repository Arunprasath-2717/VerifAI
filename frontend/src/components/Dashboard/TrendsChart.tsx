import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { TrendPoint } from '../../types/api';

interface TrendsChartProps {
  trends: TrendPoint[];
  loading: boolean;
}

export const TrendsChart: React.FC<TrendsChartProps> = ({ trends, loading }) => {
  if (loading) {
    return (
      <div className="h-80 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex items-center justify-center animate-pulse">
        <div className="text-slate-500 text-sm">Loading Historical Performance Trends...</div>
      </div>
    );
  }

  if (!trends || trends.length === 0) {
    return (
      <div className="h-80 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center justify-center text-center">
        <span className="text-slate-400 font-semibold text-sm">No Trend Data Available</span>
        <span className="text-slate-500 text-xs mt-1">No verifications matched the specified filter criteria</span>
      </div>
    );
  }

  const chartData = trends.map((t) => ({
    date: t.date,
    trustScorePct: t.trust_score !== null ? roundPct(t.trust_score) : null,
    hallucinationRatePct: roundPct(t.hallucination_rate),
    verifications: t.verifications,
    supported: t.supported,
    contradicted: t.contradicted,
    inconclusive: t.inconclusive
  }));

  function roundPct(val: number) {
    return Math.round(val * 1000) / 10;
  }

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-md backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100">Historical Trust & Hallucination Trends</h3>
          <p className="text-xs text-slate-400">Daily trust score trajectory vs hallucination rate over time</p>
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="trustGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="hallucGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
              formatter={(val: any, name: any) => [
                val !== null ? `${val}%` : 'N/A',
                name === 'trustScorePct' ? 'Overall Trust Score' : 'Hallucination Rate'
              ]}
            />
            <Legend verticalAlign="top" height={36} />
            <Area
              type="monotone"
              dataKey="trustScorePct"
              name="Overall Trust Score"
              stroke="#6366f1"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#trustGradient)"
            />
            <Area
              type="monotone"
              dataKey="hallucinationRatePct"
              name="Hallucination Rate"
              stroke="#f43f5e"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#hallucGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
