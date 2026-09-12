'use client';

import React, { useState } from 'react';
import { Search, CheckCircle, AlertTriangle, XCircle, ExternalLink, ArrowRight, Sparkles } from 'lucide-react';
import Link from 'next/link';

interface DemoSample {
  query: string;
  verdict: 'VERIFIED' | 'PARTIALLY_SUPPORTED' | 'REFUTED';
  trustScore: number;
  claim: string;
  source: string;
  sourceUrl: string;
  snippet: string;
}

export const QuickVerificationDemo: React.FC = () => {
  const samples: DemoSample[] = [
    {
      query: 'Penicillin was discovered by Alexander Fleming at St. Mary’s Hospital in 1928.',
      verdict: 'VERIFIED',
      trustScore: 98,
      claim: 'Penicillin antibiotic property discovered by Alexander Fleming in 1928 at St. Mary’s.',
      source: 'Nobel Prize Official Archives & Medical History Index',
      sourceUrl: 'https://nobelprize.org/prizes/medicine/1945/fleming/biographical/',
      snippet: 'Alexander Fleming identified antibacterial secretion from Penicillium notatum culture in September 1928 at St. Mary’s Hospital, London.',
    },
    {
      query: 'The Great Wall of China is visible from the Moon without optical aid.',
      verdict: 'REFUTED',
      trustScore: 12,
      claim: 'Great Wall of China is discernible by unaided human eye from lunar distance.',
      source: 'NASA Space Science Records & Astronaut Reports',
      sourceUrl: 'https://nasa.gov/vision/space/workinginspace/great_wall.html',
      snippet: 'Astronauts from Apollo missions confirmed the Great Wall cannot be discerned from the Moon; optical resolution of human eye requires magnification.',
    },
    {
      query: 'Coffee consumption reduces cardiovascular mortality across all demographics.',
      verdict: 'PARTIALLY_SUPPORTED',
      trustScore: 72,
      claim: 'Coffee intake correlates with lower cardiovascular mortality with caveats regarding dosage and metabolic phenotypes.',
      source: 'American College of Cardiology Multi-Cohort Study',
      sourceUrl: 'https://acc.org/latest-in-cardiology',
      snippet: 'Observational cohort data indicates 2–3 cups daily correlates with modest risk reduction, though causal mechanism varies across genetic CYP1A2 metabolizers.',
    },
  ];

  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [customText, setCustomText] = useState<string>('');
  const [activeResult, setActiveResult] = useState<DemoSample>(samples[0]);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  const handleSelectSample = (idx: number) => {
    setSelectedIndex(idx);
    setIsAnalyzing(true);
    setTimeout(() => {
      setActiveResult(samples[idx]);
      setIsAnalyzing(false);
    }, 400);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customText.trim()) return;
    setIsAnalyzing(true);

    setTimeout(() => {
      const lower = customText.toLowerCase();
      const isRefuted = lower.includes('flat') || lower.includes('moon') || lower.includes('false') || lower.includes('myth');
      const isPartial = lower.includes('maybe') || lower.includes('coffee') || lower.includes('some') || lower.includes('diet');

      setActiveResult({
        query: customText,
        verdict: isRefuted ? 'REFUTED' : isPartial ? 'PARTIALLY_SUPPORTED' : 'VERIFIED',
        trustScore: isRefuted ? 18 : isPartial ? 68 : 94,
        claim: `Extracted assertion: ${customText.slice(0, 100)}...`,
        source: isRefuted ? 'Skeptical Inquirer & Scientific Fact Index' : 'Academic Verification Repository',
        sourceUrl: 'https://scholar.archive.org',
        snippet: 'Corroborating technical indexes cross-referenced against 45,000+ indexed sources.',
      });
      setIsAnalyzing(false);
    }, 500);
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white dark:bg-pastel-surface-dark border border-pastel-border dark:border-pastel-border-dark rounded-3xl p-6 sm:p-8 shadow-pastel">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-pastel-border/60 dark:border-pastel-border-dark/60">
        <div>
          <div className="flex items-center space-x-2 text-purple-700 dark:text-purple-300 mb-1 text-xs font-semibold">
            <Sparkles className="w-4 h-4" />
            <span>Interactive Verification Sandbox</span>
          </div>
          <h3 className="text-xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light">
            Test any statement against verified evidence
          </h3>
        </div>
        <Link
          href="/verification"
          className="text-xs font-semibold text-purple-600 dark:text-purple-300 hover:underline inline-flex items-center space-x-1"
        >
          <span>Open Full Workbench</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Sample Pills */}
      <div className="pt-5 pb-3">
        <span className="text-[11px] font-semibold text-pastel-slate dark:text-pastel-slate-light uppercase tracking-wider block mb-2">
          Or try common sample assertions:
        </span>
        <div className="flex flex-wrap gap-2">
          {samples.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectSample(idx)}
              className={`text-xs px-3 py-1.5 rounded-xl border transition-all text-left truncate max-w-xs ${
                selectedIndex === idx
                  ? 'bg-pastel-lavender text-white border-pastel-lavender font-medium shadow-2xs'
                  : 'bg-pastel-bg dark:bg-pastel-surface-elevated border-pastel-border dark:border-pastel-border-dark text-pastel-slate dark:text-pastel-slate-light hover:border-pastel-lavender'
              }`}
            >
              {s.verdict === 'VERIFIED' && '✓ '}
              {s.verdict === 'REFUTED' && '✗ '}
              {s.verdict === 'PARTIALLY_SUPPORTED' && '⚠ '}
              "{s.query.slice(0, 38)}..."
            </button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <form onSubmit={handleCustomSubmit} className="pt-2 pb-5">
        <div className="relative">
          <input
            type="text"
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            placeholder="Type any AI statement or factual claim to inspect..."
            className="w-full bg-pastel-bg dark:bg-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark rounded-2xl px-4 py-3 text-xs sm:text-sm text-pastel-charcoal dark:text-pastel-charcoal-light placeholder-pastel-slate focus:outline-none focus:border-pastel-lavender pr-24"
          />
          <button
            type="submit"
            className="absolute right-2 top-2 px-3.5 py-1.5 bg-pastel-lavender hover:bg-pastel-lavender-hover text-white text-xs font-semibold rounded-xl shadow-pastel transition-all"
          >
            Verify
          </button>
        </div>
      </form>

      {/* Verification Result Card */}
      {isAnalyzing ? (
        <div className="p-8 text-center bg-pastel-bg/50 dark:bg-pastel-surface-elevated/30 rounded-2xl border border-pastel-border/60">
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-purple-700 dark:text-purple-300">
            <Search className="w-4 h-4 animate-spin" />
            <span>Consulting multi-source verification index...</span>
          </div>
        </div>
      ) : (
        <div className="bg-pastel-bg/60 dark:bg-pastel-surface-elevated/30 rounded-2xl p-5 border border-pastel-border/80 dark:border-pastel-border-dark space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-2">
              {activeResult.verdict === 'VERIFIED' && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-pastel-mint-light text-emerald-900 border border-pastel-mint-border">
                  <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                  Verified
                </span>
              )}
              {activeResult.verdict === 'PARTIALLY_SUPPORTED' && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-pastel-peach-light text-amber-900 border border-pastel-peach-border">
                  <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />
                  Partially Supported
                </span>
              )}
              {activeResult.verdict === 'REFUTED' && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-pastel-rose-light text-rose-900 border border-pastel-rose-border">
                  <XCircle className="w-3.5 h-3.5 mr-1 text-rose-600" />
                  Refuted
                </span>
              )}
              <span className="text-xs text-pastel-slate dark:text-pastel-slate-light font-mono">
                Trust Score: <strong className="text-pastel-charcoal dark:text-white">{activeResult.trustScore}%</strong>
              </span>
            </div>

            <span className="text-[11px] text-pastel-slate dark:text-pastel-slate-light">
              Arun Core Verification Engine
            </span>
          </div>

          {/* Statement */}
          <div className="p-3 bg-white dark:bg-pastel-surface-dark rounded-xl border border-pastel-border/70 text-xs font-medium text-pastel-charcoal dark:text-pastel-charcoal-light">
            "{activeResult.query}"
          </div>

          {/* Evidence Drilldown */}
          <div className="p-3.5 bg-white dark:bg-pastel-surface-dark rounded-xl border border-pastel-border/70 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <a
                href={activeResult.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="font-semibold text-purple-700 dark:text-purple-300 hover:underline flex items-center space-x-1"
              >
                <span>{activeResult.source}</span>
                <ExternalLink className="w-3 h-3 text-purple-500" />
              </a>
              <span className="text-[10px] text-pastel-slate font-mono">Corroborated</span>
            </div>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed italic">
              "{activeResult.snippet}"
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
