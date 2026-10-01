import React from 'react';
import type { DomainStat } from '../../types/api';

interface DomainAnalyticsTableProps {
  domains: DomainStat[];
  loading: boolean;
}

export const DomainAnalyticsTable: React.FC<DomainAnalyticsTableProps> = ({ domains, loading }) => {
  if (loading) {
    return (
      <div className="h-64 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex items-center justify-center animate-pulse">
        <div className="text-slate-500 text-sm">Loading Domain Analytics...</div>
      </div>
    );
  }

  if (!domains || domains.length === 0) {
    return (
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-md backdrop-blur-sm">
        <h3 className="text-base font-semibold text-slate-100 mb-2">Domain Performance Analytics</h3>
        <p className="text-xs text-slate-400">No domain verifications available for current filter set.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-md backdrop-blur-sm mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100">Domain Performance Analytics</h3>
          <p className="text-xs text-slate-400">Verification statistics grouped by domain & research topic</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="px-4 py-3">Domain</th>
              <th className="px-4 py-3">Verifications</th>
              <th className="px-4 py-3">Trust Score</th>
              <th className="px-4 py-3">Supported</th>
              <th className="px-4 py-3">Contradicted</th>
              <th className="px-4 py-3">Inconclusive</th>
              <th className="px-4 py-3">Hallucination Rate</th>
              <th className="px-4 py-3">Avg Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {domains.map((d) => (
              <tr key={d.domain} className="hover:bg-slate-800/40 transition-colors">
                <td className="px-4 py-3 font-semibold text-slate-200">{d.domain}</td>
                <td className="px-4 py-3 font-mono">{d.verification_count}</td>
                <td className="px-4 py-3 font-mono font-bold text-emerald-400">
                  {d.trust_score !== null ? `${(d.trust_score * 100).toFixed(1)}%` : 'N/A'}
                </td>
                <td className="px-4 py-3 font-mono text-emerald-400">{d.supported}</td>
                <td className="px-4 py-3 font-mono text-rose-400">{d.contradicted}</td>
                <td className="px-4 py-3 font-mono text-amber-400">{d.inconclusive}</td>
                <td className="px-4 py-3 font-mono text-rose-400 font-semibold">
                  {(d.hallucination_rate * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-3 font-mono text-sky-400">
                  {d.confidence !== null ? `${(d.confidence * 100).toFixed(1)}%` : 'No signal'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
