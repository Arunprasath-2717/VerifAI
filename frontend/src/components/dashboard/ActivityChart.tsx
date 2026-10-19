import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { ChartPoint } from '../../types';

interface ActivityChartProps {
  weeklyData: ChartPoint[];
  monthlyData: ChartPoint[];
}

export const ActivityChart: React.FC<ActivityChartProps> = ({
  weeklyData,
  monthlyData,
}) => {
  const [timeframe, setTimeframe] = useState<'weekly' | 'monthly'>('weekly');
  const [metric, setMetric] = useState<'evidence' | 'claims' | 'verifications'>('evidence');

  const currentData = timeframe === 'weekly' ? weeklyData : monthlyData;

  const metricConfig = {
    evidence: {
      label: 'Evidence Retrieved',
      color: '#2563EB',
      gradientStart: '#3B82F6',
      unit: 'citations',
    },
    claims: {
      label: 'Claims Analyzed',
      color: '#0F172A',
      gradientStart: '#334155',
      unit: 'claims',
    },
    verifications: {
      label: 'Verifications Completed',
      color: '#059669',
      gradientStart: '#10B981',
      unit: 'runs',
    },
  };

  const activeMetric = metricConfig[metric];

  // Custom Tooltip component
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900 text-white px-4 py-3 rounded-2xl shadow-xl border border-slate-800 text-xs space-y-1.5 min-w-[140px]">
          <p className="font-bold text-slate-300 border-b border-slate-800 pb-1">{label}</p>
          <div className="flex justify-between items-center text-blue-400">
            <span>Evidence:</span>
            <span className="font-mono font-bold">{data.evidence}</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span>Claims:</span>
            <span className="font-mono font-bold">{data.claims}</span>
          </div>
          <div className="flex justify-between items-center text-emerald-400">
            <span>Verifications:</span>
            <span className="font-mono font-bold">{data.verifications}</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <section className="bg-white rounded-[2.8rem] p-8 border border-slate-200/70 shadow-sm relative overflow-hidden">
      {/* Chart Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h3 className="font-extrabold text-base md:text-lg text-slate-900 tracking-tight">
              Verification Activity
            </h3>
            {/* Metric Selector Tabs */}
            <div className="hidden sm:flex items-center bg-slate-100 p-0.5 rounded-xl text-[11px] font-semibold">
              {(['evidence', 'claims', 'verifications'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMetric(m)}
                  className={`px-2.5 py-1 rounded-lg transition-all capitalize cursor-pointer ${
                    metric === m 
                      ? 'bg-white text-slate-900 shadow-xs' 
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>
          <p className="text-xs text-slate-400 font-medium mt-0.5">
            {timeframe === 'weekly' ? 'Weekly' : 'Monthly'} throughput of claims analyzed vs corroborating evidence
          </p>
        </div>

        {/* Timeframe Toggle Switch - Reference Replica */}
        <div className="flex bg-slate-100/90 p-1 rounded-2xl self-start sm:self-auto border border-slate-200/60">
          <button
            onClick={() => setTimeframe('weekly')}
            className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              timeframe === 'weekly'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-400 hover:text-slate-700'
            }`}
          >
            Weekly
          </button>
          <button
            onClick={() => setTimeframe('monthly')}
            className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              timeframe === 'monthly'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-400 hover:text-slate-700'
            }`}
          >
            Monthly
          </button>
        </div>
      </div>

      {/* Metric Callout Badge (Floating badge like the "1.2k" in the reference) */}
      <div className="relative mb-2">
        <div className="flex items-center gap-4 text-xs font-medium text-slate-500 mb-2">
          <span className="flex items-center gap-1.5">
            <span 
              className="w-2.5 h-2.5 rounded-full" 
              style={{ backgroundColor: activeMetric.color }}
            />
            <span className="font-semibold text-slate-800">{activeMetric.label}</span>
          </span>
          <span className="text-slate-300">|</span>
          <span className="tabular-nums">
            Total {timeframe === 'weekly' ? '7-Day' : '30-Day'}:{' '}
            <strong className="text-slate-900 font-mono">
              {currentData.reduce((acc, curr) => acc + curr[metric], 0).toLocaleString()}
            </strong>
          </span>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-[260px] w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={currentData} margin={{ top: 15, right: 10, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="activityColor" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={activeMetric.gradientStart} stopOpacity={0.16} />
                <stop offset="95%" stopColor={activeMetric.gradientStart} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
            <XAxis 
              dataKey="name" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#94A3B8', fontSize: 12, fontWeight: 600 }}
              dy={10}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#94A3B8', fontSize: 11 }}
            />
            <Tooltip 
              cursor={{ 
                stroke: activeMetric.color, 
                strokeWidth: 1.5, 
                strokeDasharray: '4 4', 
                strokeOpacity: 0.6 
              }}
              content={<CustomTooltip />} 
            />
            <Area 
              type="natural" 
              dataKey={metric} 
              stroke={activeMetric.color} 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#activityColor)" 
              dot={{ r: 4, fill: '#FFFFFF', stroke: activeMetric.color, strokeWidth: 2.5 }}
              activeDot={{ r: 6, fill: activeMetric.color, stroke: '#FFFFFF', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};
