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

type ResultTab = 'overview' | 'claims' | 'evidence' | 'judgments' | 'audit';

const tabs: { id: ResultTab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'claims', label: 'Claims' },
  { id: 'evidence', label: 'Evidence' },
  { id: 'judgments', label: 'Model Judgments' },
  { id: 'audit', label: 'Audit' },
];

const safeExternalUrl = (url?: string): string | undefined => {
  if (!url) return undefined;
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' || parsed.protocol === 'http:' ? parsed.href : undefined;
  } catch {
    return undefined;
  }
};

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
    let active = true;
    setFetchedRecord(null);
    setFetchError(null);
    if (!propRecord && verificationId && !isInvalidParam) {
      setIsLoadingRecord(true);
      verificationApi.getVerification(verificationId)
        .then(rec => {
          if (active) setFetchedRecord(rec);
        })
        .catch((err) => {
          if (active) setFetchError(err?.message || 'Verification record not found or could not be loaded');
        })
        .finally(() => {
          if (active) setIsLoadingRecord(false);
        });
    } else {
      setIsLoadingRecord(false);
    }
    return () => { active = false; };
  }, [verificationId, propRecord, isInvalidParam]);

  const record = propRecord || fetchedRecord || (!verificationId ? verifications[0] : null);

  const [activeTab, setActiveTab] = useState<ResultTab>('overview');
  const [expandedClaimIds, setExpandedClaimIds] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);
  const [copied, setCopied] = useState(false);

  React.useEffect(() => {
    setActiveTab('overview');
    setExpandedClaimIds([]);
  }, [verificationId]);

  if (isLoadingRecord) {
    return (
      <div className="flex flex-col items-center justify-center py-20 rounded-2xl border bg-[#FFFFFF] border-[#74C69D] dark:bg-[#1E2129] dark:border-[#2E3340] space-y-4">
        <RotateCw className="w-8 h-8 text-[#1B4332] dark:text-[#B6FF2E] animate-spin" />
        <p className="text-sm font-semibold text-[#356B52] dark:text-slate-300">
          Loading verification record...
        </p>
      </div>
    );
  }

  if (!record) {
    return (
      <div className="text-center py-16 px-4 rounded-2xl border bg-[#FFFFFF] border-[#74C69D] dark:bg-[#1E2129] dark:border-[#2E3340]">
        <h3 className="text-lg font-bold text-[#1B4332] dark:text-white">Verification record not found</h3>
        <p className="text-xs text-[#356B52] dark:text-slate-400 mt-1 mb-4">
          {fetchError || 'The requested verification record could not be loaded.'}
        </p>
        <button
          onClick={() => navigate('/history')}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-[#1B4332] text-[#D8F3DC] hover:bg-[#163E2D] dark:bg-[#B6FF2E] dark:text-[#181A20] transition-colors cursor-pointer"
        >
          Back to History
        </button>
      </div>
    );
  }

  const claims = record.claims || [];
  const evidenceEntries = claims.flatMap((claim, claimIndex) =>
    (claim.evidence || []).map(evidence => ({ claim, claimIndex, evidence }))
  );
  const judgmentEntries = claims.flatMap((claim, claimIndex) =>
    (claim.judges || []).map(judge => ({ claim, claimIndex, judge }))
  );
  const auditEntries = record.auditTrail || [];

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
      className="space-y-8 pb-16 w-full"
    >
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-xs font-semibold text-[#356B52] dark:text-slate-500">
        <Link to="/verify" className="hover:text-[#1B4332] dark:hover:text-slate-300 transition-colors">
          Verify
        </Link>
        <ChevronRight size={14} />
        <span className="text-[#1B4332] dark:text-slate-200">Result</span>
      </nav>

      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#1B4332] dark:text-white transition-colors">
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

          <p className="text-xs font-medium text-[#356B52] dark:text-slate-300">
            Recorded on {record.dateFormatted || record.timestamp} · {record.claimsCount} claims · {record.evidenceCount} evidence items
          </p>
        </div>

        {/* Top Right Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/verify')}
            className="px-3.5 py-2 rounded-xl border text-xs font-bold flex items-center gap-1.5 shadow-2xs transition-colors cursor-pointer bg-[#FFFFFF] border-[#74C69D] text-[#1B4332] hover:bg-[#D8F3DC] dark:bg-[#23262F] dark:border-[#333742] dark:text-white dark:hover:border-[#B6FF2E]/40"
          >
            <RotateCw size={14} />
            <span>Re-verify</span>
          </button>

          <button
            onClick={() => setSaved(!saved)}
            className={`px-3.5 py-2 rounded-xl border text-xs font-bold flex items-center gap-1.5 shadow-2xs transition-colors cursor-pointer ${
              saved 
                ? 'bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] dark:bg-[#B6FF2E]/15 dark:border-[#B6FF2E]/40 dark:text-[#B6FF2E]' 
                : 'bg-[#FFFFFF] border-[#74C69D] text-[#356B52] dark:bg-[#23262F] dark:border-[#333742] dark:text-white'
            }`}
          >
            <Bookmark size={14} className={saved ? 'fill-current' : ''} />
            <span>{saved ? 'Saved' : 'Save'}</span>
          </button>

          <button
            onClick={handleShare}
            className="px-3.5 py-2 rounded-xl border text-xs font-bold flex items-center gap-1.5 shadow-2xs transition-colors cursor-pointer bg-[#FFFFFF] border-[#74C69D] text-[#356B52] dark:bg-[#23262F] dark:border-[#333742] dark:text-white"
          >
            {copied ? <Check size={14} className="text-[#1B4332] dark:text-[#B6FF2E]" /> : <Share2 size={14} />}
            <span>{copied ? 'Copied' : 'Share'}</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs — each button switches an actual related data panel. */}
      <div role="tablist" aria-label="Verification result sections" className="flex items-center gap-2 border-b overflow-x-auto pb-1 border-[#74C69D] dark:border-[#333742]">
        {tabs.map(tab => {
          const label = tab.id === 'claims'
            ? `Claims (${record.claimsCount})`
            : tab.id === 'evidence'
            ? `Evidence (${record.evidenceCount})`
            : tab.label;

          return (
            <button
              key={tab.id}
              id={`verification-tab-${tab.id}`}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`verification-panel-${tab.id}`}
              tabIndex={activeTab === tab.id ? 0 : -1}
              onClick={() => setActiveTab(tab.id)}
              onKeyDown={event => {
                const index = tabs.findIndex(entry => entry.id === activeTab);
                const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length
                  : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length
                  : event.key === 'Home' ? 0
                  : event.key === 'End' ? tabs.length - 1 : null;
                if (next === null) return;
                event.preventDefault();
                setActiveTab(tabs[next].id);
                document.getElementById(`verification-tab-${tabs[next].id}`)?.focus();
              }}
              className={`px-4 py-2 text-xs font-bold rounded-xl transition-all whitespace-nowrap cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1B4332] dark:focus-visible:outline-[#B6FF2E] ${
                activeTab === tab.id
                  ? 'bg-[#1B4332] text-[#D8F3DC] dark:bg-[#B6FF2E] dark:text-[#181A20] shadow-xs'
                  : 'text-[#356B52] dark:text-slate-400 hover:text-[#1B4332] dark:hover:text-white'
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      <div
        id={`verification-panel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`verification-tab-${activeTab}`}
        tabIndex={0}
        className="space-y-6 focus:outline-none"
      >
      {activeTab === 'overview' && (
        <div className="space-y-6">
      {/* Original Answer Box */}
      <section className="rounded-[2.2rem] p-6 border shadow-xs space-y-2 transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
        <span className="text-xs font-bold uppercase tracking-wider block text-[#356B52] dark:text-slate-400">
          Original Answer Audited
        </span>
        <p className="text-sm md:text-base leading-relaxed font-sans text-[#1B4332] dark:text-slate-200">
          "{record.originalAnswer || record.query}"
        </p>
      </section>

      {/* Verification Summary - 5 Metric Cards */}
      <section className="grid grid-cols-1 min-[400px]:grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-3">
        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-[#356B52] dark:text-slate-400">Claims</p>
          <p className="text-2xl font-black font-mono mt-1 text-[#1B4332] dark:text-white">{record.claimsCount}</p>
        </div>

        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-[#1B4332] dark:text-[#B6FF2E]">Supported</p>
          <p className="text-2xl font-black font-mono mt-1 text-[#1B4332] dark:text-[#B6FF2E]">{record.supportedCount}</p>
        </div>

        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-rose-600 dark:text-rose-400">Contradicted</p>
          <p className="text-2xl font-black font-mono mt-1 text-rose-600 dark:text-rose-400">{record.contradictedCount}</p>
        </div>

        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-[#1B4332] dark:text-[#B6FF2E]">Evidence Sources</p>
          <p className="text-2xl font-black font-mono mt-1 text-[#1B4332] dark:text-[#B6FF2E]">{record.evidenceCount}</p>
        </div>

        <div className="p-4 rounded-2xl border shadow-xs text-center transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
          <p className="text-xs font-bold uppercase text-[#356B52] dark:text-slate-400">Models Used</p>
          <p className="text-sm font-semibold mt-2 text-[#1B4332] dark:text-white">
            {record.modelsUsed?.length ? record.modelsUsed.length : 'Not reported'}
          </p>
        </div>
      </section>

          <section className="rounded-2xl border p-5 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742] space-y-2">
            <h2 className="text-sm font-extrabold text-[#1B4332] dark:text-white">Verification Summary</h2>
            <p className="text-sm leading-relaxed text-[#356B52] dark:text-slate-300">
              {record.summary || 'No verification summary was provided.'}
            </p>
          </section>
        </div>
      )}

      {activeTab === 'claims' && (
        <div className="space-y-6">

      {/* Claims Breakdown */}
      <section className="space-y-4">
        <h3 className="font-extrabold text-lg tracking-tight text-[#1B4332] dark:text-white">
          Claims Breakdown
        </h3>

        <div className="space-y-3">
          {record.claims && record.claims.length > 0 ? (
            record.claims.map((claim, idx) => {
              const isExpanded = expandedClaimIds.includes(claim.id);
              return (
                <div
                  key={claim.id}
                  className="rounded-[2rem] border shadow-xs overflow-hidden transition-all bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]"
                >
                  {/* Claim Row Header */}
                  <div 
                    role="button"
                    tabIndex={0}
                    aria-expanded={isExpanded}
                    aria-controls={`claim-details-${claim.id}`}
                    onClick={() => toggleClaimExpand(claim.id)}
                    onKeyDown={event => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        toggleClaimExpand(claim.id);
                      }
                    }}
                    className="p-5 flex items-start sm:items-center justify-between gap-4 cursor-pointer transition-colors hover:bg-[#D8F3DC] dark:hover:bg-[#2A2E38] focus-visible:outline-2 focus-visible:outline-[#1B4332] dark:focus-visible:outline-[#B6FF2E]"
                  >
                    <div className="flex items-start sm:items-center gap-3.5 min-w-0">
                      <span className="font-mono font-bold text-sm mt-0.5 sm:mt-0 text-[#356B52] dark:text-slate-500">
                        {String(idx + 1).padStart(2, '0')}
                      </span>
                      <p className="text-sm sm:text-base font-bold leading-snug text-[#1B4332] dark:text-white">
                        {claim.statement}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-black uppercase ${
                        claim.status === 'SUPPORTED'
                          ? 'bg-[#74C69D]/30 text-[#1B4332] border border-[#74C69D] dark:bg-[#B6FF2E]/15 dark:text-[#B6FF2E] dark:border-[#B6FF2E]/30'
                          : claim.status === 'CONTRADICTED'
                          ? 'bg-rose-50 text-rose-800 border border-rose-200 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30'
                          : 'bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D] dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30'
                      }`}>
                        {claim.status}
                      </span>

                      <span className="hidden sm:inline text-xs font-semibold text-[#356B52] dark:text-slate-400">
                        {typeof claim.confidence === 'number' ? `${Math.round(claim.confidence * 100)}% confidence` : 'Confidence unavailable'}
                      </span>

                      <span className="text-xs font-bold flex items-center gap-0.5 text-[#1B4332] dark:text-[#B6FF2E]">
                        <span>{isExpanded ? 'Hide' : 'View Details'}</span>
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </span>
                    </div>
                  </div>

                  {/* Expanded Evidence & Provenance Details */}
                  {isExpanded && (
                    <div id={`claim-details-${claim.id}`} className="px-6 pb-6 pt-2 border-t space-y-3 animate-in fade-in border-[#74C69D] bg-[#D8F3DC] dark:border-[#333742] dark:bg-[#181A20]/50">
                      {claim.evidenceSnippet && (
                        <div className="p-4 rounded-xl border space-y-1 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#181A20] dark:border-[#333742]">
                          <span className="text-xs font-bold uppercase tracking-wider text-[#356B52] dark:text-slate-400">
                            Corroborating Excerpt
                          </span>
                          <p className="text-sm leading-relaxed text-[#356B52] dark:text-slate-200">
                            {claim.evidenceSnippet}
                          </p>
                        </div>
                      )}

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <div className="p-3.5 rounded-xl border bg-[#FFFFFF] border-[#74C69D] dark:bg-[#181A20] dark:border-[#333742]">
                          <span className="text-xs font-bold uppercase block mb-1 text-[#356B52] dark:text-slate-400">
                            Primary Source
                          </span>
                          {claim.sourceUrl ? (
                            <a href={claim.sourceUrl} target="_blank" rel="noopener noreferrer"
                               className="text-sm font-bold hover:underline flex items-center gap-1.5 text-[#1B4332] dark:text-[#B6FF2E]">
                              <span>{claim.sourceTitle || 'Source link'}</span>
                              <ExternalLink size={13} />
                            </a>
                          ) : (
                            <span className="text-sm font-semibold text-[#356B52] dark:text-slate-300">
                              {claim.sourceTitle || 'No source link supplied'}
                            </span>
                          )}
                          <span className="text-xs block mt-1 text-[#356B52] dark:text-slate-400">
                            Domain: {claim.domain || 'Not provided'}
                          </span>
                        </div>

                        <div className="p-3.5 rounded-xl border bg-[#FFFFFF] border-[#74C69D] dark:bg-[#181A20] dark:border-[#333742]">
                          <span className="text-xs font-bold uppercase block mb-1 text-[#356B52] dark:text-slate-400">
                            Model Agreement & Judging
                          </span>
                          <p className="text-sm font-semibold text-[#356B52] dark:text-slate-200">
                            Per-model agreement metrics are not available in this record.
                          </p>
                          <span className="text-xs font-bold block mt-1 text-[#1B4332] dark:text-[#B6FF2E]">
                            Refer to the recorded evidence above for details.
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
        </div>
      )}

      {activeTab === 'evidence' && (
        <section className="space-y-4" aria-label="Retrieved evidence">
          <div>
            <h2 className="font-extrabold text-lg tracking-tight text-[#1B4332] dark:text-white">
              Evidence & Sources
            </h2>
            <p className="text-xs text-[#356B52] dark:text-slate-400 mt-1">
              Evidence passages associated with individual claims in this verification.
            </p>
          </div>
          {evidenceEntries.length > 0 ? (
            <div className="grid grid-cols-1 gap-4">
              {evidenceEntries.map(({ claim, claimIndex, evidence }, index) => {
                const href = safeExternalUrl(evidence.sourceUrl);
                return (
                  <article key={`${claim.id}-${evidence.id}-${index}`} className="rounded-2xl border shadow-xs p-5 space-y-3 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1 min-w-0">
                        <p className="text-xs font-bold text-[#1B4332] dark:text-[#B6FF2E]">
                          Claim {String(claimIndex + 1).padStart(2, '0')}
                        </p>
                        <p className="text-xs text-[#356B52] dark:text-slate-300">{claim.statement}</p>
                      </div>
                      <span className="text-[11px] font-bold text-[#356B52] dark:text-slate-400 shrink-0">
                        Evidence {index + 1}
                      </span>
                    </div>
                    <div className="border-t border-[#74C69D] dark:border-[#333742] pt-3">
                      {href ? (
                        <a href={href} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm font-extrabold text-[#1B4332] dark:text-[#B6FF2E] hover:underline">
                          {evidence.sourceTitle || evidence.documentTitle || evidence.publisher || 'Open source'}
                          <ExternalLink size={14} />
                        </a>
                      ) : (
                        <h3 className="text-sm font-extrabold text-[#1B4332] dark:text-white">
                          {evidence.sourceTitle || evidence.documentTitle || evidence.publisher || 'Source not specified'}
                        </h3>
                      )}
                      {(evidence.publisher || evidence.publicationDate) && (
                        <p className="text-xs text-[#356B52] dark:text-slate-400 mt-1">
                          {[evidence.publisher, evidence.publicationDate].filter(Boolean).join(' · ')}
                        </p>
                      )}
                    </div>
                    <p className="text-sm leading-relaxed text-[#356B52] dark:text-slate-200 whitespace-pre-wrap">
                      {evidence.snippet || 'No evidence excerpt was returned.'}
                    </p>
                    {(evidence.evidenceSource || evidence.retrieverName || typeof evidence.relevanceScore === 'number') && (
                      <div className="flex flex-wrap gap-2 text-[11px] font-semibold text-[#356B52] dark:text-slate-300">
                        {evidence.evidenceSource && <span className="rounded-lg bg-[#D8F3DC] dark:bg-[#181A20] px-2 py-1">{evidence.evidenceSource}</span>}
                        {evidence.retrieverName && <span className="rounded-lg bg-[#D8F3DC] dark:bg-[#181A20] px-2 py-1">Retriever: {evidence.retrieverName}</span>}
                        {typeof evidence.relevanceScore === 'number' && <span className="rounded-lg bg-[#D8F3DC] dark:bg-[#181A20] px-2 py-1">Relevance: {evidence.relevanceScore.toFixed(2)}</span>}
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="rounded-2xl border p-6 text-sm text-[#356B52] dark:text-slate-300 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
              {record.evidenceCount > 0
                ? `This record reports ${record.evidenceCount} evidence items, but individual evidence details are not available here.`
                : 'No retrieved evidence was returned for this verification.'}
            </div>
          )}
        </section>
      )}

      {activeTab === 'judgments' && (
        <section className="space-y-4" aria-label="Model judgments">
          <div>
            <h2 className="font-extrabold text-lg tracking-tight text-[#1B4332] dark:text-white">Model Judgments</h2>
            <p className="text-xs text-[#356B52] dark:text-slate-400 mt-1">
              Actual judge evaluations returned for each claim; not inferred from the overall verdict.
            </p>
          </div>
          {judgmentEntries.length > 0 ? (
            <div className="space-y-4">
              {judgmentEntries.map(({ claim, claimIndex, judge }, index) => (
                <article key={`${claim.id}-${judge.id}-${index}`} className="rounded-2xl border shadow-xs p-5 space-y-3 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
                  <div className="flex flex-wrap justify-between items-start gap-3">
                    <div>
                      <p className="text-xs font-bold text-[#1B4332] dark:text-[#B6FF2E]">Claim {String(claimIndex + 1).padStart(2, '0')}</p>
                      <h3 className="font-extrabold text-base text-[#1B4332] dark:text-white">{judge.judgeName}</h3>
                      <p className="text-xs text-[#356B52] dark:text-slate-300 mt-1">{claim.statement}</p>
                    </div>
                    <div className="text-right">
                      <span className="inline-block px-3 py-1 rounded-xl bg-[#D8F3DC] dark:bg-[#181A20] text-[#1B4332] dark:text-[#B6FF2E] font-bold text-xs">
                        {judge.judgment}
                      </span>
                      {typeof judge.confidence === 'number' && (
                        <p className="text-xs text-[#356B52] dark:text-slate-400 mt-1">
                          {Math.round(judge.confidence * 100)}% confidence
                        </p>
                      )}
                    </div>
                  </div>
                  <p className="text-sm leading-relaxed text-[#356B52] dark:text-slate-200 whitespace-pre-wrap">
                    {judge.rationale || 'No judgment rationale was supplied.'}
                  </p>
                  {judge.evidenceReferences && judge.evidenceReferences.length > 0 && (
                    <div className="pt-2 border-t border-[#74C69D] dark:border-[#333742]">
                      <span className="text-xs font-bold text-[#356B52] dark:text-slate-400">Referenced evidence IDs</span>
                      <p className="text-xs font-mono text-[#356B52] dark:text-slate-300 break-all">{judge.evidenceReferences.join(', ')}</p>
                    </div>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border p-6 text-sm text-[#356B52] dark:text-slate-300 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
              No individual model judgments were returned for this verification.
            </div>
          )}
        </section>
      )}

      {activeTab === 'audit' && (
        <section className="space-y-4" aria-label="Verification audit trail">
          <div>
            <h2 className="font-extrabold text-lg tracking-tight text-[#1B4332] dark:text-white">Verification Audit Trail</h2>
            <p className="text-xs text-[#356B52] dark:text-slate-400 mt-1">
              Recorded backend lifecycle events. These are not cryptographically signed attestations.
            </p>
          </div>
          {auditEntries.length > 0 ? (
            <ol className="space-y-3">
              {auditEntries.map((entry, index) => (
                <li key={`${entry.id}-${index}`} className="rounded-2xl border p-5 space-y-2 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
                  <div className="flex flex-wrap justify-between items-start gap-3">
                    <div>
                      <p className="font-extrabold text-sm text-[#1B4332] dark:text-white">{entry.stage || 'Unspecified stage'}</p>
                      <p className="text-xs text-[#356B52] dark:text-slate-400">{entry.eventType || 'Event type not supplied'}</p>
                    </div>
                    <span className="rounded-lg px-2 py-1 text-xs font-extrabold bg-[#D8F3DC] dark:bg-[#181A20] text-[#1B4332] dark:text-[#B6FF2E]">{entry.status}</span>
                  </div>
                  <p className="text-sm text-[#356B52] dark:text-slate-200 whitespace-pre-wrap">{entry.message}</p>
                  {entry.timestamp && (
                    <time dateTime={entry.timestamp} className="text-xs text-[#356B52] dark:text-slate-400">
                      {Number.isNaN(Date.parse(entry.timestamp)) ? entry.timestamp : new Date(entry.timestamp).toLocaleString()}
                    </time>
                  )}
                </li>
              ))}
            </ol>
          ) : (
            <div className="rounded-2xl border p-6 text-sm text-[#356B52] dark:text-slate-300 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
              No backend audit events are available for this verification.
            </div>
          )}
        </section>
      )}
      </div>

    </motion.div>
  );
};
export default VerificationResultPage;
