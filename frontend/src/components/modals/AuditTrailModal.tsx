import React, { useState } from 'react';
import { X, FileCheck2, Download, Copy, Check, ShieldCheck, Key, Hash } from 'lucide-react';
import { VerificationRecord, UserProfile } from '../../types';

interface AuditTrailModalProps {
  isOpen: boolean;
  onClose: () => void;
  verifications: VerificationRecord[];
  user: { name?: string; fullName?: string; email: string };
}

export const AuditTrailModal: React.FC<AuditTrailModalProps> = ({
  isOpen,
  onClose,
  verifications,
  user,
}) => {
  const [copied, setCopied] = useState(false);
  const [format, setFormat] = useState<'json' | 'summary'>('summary');

  if (!isOpen) return null;

  const auditDigest = {
    exportType: 'verifai-session-verifications',
    generatedAt: new Date().toISOString(),
    auditor: user.fullName || user.name || 'Unspecified',
    email: user.email,
    sessionVerificationCount: verifications.length,
    records: verifications.map(v => ({
      id: v.id,
      query: v.query,
      status: v.status,
      evidenceCited: v.evidenceCount,
      claimsTotal: v.claimsCount,
      modelEvaluated: v.model,
      timestamp: v.timestamp
    }))
  };

  const handleDownload = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(auditDigest, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `verifai-audit-trail-${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(auditDigest, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#FFFFFF] dark:bg-[#1E2129] rounded-2xl w-full max-w-2xl border border-[#74C69D] dark:border-[#333742] shadow-2xl p-5 sm:p-6 md:p-7 space-y-5 my-8 animate-in fade-in zoom-in-95 text-[#1B4332] dark:text-white">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#74C69D] dark:border-[#333742]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#1B4332] dark:bg-[#181A20] text-[#D8F3DC] dark:text-[#B6FF2E] flex items-center justify-center border border-[#1B4332] dark:border-[#B6FF2E]/30">
              <FileCheck2 size={20} />
            </div>
            <div>
              <h3 className="font-extrabold text-lg text-[#1B4332] dark:text-white tracking-tight">
                Verification Session Export
              </h3>
              <p className="text-xs text-[#356B52] dark:text-slate-400 font-medium">
                JSON export of visible verification records; no cryptographic signature is attached.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-xl bg-[#D8F3DC] hover:bg-[#D8F3DC] text-[#356B52] dark:bg-[#181A20] dark:hover:bg-[#2A2E38] dark:text-slate-300 flex items-center justify-center transition-colors cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        <p className="p-3 text-xs text-[#356B52] dark:text-slate-300 bg-[#D8F3DC] dark:bg-[#14161C] border border-[#74C69D] dark:border-[#333742] rounded-xl">
          This export contains the verification data displayed in this session. It is not a signed Merkle ledger or an independently validated compliance artifact.
        </p>

        {/* Audit summary metrics */}
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-[#D8F3DC] dark:bg-[#181A20] rounded-2xl border border-[#74C69D] dark:border-[#333742]">
            <span className="text-[#356B52] dark:text-slate-400 block font-medium">Auditor</span>
            <span className="font-bold text-[#1B4332] dark:text-white">{user.fullName || user.name || 'Arun Prasath'}</span>
          </div>
          <div className="p-3 bg-[#D8F3DC] dark:bg-[#181A20] rounded-2xl border border-[#74C69D] dark:border-[#333742]">
            <span className="text-[#356B52] dark:text-slate-400 block font-medium">Verified Records</span>
            <span className="font-bold text-[#1B4332] dark:text-white">{verifications.length} records</span>
          </div>
          <div className="p-3 bg-[#D8F3DC] dark:bg-[#181A20] rounded-2xl border border-[#74C69D] dark:border-[#333742]">
            <span className="text-[#356B52] dark:text-slate-400 block font-medium">Protocol</span>
            <span className="font-bold text-[#1B4332] dark:text-white">JSON (unsigned)</span>
          </div>
        </div>

        {/* Code / JSON Preview */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <label className="font-bold text-[#1B4332] dark:text-slate-200">Audit Ledger Payload</label>
            <button
              onClick={handleCopy}
              className="text-xs text-[#1B4332] dark:text-[#B6FF2E] hover:underline flex items-center gap-1 font-semibold cursor-pointer"
            >
              {copied ? <Check size={13} className="text-[#1B4332] dark:text-[#B6FF2E]" /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <pre className="bg-[#181A20] text-slate-200 p-4 rounded-2xl text-[11px] font-mono overflow-x-auto max-h-48 border border-[#333742]">
            {JSON.stringify(auditDigest, null, 2)}
          </pre>
        </div>

        {/* Footer actions */}
        <div className="pt-2 flex justify-between items-center border-t border-[#74C69D] dark:border-[#333742]">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-[#356B52] hover:text-[#1B4332] dark:text-slate-400 dark:hover:text-white cursor-pointer"
          >
            Cancel
          </button>
          <div className="flex gap-2">
            <button
              onClick={handleDownload}
              className="bg-[#1B4332] hover:bg-[#163E2D] text-[#D8F3DC] dark:bg-[#B6FF2E] dark:hover:bg-[#A3E823] dark:text-[#181A20] px-5 py-2.5 rounded-xl font-bold text-xs shadow-md transition-all flex items-center gap-2 cursor-pointer"
            >
              <Download size={14} />
              <span>Download JSON Trail</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
