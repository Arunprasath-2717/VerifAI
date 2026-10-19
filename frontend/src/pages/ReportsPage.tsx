import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart3, 
  Sparkles
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid
} from 'recharts';
import { motion } from 'motion/react';
import { ChartPoint } from '../types';
import { reportsApi, AnalyticsReportResponse } from '../api';
import { useTheme } from '../context/ThemeContext';

interface ReportsPageProps {
  weeklyChartData: ChartPoint[];
  monthlyChartData: ChartPoint[];
  theme?: 'light' | 'dark';
}

export const ReportsPage: React.FC<ReportsPageProps> = ({
  weeklyChartData,
  monthlyChartData,
  theme: propTheme,
}) => {
  const navigate = useNavigate();
  const context = useTheme();
  const isDark = (propTheme || context.theme) === 'dark';
  const [timeframe, setTimeframe] = useState<'7D' | '30D' | '90D' | '1Y'>('30D');
  const [analytics, setAnalytics] = useState<AnalyticsReportResponse | null>(null);

  React.useEffect(() => {
    const period = timeframe === '7D' ? '7d' : timeframe === '90D' ? '90d' : '30d';
    reportsApi.getAnalytics(period)
      .then(res => setAnalytics(res))
      .catch(() => {});
  }, [timeframe]);

  const rawModelUsage = (analytics as any)?.model_usage || (analytics as any)?.model_breakdown;
  const modelUsageData = Array.isArray(rawModelUsage) && rawModelUsage.length > 0
    ? rawModelUsage.map((m: any) => ({ model: m.model || m.model_name, usage: m.usage || m.total_runs || 0 }))
    : [
        { model: 'GPT-4o', usage: 48 },
        { model: 'Claude 3.5', usage: 36 },
        { model: 'Gemini 1.5', usage: 28 },
        { model: 'Ollama', usage: 14 },
      ];

  const rawEvidence = analytics?.evidence_sources;
  const evidenceSourceData = Array.isArray(rawEvidence) && rawEvidence.length > 0
    ? rawEvidence.map((e: any) => ({ domain: e.domain || e.source || 'Verified Source', count: e.count || 0 }))
    : [
        { domain: 'Academic', count: 184 },
        { domain: 'EPA / Reg', count: 142 },
        { domain: 'arXiv', count: 98 },
        { domain: 'Corp Docs', count: 64 },
      ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-8 pb-16"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4] dark:bg-[#181A20] dark:text-[#B6FF2E] dark:border-[#333742] dark:shadow-[0_0_15px_rgba(182,255,46,0.15)] shadow-xs transition-colors">
            <BarChart3 size={24} />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#2E0A12] dark:text-white transition-colors">
              Reports & Benchmarks
            </h1>
            <p className="text-xs md:text-sm font-medium text-[#6C3B45] dark:text-slate-300 transition-colors">
              Analytics and insights from your verification activity.
            </p>
          </div>
        </div>

        {/* Actions & Time Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => navigate('/leaderboard')}
            className="px-4 py-2 rounded-2xl border text-xs font-bold shadow-2xs flex items-center gap-1.5 transition-colors cursor-pointer bg-[#FFFDFA] border-[#E9D6C4] text-[#800020] hover:bg-[#FBF1E3] dark:bg-[#23262F] dark:border-[#333742] dark:text-white dark:hover:border-[#B6FF2E]/40"
          >
            <Sparkles size={14} className="text-[#800020] dark:text-[#B6FF2E]" />
            <span>Model Performance Leaderboard</span>
          </button>

          {/* Time Filters */}
          <div className="flex p-1 rounded-2xl border shadow-2xs self-start sm:self-auto bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
            {(['7D', '30D', '90D', '1Y'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTimeframe(t)}
                className={`px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  timeframe === t 
                    ? 'bg-[#800020] text-[#FBF1E3] dark:bg-[#B6FF2E] dark:text-[#181A20] shadow-xs' 
                    : 'text-[#8A6A72] dark:text-slate-400 hover:text-[#2E0A12] dark:hover:text-white'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Top Grid: Verification Activity + Claim Outcomes */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Verification Activity Curve */}
        <section className="lg:col-span-8 rounded-[2.8rem] p-7 border shadow-xs space-y-4 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-extrabold text-base tracking-tight text-[#2E0A12] dark:text-white">
                Verification Activity
              </h3>
              <p className="text-xs font-medium text-[#8A6A72] dark:text-slate-400">Daily verified proposition volume</p>
            </div>
            <span className="text-xs font-bold font-mono px-3 py-1 rounded-full bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4] dark:bg-[#B6FF2E]/15 dark:text-[#B6FF2E] dark:border dark:border-[#B6FF2E]/30">
              +28% throughput
            </span>
          </div>

          <div className="h-[240px] w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={weeklyChartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="repCurveColor" x1="0" y1="0" x2="0" y2="1">
                    <stop 
                      offset="5%" 
                      stopColor={isDark ? '#B6FF2E' : '#800020'} 
                      stopOpacity={isDark ? 0.35 : 0.25} 
                    />
                    <stop 
                      offset="95%" 
                      stopColor={isDark ? '#B6FF2E' : '#D8AE9B'} 
                      stopOpacity={0.0} 
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  vertical={false} 
                  stroke={isDark ? '#333742' : '#E9D6C4'} 
                />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: isDark ? '#94A3B8' : '#8A6A72', fontSize: 11 }} 
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: isDark ? '#94A3B8' : '#8A6A72', fontSize: 11 }} 
                />
                <Tooltip 
                  cursor={{ 
                    stroke: isDark ? '#B6FF2E' : '#800020', 
                    strokeWidth: 1.5, 
                    strokeDasharray: '4 4', 
                    strokeOpacity: 0.6 
                  }}
                  contentStyle={{ 
                    borderRadius: '16px', 
                    background: isDark ? '#14161C' : '#FFFDFA', 
                    color: isDark ? '#FFFFFF' : '#2E0A12', 
                    border: isDark ? '1px solid #333742' : '1px solid #E9D6C4', 
                    boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
                    fontSize: '12px' 
                  }} 
                />
                <Area 
                  type="natural" 
                  dataKey="claims" 
                  stroke={isDark ? '#B6FF2E' : '#800020'} 
                  strokeWidth={3} 
                  fill="url(#repCurveColor)" 
                  dot={{ 
                    r: 4, 
                    fill: isDark ? '#14161C' : '#FFFDFA', 
                    stroke: isDark ? '#B6FF2E' : '#800020', 
                    strokeWidth: 2 
                  }}
                  activeDot={{ 
                    r: 6, 
                    fill: isDark ? '#B6FF2E' : '#800020', 
                    stroke: isDark ? '#14161C' : '#FFFDFA', 
                    strokeWidth: 2.5 
                  }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Claim Outcomes Ring Breakdown */}
        <section className="lg:col-span-4 rounded-[2.8rem] p-7 border shadow-xs space-y-6 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <div>
            <h3 className="font-extrabold text-base tracking-tight text-[#2E0A12] dark:text-white">
              Claim Outcomes
            </h3>
            <p className="text-xs font-medium text-[#8A6A72] dark:text-slate-400">Calibrated accuracy distribution</p>
          </div>

          {/* Donut representation */}
          <div className="relative flex items-center justify-center py-2">
            <div className="w-32 h-32 rounded-full border-8 border-[#800020] dark:border-[#B6FF2E] border-t-rose-500 border-r-amber-400 flex flex-col items-center justify-center shadow-inner">
              <span className="text-2xl font-black font-mono text-[#2E0A12] dark:text-white">42</span>
              <span className="text-[10px] font-bold uppercase text-[#8A6A72] dark:text-slate-400">Total</span>
            </div>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 font-bold text-slate-700 dark:text-slate-200">
                <span className="w-2.5 h-2.5 rounded-full bg-[#800020] dark:bg-[#B6FF2E]" />
                <span>Supported</span>
              </span>
              <span className="font-mono font-bold text-slate-900 dark:text-white">65%</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 font-bold text-slate-700 dark:text-slate-200">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span>Contradicted</span>
              </span>
              <span className="font-mono font-bold text-slate-900 dark:text-white">20%</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 font-bold text-slate-700 dark:text-slate-200">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                <span>Unknown</span>
              </span>
              <span className="font-mono font-bold text-slate-900 dark:text-white">15%</span>
            </div>
          </div>
        </section>

      </div>

      {/* Bottom Grid: Model Usage + Evidence Sources + Domain Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Model Usage Bar Chart */}
        <section className="rounded-[2.5rem] p-6 border shadow-xs space-y-4 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <h4 className="font-extrabold text-sm text-[#2E0A12] dark:text-white">Model Usage</h4>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelUsageData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={isDark ? '#333742' : '#E9D6C4'} />
                <XAxis dataKey="model" axisLine={false} tickLine={false} tick={{ fill: isDark ? '#94A3B8' : '#8A6A72', fontSize: 10 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: isDark ? '#94A3B8' : '#8A6A72', fontSize: 10 }} />
                <Tooltip 
                  cursor={{ 
                    fill: isDark ? 'rgba(182, 255, 46, 0.08)' : 'rgba(128, 0, 32, 0.06)', 
                    radius: 8 
                  }}
                  contentStyle={{ 
                    borderRadius: '12px', 
                    background: isDark ? '#14161C' : '#FFFDFA', 
                    color: isDark ? '#FFFFFF' : '#2E0A12', 
                    border: isDark ? '1px solid #333742' : '1px solid #E9D6C4',
                    fontSize: '11px' 
                  }} 
                />
                <Bar 
                  dataKey="usage" 
                  fill={isDark ? '#B6FF2E' : '#800020'} 
                  radius={[6, 6, 0, 0]}
                  activeBar={{ fill: isDark ? '#CEFF6B' : '#9E0028' }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Evidence Sources */}
        <section className="rounded-[2.5rem] p-6 border shadow-xs space-y-4 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <h4 className="font-extrabold text-sm text-[#2E0A12] dark:text-white">Evidence Sources</h4>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={evidenceSourceData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={isDark ? '#333742' : '#E9D6C4'} />
                <XAxis dataKey="domain" axisLine={false} tickLine={false} tick={{ fill: isDark ? '#94A3B8' : '#8A6A72', fontSize: 9 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: isDark ? '#94A3B8' : '#8A6A72', fontSize: 10 }} />
                <Tooltip 
                  cursor={{ 
                    fill: isDark ? 'rgba(182, 255, 46, 0.08)' : 'rgba(128, 0, 32, 0.06)', 
                    radius: 8 
                  }}
                  contentStyle={{ 
                    borderRadius: '12px', 
                    background: isDark ? '#14161C' : '#FFFDFA', 
                    color: isDark ? '#FFFFFF' : '#2E0A12', 
                    border: isDark ? '1px solid #333742' : '1px solid #E9D6C4',
                    fontSize: '11px' 
                  }} 
                />
                <Bar 
                  dataKey="count" 
                  fill={isDark ? '#B6FF2E' : '#800020'} 
                  radius={[6, 6, 0, 0]}
                  activeBar={{ fill: isDark ? '#CEFF6B' : '#9E0028' }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Domain Distribution */}
        <section className="rounded-[2.5rem] p-6 border shadow-xs space-y-4 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <h4 className="font-extrabold text-sm text-[#2E0A12] dark:text-white">Domain Distribution</h4>
          <div className="space-y-3 pt-2 text-xs">
            {[
              { label: 'News & Media', pct: '32%', color: 'bg-[#800020] dark:bg-[#B6FF2E]' },
              { label: 'Academic & Peer Review', pct: '28%', color: 'bg-[#D8AE9B] dark:bg-emerald-400' },
              { label: 'Government & Regulators', pct: '18%', color: 'bg-amber-600 dark:bg-amber-400' },
              { label: 'Other Public Sources', pct: '22%', color: 'bg-slate-400 dark:bg-slate-600' },
            ].map((d, i) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between font-semibold text-[#6C3B45] dark:text-slate-300">
                  <span>{d.label}</span>
                  <span className="font-mono text-[#2E0A12] dark:text-white">{d.pct}</span>
                </div>
                <div className="h-2 w-full rounded-full overflow-hidden bg-[#FBF1E3] dark:bg-[#181A20]">
                  <div className={`h-full ${d.color}`} style={{ width: d.pct }} />
                </div>
              </div>
            ))}
          </div>
        </section>

      </div>
    </motion.div>
  );
};
export default ReportsPage;
