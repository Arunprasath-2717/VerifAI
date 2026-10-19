import React from 'react';
import { 
  ShieldCheck, 
  FileText, 
  BookOpen, 
  ChevronRight, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle,
  FileCheck2
} from 'lucide-react';

interface RightPanelProps {
  totalVerifications: number;
  claimsAnalyzed: number;
  evidenceSources: number;
  supportedCount: number;
  contradictedCount: number;
  unknownCount: number;
  onSelectStat: (stat: string) => void;
  onOpenDetails: () => void;
  onOpenAuditReport: () => void;
}

export const RightPanel: React.FC<RightPanelProps> = ({
  totalVerifications,
  claimsAnalyzed,
  evidenceSources,
  supportedCount,
  contradictedCount,
  unknownCount,
  onSelectStat,
  onOpenDetails,
  onOpenAuditReport,
}) => {
  const statCards = [
    {
      id: 'verifications',
      label: 'Total Verifications',
      value: totalVerifications.toLocaleString(),
      icon: ShieldCheck,
      iconBg: 'bg-blue-50 text-blue-600',
    },
    {
      id: 'claims',
      label: 'Claims Analyzed',
      value: `${(claimsAnalyzed / 1000).toFixed(1)}k`,
      icon: FileText,
      iconBg: 'bg-indigo-50 text-indigo-600',
    },
    {
      id: 'evidence',
      label: 'Evidence Sources',
      value: evidenceSources.toLocaleString(),
      icon: BookOpen,
      iconBg: 'bg-emerald-50 text-emerald-600',
    },
  ];

  const totalStatus = supportedCount + contradictedCount + unknownCount;
  const supportedPct = totalStatus > 0 ? Math.round((supportedCount / totalStatus) * 100) : 0;
  const contradictedPct = totalStatus > 0 ? Math.round((contradictedCount / totalStatus) * 100) : 0;
  const unknownPct = totalStatus > 0 ? 100 - supportedPct - contradictedPct : 0;

  return (
    <aside className="space-y-6">
      {/* 3 Quick Stacked Stat Cards - Reference Exact Match */}
      <div className="space-y-3.5">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.id}
              onClick={() => onSelectStat(card.id)}
              className="bg-white p-5 rounded-[2rem] border border-slate-200/70 flex items-center justify-between group hover:shadow-md hover:border-slate-300 transition-all cursor-pointer select-none"
            >
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-2xl ${card.iconBg} flex items-center justify-center transition-transform group-hover:scale-105`}>
                  <Icon size={20} strokeWidth={2.2} />
                </div>
                <div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    {card.label}
                  </p>
                  <h4 className="text-xl font-extrabold text-slate-900 leading-tight font-mono tabular-nums">
                    {card.value}
                  </h4>
                </div>
              </div>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-slate-300 group-hover:text-slate-700 transition-colors">
                <ChevronRight size={18} className="group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Status Overview Card (Replaces Reference "Followers" Card) */}
      <section className="bg-white rounded-[2.5rem] p-6 border border-slate-200/70 shadow-sm space-y-5">
        <div className="flex items-center justify-between">
          <h4 className="font-extrabold text-sm text-slate-900 tracking-tight">
            Status Overview
          </h4>
          <button 
            onClick={onOpenDetails}
            className="text-[11px] font-bold text-slate-400 hover:text-blue-600 uppercase tracking-wider transition-colors cursor-pointer"
          >
            Details
          </button>
        </div>

        {/* Visual Distribution Bar */}
        <div className="space-y-1.5">
          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden flex">
            <div 
              style={{ width: `${supportedPct}%` }} 
              className="bg-emerald-500 h-full transition-all duration-500" 
              title={`Supported: ${supportedPct}%`}
            />
            <div 
              style={{ width: `${contradictedPct}%` }} 
              className="bg-rose-500 h-full transition-all duration-500" 
              title={`Contradicted: ${contradictedPct}%`}
            />
            <div 
              style={{ width: `${unknownPct}%` }} 
              className="bg-amber-400 h-full transition-all duration-500" 
              title={`Unknown: ${unknownPct}%`}
            />
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 font-medium px-0.5">
            <span>{supportedPct}% Supported</span>
            <span>{contradictedPct}% Contradicted</span>
            <span>{unknownPct}% Unknown</span>
          </div>
        </div>

        {/* Status Rows */}
        <div className="space-y-4 pt-1">
          {/* Supported */}
          <div className="flex items-center justify-between group cursor-default">
            <div className="flex items-center gap-3">
              <div className="w-1.5 h-6 rounded-full bg-emerald-500 opacity-80 group-hover:opacity-100 transition-opacity" />
              <div>
                <p className="text-xs font-bold text-slate-900 leading-none mb-1">
                  Supported
                </p>
                <p className="text-[10px] text-slate-400 font-medium">Corroborated claims</p>
              </div>
            </div>
            <span className="text-sm font-extrabold text-slate-900 font-mono tabular-nums">
              {supportedCount.toLocaleString()}
            </span>
          </div>

          {/* Contradicted */}
          <div className="flex items-center justify-between group cursor-default">
            <div className="flex items-center gap-3">
              <div className="w-1.5 h-6 rounded-full bg-rose-500 opacity-80 group-hover:opacity-100 transition-opacity" />
              <div>
                <p className="text-xs font-bold text-slate-900 leading-none mb-1">
                  Contradicted
                </p>
                <p className="text-[10px] text-slate-400 font-medium">Refuted by evidence</p>
              </div>
            </div>
            <span className="text-sm font-extrabold text-slate-900 font-mono tabular-nums">
              {contradictedCount.toLocaleString()}
            </span>
          </div>

          {/* Unknown */}
          <div className="flex items-center justify-between group cursor-default">
            <div className="flex items-center gap-3">
              <div className="w-1.5 h-6 rounded-full bg-amber-400 opacity-80 group-hover:opacity-100 transition-opacity" />
              <div>
                <p className="text-xs font-bold text-slate-900 leading-none mb-1">
                  Unknown
                </p>
                <p className="text-[10px] text-slate-400 font-medium">Insufficient sources</p>
              </div>
            </div>
            <span className="text-sm font-extrabold text-slate-900 font-mono tabular-nums">
              {unknownCount.toLocaleString()}
            </span>
          </div>
        </div>
      </section>

      {/* Advanced Reporting Card (Replaces Reference "Buy Pro Account" Card) */}
      <section className="bg-[#111111] rounded-[2.5rem] p-7 text-white relative overflow-hidden shadow-lg group">
        {/* Subtle radial lighting */}
        <div className="absolute -bottom-8 -right-8 w-36 h-36 bg-blue-600/25 rounded-full blur-3xl group-hover:bg-blue-600/35 transition-all pointer-events-none" />

        <div className="relative z-10 space-y-3">
          <div className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center text-blue-400">
            <FileCheck2 size={18} />
          </div>

          <div>
            <h4 className="text-base font-extrabold mb-1.5 leading-snug tracking-tight">
              Advanced Reporting
            </h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Export verifiable PDF audit trails and deep-dive evidence maps for institutional compliance.
            </p>
          </div>

          <div className="pt-2">
            <button 
              onClick={onOpenAuditReport}
              className="w-full bg-white text-slate-900 py-3 rounded-2xl text-xs font-extrabold hover:bg-slate-100 active:scale-[0.98] transition-all cursor-pointer shadow-md"
            >
              Export Audit Trail
            </button>
          </div>
        </div>
      </section>
    </aside>
  );
};
