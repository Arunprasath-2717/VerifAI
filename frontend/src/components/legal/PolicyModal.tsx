import React, { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Check, ChevronRight, FileText, LockKeyhole, ShieldCheck, X } from 'lucide-react';
import {
  LEGAL_CONFIG, TERMS_AND_CONDITIONS_SECTIONS, PRIVACY_POLICY_SECTIONS,
  type PolicySection,
} from '../../config/legal';
import './LegalExperience.css';

export type PolicyTab = 'terms' | 'privacy';

interface PolicyModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: PolicyTab;
  onAcceptAndClose?: () => void;
}

/** Policy copy remains sourced from the existing versioned legal configuration. */
export const PolicyModal: React.FC<PolicyModalProps> = ({
  isOpen, onClose, initialTab = 'terms', onAcceptAndClose,
}) => {
  const [activeTab, setActiveTab] = useState<PolicyTab>(initialTab);
  const [selectedSectionId, setSelectedSectionId] = useState('');
  const dialogRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const openerRef = useRef<Element | null>(null);

  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      setSelectedSectionId('');
    }
  }, [isOpen, initialTab]);

  useEffect(() => {
    if (!isOpen) return;
    openerRef.current = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    dialogRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
      if (event.key !== 'Tab') return;
      const controls = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      ).filter(node => node.getClientRects().length > 0);
      if (!controls.length) return;
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKeyDown);
      if (openerRef.current instanceof HTMLElement) openerRef.current.focus();
    };
  }, [isOpen, onClose]);

  const sections: PolicySection[] = activeTab === 'terms'
    ? TERMS_AND_CONDITIONS_SECTIONS : PRIVACY_POLICY_SECTIONS;
  const title = activeTab === 'terms' ? 'Terms of Service' : 'Privacy Policy';
  const version = activeTab === 'terms'
    ? LEGAL_CONFIG.TERMS_VERSION : LEGAL_CONFIG.PRIVACY_POLICY_VERSION;
  const effective = activeTab === 'terms'
    ? LEGAL_CONFIG.TERMS_EFFECTIVE_DATE : LEGAL_CONFIG.PRIVACY_EFFECTIVE_DATE;

  const changeTab = (tab: PolicyTab) => {
    setActiveTab(tab);
    setSelectedSectionId('');
    scrollRef.current?.scrollTo({ top: 0 });
  };

  const goToSection = (id: string) => {
    setSelectedSectionId(id);
    const target = document.getElementById('policy-section-' + activeTab + '-' + id);
    const scroller = scrollRef.current;
    if (target && scroller) {
      scroller.scrollTo({
        top: target.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop - 12,
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="legal-studio__overlay">
      <div
        role="dialog" aria-modal="true"
        aria-labelledby="policy-modal-title" aria-describedby="policy-modal-summary"
        tabIndex={-1} ref={dialogRef} className="legal-studio__modal"
      >
        <aside className="legal-studio__illustration-panel">
          <div className="legal-studio__aside-brand">
            <span className="legal-studio__brand-symbol"><ShieldCheck size={19}/></span>
            <span>Verif<span>AI</span></span>
          </div>
          <div className="legal-studio__art">
            <img src="/auth/verifai-trust-art.webp" alt="Evidence documents and a green verification shield"/>
          </div>
          <div className="legal-studio__aside-bottom">
            <span>POLICY LIBRARY / 2026</span>
            <p>Clarity in every<br/><em>commitment.</em></p>
            <span>Understand your rights before you continue.</span>
          </div>
        </aside>

        <div className="legal-studio__reader">
          <div className="legal-studio__topline">
            <span className="legal-studio__eyebrow">VERIFAI <ChevronRight size={13}/> TRUST & ACCOUNTABILITY</span>
            <button type="button" onClick={onClose} className="legal-studio__close" aria-label="Close policy dialog">
              <X size={20}/>
            </button>
          </div>

          <div className="legal-studio__tab-row" role="tablist" aria-label="Legal documents">
            <button type="button" role="tab" aria-selected={activeTab === 'terms'}
              className={activeTab === 'terms' ? 'legal-studio__tab is-active' : 'legal-studio__tab'}
              onClick={() => changeTab('terms')}>
              <FileText size={16}/> Terms of Service
            </button>
            <button type="button" role="tab" aria-selected={activeTab === 'privacy'}
              className={activeTab === 'privacy' ? 'legal-studio__tab is-active' : 'legal-studio__tab'}
              onClick={() => changeTab('privacy')}>
              <LockKeyhole size={16}/> Privacy Policy
            </button>
            <a className="legal-studio__newtab" href={activeTab === 'terms' ? '/terms' : '/privacy'}
              target="_blank" rel="noopener noreferrer" aria-label={'Open ' + title + ' full page'}>
              <ArrowUpRight size={18}/>
            </a>
          </div>

          <div className="legal-studio__reading-pane" ref={scrollRef} role="tabpanel" tabIndex={0}>
            <div className="legal-studio__document-heading">
              <div className="legal-studio__numberline">
                <span>LEGAL DOCUMENT</span><span>{activeTab === 'terms' ? '01 / 02' : '02 / 02'}</span>
              </div>
              <h2 id="policy-modal-title">{title}<span>.</span></h2>
              <p id="policy-modal-summary">The policies governing your VerifAI account, presented clearly in one place.</p>
              <div className="legal-studio__metadata">
                <span>Effective {effective}</span><span>Version {version}</span><span>{sections.length} sections</span>
              </div>
            </div>

            <div className="legal-studio__draft-note">
              <span className="legal-studio__note-dot"/>
              <p><strong>Operational draft · legal review required.</strong> Configuration placeholders, jurisdiction, and entity details must be finalized by qualified legal counsel before commercial launch.</p>
            </div>

            <nav className="legal-studio__toc" aria-label={title + ' sections'}>
              {sections.map((section, index) => (
                <button key={section.id} type="button"
                  className={selectedSectionId === section.id ? 'is-active' : ''}
                  onClick={() => goToSection(section.id)}>
                  <span>{String(index + 1).padStart(2, '0')}</span>{section.title.replace(/^\d+\.\s*/, '')}
                </button>
              ))}
            </nav>

            <div className="legal-studio__articles">
              {sections.map((section, index) => (
                <section key={section.id}
                  id={'policy-section-' + activeTab + '-' + section.id}
                  className="legal-studio__article">
                  <div className="legal-studio__article-number">{String(index + 1).padStart(2, '0')}</div>
                  <div>
                    <h3>{section.title.replace(/^\d+\.\s*/, '')}</h3>
                    {section.content.map((paragraph, i) => <p key={i}>{paragraph}</p>)}
                  </div>
                </section>
              ))}
            </div>

            <div className="legal-studio__document-end">
              <ShieldCheck size={17}/>
              <span>Questions? Contact {LEGAL_CONFIG.LEGAL_CONTACT_EMAIL}</span>
            </div>
          </div>

          <footer className="legal-studio__actions">
            <span>Reviewing policies won't reset your signup form.</span>
            <div>
              <button type="button" className="legal-studio__cancel" onClick={onClose}>Close</button>
              {onAcceptAndClose && (
                <button type="button" className="legal-studio__confirm"
                  onClick={() => { onAcceptAndClose(); onClose(); }}>
                  <Check size={17}/> Agree & Continue
                </button>
              )}
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
};
