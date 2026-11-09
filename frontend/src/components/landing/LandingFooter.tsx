import React from 'react';
import { ShieldCheck, ArrowUpRight } from 'lucide-react';

interface LandingFooterProps {
  isAuthenticated: boolean;
}

export function LandingFooter({ isAuthenticated }: LandingFooterProps) {
  const accountPath = isAuthenticated ? '/dashboard' : '/login';

  return (
    <footer className="w-full bg-black border-t border-neutral-900 py-16 px-4 sm:px-6 md:px-10 text-white select-none">
      <div className="w-full max-w-[1400px] mx-auto">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-10 pb-12 border-b border-neutral-900">
          <div>
            <div className="inline-flex items-center gap-2.5 text-white mb-3">
              <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-emerald-500/10 border border-white/20">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
              </div>
              <span className="text-lg font-light tracking-tight">
                verif<span className="font-semibold text-emerald-400">ai</span>
              </span>
            </div>
            <p className="text-xs sm:text-sm text-neutral-400 font-light max-w-sm leading-relaxed">
              Autonomous truth & evidence engine. Decoupling AI model consensus from factual ground truth.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-8 text-xs sm:text-sm font-light text-neutral-400">
            <a href="#benefits" className="hover:text-white transition">Key Benefits</a>
            <a href="#pipeline" className="hover:text-white transition">Architecture</a>
            <a href="#inspector" className="hover:text-white transition">Claim Inspector</a>
            <a href="/privacy" className="hover:text-white transition">Privacy Policy</a>
            <a href="/terms" className="hover:text-white transition">Terms of Service</a>
            <a href={accountPath} className="text-emerald-400 hover:text-emerald-300 font-medium transition inline-flex items-center gap-1">
              <span>{isAuthenticated ? 'Dashboard' : 'Sign In'}</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-neutral-600">
          <span>© 2026 VerifAI Technologies Inc. All rights reserved.</span>
          <span>EVIDENCE-FIRST • UNCERTAINTY PRESERVED • ZERO FABRICATIONS</span>
        </div>
      </div>
    </footer>
  );
}
