'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { HeroPreviewMockup } from '@/components/HeroPreviewMockup';
import { FeatureCarousel } from '@/components/FeatureCarousel';
import { FeatureCard } from '@/components/FeatureCard';
import { QuickVerificationDemo } from '@/components/QuickVerificationDemo';
import {
  ShieldCheck,
  MessageSquare,
  Search,
  CheckCircle2,
  Chrome,
  ArrowRight,
  GraduationCap,
  Microscope,
  Newspaper,
  TrendingUp,
  Award,
  Layers,
  Sparkles,
  Lock,
} from 'lucide-react';

export default function LandingPage() {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    // Parallax scroll listener with reduced-motion check
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="relative overflow-hidden">
      {/* =========================================================================
          PARALLAX BACKGROUND DECORATIVE PASTEL SHAPES (Subtle, slow, accessible)
          ========================================================================= */}
      <div
        className="absolute top-20 left-[10%] w-72 h-72 rounded-full bg-pastel-lavender/15 dark:bg-pastel-lavender/10 blur-3xl pointer-events-none -z-10 transition-transform duration-700 ease-out"
        style={{ transform: `translateY(${scrollY * 0.08}px)` }}
        aria-hidden="true"
      />
      <div
        className="absolute top-96 right-[8%] w-80 h-80 rounded-full bg-pastel-blue/15 dark:bg-pastel-blue/10 blur-3xl pointer-events-none -z-10 transition-transform duration-700 ease-out"
        style={{ transform: `translateY(${scrollY * -0.06}px)` }}
        aria-hidden="true"
      />
      <div
        className="absolute top-[1300px] left-[5%] w-64 h-64 rounded-full bg-pastel-peach/15 dark:bg-pastel-peach/10 blur-3xl pointer-events-none -z-10 transition-transform duration-700 ease-out"
        style={{ transform: `translateY(${scrollY * 0.05}px)` }}
        aria-hidden="true"
      />
      <div
        className="absolute top-[2200px] right-[12%] w-72 h-72 rounded-full bg-pastel-mint/15 dark:bg-pastel-mint/10 blur-3xl pointer-events-none -z-10 transition-transform duration-700 ease-out"
        style={{ transform: `translateY(${scrollY * -0.04}px)` }}
        aria-hidden="true"
      />

      {/* =========================================================================
          SECTION 1: HERO SECTION
          ========================================================================= */}
      <section className="pt-8 sm:pt-16 pb-16 sm:pb-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* HERO LEFT */}
          <div className="lg:col-span-6 space-y-6 text-left">
            {/* Small Badge */}
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-pastel-lavender-light dark:bg-purple-950/50 border border-pastel-lavender-border text-xs font-semibold text-purple-800 dark:text-purple-300 shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-pastel-lavender animate-pulse" />
              <span>AI Information Verification</span>
            </div>

            {/* Main Heading */}
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-pastel-charcoal dark:text-pastel-charcoal-light leading-[1.15]">
              Understand what you can <span className="text-pastel-lavender underline decoration-pastel-lavender/40 decoration-wavy underline-offset-8">trust</span>.
            </h1>

            {/* Supporting Text */}
            <p className="text-sm sm:text-base text-pastel-slate dark:text-pastel-slate-light leading-relaxed max-w-xl">
              Examine AI-generated information, verify assertions against peer-reviewed citations, and inspect corroborating evidence in real-time. Designed for students, researchers, analysts, and professionals seeking truth over hallucination.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2">
              <Link
                href="/chat"
                className="inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-2xl text-xs sm:text-sm font-semibold bg-pastel-lavender hover:bg-pastel-lavender-hover text-white shadow-pastel hover:shadow-pastel-hover transition-all transform active:scale-95"
              >
                <MessageSquare className="w-4 h-4" />
                <span>Start a conversation</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <Link
                href="/verification"
                className="inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-2xl text-xs sm:text-sm font-semibold bg-white dark:bg-pastel-surface-dark border border-pastel-lavender text-purple-700 dark:text-purple-300 hover:bg-pastel-lavender-light dark:hover:bg-pastel-surface-elevated transition-all"
              >
                <Search className="w-4 h-4" />
                <span>Verify content</span>
              </Link>
            </div>

            {/* Trust Badges */}
            <div className="pt-4 border-t border-pastel-border/60 dark:border-pastel-border-dark/60 flex flex-wrap items-center gap-4 text-[11px] text-pastel-slate dark:text-pastel-slate-light">
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-pastel-mint-dark dark:text-emerald-400" />
                <span>Multi-Source Corroboration</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-pastel-lavender-dark dark:text-purple-400" />
                <span>No Black-Box Hallucinations</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Lock className="w-3.5 h-3.5 text-pastel-blue-dark dark:text-blue-400" />
                <span>Privacy Guaranteed</span>
              </div>
            </div>
          </div>

          {/* HERO RIGHT: Product Preview Mockup with 4-phase transition */}
          <div className="lg:col-span-6 w-full">
            <HeroPreviewMockup />
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 2: INTERACTIVE VERIFICATION QUICK DEMO
          ========================================================================= */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <QuickVerificationDemo />
      </section>

      {/* =========================================================================
          SECTION 3: FEATURE SHOWCASE CAROUSEL (Horizontal, 01 - 04)
          ========================================================================= */}
      <section className="py-16 sm:py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pastel-blue-light dark:bg-blue-950/40 border border-pastel-blue-border text-xs font-semibold text-blue-800 dark:text-blue-300">
            <span>Core Capabilities</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light tracking-tight">
            Designed for rigor and precision
          </h2>
          <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
            From streaming multi-model conversations to granular claim extraction and citation inspection, every feature is tailored for critical inquiry.
          </p>
        </div>

        <FeatureCarousel />
      </section>

      {/* =========================================================================
          SECTION 4: FEATURE CARDS GRID (Section 9 Specs)
          ========================================================================= */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-xl mx-auto mb-12 space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light">
            Everything you need to check AI outputs
          </h2>
          <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light">
            Empower your research workflow with transparent, reproducible claim validation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <FeatureCard
            icon={<MessageSquare className="w-5 h-5" />}
            iconBgColor="bg-pastel-lavender-light dark:bg-purple-950/40"
            iconTextColor="text-purple-700 dark:text-purple-300"
            title="Progressive SSE Streaming"
            description="Experience low-latency token streaming from top models without fake typing animations or deceptive pauses."
            tag="Real-Time"
            link="/chat"
          />

          <FeatureCard
            icon={<CheckCircle2 className="w-5 h-5" />}
            iconBgColor="bg-pastel-mint-light dark:bg-emerald-950/40"
            iconTextColor="text-emerald-700 dark:text-emerald-300"
            title="Granular Claim Segmentation"
            description="Deconstruct complex answers into individual verifiable propositions with clear confidence ratings and semantic status tags."
            tag="Verification"
            link="/verification"
          />

          <FeatureCard
            icon={<Search className="w-5 h-5" />}
            iconBgColor="bg-pastel-blue-light dark:bg-blue-950/40"
            iconTextColor="text-blue-700 dark:text-blue-300"
            title="Multi-Source Corroboration"
            description="Cross-reference claims across PubMed, NASA, IEEE, and authoritative fact indexes to detect hallucinated citations."
            tag="Evidence"
            link="/about"
          />

          <FeatureCard
            icon={<Chrome className="w-5 h-5" />}
            iconBgColor="bg-pastel-peach-light dark:bg-amber-950/40"
            iconTextColor="text-amber-700 dark:text-amber-300"
            title="Companion Chrome Extension"
            description="Highlight text across ChatGPT, Claude, Perplexity, or academic PDF viewers to inspect claims without leaving your tab."
            tag="Browser"
            link="/extension"
          />

          <FeatureCard
            icon={<Award className="w-5 h-5" />}
            iconBgColor="bg-pastel-lavender-light dark:bg-purple-950/40"
            iconTextColor="text-purple-700 dark:text-purple-300"
            title="Calibrated Trust Scoring"
            description="Review a weighted numeric trust score (0–100%) grounded in source authority, relevance, and statement specificity."
            tag="Analytics"
            link="/about"
          />

          <FeatureCard
            icon={<Layers className="w-5 h-5" />}
            iconBgColor="bg-pastel-rose-light dark:bg-rose-950/40"
            iconTextColor="text-rose-700 dark:text-rose-300"
            title="Exportable Audit Reports"
            description="Download structured verification dossiers formatted in Markdown or JSON for peer reviews, journalism notes, or academic bibliographies."
            tag="Productivity"
            link="/verification"
          />
        </div>
      </section>

      {/* =========================================================================
          SECTION 5: TARGET AUDIENCE WORKFLOWS
          ========================================================================= */}
      <section className="py-16 sm:py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto bg-pastel-lavender-light/30 dark:bg-pastel-surface-dark/40 rounded-3xl my-8 border border-pastel-border/60 dark:border-pastel-border-dark/60">
        <div className="max-w-3xl mx-auto text-center mb-12 space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pastel-mint-light dark:bg-emerald-950/40 border border-pastel-mint-border text-xs font-semibold text-emerald-900 dark:text-emerald-300">
            <span>Built For Inquisitive Minds</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light">
            Tailored for rigorous analytical workflows
          </h2>
          <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light">
            Whether preparing thesis literature, writing investigative articles, or conducting market diligence.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-pastel-surface-dark p-5 rounded-2xl border border-pastel-border dark:border-pastel-border-dark shadow-2xs space-y-3">
            <div className="w-9 h-9 rounded-xl bg-pastel-lavender-light flex items-center justify-center text-purple-700 dark:text-purple-300">
              <GraduationCap className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-sm text-pastel-charcoal dark:text-pastel-charcoal-light">
              College Students
            </h3>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              Verify lecture summaries, validate citations before submitting coursework, and distinguish verified facts from hallucinated claims.
            </p>
          </div>

          <div className="bg-white dark:bg-pastel-surface-dark p-5 rounded-2xl border border-pastel-border dark:border-pastel-border-dark shadow-2xs space-y-3">
            <div className="w-9 h-9 rounded-xl bg-pastel-blue-light flex items-center justify-center text-blue-700 dark:text-blue-300">
              <Microscope className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-sm text-pastel-charcoal dark:text-pastel-charcoal-light">
              Researchers & Academics
            </h3>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              Audit literature reviews, cross-examine statistical assertions, and inspect original DOI source texts with confidence.
            </p>
          </div>

          <div className="bg-white dark:bg-pastel-surface-dark p-5 rounded-2xl border border-pastel-border dark:border-pastel-border-dark shadow-2xs space-y-3">
            <div className="w-9 h-9 rounded-xl bg-pastel-peach-light flex items-center justify-center text-amber-700 dark:text-amber-300">
              <Newspaper className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-sm text-pastel-charcoal dark:text-pastel-charcoal-light">
              Journalists & Writers
            </h3>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              Verify breaking claims, corroborate background context against primary sources, and protect journalistic integrity.
            </p>
          </div>

          <div className="bg-white dark:bg-pastel-surface-dark p-5 rounded-2xl border border-pastel-border dark:border-pastel-border-dark shadow-2xs space-y-3">
            <div className="w-9 h-9 rounded-xl bg-pastel-mint-light flex items-center justify-center text-emerald-700 dark:text-emerald-300">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-sm text-pastel-charcoal dark:text-pastel-charcoal-light">
              Analysts & Professionals
            </h3>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              Ensure diligence reports, market analyses, and executive briefings are grounded in verifiable, accurate evidence.
            </p>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 6: FINAL CTA BANNER
          ========================================================================= */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto text-center">
        <div className="bg-gradient-to-br from-pastel-lavender-light/80 via-white to-pastel-blue-light/60 dark:from-pastel-surface-dark dark:to-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark rounded-3xl p-8 sm:p-12 shadow-pastel space-y-6">
          <div className="w-12 h-12 rounded-2xl bg-pastel-lavender/20 border border-pastel-lavender flex items-center justify-center mx-auto text-purple-600 dark:text-purple-300">
            <Sparkles className="w-6 h-6" />
          </div>

          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light tracking-tight">
            Start verifying your AI research today.
          </h2>

          <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light max-w-md mx-auto leading-relaxed">
            Free and distraction-free. Test claims, inspect citations, and elevate your standard of factual accuracy.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link
              href="/chat"
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-2xl text-xs sm:text-sm font-semibold bg-pastel-lavender hover:bg-pastel-lavender-hover text-white shadow-pastel hover:shadow-pastel-hover transition-all"
            >
              <MessageSquare className="w-4 h-4" />
              <span>Open Research Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              href="/extension"
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-2xl text-xs sm:text-sm font-semibold bg-white dark:bg-pastel-surface-dark border border-pastel-lavender text-purple-700 dark:text-purple-300 hover:bg-pastel-lavender-light dark:hover:bg-pastel-surface-elevated transition-all"
            >
              <Chrome className="w-4 h-4" />
              <span>Add to Chrome</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
