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
          <div key={i} className="h-32 bg-white/20 backdrop-blur-xl rounded-2xl border border-white/40 animate-pulse p-5 flex flex-col justify-between">
            <div className="h-4 bg-white/50 rounded w-1/2"></div>
            <div className="h-9 bg-white/50 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-rose-50/80 border border-rose-200 rounded-2xl text-rose-700 mb-8 text-sm flex items-center justify-between shadow-lg">
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
      gradient: 'from-emerald-100/50 via-teal-100/30 to-transparent',
      borderColor: 'border-emerald-300',
      iconBg: 'bg-emerald-100 text-emerald-600 border border-emerald-200',
      textColor: 'text-emerald-700',
      badge: 'Core Engine'
    },
    {
      title: 'Total Verifications',
      value: overview.total_verifications.toLocaleString(),
      subtext: `${overview.total_claims.toLocaleString()} Verified Claims`,
      icon: Layers,
      gradient: 'from-indigo-100/50 via-purple-100/30 to-transparent',
      borderColor: 'border-indigo-300',
      iconBg: 'bg-indigo-100 text-indigo-600 border border-indigo-200',
      textColor: 'text-indigo-700'
    },
    {
      title: 'Supported Claims',
      value: overview.supported_claims.toLocaleString(),
      subtext: overview.total_claims > 0 ? `${((overview.supported_claims / overview.total_claims) * 100).toFixed(1)}% of total claims` : '0%',
      icon: CheckCircle,
      gradient: 'from-emerald-200/50 via-green-100/30 to-transparent',
      borderColor: 'border-emerald-300',
      iconBg: 'bg-emerald-100 text-emerald-600 border border-emerald-200',
      textColor: 'text-emerald-700'
    },
    {
      title: 'Contradicted Claims',
      value: overview.contradicted_claims.toLocaleString(),
      subtext: overview.total_claims > 0 ? `${((overview.contradicted_claims / overview.total_claims) * 100).toFixed(1)}% of total claims` : '0%',
      icon: AlertTriangle,
      gradient: 'from-rose-100/50 via-red-100/30 to-transparent',
      borderColor: 'border-rose-300',
      iconBg: 'bg-rose-100 text-rose-600 border border-rose-200',
      textColor: 'text-rose-700'
    },
    {
      title: 'Inconclusive Claims',
      value: overview.inconclusive_claims.toLocaleString(),
      subtext: overview.total_claims > 0 ? `${((overview.inconclusive_claims / overview.total_claims) * 100).toFixed(1)}% of total claims` : '0%',
      icon: HelpCircle,
      gradient: 'from-amber-100/50 via-yellow-100/30 to-transparent',
      borderColor: 'border-amber-300',
      iconBg: 'bg-amber-100 text-amber-600 border border-amber-200',
      textColor: 'text-amber-700'
    },
    {
      title: 'Hallucination Rate',
      value: `${(overview.hallucination_rate * 100).toFixed(1)}%`,
      subtext: 'Contradicted / Evaluated Claims',
      icon: Activity,
      gradient: 'from-pink-100/50 via-rose-100/30 to-transparent',
      borderColor: 'border-rose-300',
      iconBg: 'bg-pink-100 text-pink-600 border border-pink-200',
      textColor: 'text-pink-700'
    },
    {
      title: 'Average Confidence',
      value: confidenceFormatted,
      subtext: overview.average_confidence !== null ? 'Evaluated confidence signal' : 'Preserved signal state',
      icon: Gauge,
      gradient: 'from-sky-100/50 via-blue-100/30 to-transparent',
      borderColor: 'border-sky-300',
      iconBg: 'bg-sky-100 text-sky-600 border border-sky-200',
      textColor: 'text-sky-700'
    },
    {
      title: 'Signal Quality',
      value: `${(overview.signal_quality * 100).toFixed(1)}%`,
      subtext: 'Consistency Quality Index',
      icon: Cpu,
      gradient: 'from-sky-100/50 via-purple-100/30 to-transparent',
      borderColor: 'border-sky-300',
      iconBg: 'bg-sky-100 text-sky-600 border border-sky-200',
      textColor: 'text-sky-700'
    },
    {
      title: 'Evidence Quality',
      value: `${(overview.evidence_quality * 100).toFixed(1)}%`,
      subtext: 'Mean Evidence Strength',
      icon: FileCheck,
      gradient: 'from-teal-100/50 via-cyan-100/30 to-transparent',
      borderColor: 'border-teal-300',
      iconBg: 'bg-teal-100 text-teal-600 border border-teal-200',
      textColor: 'text-teal-700'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
      {cards.map((c, idx) => {
        const IconComponent = c.icon;
        return (
          <div
            key={idx}
            className={`relative group bg-white/30 backdrop-blur-md border ${c.borderColor} rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1 overflow-hidden`}
          >
            {/* Background Gradient Accent */}
            <div className={`absolute inset-0 bg-gradient-to-br ${c.gradient} pointer-events-none opacity-60 group-hover:opacity-100 transition-opacity`}></div>

            <div className="relative z-10 flex flex-col justify-between h-full">
              
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-600 tracking-wider uppercase">
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
                  <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-300">
                    {c.badge}
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-500 font-medium mt-3">
                {c.subtext}
              </p>

            </div>
          </div>
        );
      })}
    </div>
  );
};
