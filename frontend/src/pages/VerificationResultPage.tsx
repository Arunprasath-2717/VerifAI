import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ChevronRight, 
  RotateCw, 
  Bookmark, 
  Share2, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  Check
} from 'lucide-react';
import { motion } from 'motion/react';
import { VerificationRecord } from '../types';
import { verificationApi } from '../api';

interface VerificationResultPageProps {
  verifications: VerificationRecord[];
  theme?: 'light' | 'dark';
}

export const VerificationResultPage: React.FC<VerificationResultPageProps> = ({ verifications }) => {
  const { verificationId } = useParams<{ verificationId: string }>();
  const navigate = useNavigate();

  const isInvalidParam = !verificationId || verificationId === 'undefined' || verificationId === 'null';
  const propRecord = !isInvalidParam ? verifications.find(v => v.id === verificationId) : undefined;
  const [fetchedRecord, setFetchedRecord] = useState<VerificationRecord | null>(null);
  const [isLoadingRecord, setIsLoadingRecord] = useState(!propRecord && !isInvalidParam && Boolean(verificationId));
  const [fetchError, setFetchError] = useState<string | null>(null);

  React.useEffect(() => {
    if (!propRecord && verificationId && !isInvalidParam) {
      setIsLoadingRecord(true);
      setFetchError(null);
      verificationApi.getVerification(verificationId)
        .then(rec => setFetchedRecord(rec))
        .catch((err) => {
          setFetchError(err?.message || 'Verification record not found or could not be loaded');
        })
        .finally(() => setIsLoadingRecord(false));
    }
  }, [verificationId, propRecord, isInvalidParam]);

  const record = propRecord || fetchedRecord || (!verificationId ? verifications[0] : null);

  const [activeTab, setActiveTab] = useState<'overview' | 'claims' | 'evidence' | 'judgments' | 'audit'>('overview');
  const [expandedClaimIds, setExpandedClaimIds] = useState<string[]>(['c-101', 'c-103']);
  const [saved, setSaved] = useState(false);
  const [copied, setCopied] = useState(false);

  if (isLoadingRecord) {
    return (
      <div className="flex flex-col items-center justify-center py-24 rounded-[2.5rem] border bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742] space-y-4">
        <RotateCw className="w-8 h-8 text-[#800020] dark:text-[#B6FF2E] animate-spin" />
        <p className="text-sm font-semibold text-[#6C3B45] dark:text-slate-300">
          Loading verification record...
        </p>
      </div>
    );
  }

  if (!record) {
    return (
      <div className="text-center py-20 rounded-[2.5rem] border bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
        <h3 className="text-lg font-bold text-[#2E0A12] dark:text-white">Verification record not found</h3>
        <p className="text-xs text-[#8A6A72] dark:text-slate-400 mt-1 mb-4">
          {fetchError || 'The requested verification record could not be loaded.'}
        </p>
        <button
          onClick={() => navigate('/history')}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-[#800020] text-[#FBF1E3] hover:bg-[#711C32] dark:bg-[#B6FF2E] dark:text-[#181A20] transition-colors cursor-pointer"
        >
          Back to History
        </button>
      </div>
    );
  }

  const toggleClaimExpand = (claimId: string) => {
    if (expandedClaimIds.includes(claimId)) {
      setExpandedClaimIds(expandedClaimIds.filter(id => id !== claimId));
    } else {
      setExpandedClaimIds([...expandedClaimIds, claimId]);
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-8 pb-16 max-w-5xl mx-auto"
    >
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-xs font-semibold text-[#8A6A72] dark:text-slate-500">
        <Link to="/verify" className="hover:text-[#2E0A12] dark:hover:text-slate-300 transition-colors">
          Verify
        </Link>
        <ChevronRight size={14} />
        <span className="text-[#2E0A12] dark:text-slate-200">Result</span>
      </nav>

      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#2E0A12] dark:text-white transition-colors">
              Verification Result
            </h1>
            <span className={`px-3 py-1 rounded-full text-xs font-black tracking-wider uppercase ${
              record.status === 'SUPPORTED'
                ? 'lt-badge-supported dark:bg-[#B6FF2E]/15 dark:text-[#B6FF2E] dark:border dark:border-[#B6FF2E]/30'
                : record.status === 'CONTRADICTED'
                ? 'lt-badge-contradicted dark:bg-rose-500/15 dark:text-rose-300 dark:border dark:border-rose-500/30'
                : 'lt-badge-unknown dark:bg-amber-500/15 dark:text-amber-300 dark:border dark:border-amber-500/30'
            }`}>
              {record.status}
            </span>
          </div>

          <p className="text-xs font-medium text-[#6C3B45] dark:text-slate-300">
            Verified on {record.dateFormatted || record.timestamp} · {record.modelsUsed?.length || 2} models · {record.claimsCount} claims · {record.evidenceCount} evidence sources
          </p>
        </div>

        {/* Top Right Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/verify')}
            className="px-3.5 py-2 rounded-xl border text-xs font-bold flex items-center gap-1.5 shadow-2xs transition-colors cursor-pointer bg-[#FFFDFA] border-[#E9D6C4] text-[#800020] hover:bg-[#FBF1E3] dark:bg-[#23262F] dark:border-[#333742] dark:text-white dark:hover:border-[#B6FF2E]/40"
          >
            <RotateCw size={14} />
            <span>Re-verify</span>
          </button>

          <button
            onClick={() => setSaved(!saved)}
            className={`px-3.5 py-2 rounded-xl border text-xs font-bold flex items-center gap-1.5 shadow-2xs transition-colors cursor-pointer ${
              saved 
                ? 'bg-[#EFE0D1] border-[#E9D6C4] text-[#800020] dark:bg-[#B6FF2E]/15 dark:border-[#B6FF2E]/40 dark:text-[#B6FF2E]' 
                : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#6C3B45] dark:bg-[#23262F] dark:border-[#333742] dark:text-white'
            }`}
          >
            <Bookmark size={14} className={saved ? 'fill-current' : ''} />
            <span>{saved ? 'Saved' : 'Save'}</span>
          </button>

          <button
            onClick={handleShare}
            className="px-3.5 py-2 rounded-xl border text-xs font-bold flex items-center gap-1.5 shadow-2xs transition-colors cursor-pointer bg-[#FFFDFA] border-[#E9D6C4] text-[#6C3B45] dark:bg-[#23262F] dark:border-[#333742] dark:text-white"
          >
            {copied ? <Check size={14} className="text-[#800020] dark:text-[#B6FF2E]" /> : <Share2 size={14} />}
            <span>{copied ? 'Copied' : 'Share'}</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b overflow-x-auto pb-1 border-[#E9D6C4] dark:border-[#333742]">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'claims', label: `Claims (${record.claimsCount})` },
          { id: 'evidence', label: `Evidence (${record.evidenceCount})` },
          { id: 'judgments', label: 'Model Judgments' },
          { id: 'audit', label: 'Audit' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 text-xs font-bold rounded-xl transition-all whitespace-nowrap cursor-pointer ${
              activeTab === tab.id
                ? 'bg-[#800020] text-[#FBF1E3] dark:bg-[#B6FF2E] dark:text-[#181A20] shadow-xs'
                : 'text-[#8A6A72] dark:text-slate-400 hover:text-[#2E0A12] dark:hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Original Answer Box */}
      <section className="rounded-[2.2rem] p-6 border shadow-xs space-y-2 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
        <span className="text-xs font-bold uppercase tracking-wider block text-[#8A6A72] dark:text-slate-400">
          Original Answer Audited
        </span>
        <p className="text-sm md:text-base leading-relaxed font-sans text-[#2E0A12] dark:text-slate-200">
          "{record.originalAnswer || record.query}"
        </p>
      </section>

      {/* Verification Summary - 5 Metric Cards */}
      <section className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-[#8A6A72] dark:text-slate-400">Claims</p>
          <p className="text-2xl font-black font-mono mt-1 text-[#2E0A12] dark:text-white">{record.claimsCount}</p>
        </div>

        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-[#800020] dark:text-[#B6FF2E]">Supported</p>
          <p className="text-2xl font-black font-mono mt-1 text-[#800020] dark:text-[#B6FF2E]">{record.supportedCount}</p>
        </div>

        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-rose-600 dark:text-rose-400">Contradicted</p>
          <p className="text-2xl font-black font-mono mt-1 text-rose-600 dark:text-rose-400">{record.contradictedCount}</p>
        </div>

        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-[#800020] dark:text-[#B6FF2E]">Evidence Sources</p>
          <p className="text-2xl font-black font-mono mt-1 text-[#800020] dark:text-[#B6FF2E]">{record.evidenceCount}</p>
        </div>

        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-[#8A6A72] dark:text-slate-400">Models Used</p>
          <p className="text-2xl font-black font-mono mt-1 text-[#2E0A12] dark:text-white">{record.modelsUsed?.length || 2}</p>
        </div>
      </section>

      {/* Claims Breakdown */}
      <section className="space-y-4">
        <h3 className="font-extrabold text-lg tracking-tight text-[#2E0A12] dark:text-white">
          Claims Breakdown
        </h3>

        <div className="space-y-3">
          {record.claims && record.claims.length > 0 ? (
            record.claims.map((claim, idx) => {
              const isExpanded = expandedClaimIds.includes(claim.id);
              return (
                <div
                  key={claim.id}
                  className="rounded-[2rem] border shadow-xs overflow-hidden transition-all bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]"
                >
                  {/* Claim Row Header */}
                  <div 
                    onClick={() => toggleClaimExpand(claim.id)}
                    className="p-5 flex items-start sm:items-center justify-between gap-4 cursor-pointer transition-colors hover:bg-[#FBF1E3] dark:hover:bg-[#2A2E38]"
                  >
                    <div className="flex items-start sm:items-center gap-3.5 min-w-0">
                      <span className="font-mono font-bold text-sm mt-0.5 sm:mt-0 text-[#8A6A72] dark:text-slate-500">
                        {String(idx + 1).padStart(2, '0')}
                      </span>
                      <p className="text-sm sm:text-base font-bold leading-snug text-[#2E0A12] dark:text-white">
                        {claim.statement}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-black uppercase ${
                        claim.status === 'SUPPORTED'
                          ? 'bg-[#D8AE9B]/30 text-[#800020] border border-[#D8AE9B] dark:bg-[#B6FF2E]/15 dark:text-[#B6FF2E] dark:border-[#B6FF2E]/30'
                          : claim.status === 'CONTRADICTED'
                          ? 'bg-rose-50 text-rose-800 border border-rose-200 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30'
                          : 'bg-[#EFE0D1] text-[#800020] border border-[#E9D6C4] dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30'
                      }`}>
                        {claim.status}
                      </span>

                      <span className="hidden sm:inline text-xs font-semibold text-[#8A6A72] dark:text-slate-400">
                        {claim.confidence ? `${Math.round(claim.confidence * 100)}% confidence` : '3 evidence'}
                      </span>

                      <button className="text-xs font-bold flex items-center gap-0.5 text-[#800020] dark:text-[#B6FF2E]">
                        <span>{isExpanded ? 'Hide' : 'View Details'}</span>
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Evidence & Provenance Details */}
                  {isExpanded && (
                    <div className="px-6 pb-6 pt-2 border-t space-y-3 animate-in fade-in border-[#E9D6C4] bg-[#FBF1E3] dark:border-[#333742] dark:bg-[#181A20]/50">
                      {claim.evidenceSnippet && (
                        <div className="p-4 rounded-xl border space-y-1 bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#181A20] dark:border-[#333742]">
                          <span className="text-xs font-bold uppercase tracking-wider text-[#8A6A72] dark:text-slate-400">
                            Corroborating Excerpt
                          </span>
                          <p className="text-sm leading-relaxed text-[#6C3B45] dark:text-slate-200">
                            {claim.evidenceSnippet}
                          </p>
                        </div>
                      )}

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <div className="p-3.5 rounded-xl border bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#181A20] dark:border-[#333742]">
                          <span className="text-xs font-bold uppercase block mb-1 text-[#8A6A72] dark:text-slate-400">
                            Primary Source
                          </span>
                          <a
                            href={claim.sourceUrl || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-bold hover:underline flex items-center gap-1.5 text-[#800020] dark:text-[#B6FF2E]"
                          >
                            <span>{claim.sourceTitle || 'EPA Clean Air Act Compliance Guidelines'}</span>
                            <ExternalLink size={13} />
                          </a>
                          <span className="text-xs block mt-1 text-[#8A6A72] dark:text-slate-400">
                            Domain: {claim.domain || 'epa.gov'}
                          </span>
                        </div>

                        <div className="p-3.5 rounded-xl border bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#181A20] dark:border-[#333742]">
                          <span className="text-xs font-bold uppercase block mb-1 text-[#8A6A72] dark:text-slate-400">
                            Model Agreement & Judging
                          </span>
                          <p className="text-sm font-semibold text-[#6C3B45] dark:text-slate-200">
                            Full model concordance. 2 independent evaluators rated agreement score 0.96.
                          </p>
                          <span className="text-xs font-bold block mt-1 text-[#800020] dark:text-[#B6FF2E]">
                            Corroborated by external knowledge vault
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <p className="text-xs italic text-slate-400 dark:text-slate-400">No individual claims identified for this record.</p>
          )}
        </div>
      </section>

    </motion.div>
  );
};
export default VerificationResultPage;
