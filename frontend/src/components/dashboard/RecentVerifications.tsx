import React from 'react';
import { ShieldCheck, AlertCircle, HelpCircle, FileText, ChevronRight, ArrowRight } from 'lucide-react';
import { VerificationRecord, VerificationStatus } from '../../types';

interface RecentVerificationsProps {
  verifications: VerificationRecord[];
  onSelectRecord: (record: VerificationRecord) => void;
  onStartVerification: () => void;
}

export const RecentVerifications: React.FC<RecentVerificationsProps> = ({
  verifications,
  onSelectRecord,
  onStartVerification,
}) => {
  const getStatusBadge = (status: VerificationStatus) => {
    switch (status) {
      case 'SUPPORTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60">
            <ShieldCheck size={13} className="text-emerald-600" />
            <span>SUPPORTED</span>
          </span>
        );
      case 'CONTRADICTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200/60">
            <AlertCircle size={13} className="text-rose-600" />
            <span>CONTRADICTED</span>
          </span>
        );
      case 'UNKNOWN':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200/60">
            <HelpCircle size={13} className="text-amber-600" />
            <span>UNKNOWN</span>
          </span>
        );
    }
  };

  return (
    <section className="bg-white rounded-[2.8rem] p-8 border border-slate-200/70 shadow-sm space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-extrabold text-base md:text-lg text-slate-900 tracking-tight">
            Recent Verifications
          </h3>
          <p className="text-xs text-slate-400 font-medium">
            Claims extracted and audited against corroborated ground truth
          </p>
        </div>
        <span className="text-xs font-semibold text-slate-400">
          {verifications.length} records
        </span>
      </div>

      {verifications.length === 0 ? (
        <div className="text-center py-12 px-4 rounded-3xl bg-slate-50 border border-dashed border-slate-200">
          <FileText className="mx-auto text-slate-400 mb-3" size={32} />
          <h4 className="text-sm font-bold text-slate-800 mb-1">No verifications yet</h4>
          <p className="text-xs text-slate-500 mb-4 max-w-sm mx-auto">
            Audit any LLM response, medical claim, or technical output against verified sources.
          </p>
          <button
            onClick={onStartVerification}
            className="px-5 py-2.5 bg-slate-900 text-white rounded-xl text-xs font-bold hover:bg-black transition-all cursor-pointer"
          >
            Verify your first AI answer
          </button>
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {verifications.map((record) => (
            <div
              key={record.id}
              onClick={() => onSelectRecord(record)}
              className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4 group cursor-pointer hover:bg-slate-50/80 -mx-4 px-4 rounded-2xl transition-colors"
            >
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  {getStatusBadge(record.status)}
                  <span className="text-[11px] text-slate-400 font-medium">·</span>
                  <span className="text-xs font-bold text-slate-700">{record.model}</span>
                  <span className="text-[11px] text-slate-400 font-medium">·</span>
                  <span className="text-[11px] text-slate-400">{record.timestamp}</span>
                </div>
                <h4 className="text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors truncate">
                  {record.query}
                </h4>
                <p className="text-xs text-slate-500 line-clamp-1">
                  {record.summary}
                </p>
              </div>

              <div className="flex items-center gap-4 sm:shrink-0 self-end sm:self-center">
                <div className="text-right text-xs">
                  <p className="font-bold text-slate-800 tabular-nums">
                    {record.claimsCount} claims
                  </p>
                  <p className="text-[11px] text-slate-400 tabular-nums">
                    {record.evidenceCount} sources
                  </p>
                </div>
                <div className="w-8 h-8 rounded-xl bg-slate-100 group-hover:bg-blue-600 group-hover:text-white flex items-center justify-center text-slate-400 transition-colors">
                  <ChevronRight size={16} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};
