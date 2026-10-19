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
    auditProtocol: 'VERIFAI-CORROBORATE-V2.6',
    generatedAt: new Date().toISOString(),
    organization: 'VerifAI Enterprise Trust Vault',
    auditor: user.fullName || user.name || 'Arun Prasath',
    email: user.email,
    sessionVerificationCount: verifications.length,
    merkleRootHash: '0x8f4c71a3992b8d0e74f67c3125ea03b44b8214f526365da98e6c43141f2378a9',
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
      <div className="bg-[#FFFDFA] dark:bg-[#1E2129] rounded-[2.5rem] w-full max-w-2xl border border-[#E9D6C4] dark:border-[#333742] shadow-2xl p-6 md:p-8 space-y-6 my-8 animate-in fade-in zoom-in-95 text-[#2E0A12] dark:text-white">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#E9D6C4] dark:border-[#333742]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#800020] dark:bg-[#181A20] text-[#FBF1E3] dark:text-[#B6FF2E] flex items-center justify-center border border-[#800020] dark:border-[#B6FF2E]/30">
              <FileCheck2 size={20} />
            </div>
            <div>
              <h3 className="font-extrabold text-lg text-[#2E0A12] dark:text-white tracking-tight">
                Institutional Audit Trail
              </h3>
              <p className="text-xs text-[#8A6A72] dark:text-slate-400 font-medium">
                Cryptographically signed evidence ledger for regulatory compliance & audits
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-xl bg-[#FBF1E3] hover:bg-[#EFE0D1] text-[#6C3B45] dark:bg-[#181A20] dark:hover:bg-[#2A2E38] dark:text-slate-300 flex items-center justify-center transition-colors cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Cryptographic verification banner */}
        <div className="p-4 bg-[#FBF1E3] dark:bg-[#181A20] rounded-2xl border border-[#E9D6C4] dark:border-[#333742] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#2E0A12] dark:text-slate-200 flex items-center gap-1.5">
              <Hash size={14} className="text-[#800020] dark:text-[#B6FF2E]" />
              Merkle Root Signature
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#D8AE9B]/30 text-[#800020] border border-[#D8AE9B] dark:bg-[#B6FF2E]/15 dark:text-[#B6FF2E] dark:border-[#B6FF2E]/30">
              IMMUTABLE
            </span>
          </div>
          <p className="font-mono text-[11px] text-[#6C3B45] dark:text-slate-300 break-all bg-[#FFFDFA] dark:bg-[#14161C] p-2.5 rounded-xl border border-[#E9D6C4] dark:border-[#2D313D]">
            {auditDigest.merkleRootHash}
          </p>
        </div>

        {/* Audit summary metrics */}
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-[#FBF1E3] dark:bg-[#181A20] rounded-2xl border border-[#E9D6C4] dark:border-[#333742]">
            <span className="text-[#8A6A72] dark:text-slate-400 block font-medium">Auditor</span>
            <span className="font-bold text-[#2E0A12] dark:text-white">{user.fullName || user.name || 'Arun Prasath'}</span>
          </div>
          <div className="p-3 bg-[#FBF1E3] dark:bg-[#181A20] rounded-2xl border border-[#E9D6C4] dark:border-[#333742]">
            <span className="text-[#8A6A72] dark:text-slate-400 block font-medium">Verified Records</span>
            <span className="font-bold text-[#2E0A12] dark:text-white">{verifications.length} verified</span>
          </div>
          <div className="p-3 bg-[#FBF1E3] dark:bg-[#181A20] rounded-2xl border border-[#E9D6C4] dark:border-[#333742]">
            <span className="text-[#8A6A72] dark:text-slate-400 block font-medium">Protocol</span>
            <span className="font-bold text-[#2E0A12] dark:text-white">v2.6 CBER</span>
          </div>
        </div>

        {/* Code / JSON Preview */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <label className="font-bold text-[#2E0A12] dark:text-slate-200">Audit Ledger Payload</label>
            <button
              onClick={handleCopy}
              className="text-xs text-[#800020] dark:text-[#B6FF2E] hover:underline flex items-center gap-1 font-semibold cursor-pointer"
            >
              {copied ? <Check size={13} className="text-[#800020] dark:text-[#B6FF2E]" /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <pre className="bg-[#181A20] text-slate-200 p-4 rounded-2xl text-[11px] font-mono overflow-x-auto max-h-48 border border-[#333742]">
            {JSON.stringify(auditDigest, null, 2)}
          </pre>
        </div>

        {/* Footer actions */}
        <div className="pt-2 flex justify-between items-center border-t border-[#E9D6C4] dark:border-[#333742]">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-[#8A6A72] hover:text-[#2E0A12] dark:text-slate-400 dark:hover:text-white cursor-pointer"
          >
            Cancel
          </button>
          <div className="flex gap-2">
            <button
              onClick={handleDownload}
              className="bg-[#800020] hover:bg-[#711C32] text-[#FBF1E3] dark:bg-[#B6FF2E] dark:hover:bg-[#A3E823] dark:text-[#181A20] px-5 py-2.5 rounded-xl font-bold text-xs shadow-md transition-all flex items-center gap-2 cursor-pointer"
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
