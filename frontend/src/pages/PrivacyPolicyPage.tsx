import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  ArrowLeft, 
  Lock, 
  AlertTriangle, 
  ExternalLink, 
  ChevronRight, 
  Calendar, 
  FileText, 
  Globe, 
  Database, 
  Layers 
} from 'lucide-react';
import { LEGAL_CONFIG, PRIVACY_POLICY_SECTIONS } from '../config/legal';

interface PrivacyPolicyPageProps {
  theme?: 'light' | 'dark';
}

export const PrivacyPolicyPage: React.FC<PrivacyPolicyPageProps> = () => {
  const navigate = useNavigate();
  const [activeSectionId, setActiveSectionId] = useState<string>('');

  const scrollToSection = (id: string) => {
    setActiveSectionId(id);
    const element = document.getElementById(`privacy-sec-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0D14] text-white selection:bg-sky-500/30 font-sans">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 w-full backdrop-blur-xl bg-[#0A0D14]/85 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/signup')}
              className="flex items-center gap-2 text-xs sm:text-sm text-white/70 hover:text-white transition-colors py-1.5 px-3 rounded-lg hover:bg-white/5 cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Sign Up</span>
            </button>
            <div className="h-4 w-[1px] bg-white/20 hidden sm:block" />
            <Link to="/signup" className="flex items-center gap-2 text-white font-semibold tracking-tight">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-sky-500 to-indigo-400 flex items-center justify-center shadow-md">
                <ShieldCheck className="w-4 h-4 text-black" />
              </div>
              <span className="text-base sm:text-lg">VerifAI</span>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 text-xs font-mono rounded-full bg-white/10 text-white/90 border border-white/15">
              Privacy v{LEGAL_CONFIG.PRIVACY_POLICY_VERSION}
            </span>
            <Link
              to="/terms"
              className="text-xs sm:text-sm text-white/60 hover:text-white transition-colors hidden sm:inline-flex items-center gap-1"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Terms & Conditions</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div className="relative border-b border-white/10 bg-gradient-to-b from-white/[0.04] to-transparent py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-300 text-xs font-medium">
            <Lock className="w-3.5 h-3.5" />
            <span>Privacy Governance & Data Practices</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white drop-shadow-sm">
            Privacy Policy
          </h1>

          <div className="flex flex-wrap items-center justify-center gap-4 text-xs sm:text-sm text-white/60 pt-1">
            <span className="flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-sky-400" />
              Effective Date: <strong className="text-white/90">{LEGAL_CONFIG.PRIVACY_EFFECTIVE_DATE}</strong>
            </span>
            <span>•</span>
            <span>Version: <code className="font-mono text-sky-300">v{LEGAL_CONFIG.PRIVACY_POLICY_VERSION}</code></span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Globe className="w-3.5 h-3.5 text-emerald-400" />
              Jurisdiction: <code className="font-mono text-white/80">{LEGAL_CONFIG.GOVERNING_LAW}</code>
            </span>
          </div>

          {/* Operational Draft Notice Callout */}
          <div className="mt-6 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-left flex items-start gap-3.5 text-xs sm:text-sm text-amber-200/90 shadow-lg">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="font-bold text-amber-300 uppercase tracking-wide text-xs">
                Operational Disclosure & Review Notice
              </div>
              <p className="leading-relaxed text-amber-100/90">
                This Privacy Policy accurately reflects actual data storage in PostgreSQL, authentication exchange with Firebase RS256 JWTs, browser localStorage usage, and verification evidence retrieval. Institutional contact points and minimum age criteria designated by <code className="bg-amber-950/70 text-amber-300 px-1.5 py-0.5 rounded font-mono">[CONFIGURED_...]</code> must be validated by the operating organization.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Layout with Sticky Table of Contents */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Sidebar Navigation */}
          <aside className="lg:col-span-4 hidden lg:block">
            <div className="sticky top-24 p-5 rounded-2xl bg-white/[0.03] border border-white/10 backdrop-blur-md space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-white/50 px-2 flex items-center justify-between">
                <span>Privacy Sections</span>
                <span className="text-[10px] font-mono bg-white/10 px-2 py-0.5 rounded-full">{PRIVACY_POLICY_SECTIONS.length} Sections</span>
              </div>
              <nav aria-label="Privacy table of contents" className="space-y-1 max-h-[calc(100vh-180px)] overflow-y-auto pr-1">
                {PRIVACY_POLICY_SECTIONS.map((sec) => (
                  <button
                    key={sec.id}
                    onClick={() => scrollToSection(sec.id)}
                    className={`w-full text-left px-3 py-2 rounded-xl text-xs transition-all flex items-center justify-between cursor-pointer ${
                      activeSectionId === sec.id
                        ? 'bg-sky-500/20 text-sky-300 font-semibold border border-sky-500/30'
                        : 'text-white/70 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span className="truncate">{sec.title}</span>
                    <ChevronRight className="w-3.5 h-3.5 opacity-40 shrink-0 ml-1" />
                  </button>
                ))}
              </nav>

              <div className="pt-3 border-t border-white/10 flex flex-col gap-2">
                <Link
                  to="/terms"
                  className="flex items-center justify-between text-xs text-emerald-400 hover:text-emerald-300 p-2 rounded-lg hover:bg-emerald-500/10 transition-colors"
                >
                  <span className="flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5" />
                    Read Terms & Conditions
                  </span>
                  <ExternalLink className="w-3 h-3" />
                </Link>
                <button
                  onClick={() => navigate('/signup')}
                  className="w-full py-2 px-3 rounded-xl text-xs font-semibold text-white bg-white/10 hover:bg-white/20 border border-white/20 transition-all text-center cursor-pointer"
                >
                  Return to Signup Form
                </button>
              </div>
            </div>
          </aside>

          {/* Document Body Sections */}
          <article className="lg:col-span-8 space-y-8">
            {PRIVACY_POLICY_SECTIONS.map((section) => (
              <section
                key={section.id}
                id={`privacy-sec-${section.id}`}
                className="scroll-mt-24 p-6 sm:p-8 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-white/20 transition-all space-y-4 shadow-sm"
              >
                <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.6)]" />
                  {section.title}
                </h2>
                <div className="space-y-3 text-sm sm:text-[15px] text-white/80 leading-relaxed font-normal">
                  {section.content.map((paragraph, pIdx) => (
                    <p key={pIdx} className="leading-relaxed">
                      {paragraph}
                    </p>
                  ))}
                </div>
              </section>
            ))}

            {/* Architecture Disclosure Matrix */}
            <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-white/[0.05] to-white/[0.02] border border-white/20 space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Database className="w-5 h-5 text-sky-400" />
                <span>Technical Implementation & Storage Transparency</span>
              </h3>
              <p className="text-xs sm:text-sm text-white/70 leading-relaxed">
                VerifAI maintains strict separation between telemetry data, user knowledge assets, and model inference contexts.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs font-mono text-white/80">
                <div className="p-3 rounded-xl bg-black/40 border border-white/10">
                  <span className="text-white/40 block text-[10px] uppercase">Storage Engine</span>
                  <span>PostgreSQL + SQLAlchemy Async Session</span>
                </div>
                <div className="p-3 rounded-xl bg-black/40 border border-white/10">
                  <span className="text-white/40 block text-[10px] uppercase">Authentication Cryptography</span>
                  <span>Firebase RS256 JWT Verification</span>
                </div>
                <div className="p-3 rounded-xl bg-black/40 border border-white/10">
                  <span className="text-white/40 block text-[10px] uppercase">Client Storage</span>
                  <span>localStorage (`auth_token`, `verifai-theme`)</span>
                </div>
                <div className="p-3 rounded-xl bg-black/40 border border-white/10">
                  <span className="text-white/40 block text-[10px] uppercase">Consent Record Schema</span>
                  <span>`user_consents` (UTC timestamped)</span>
                </div>
              </div>
            </div>
          </article>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8 bg-[#07090E] text-xs text-white/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            © {new Date().getFullYear()} VerifAI Intelligent Systems. All rights reserved.
          </div>
          <div className="flex items-center gap-6">
            <Link to="/terms" className="hover:text-white transition-colors">
              Terms & Conditions
            </Link>
            <Link to="/privacy" className="text-white hover:underline">
              Privacy Policy
            </Link>
            <Link to="/signup" className="hover:text-white transition-colors">
              Sign Up
            </Link>
            <Link to="/login" className="hover:text-white transition-colors">
              Sign In
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PrivacyPolicyPage;
