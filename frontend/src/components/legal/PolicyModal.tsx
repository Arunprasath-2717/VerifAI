import React, { useEffect, useState, useRef } from 'react';
import { X, ShieldAlert, FileText, Lock, ExternalLink, ChevronRight, Check } from 'lucide-react';
import { 
  LEGAL_CONFIG, 
  TERMS_AND_CONDITIONS_SECTIONS, 
  PRIVACY_POLICY_SECTIONS, 
  PolicySection 
} from '../../config/legal';

export type PolicyTab = 'terms' | 'privacy';

interface PolicyModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: PolicyTab;
  onAcceptAndClose?: () => void;
}

export const PolicyModal: React.FC<PolicyModalProps> = ({
  isOpen,
  onClose,
  initialTab = 'terms',
  onAcceptAndClose,
}) => {
  const [activeTab, setActiveTab] = useState<PolicyTab>(initialTab);
  const [selectedSectionId, setSelectedSectionId] = useState<string>('');
  const modalContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  // Handle ESC key to dismiss
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sections: PolicySection[] =
    activeTab === 'terms' ? TERMS_AND_CONDITIONS_SECTIONS : PRIVACY_POLICY_SECTIONS;
  const currentVersion =
    activeTab === 'terms' ? LEGAL_CONFIG.TERMS_VERSION : LEGAL_CONFIG.PRIVACY_POLICY_VERSION;
  const currentEffectiveDate =
    activeTab === 'terms' ? LEGAL_CONFIG.TERMS_EFFECTIVE_DATE : LEGAL_CONFIG.PRIVACY_EFFECTIVE_DATE;
  const policyTitle =
    activeTab === 'terms' ? 'Terms & Conditions' : 'Privacy Policy';

  const scrollToSection = (id: string) => {
    setSelectedSectionId(id);
    const element = document.getElementById(`modal-sec-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="policy-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/65 backdrop-blur-md animate-in fade-in duration-200"
    >
      <div 
        className="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-[#0D1017]/90 backdrop-blur-2xl text-white border border-white/25 rounded-2xl sm:rounded-3xl shadow-[0_30px_90px_-15px_rgba(0,0,0,0.95)] overflow-hidden"
      >
        {/* Top Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/[0.03]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center shadow-inner">
              {activeTab === 'terms' ? (
                <FileText className="w-5 h-5 text-emerald-400" />
              ) : (
                <Lock className="w-5 h-5 text-sky-400" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="policy-modal-title" className="text-lg sm:text-xl font-bold tracking-tight text-white">
                  VerifAI {policyTitle}
                </h2>
                <span className="px-2 py-0.5 text-[11px] font-mono rounded-full bg-white/10 text-white/80 border border-white/15">
                  v{currentVersion}
                </span>
              </div>
              <p className="text-xs text-white/60">
                Effective: {currentEffectiveDate} • Operational Draft
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close policy dialog"
            className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/15 border border-white/10 flex items-center justify-center text-white/70 hover:text-white transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-emerald-400"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 px-6 py-2.5 bg-black/40 border-b border-white/10">
          <button
            type="button"
            onClick={() => {
              setActiveTab('terms');
              setSelectedSectionId('');
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all cursor-pointer ${
              activeTab === 'terms'
                ? 'bg-white/20 text-white shadow-sm border border-white/30 font-semibold'
                : 'text-white/60 hover:text-white/90 hover:bg-white/5'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Terms & Conditions
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('privacy');
              setSelectedSectionId('');
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all cursor-pointer ${
              activeTab === 'privacy'
                ? 'bg-white/20 text-white shadow-sm border border-white/30 font-semibold'
                : 'text-white/60 hover:text-white/90 hover:bg-white/5'
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            Privacy Policy
          </button>

          <div className="ml-auto flex items-center gap-2 text-xs text-white/50">
            <a
              href={activeTab === 'terms' ? '/terms' : '/privacy'}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-white/70 hover:text-white hover:underline transition-colors"
            >
              <span>Full page view</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* Operational Draft Legal Banner */}
        <div className="mx-6 mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 flex items-start gap-3 text-xs text-amber-200/90">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold text-amber-300">Notice for Legal Review: </span>
            This document reflects actual technical functionality and operational safeguards implemented in the VerifAI system. Specific jurisdictional and corporate entity placeholders (e.g. <code className="text-amber-100 bg-amber-950/60 px-1 py-0.5 rounded font-mono">[CONFIGURED_...]</code>) must be finalized by qualified legal counsel prior to formal commercial launch.
          </div>
        </div>

        {/* Modal Body: Split view on desktop with Table of Contents */}
        <div className="flex-1 flex overflow-hidden min-h-0 p-6 gap-6">
          {/* Quick Table of Contents (Desktop sidebar) */}
          <nav 
            aria-label="Table of contents"
            className="hidden md:block w-64 shrink-0 overflow-y-auto pr-2 space-y-1 text-xs text-white/70 border-r border-white/10"
          >
            <div className="text-[11px] font-bold uppercase tracking-wider text-white/40 mb-2 px-2">
              Sections ({sections.length})
            </div>
            {sections.map((sec) => (
              <button
                key={sec.id}
                type="button"
                onClick={() => scrollToSection(sec.id)}
                className={`w-full text-left px-2.5 py-1.5 rounded-lg transition-colors flex items-center justify-between text-xs cursor-pointer ${
                  selectedSectionId === sec.id
                    ? 'bg-white/15 text-white font-medium border border-white/20'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="truncate">{sec.title}</span>
                <ChevronRight className="w-3 h-3 opacity-40 shrink-0 ml-1" />
              </button>
            ))}
          </nav>

          {/* Main Scrollable Document Content */}
          <div 
            ref={modalContentRef} 
            tabIndex={0}
            className="flex-1 overflow-y-auto pr-2 space-y-6 focus:outline-none"
          >
            {sections.map((sec) => (
              <section 
                key={sec.id} 
                id={`modal-sec-${sec.id}`}
                className="scroll-mt-4 p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-colors"
              >
                <h3 className="text-base sm:text-lg font-semibold text-white/95 mb-2.5 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400/80" />
                  {sec.title}
                </h3>
                <div className="space-y-2 text-xs sm:text-[13px] text-white/80 leading-relaxed">
                  {sec.content.map((p, pIdx) => (
                    <p key={pIdx} className="leading-relaxed">
                      {p}
                    </p>
                  ))}
                </div>
              </section>
            ))}

            {/* Document Verification & Config Metadata Block */}
            <div className="p-4 rounded-xl bg-white/[0.04] border border-white/15 text-xs text-white/70 space-y-1.5 font-mono">
              <div className="text-[11px] uppercase tracking-wider text-white/40 font-bold mb-1">
                Document Configuration Metadata
              </div>
              <div>• Active Version: {currentVersion}</div>
              <div>• Effective Date: {currentEffectiveDate}</div>
              <div>• Verification Protocol: VerifAI Deterministic Hash & Claim Classifier</div>
              <div>• Legal Support: {LEGAL_CONFIG.LEGAL_CONTACT_EMAIL}</div>
              <div>• Governing Jurisdiction: {LEGAL_CONFIG.GOVERNING_LAW}</div>
            </div>
          </div>
        </div>

        {/* Modal Bottom Actions */}
        <div className="px-6 py-4 border-t border-white/10 bg-white/[0.02] flex items-center justify-between gap-4">
          <div className="text-xs text-white/60 hidden sm:block">
            Reviewing does not alter your form progress.
          </div>

          <div className="flex items-center gap-3 ml-auto">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs sm:text-sm font-medium text-white/80 hover:text-white bg-white/5 hover:bg-white/15 border border-white/10 transition-all cursor-pointer"
            >
              Close
            </button>
            {onAcceptAndClose && (
              <button
                type="button"
                onClick={() => {
                  onAcceptAndClose();
                  onClose();
                }}
                className="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <Check className="w-4 h-4 stroke-[3]" />
                <span>Agree & Continue</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
