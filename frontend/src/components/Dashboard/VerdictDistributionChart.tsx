import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import type { VerificationStats } from '../../types/api';

interface VerdictDistributionChartProps {
  stats: VerificationStats | null;
  loading: boolean;
}

const COLORS = {
  SUPPORTED: '#10b981',   // Emerald 500
  CONTRADICTED: '#f43f5e', // Rose 500
  INCONCLUSIVE: '#f59e0b'  // Amber 500
};

export const VerdictDistributionChart: React.FC<VerdictDistributionChartProps> = ({ stats, loading }) => {
  if (loading) {
    return (
      <div className="h-72 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex items-center justify-center animate-pulse">
        <div className="text-slate-500 text-sm">Loading Verdict Distribution...</div>
      </div>
    );
  }

  if (!stats || stats.total_claims === 0) {
    return (
      <div className="h-72 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center justify-center text-center">
        <span className="text-slate-400 font-semibold text-sm">No Claims Available</span>
        <span className="text-slate-500 text-xs mt-1">Adjust active filters to view verdict distribution</span>
      </div>
    );
  }

  const data = [
    { name: 'SUPPORTED', value: stats.supported.count, percentage: stats.supported.percentage },
    { name: 'CONTRADICTED', value: stats.contradicted.count, percentage: stats.contradicted.percentage },
    { name: 'INCONCLUSIVE', value: stats.inconclusive.count, percentage: stats.inconclusive.percentage }
  ];

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-md backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100">Verification Verdict Distribution</h3>
          <p className="text-xs text-slate-400">Strict separation of Supported, Contradicted, and Inconclusive</p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
          {stats.total_claims.toLocaleString()} Total
        </span>
      </div>

      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
              formatter={(val: any, name: any, item: any) => [
                `${val} claims (${item.payload.percentage}%)`,
                name
              ]}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              formatter={(value: string) => (
                <span className="text-xs font-semibold text-slate-300 ml-1">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
