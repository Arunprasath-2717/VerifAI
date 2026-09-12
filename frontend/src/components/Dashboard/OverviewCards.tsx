import React from 'react';
import { ShieldCheck, Layers, CheckCircle, AlertTriangle, HelpCircle, Activity, Gauge, Cpu, FileCheck } from 'lucide-react';
import type { DashboardOverview } from '../../types/api';

interface OverviewCardsProps {
  overview: DashboardOverview | null;
  loading: boolean;
  error: string | null;
}

export const OverviewCards: React.FC<OverviewCardsProps> = ({ overview, loading, error }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="h-32 bg-slate-900/60 rounded-2xl border border-slate-800 animate-pulse p-5 flex flex-col justify-between">
            <div className="h-4 bg-slate-800 rounded w-1/2"></div>
            <div className="h-9 bg-slate-800 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-rose-950/60 border border-rose-800/80 rounded-2xl text-rose-200 mb-8 text-sm flex items-center justify-between shadow-lg">
        <span>Error loading overview metrics: {error}</span>
      </div>
    );
  }

  if (!overview) return null;

  const trustScoreFormatted = overview.overall_trust_score !== null
    ? `${(overview.overall_trust_score * 100).toFixed(1)}%`
    : 'Not available';

  const confidenceFormatted = overview.average_confidence !== null
    ? `${(overview.average_confidence * 100).toFixed(1)}%`
    : 'No signal';

  const cards = [
    {
      title: 'Overall Trust Score',
      value: trustScoreFormatted,
      subtext: 'Centralized Core Metric',
      icon: ShieldCheck,
      gradient: 'from-emerald-500/20 via-teal-500/10 to-transparent',
      borderColor: 'border-emerald-500/40',
      iconBg: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40',
      textColor: 'text-emerald-400',
      badge: 'Core Engine'
    },
    {
      title: 'Total Verifications',
      value: overview.total_verifications.toLocaleString(),
      subtext: `${overview.total_claims.toLocaleString()} Verified Claims`,
      icon: Layers,
      gradient: 'from-indigo-500/20 via-purple-500/10 to-transparent',
      borderColor: 'border-indigo-500/40',
      iconBg: 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/40',
      textColor: 'text-indigo-300'
    },
    {
      title: 'Supported Claims',
      value: overview.supported_claims.toLocaleString(),
      subtext: overview.total_claims > 0 ? `${((overview.supported_claims / overview.total_claims) * 100).toFixed(1)}% of total claims` : '0%',
      icon: CheckCircle,
      gradient: 'from-emerald-600/20 via-green-500/10 to-transparent',
      borderColor: 'border-emerald-500/40',
      iconBg: 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/40',
      textColor: 'text-emerald-400'
    },
    {
      title: 'Contradicted Claims',
      value: overview.contradicted_claims.toLocaleString(),
      subtext: overview.total_claims > 0 ? `${((overview.contradicted_claims / overview.total_claims) * 100).toFixed(1)}% of total claims` : '0%',
      icon: AlertTriangle,
      gradient: 'from-rose-600/20 via-red-500/10 to-transparent',
      borderColor: 'border-rose-500/40',
      iconBg: 'bg-rose-600/20 text-rose-400 border border-rose-500/40',
      textColor: 'text-rose-400'
    },
    {
      title: 'Inconclusive Claims',
      value: overview.inconclusive_claims.toLocaleString(),
      subtext: overview.total_claims > 0 ? `${((overview.inconclusive_claims / overview.total_claims) * 100).toFixed(1)}% of total claims` : '0%',
      icon: HelpCircle,
      gradient: 'from-amber-500/20 via-yellow-500/10 to-transparent',
      borderColor: 'border-amber-500/40',
      iconBg: 'bg-amber-500/20 text-amber-400 border border-amber-500/40',
      textColor: 'text-amber-400'
    },
    {
      title: 'Hallucination Rate',
      value: `${(overview.hallucination_rate * 100).toFixed(1)}%`,
      subtext: 'Contradicted / Evaluated Claims',
      icon: Activity,
      gradient: 'from-pink-500/20 via-rose-500/10 to-transparent',
      borderColor: 'border-rose-500/40',
      iconBg: 'bg-pink-500/20 text-pink-400 border border-pink-500/40',
      textColor: 'text-pink-400'
    },
    {
      title: 'Average Confidence',
      value: confidenceFormatted,
      subtext: overview.average_confidence !== null ? 'Evaluated confidence signal' : 'Preserved signal state',
      icon: Gauge,
      gradient: 'from-sky-500/20 via-blue-500/10 to-transparent',
      borderColor: 'border-sky-500/40',
      iconBg: 'bg-sky-500/20 text-sky-400 border border-sky-500/40',
      textColor: 'text-sky-400'
    },
    {
      title: 'Signal Quality',
      value: `${(overview.signal_quality * 100).toFixed(1)}%`,
      subtext: 'Consistency Quality Index',
      icon: Cpu,
      gradient: 'from-violet-500/20 via-purple-500/10 to-transparent',
      borderColor: 'border-violet-500/40',
      iconBg: 'bg-violet-500/20 text-violet-400 border border-violet-500/40',
      textColor: 'text-violet-300'
    },
    {
      title: 'Evidence Quality',
      value: `${(overview.evidence_quality * 100).toFixed(1)}%`,
      subtext: 'Mean Evidence Strength',
      icon: FileCheck,
      gradient: 'from-teal-500/20 via-cyan-500/10 to-transparent',
      borderColor: 'border-teal-500/40',
      iconBg: 'bg-teal-500/20 text-teal-400 border border-teal-500/40',
      textColor: 'text-teal-300'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
      {cards.map((c, idx) => {
        const IconComponent = c.icon;
        return (
          <div
            key={idx}
            className={`relative group bg-slate-900/80 border ${c.borderColor} rounded-2xl p-5 shadow-xl backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl overflow-hidden`}
          >
            {/* Background Gradient Accent */}
            <div className={`absolute inset-0 bg-gradient-to-br ${c.gradient} pointer-events-none opacity-60 group-hover:opacity-100 transition-opacity`}></div>

            <div className="relative z-10 flex flex-col justify-between h-full">
              
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-400 tracking-wider uppercase">
                  {c.title}
                </span>
                <div className={`p-2.5 rounded-xl ${c.iconBg} shadow-sm`}>
                  <IconComponent className="h-4 w-4" />
                </div>
              </div>

              <div className="flex items-baseline justify-between mt-2">
                <span className={`text-3xl font-extrabold tracking-tight ${c.textColor}`}>
                  {c.value}
                </span>
                {c.badge && (
                  <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800/80">
                    {c.badge}
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-400 font-medium mt-3">
                {c.subtext}
              </p>

            </div>
          </div>
        );
      })}
    </div>
  );
};
