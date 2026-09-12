'use client';

import React from 'react';
import { ShieldCheck, CheckCircle, Scale, Database, Lock, Eye, BookOpen, Sparkles } from 'lucide-react';
import Link from 'next/link';

export default function AboutPage() {
  return (
    <div className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pastel-lavender-light dark:bg-purple-950/40 border border-pastel-lavender-border text-xs font-semibold text-purple-800 dark:text-purple-300">
          <BookOpen className="w-3.5 h-3.5" />
          <span>Transparency & Methodology</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light tracking-tight">
          How Credence Verifies AI Information
        </h1>
        <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
          Our mission is to replace black-box trust with verifiable evidence. Learn how our multi-stage claim verification engine operates.
        </p>
      </div>

      {/* 4-Stage Verification Pipeline */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light text-center">
          The 4-Stage Verification Pipeline
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-pastel-surface-dark p-6 rounded-3xl border border-pastel-border shadow-pastel space-y-3">
            <div className="w-10 h-10 rounded-2xl bg-pastel-lavender-light text-purple-700 flex items-center justify-center font-bold text-sm">
              01
            </div>
            <h3 className="font-bold text-base text-pastel-charcoal dark:text-white">
              Assertion Segmentation
            </h3>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              When an AI assistant produces an answer, our parser segments natural language text into discrete, testable empirical propositions, discarding non-factual greetings or stylistic prose.
            </p>
          </div>

          <div className="bg-white dark:bg-pastel-surface-dark p-6 rounded-3xl border border-pastel-border shadow-pastel space-y-3">
            <div className="w-10 h-10 rounded-2xl bg-pastel-blue-light text-blue-700 flex items-center justify-center font-bold text-sm">
              02
            </div>
            <h3 className="font-bold text-base text-pastel-charcoal dark:text-white">
              Multi-Index Evidence Retrieval
            </h3>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              Extracted claims are queried against our curated repository of peer-reviewed journals, academic indexes, government datasets, and standards bureau publications using semantic vector embeddings.
            </p>
          </div>

          <div className="bg-white dark:bg-pastel-surface-dark p-6 rounded-3xl border border-pastel-border shadow-pastel space-y-3">
            <div className="w-10 h-10 rounded-2xl bg-pastel-mint-light text-emerald-800 flex items-center justify-center font-bold text-sm">
              03
            </div>
            <h3 className="font-bold text-base text-pastel-charcoal dark:text-white">
              NLI Entailment & Verdict Assessment
            </h3>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              Natural Language Inference models cross-examine each retrieved excerpt against the claim to determine whether the source strictly entails (Verified), contradicts (Refuted), or qualifies (Partially Supported) the assertion.
            </p>
          </div>

          <div className="bg-white dark:bg-pastel-surface-dark p-6 rounded-3xl border border-pastel-border shadow-pastel space-y-3">
            <div className="w-10 h-10 rounded-2xl bg-pastel-peach-light text-amber-800 flex items-center justify-center font-bold text-sm">
              04
            </div>
            <h3 className="font-bold text-base text-pastel-charcoal dark:text-white">
              Calibrated Trust Score Synthesis
            </h3>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              Scores are calibrated from 0 to 100% based on citation relevance, publisher authority weightings, corroboration count, and assertion specificity, providing researchers with actionable clarity.
            </p>
          </div>
        </div>
      </div>

      {/* Core Principles */}
      <div className="bg-pastel-lavender-light/30 dark:bg-pastel-surface-dark/40 rounded-3xl p-8 border border-pastel-border space-y-6">
        <h2 className="text-xl font-bold text-pastel-charcoal dark:text-white text-center">
          Our Commitments to Truth & Integrity
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-purple-700 font-semibold text-xs">
              <Scale className="w-4 h-4" />
              <span>Objective Standard</span>
            </div>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              We do not judge opinions, philosophical queries, or subjective preferences. Our engine exclusively evaluates empirical and verifiable assertions.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-purple-700 font-semibold text-xs">
              <Lock className="w-4 h-4" />
              <span>Zero-Retention Privacy</span>
            </div>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              Your research prompts and private drafts are never used to train public language models. User data is strictly protected.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-purple-700 font-semibold text-xs">
              <Eye className="w-4 h-4" />
              <span>Full Auditability</span>
            </div>
            <p className="text-xs text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              Every score links back to the exact passage and URL citation so you can independently confirm the findings.
            </p>
          </div>
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="text-center pt-4">
        <Link
          href="/chat"
          className="inline-flex items-center space-x-2 px-6 py-3.5 rounded-2xl text-xs sm:text-sm font-semibold bg-pastel-lavender hover:bg-pastel-lavender-hover text-white shadow-pastel"
        >
          <span>Start an Investigation</span>
        </Link>
      </div>
    </div>
  );
}
