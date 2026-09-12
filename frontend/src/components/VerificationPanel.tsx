'use client';

import React, { useState, useEffect } from 'react';
import { VerificationResult, Claim, Evidence } from '@/lib/types';
import { ArunVerificationService } from '@/lib/arun-verification-service';
import {
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ExternalLink,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  FileText,
  X,
  Layers,
  Sparkles,
} from 'lucide-react';

interface VerificationPanelProps {
  verificationResult: VerificationResult | null;
  onReverify?: (verificationId: string) => Promise<void>;
  onClose?: () => void;
  isDocked?: boolean;
}

export const VerificationPanel: React.FC<VerificationPanelProps> = ({
  verificationResult,
  onReverify,
  onClose,
  isDocked = true,
}) => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [evidenceMap, setEvidenceMap] = useState<Record<string, Evidence[]>>({});
  const [expandedClaims, setExpandedClaims] = useState<Record<string, boolean>>({});
  const [loadingClaims, setLoadingClaims] = useState<boolean>(false);
  const [isReverifying, setIsReverifying] = useState<boolean>(false);

  useEffect(() => {
    if (verificationResult?.verification_id) {
      loadClaims(verificationResult.verification_id);
    } else {
      setClaims([]);
      setEvidenceMap({});
    }
  }, [verificationResult?.verification_id]);

  const loadClaims = async (verificationId: string) => {
    setLoadingClaims(true);
    try {
      const claimsData = await ArunVerificationService.getClaims(verificationId);
      setClaims(claimsData);

      const evMap: Record<string, Evidence[]> = {};
      const initExpanded: Record<string, boolean> = {};

      for (const claim of claimsData) {
        const ev = await ArunVerificationService.getClaimEvidence(claim.claim_id);
        evMap[claim.claim_id] = ev;
        initExpanded[claim.claim_id] = true; // expanded by default for researchers
      }

      setEvidenceMap(evMap);
      setExpandedClaims(initExpanded);
    } catch (err) {
      console.error('Failed to fetch claims and evidence:', err);
    } finally {
      setLoadingClaims(false);
    }
  };

  const toggleClaimExpand = (claimId: string) => {
    setExpandedClaims((prev) => ({ ...prev, [claimId]: !prev[claimId] }));
  };

  const handleReverifyClick = async () => {
    if (!verificationResult?.verification_id || !onReverify) return;
    setIsReverifying(true);
    try {
      await onReverify(verificationResult.verification_id);
      await loadClaims(verificationResult.verification_id);
    } finally {
      setIsReverifying(false);
    }
  };

  // Pastel Semantic Badge for Verdicts
  const renderVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case 'SUPPORTED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-mint-light text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300 border border-pastel-mint-border">
            <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-600 dark:text-emerald-400" />
            Verified
          </span>
        );
      case 'REFUTED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-rose-light text-rose-900 dark:bg-rose-950/50 dark:text-rose-300 border border-pastel-rose-border">
            <XCircle className="w-3.5 h-3.5 mr-1 text-rose-600 dark:text-rose-400" />
            Failed / Refuted
          </span>
        );
      case 'MIXED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-peach-light text-amber-900 dark:bg-amber-950/50 dark:text-amber-300 border border-pastel-peach-border">
            <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600 dark:text-amber-400" />
            Partially Supported
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-lavender-light text-purple-900 dark:bg-purple-950/50 dark:text-purple-300 border border-pastel-lavender-border">
            <HelpCircle className="w-3.5 h-3.5 mr-1 text-purple-600 dark:text-purple-400" />
            Unverified
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-full bg-pastel-blue-light/20 dark:bg-pastel-surface-dark border-l border-pastel-border dark:border-pastel-border-dark overflow-hidden select-none">
      {/* Panel Header */}
      <div className="p-4 border-b border-pastel-border dark:border-pastel-border-dark bg-white dark:bg-pastel-surface-elevated flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-pastel-lavender/20 border border-pastel-lavender text-purple-700 dark:text-purple-300 flex items-center justify-center">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-pastel-charcoal dark:text-pastel-charcoal-light">
              Verification
            </h3>
            <p className="text-[10px] text-pastel-slate dark:text-pastel-slate-light font-mono truncate max-w-[170px]">
              {verificationResult?.verification_id ? `ID: ${verificationResult.verification_id}` : 'Evidence Inspector'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1">
          {verificationResult && onReverify && (
            <button
              onClick={handleReverifyClick}
              disabled={isReverifying}
              title="Re-verify against index"
              className="p-1.5 rounded-lg text-pastel-slate hover:text-purple-700 hover:bg-pastel-lavender-light dark:hover:bg-pastel-surface-dark transition-colors disabled:opacity-40"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isReverifying ? 'animate-spin text-purple-600' : ''}`} />
            </button>
          )}

          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-pastel-slate hover:text-pastel-charcoal hover:bg-pastel-lavender-light dark:hover:bg-pastel-surface-dark transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Content Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!verificationResult ? (
          /* Empty State */
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-pastel-lavender-light dark:bg-pastel-surface-elevated border border-pastel-lavender-border flex items-center justify-center text-purple-600 dark:text-purple-300 shadow-2xs">
              <Layers className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-pastel-charcoal dark:text-pastel-charcoal-light">
              No verification selected
            </h4>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed max-w-xs">
              Choose an AI response in the conversation to inspect its segmented claims and corroborating evidence.
            </p>
          </div>
        ) : (
          <>
            {/* Overall Verdict & Trust Score Card */}
            <div className="bg-white dark:bg-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark rounded-2xl p-4 shadow-pastel-card space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-pastel-slate dark:text-pastel-slate-light uppercase tracking-wider">
                  Overall Verdict
                </span>
                {renderVerdictBadge(verificationResult.verdict)}
              </div>

              {/* Calibrated Trust Score Meter */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1.5">
                  <span className="font-medium text-pastel-charcoal dark:text-pastel-charcoal-light">
                    Trust Score
                  </span>
                  <span className="font-bold text-sm text-pastel-charcoal dark:text-white">
                    {verificationResult.trust_score}%
                  </span>
                </div>
                <div className="w-full bg-pastel-bg dark:bg-pastel-surface-dark rounded-full h-2.5 overflow-hidden p-0.5 border border-pastel-border dark:border-pastel-border-dark">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      verificationResult.trust_score >= 80
                        ? 'bg-emerald-400 dark:bg-emerald-500'
                        : verificationResult.trust_score >= 50
                        ? 'bg-amber-400 dark:bg-amber-500'
                        : 'bg-rose-400 dark:bg-rose-500'
                    }`}
                    style={{ width: `${Math.min(Math.max(verificationResult.trust_score, 5), 100)}%` }}
                  />
                </div>
              </div>

              {verificationResult.summary && (
                <p className="text-xs text-pastel-slate dark:text-pastel-slate-light pt-2 border-t border-pastel-border/60 dark:border-pastel-border-dark/60 leading-relaxed font-normal">
                  {verificationResult.summary}
                </p>
              )}
            </div>

            {/* Extracted Claims Section */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs font-semibold text-pastel-charcoal dark:text-pastel-charcoal-light uppercase tracking-wider pt-1">
                <span>Extracted Claims ({claims.length})</span>
                <span className="text-[10px] text-pastel-slate dark:text-pastel-slate-light lowercase font-normal">
                  click to expand
                </span>
              </div>

              {loadingClaims ? (
                /* Skeleton Loader */
                <div className="space-y-2 pt-2">
                  <div className="h-14 bg-white dark:bg-pastel-surface-elevated rounded-xl border border-pastel-border dark:border-pastel-border-dark animate-pulse" />
                  <div className="h-14 bg-white dark:bg-pastel-surface-elevated rounded-xl border border-pastel-border dark:border-pastel-border-dark animate-pulse" />
                </div>
              ) : claims.length === 0 ? (
                <div className="p-4 rounded-xl bg-white dark:bg-pastel-surface-elevated border border-pastel-border text-xs text-pastel-slate text-center">
                  No individual claims detected in this response.
                </div>
              ) : (
                <div className="space-y-3">
                  {claims.map((claim, idx) => {
                    const isExpanded = !!expandedClaims[claim.claim_id];
                    const evidenceList = evidenceMap[claim.claim_id] || [];

                    return (
                      <div
                        key={claim.claim_id}
                        className={`bg-white dark:bg-pastel-surface-elevated border rounded-2xl overflow-hidden transition-all shadow-2xs ${
                          isExpanded
                            ? 'border-pastel-lavender dark:border-pastel-lavender shadow-pastel-card'
                            : 'border-pastel-border dark:border-pastel-border-dark hover:border-pastel-lavender/60'
                        }`}
                      >
                        {/* Claim Accordion Header */}
                        <div
                          onClick={() => toggleClaimExpand(claim.claim_id)}
                          className="p-3.5 bg-white dark:bg-pastel-surface-elevated hover:bg-pastel-lavender-light/30 dark:hover:bg-pastel-surface-dark cursor-pointer flex items-start justify-between gap-2"
                        >
                          <div className="flex items-start space-x-2">
                            <span className="text-xs font-bold text-pastel-lavender dark:text-purple-300 font-mono">
                              {idx + 1}.
                            </span>
                            <div>
                              <p className="text-xs font-semibold text-pastel-charcoal dark:text-pastel-charcoal-light leading-snug">
                                {claim.text}
                              </p>
                              <div className="flex items-center space-x-2 mt-1 text-[10px] text-pastel-slate dark:text-pastel-slate-light">
                                <span>Confidence: {Math.round(claim.confidence * 100)}%</span>
                                <span>•</span>
                                <span>Evidence: {evidenceList.length} sources</span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-1.5 flex-shrink-0">
                            {renderVerdictBadge(claim.verdict)}
                            {isExpanded ? (
                              <ChevronDown className="w-4 h-4 text-pastel-slate" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-pastel-slate" />
                            )}
                          </div>
                        </div>

                        {/* Accordion Evidence Drawer */}
                        {isExpanded && (
                          <div className="p-3.5 border-t border-pastel-border/70 dark:border-pastel-border-dark/70 bg-pastel-bg/60 dark:bg-pastel-surface-dark space-y-2.5">
                            <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-pastel-slate dark:text-pastel-slate-light">
                              <span className="flex items-center space-x-1">
                                <FileText className="w-3 h-3 text-purple-600 dark:text-purple-300" />
                                <span>Supporting Citations ({evidenceList.length})</span>
                              </span>
                            </div>

                            {evidenceList.length === 0 ? (
                              <p className="text-[11px] text-pastel-slate italic">
                                No direct citations indexed.
                              </p>
                            ) : (
                              evidenceList.map((ev) => (
                                <div
                                  key={ev.evidence_id}
                                  className="p-3 bg-white dark:bg-pastel-surface-elevated rounded-xl border border-pastel-border dark:border-pastel-border-dark space-y-1.5 shadow-2xs"
                                >
                                  <div className="flex items-center justify-between text-[11px] gap-2">
                                    <a
                                      href={ev.source_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="text-purple-700 dark:text-purple-300 hover:underline flex items-center space-x-1 font-semibold truncate max-w-[200px]"
                                    >
                                      <span>{ev.source_title}</span>
                                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                                    </a>
                                    <span className="text-[10px] font-medium bg-pastel-mint-light text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300 px-1.5 py-0.5 rounded border border-pastel-mint-border">
                                      {Math.round(ev.relevance_score * 100)}% Match
                                    </span>
                                  </div>
                                  <p className="text-[11px] text-pastel-slate dark:text-pastel-slate-light leading-relaxed italic">
                                    "{ev.snippet}"
                                  </p>
                                </div>
                              ))
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Panel Footer */}
      <div className="p-3 border-t border-pastel-border dark:border-pastel-border-dark bg-white dark:bg-pastel-surface-elevated text-[10px] text-pastel-slate dark:text-pastel-slate-light text-center font-medium">
        Cross-referenced against verified evidence repository
      </div>
    </div>
  );
};
