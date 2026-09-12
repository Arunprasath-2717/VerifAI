'use client';

import React, { useState } from 'react';
import {
  Chrome,
  ShieldCheck,
  CheckCircle,
  ExternalLink,
  Sparkles,
  Layers,
  ArrowRight,
  Download,
  Terminal,
} from 'lucide-react';
import Link from 'next/link';

export default function ExtensionPage() {
  const [sampleText, setSampleText] = useState('Superconducting qubits experience decoherence primarily due to high-frequency dielectric loss in amorphous substrate interfaces.');
  const [isVerifying, setIsVerifying] = useState(false);
  const [showResult, setShowResult] = useState(true);

  const handleSimulate = () => {
    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      setShowResult(true);
    }, 500);
  };

  return (
    <div className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pastel-lavender-light dark:bg-purple-950/40 border border-pastel-lavender-border text-xs font-semibold text-purple-800 dark:text-purple-300">
          <Chrome className="w-4 h-4" />
          <span>Chrome Companion Extension</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light tracking-tight">
          Verify AI everywhere you browse
        </h1>
        <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
          Inspect assertions inside ChatGPT, Claude, Perplexity, Google Gemini, and online scientific journals with one click.
        </p>
      </div>

      {/* Interactive Extension Simulator & Feature Showcase */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
        {/* Left: Interactive Popup Simulator */}
        <div className="lg:col-span-6 flex justify-center">
          <div className="w-full max-w-sm bg-white dark:bg-pastel-surface-dark border border-pastel-border dark:border-pastel-border-dark rounded-3xl shadow-pastel overflow-hidden">
            {/* Popup Header */}
            <div className="p-4 bg-pastel-lavender-light/40 dark:bg-pastel-surface-elevated border-b border-pastel-border flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-7 h-7 rounded-lg bg-pastel-lavender flex items-center justify-center text-white shadow-2xs font-bold text-xs">
                  C
                </div>
                <div>
                  <h3 className="font-bold text-xs text-pastel-charcoal dark:text-white">Credence</h3>
                  <p className="text-[10px] text-pastel-slate">Companion Extension</p>
                </div>
              </div>
              <span className="text-[10px] bg-pastel-mint-light text-emerald-800 px-2 py-0.5 rounded-full font-medium border border-pastel-mint-border">
                Engine Ready
              </span>
            </div>

            {/* Popup Body */}
            <div className="p-4 space-y-3.5">
              <div>
                <label className="text-[11px] font-semibold text-pastel-slate uppercase tracking-wider block mb-1">
                  Selected Web Text:
                </label>
                <textarea
                  value={sampleText}
                  onChange={(e) => setSampleText(e.target.value)}
                  rows={3}
                  className="w-full bg-pastel-bg dark:bg-pastel-surface-elevated border border-pastel-border rounded-xl p-2.5 text-xs text-pastel-charcoal dark:text-white focus:outline-none focus:border-pastel-lavender resize-none"
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleSimulate}
                  className="flex-1 py-2 bg-pastel-lavender hover:bg-pastel-lavender-hover text-white rounded-xl text-xs font-semibold shadow-pastel transition-all"
                >
                  {isVerifying ? 'Checking...' : 'Verify Selection'}
                </button>
              </div>

              {/* Simulated Result */}
              {showResult && (
                <div className="p-3 bg-pastel-bg dark:bg-pastel-surface-elevated rounded-xl border border-pastel-border space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center text-emerald-800 dark:text-emerald-300 font-bold">
                      <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                      Verified (94% Trust)
                    </span>
                    <span className="text-[10px] text-pastel-slate font-mono">2 Sources</span>
                  </div>
                  <p className="text-[11px] text-pastel-slate italic">
                    "Corroborated by Applied Physics Letters & IEEE Quantum Transactions..."
                  </p>
                  <div className="pt-1 flex justify-between items-center text-[11px]">
                    <span className="text-pastel-slate">High confidence</span>
                    <Link href="/chat" className="text-purple-600 font-semibold hover:underline">
                      Open full analysis &rarr;
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Popup Footer */}
            <div className="p-3 border-t border-pastel-border bg-pastel-bg/50 text-[10px] text-pastel-slate text-center">
              Selected from active browser tab
            </div>
          </div>
        </div>

        {/* Right: Installation & Capabilities */}
        <div className="lg:col-span-6 space-y-6">
          <div className="space-y-3">
            <h2 className="text-2xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light">
              Seamless fact verification while reading
            </h2>
            <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
              The companion extension lives in your Chrome toolbar. Simply select any claim on a webpage or let it automatically inspect responses generated on ChatGPT, Claude, and Gemini interfaces.
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-start space-x-3 p-3.5 rounded-2xl bg-white dark:bg-pastel-surface-dark border border-pastel-border shadow-2xs">
              <div className="w-8 h-8 rounded-xl bg-pastel-lavender-light flex items-center justify-center text-purple-700 flex-shrink-0">
                1
              </div>
              <div>
                <h3 className="text-xs font-semibold text-pastel-charcoal dark:text-white">
                  Highlight Any Statement
                </h3>
                <p className="text-xs text-pastel-slate dark:text-pastel-slate-light">
                  Select any text on any webpage to trigger the Credence badge or inspect via the popup.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3.5 rounded-2xl bg-white dark:bg-pastel-surface-dark border border-pastel-border shadow-2xs">
              <div className="w-8 h-8 rounded-xl bg-pastel-blue-light flex items-center justify-center text-blue-700 flex-shrink-0">
                2
              </div>
              <div>
                <h3 className="text-xs font-semibold text-pastel-charcoal dark:text-white">
                  Instant Factual Corroboration
                </h3>
                <p className="text-xs text-pastel-slate dark:text-pastel-slate-light">
                  Get a calibrated trust score, claim segmentation, and corroborating citations in under 500ms.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3.5 rounded-2xl bg-white dark:bg-pastel-surface-dark border border-pastel-border shadow-2xs">
              <div className="w-8 h-8 rounded-xl bg-pastel-mint-light flex items-center justify-center text-emerald-700 flex-shrink-0">
                3
              </div>
              <div>
                <h3 className="text-xs font-semibold text-pastel-charcoal dark:text-white">
                  Deep Dive in Studio
                </h3>
                <p className="text-xs text-pastel-slate dark:text-pastel-slate-light">
                  One-click handoff to the full Credence research workspace for deep citation inspection.
                </p>
              </div>
            </div>
          </div>

          {/* Installation Instructions */}
          <div className="p-5 rounded-2xl bg-pastel-lavender-light/30 dark:bg-pastel-surface-dark border border-pastel-border space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-purple-800 dark:text-purple-300 flex items-center space-x-1.5">
              <Terminal className="w-3.5 h-3.5" />
              <span>Developer Installation (Load Unpacked)</span>
            </h3>
            <ol className="text-xs text-pastel-slate dark:text-pastel-slate-light list-decimal list-inside space-y-1">
              <li>Open Chrome and navigate to <code className="bg-white dark:bg-pastel-surface-elevated px-1.5 py-0.5 rounded text-purple-700 font-mono">chrome://extensions</code></li>
              <li>Toggle <strong>Developer mode</strong> in the top-right corner</li>
              <li>Click <strong>Load unpacked</strong> and select the <code className="bg-white dark:bg-pastel-surface-elevated px-1.5 py-0.5 rounded text-purple-700 font-mono">d:\verif\extension</code> directory</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
