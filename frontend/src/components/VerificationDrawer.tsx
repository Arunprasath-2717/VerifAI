'use client';

import React, { useState, useEffect } from 'react';
import { VerificationResult, Claim, Evidence } from '@/lib/types';
import { ArunVerificationService } from '@/lib/arun-verification-service';
import { X, ShieldCheck, ShieldAlert, AlertTriangle, ExternalLink, RefreshCw, ChevronDown, ChevronRight, CheckCircle, HelpCircle, FileText } from 'lucide-react';

interface VerificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  verificationResult: VerificationResult | null;
  conversationId: string;
  onReverify: (verificationId: string) => void;
}

export const VerificationDrawer: React.FC<VerificationDrawerProps> = ({
  isOpen,
  onClose,
  verificationResult,
  conversationId,
  onReverify,
}) => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [evidenceMap, setEvidenceMap] = useState<Record<string, Evidence[]>>({});
  const [expandedClaims, setExpandedClaims] = useState<Record<string, boolean>>({});
  const [loadingClaims, setLoadingClaims] = useState(false);
  const [isReverifying, setIsReverifying] = useState(false);

  useEffect(() => {
    if (verificationResult?.verification_id) {
      loadClaims(verificationResult.verification_id);
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
        initExpanded[claim.claim_id] = true;
      }

      setEvidenceMap(evMap);
      setExpandedClaims(initExpanded);
    } catch (err) {
      console.error('Failed to load claims & evidence:', err);
    } finally {
      setLoadingClaims(false);
    }
  };

  const toggleClaimExpand = (claimId: string) => {
    setExpandedClaims((prev) => ({ ...prev, [claimId]: !prev[claimId] }));
  };

  const handleReverifyClick = async () => {
    if (!verificationResult?.verification_id) return;
    setIsReverifying(true);
    try {
      await onReverify(verificationResult.verification_id);
      await loadClaims(verificationResult.verification_id);
    } finally {
      setIsReverifying(false);
    }
  };

  if (!isOpen || !verificationResult) return null;

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case 'SUPPORTED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200 shadow-2xs">
            <CheckCircle className="w-3 h-3 mr-1 text-emerald-600" />
            Verified
          </span>
        );
      case 'REFUTED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200 shadow-2xs">
            <ShieldAlert className="w-3 h-3 mr-1 text-rose-600" />
            Refuted
          </span>
        );
      case 'MIXED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200 shadow-2xs">
            <AlertTriangle className="w-3 h-3 mr-1 text-amber-600" />
            Partially Supported
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-100 text-orange-800 border border-orange-200 shadow-2xs">
            <HelpCircle className="w-3 h-3 mr-1 text-orange-600" />
            Unverified
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/30 flex justify-end transition-opacity backdrop-blur-2xs">
      <div className="w-full max-w-md bg-[#f0f4ff] h-full border-l border-indigo-100 flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-indigo-100 flex items-center justify-between bg-white">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-800">Arun Verification Core</h2>
              <p className="text-[10px] text-slate-500 font-mono">
                Verification ID: {verificationResult.verification_id}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Panel Content Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Overall Verdict Card */}
          <div className="bg-white border border-indigo-100 rounded-2xl p-4 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600 font-semibold">Overall Result</span>
              {getVerdictBadge(verificationResult.verdict)}
            </div>

            {/* Trust Score Bar */}
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-500 font-medium">Trust Score</span>
                <span className="font-bold text-slate-800">{verificationResult.trust_score}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden p-0.5 border border-slate-200">
                <div
                  className={`h-1.5 rounded-full transition-all duration-500 ${verificationResult.trust_score >= 80
                      ? 'bg-emerald-500'
                      : verificationResult.trust_score >= 50
                        ? 'bg-amber-500'
                        : 'bg-rose-500'
                    }`}
                  style={{ width: `${verificationResult.trust_score}%` }}
                />
              </div>
            </div>

            {verificationResult.summary && (
              <p className="text-xs text-slate-600 leading-relaxed pt-2 border-t border-slate-100 font-normal">
                {verificationResult.summary}
              </p>
            )}
          </div>

          {/* Action Row */}
          <div className="flex items-center justify-between pt-1">
            <h3 className="text-xs font-bold text-slate-700 tracking-wide uppercase">Claims & Evidence</h3>
            <button
              onClick={handleReverifyClick}
              disabled={isReverifying}
              className="flex items-center space-x-1.5 text-xs bg-white hover:bg-purple-50 text-purple-700 px-3 py-1.5 rounded-xl border border-purple-200 transition-all font-medium shadow-2xs disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isReverifying ? 'animate-spin' : ''}`} />
              <span>{isReverifying ? 'Reverifying...' : 'Reverify'}</span>
            </button>
          </div>

          {/* Claims List */}
          {loadingClaims ? (
            <div className="text-center py-8 text-xs text-slate-500">Fetching claims & evidence from Arun Core...</div>
          ) : claims.length === 0 ? (
            <div className="text-center py-6 text-xs text-slate-500 bg-white border border-indigo-100 rounded-2xl">
              No specific factual claims extracted for this response.
            </div>
          ) : (
            <div className="space-y-3">
              {claims.map((claim, idx) => {
                const isExpanded = expandedClaims[claim.claim_id];
                const evidenceList = evidenceMap[claim.claim_id] || [];

                return (
                  <div
                    key={claim.claim_id}
                    className={`bg-white border rounded-2xl overflow-hidden transition-all shadow-2xs ${isExpanded ? 'border-purple-300 ring-2 ring-purple-100/50' : 'border-indigo-100 hover:border-purple-200'
                      }`}
                  >
                    {/* Claim Header */}
                    <div
                      onClick={() => toggleClaimExpand(claim.claim_id)}
                      className="p-3.5 bg-white hover:bg-purple-50/40 cursor-pointer flex items-start justify-between space-x-2"
                    >
                      <div className="flex items-start space-x-2">
                        <span className="text-xs font-bold text-purple-600">{idx + 1}.</span>
                        <p className="text-xs text-slate-800 font-semibold leading-snug">{claim.text}</p>
                      </div>
                      <div className="flex items-center space-x-2 flex-shrink-0">
                        {getVerdictBadge(claim.verdict)}
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {/* Evidence Drilldown */}
                    {isExpanded && (
                      <div className="p-3.5 border-t border-purple-100 space-y-2.5 bg-purple-50/20">
                        <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600">
                          <span className="flex items-center space-x-1">
                            <FileText className="w-3 h-3 text-purple-600" />
                            <span>Supporting Evidence ({evidenceList.length})</span>
                          </span>
                        </div>
                        {evidenceList.length === 0 ? (
                          <p className="text-[11px] text-slate-400 italic">No direct evidence items indexed.</p>
                        ) : (
                          evidenceList.map((ev) => (
                            <div
                              key={ev.evidence_id}
                              className="p-3 bg-white rounded-xl border border-slate-200/80 space-y-1.5 shadow-2xs"
                            >
                              <div className="flex items-center justify-between text-[11px]">
                                <a
                                  href={ev.source_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-purple-700 hover:underline flex items-center space-x-1 font-semibold truncate max-w-[220px]"
                                >
                                  <span>{ev.source_title}</span>
                                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                                </a>
                                <span className="text-emerald-800 text-[10px] font-medium bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                                  Relevance: {Math.round(ev.relevance_score * 100)}%
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-600 leading-normal">{ev.snippet}</p>
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

        {/* Footer Note */}
        <div className="p-3 border-t border-indigo-100 bg-white text-[10px] text-slate-500 text-center font-medium">
          Verification claims and trust metrics calculated by Arun Core Verification Module.
        </div>
      </div>
    </div>
  );
};
