'use client';

import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, CheckCircle2, FileSearch, Chrome, ChevronLeft, ChevronRight, ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface FeatureSlide {
  number: string;
  title: string;
  tagline: string;
  explanation: string;
  ctaText: string;
  ctaLink: string;
  icon: React.ReactNode;
  preview: React.ReactNode;
}

export const FeatureCarousel: React.FC = () => {
  const [current, setCurrent] = useState<number>(0);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const touchStartX = useRef<number>(0);
  const touchEndX = useRef<number>(0);

  const slides: FeatureSlide[] = [
    {
      number: '01',
      title: 'AI Conversation',
      tagline: 'Research-grade dialogue with multi-model capability',
      explanation: 'Engage with top-tier AI models (GPT-4o, Claude 3.5 Sonnet, Llama 3) via progressive token streaming. Discuss academic hypotheses, literature summaries, and technical claims in an distraction-free pastel environment.',
      ctaText: 'Open Chat Workspace',
      ctaLink: '/chat',
      icon: <MessageSquare className="w-5 h-5 text-purple-600 dark:text-purple-300" />,
      preview: (
        <div className="bg-white dark:bg-pastel-surface-elevated rounded-xl p-4 border border-pastel-border dark:border-pastel-border-dark shadow-xs space-y-2.5 text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-pastel-border/60">
            <span className="font-semibold text-pastel-charcoal dark:text-white">Active Session</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-pastel-lavender-light text-purple-700 dark:bg-purple-950/40 dark:text-purple-300">
              GPT-4o • SSE Streaming
            </span>
          </div>
          <div className="bg-pastel-lavender-light/40 dark:bg-pastel-surface-dark p-2.5 rounded-lg text-pastel-slate dark:text-pastel-slate-light">
            "Summarize the findings of recent clinical trials on mRNA lipid nanoparticles."
          </div>
          <div className="bg-white dark:bg-pastel-surface-elevated p-2.5 rounded-lg border border-pastel-border/80 text-pastel-charcoal dark:text-pastel-charcoal-light">
            Lipid nanoparticles facilitate intracellular delivery by transiently destabilizing the endosomal membrane...
          </div>
        </div>
      ),
    },
    {
      number: '02',
      title: 'Claim Verification',
      tagline: 'Automated claim segmentation & assertion checking',
      explanation: 'Every assistant response is segmented into discrete, testable factual assertions. Each claim is cross-referenced against authoritative factual indexes, generating clear status verdicts: Verified, Partially Supported, Unverified, or Refuted.',
      ctaText: 'Test Claim Engine',
      ctaLink: '/verification',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-300" />,
      preview: (
        <div className="bg-white dark:bg-pastel-surface-elevated rounded-xl p-4 border border-pastel-border dark:border-pastel-border-dark shadow-xs space-y-2.5 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-pastel-charcoal dark:text-white">Extracted Claims</span>
            <span className="text-[10px] text-pastel-mint-dark dark:text-emerald-300 font-bold bg-pastel-mint-light px-2 py-0.5 rounded">
              92% Corroborated
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-pastel-mint-light/40 border border-pastel-mint-border flex items-start space-x-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1 flex-shrink-0" />
            <div>
              <p className="font-medium text-emerald-950 dark:text-emerald-200">Claim 01: Endosomal escape efficiency ranges from 1-2%</p>
              <p className="text-[10px] text-emerald-800 dark:text-emerald-300">Status: Verified • High confidence</p>
            </div>
          </div>
          <div className="p-2.5 rounded-lg bg-pastel-peach-light/40 border border-pastel-peach-border flex items-start space-x-2">
            <div className="w-2 h-2 rounded-full bg-amber-500 mt-1 flex-shrink-0" />
            <div>
              <p className="font-medium text-amber-950 dark:text-amber-200">Claim 02: Ionizable lipids remain non-toxic at standard dosing</p>
              <p className="text-[10px] text-amber-800 dark:text-amber-300">Status: Partially Supported • Caveats noted</p>
            </div>
          </div>
        </div>
      ),
    },
    {
      number: '03',
      title: 'Evidence Inspection',
      tagline: 'Deep academic & scientific citation drilldown',
      explanation: 'Inspect exact source excerpts, publication dates, and empirical relevance scores. Rather than accepting black-box AI outputs, examine corroborating peer-reviewed journals, government datasets, and standards publications.',
      ctaText: 'Explore Evidence View',
      ctaLink: '/verification',
      icon: <FileSearch className="w-5 h-5 text-blue-600 dark:text-blue-300" />,
      preview: (
        <div className="bg-white dark:bg-pastel-surface-elevated rounded-xl p-4 border border-pastel-border dark:border-pastel-border-dark shadow-xs space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-pastel-charcoal dark:text-white">Indexed Citations</span>
            <span className="text-[10px] text-blue-700 bg-pastel-blue-light px-2 py-0.5 rounded">
              3 Primary Sources
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-pastel-blue-light/30 border border-pastel-blue-border space-y-1">
            <div className="flex justify-between items-center text-[10px] font-semibold text-blue-900 dark:text-blue-200">
              <span>Nature Nanotechnology (2023)</span>
              <span>Relevance 94%</span>
            </div>
            <p className="text-[11px] text-pastel-slate dark:text-pastel-slate-light italic">
              "Direct measurements demonstrate release rates under physiological conditions confirm model..."
            </p>
          </div>
          <div className="p-2.5 rounded-lg bg-pastel-bg dark:bg-pastel-surface-dark border border-pastel-border/60 text-[11px] text-pastel-slate">
            <span>PubMed Central ID: PMC8492019 • Peer Reviewed</span>
          </div>
        </div>
      ),
    },
    {
      number: '04',
      title: 'Browser Extension',
      tagline: 'Instant fact-checking across ChatGPT, Claude & the web',
      explanation: 'Verify AI statements directly on any web page with our companion Chrome extension. Highlight any sentence or paragraph to view an instant trust score, claim breakdown, and link to the full research workspace.',
      ctaText: 'Get Companion Extension',
      ctaLink: '/extension',
      icon: <Chrome className="w-5 h-5 text-purple-600 dark:text-purple-300" />,
      preview: (
        <div className="bg-white dark:bg-pastel-surface-elevated rounded-xl p-4 border border-pastel-border dark:border-pastel-border-dark shadow-xs space-y-2 text-xs">
          <div className="flex items-center justify-between pb-1.5 border-b border-pastel-border/60">
            <div className="flex items-center space-x-1.5">
              <div className="w-3 h-3 rounded-full bg-pastel-lavender" />
              <span className="font-bold text-[11px] text-pastel-charcoal dark:text-white">Credence Companion</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-700 bg-pastel-mint-light px-1.5 py-0.5 rounded">Active</span>
          </div>
          <div className="p-2 bg-pastel-bg dark:bg-pastel-surface-dark rounded border border-pastel-border text-[11px] text-pastel-slate">
            "Highlighted: Quantum entanglement occurs when pairs of particles interact..."
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-emerald-600 font-semibold">✓ 91% Verified</span>
            <span className="text-purple-600 font-medium">Open full analysis &rarr;</span>
          </div>
        </div>
      ),
    },
  ];

  // Autoplay (6 seconds) with reduced-motion check
  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion || isPaused) return;

    const interval = setInterval(() => {
      setCurrent((prev) => (prev + 1) % slides.length);
    }, 6000);

    return () => clearInterval(interval);
  }, [isPaused, slides.length]);

  const handlePrev = () => {
    setCurrent((prev) => (prev === 0 ? slides.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrent((prev) => (prev + 1) % slides.length);
  };

  // Touch handlers for mobile swipe
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = () => {
    const diff = touchStartX.current - touchEndX.current;
    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        handleNext();
      } else {
        handlePrev();
      }
    }
  };

  const active = slides[current];

  return (
    <div
      className="relative w-full max-w-5xl mx-auto"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Main Slide Card */}
      <div className="bg-white dark:bg-pastel-surface-dark border border-pastel-border dark:border-pastel-border-dark rounded-3xl p-6 sm:p-10 shadow-pastel transition-all duration-300">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Slide Text Details */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center space-x-3">
              <span className="text-2xl font-bold font-mono text-pastel-lavender">
                {active.number}
              </span>
              <div className="w-8 h-8 rounded-xl bg-pastel-lavender-light dark:bg-pastel-surface-elevated flex items-center justify-center">
                {active.icon}
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-pastel-slate dark:text-pastel-slate-light">
                Feature Deep Dive
              </span>
            </div>

            <h3 className="text-2xl sm:text-3xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light tracking-tight">
              {active.title}
            </h3>

            <p className="text-xs sm:text-sm font-semibold text-purple-700 dark:text-purple-300">
              {active.tagline}
            </p>

            <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              {active.explanation}
            </p>

            <div className="pt-2">
              <Link
                href={active.ctaLink}
                className="inline-flex items-center space-x-2 text-xs font-semibold text-white bg-pastel-lavender hover:bg-pastel-lavender-hover px-4 py-2.5 rounded-xl shadow-pastel transition-all"
              >
                <span>{active.ctaText}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Slide Visual Mockup */}
          <div className="lg:col-span-5 bg-pastel-bg/80 dark:bg-pastel-surface-elevated/40 p-4 rounded-2xl border border-pastel-border/60 dark:border-pastel-border-dark/60">
            {active.preview}
          </div>
        </div>

        {/* Carousel Bottom Bar (Nav buttons & dots) */}
        <div className="mt-8 pt-6 border-t border-pastel-border/60 dark:border-pastel-border-dark/60 flex items-center justify-between">
          {/* Pagination Dots */}
          <div className="flex items-center space-x-2">
            {slides.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrent(idx)}
                aria-label={`Go to slide ${idx + 1}`}
                className={`h-2 rounded-full transition-all ${
                  current === idx
                    ? 'w-7 bg-pastel-lavender'
                    : 'w-2 bg-pastel-border dark:bg-pastel-border-dark hover:bg-pastel-lavender/60'
                }`}
              />
            ))}
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-2">
            <span className="text-[11px] text-pastel-slate dark:text-pastel-slate-light mr-2 hidden sm:inline">
              {isPaused ? '(Autoplay Paused)' : 'Auto-advancing 6s'}
            </span>
            <button
              onClick={handlePrev}
              aria-label="Previous slide"
              className="p-2 rounded-xl border border-pastel-border dark:border-pastel-border-dark bg-white dark:bg-pastel-surface-elevated text-pastel-charcoal dark:text-white hover:bg-pastel-lavender-light hover:border-pastel-lavender transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={handleNext}
              aria-label="Next slide"
              className="p-2 rounded-xl border border-pastel-border dark:border-pastel-border-dark bg-white dark:bg-pastel-surface-elevated text-pastel-charcoal dark:text-white hover:bg-pastel-lavender-light hover:border-pastel-lavender transition-all"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
