'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldCheck, ArrowUpRight } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-pastel-border dark:border-pastel-border-dark bg-white dark:bg-pastel-surface-dark transition-colors mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-pastel-lavender/20 border border-pastel-lavender flex items-center justify-center text-purple-600 dark:text-purple-300">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <span className="font-semibold text-base text-pastel-charcoal dark:text-pastel-charcoal-light">
                Credence
              </span>
            </div>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed max-w-sm">
              An evidence-backed research workspace designed for college students, researchers, analysts, and journalists to verify AI statements, inspect source corroboration, and conduct trustworthy conversations.
            </p>
            <div className="flex items-center space-x-2 pt-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-pastel-mint-light text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 border border-pastel-mint-border">
                WCAG AA Compliant
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-pastel-blue-light text-blue-800 dark:bg-blue-950/40 dark:text-blue-300 border border-pastel-blue-border">
                Multi-Source Index
              </span>
            </div>
          </div>

          {/* Product Links */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-pastel-charcoal dark:text-white">
              Product
            </h4>
            <ul className="space-y-1.5 text-xs text-pastel-slate dark:text-pastel-slate-light">
              <li>
                <Link href="/chat" className="hover:text-pastel-lavender transition-colors">
                  AI Conversation
                </Link>
              </li>
              <li>
                <Link href="/verification" className="hover:text-pastel-lavender transition-colors">
                  Claim Verification
                </Link>
              </li>
              <li>
                <Link href="/extension" className="hover:text-pastel-lavender transition-colors">
                  Browser Extension
                </Link>
              </li>
              <li>
                <Link href="/verification" className="hover:text-pastel-lavender transition-colors">
                  Evidence Inspector
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources & Docs */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-pastel-charcoal dark:text-white">
              Resources
            </h4>
            <ul className="space-y-1.5 text-xs text-pastel-slate dark:text-pastel-slate-light">
              <li>
                <Link href="/about" className="hover:text-pastel-lavender transition-colors">
                  Methodology & Scoring
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-pastel-lavender transition-colors">
                  Authoritative Sources
                </Link>
              </li>
              <li>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-pastel-lavender transition-colors inline-flex items-center space-x-1"
                >
                  <span>Developer API</span>
                  <ArrowUpRight className="w-3 h-3" />
                </a>
              </li>
              <li>
                <Link href="/about" className="hover:text-pastel-lavender transition-colors">
                  Academic Citations
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal / About */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-pastel-charcoal dark:text-white">
              Trust & Legal
            </h4>
            <ul className="space-y-1.5 text-xs text-pastel-slate dark:text-pastel-slate-light">
              <li>
                <Link href="/about" className="hover:text-pastel-lavender transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-pastel-lavender transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-pastel-lavender transition-colors">
                  Ethics Statement
                </Link>
              </li>
              <li>
                <span className="text-[11px] text-pastel-slate/70 dark:text-pastel-slate-light/70">
                  Version 2.4.0 (Pastel Edition)
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-8 pt-6 border-t border-pastel-border/60 dark:border-pastel-border-dark/60 flex flex-col sm:flex-row items-center justify-between text-[11px] text-pastel-slate dark:text-pastel-slate-light">
          <p>© {new Date().getFullYear()} Credence Verification Systems. Built for truth and accuracy in AI research.</p>
          <div className="flex items-center space-x-4 mt-2 sm:mt-0">
            <span>Pastel Visual Identity</span>
            <span>•</span>
            <span>WCAG AA Certified</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
