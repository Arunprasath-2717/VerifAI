import React from 'react';
import { Bot, Check, AlertTriangle, ArrowRight, Layers, Sparkles } from 'lucide-react';

const MODELS = [
  {
    name: 'Gemini 1.5 Pro',
    provider: 'Google',
    assertion: 'Reports common belief that camels store water directly in their humps for dessert journeys.',
    confidence: '95% (Synthetic Confidence)',
    state: 'Misconception Propagated',
    statusColor: 'text-rose-400',
  },
  {
    name: 'Claude 3.5 Sonnet',
    provider: 'Anthropic',
    assertion: 'Mentions that humps store metabolic fat reservoirs that can release water during respiration.',
    confidence: '98% (High Semantic Fluency)',
    state: 'Nuanced Explanation',
    statusColor: 'text-amber-400',
  },
  {
    name: 'GPT-4o',
    provider: 'OpenAI',
    assertion: 'Explains specialized oval red blood cells and fat-storing tissue in humps, avoiding water-tank myth.',
    confidence: '96% (Authoritative Tone)',
    state: 'Factually Delineated',
    statusColor: 'text-emerald-400',
  },
];

export function ModelConsensusSection() {
  return (
    <section className="relative w-full bg-black py-20 sm:py-28 px-4 sm:px-6 md:px-10 border-t border-neutral-900" id="consensus">
      <div className="w-full max-w-[1400px] mx-auto">
        <div className="max-w-3xl mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-300 text-xs uppercase tracking-wider mb-4 font-mono">
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            Consensus vs Ground Truth
          </div>
          <h2
            className="text-white text-3xl sm:text-4xl md:text-5xl font-light tracking-tight mb-4"
            style={{ letterSpacing: '-0.04em' }}
          >
            Three models agree.<br />
            <span className="text-white/50">Does that make it true?</span>
          </h2>
          <p className="text-white/70 text-sm sm:text-base font-light max-w-2xl leading-relaxed">
            LLMs trained on overlapping web crawl data often share the same misconceptions, blind spots, and hallucinations. VerifAI decouples model consensus from scientific ground truth.
          </p>
        </div>

        {/* Comparison Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {MODELS.map((model, idx) => (
            <div
              key={idx}
              className="rounded-2xl bg-neutral-950 border border-neutral-800/80 p-6 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between pb-4 mb-4 border-b border-neutral-900">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white">{model.name}</h4>
                      <span className="text-[11px] font-mono text-neutral-500">{model.provider}</span>
                    </div>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-neutral-900 text-neutral-400 border border-neutral-800">
                    Lane 0{idx + 1}
                  </span>
                </div>

                <p className="text-xs sm:text-[13px] text-neutral-300 font-light leading-relaxed mb-4">
                  "{model.assertion}"
                </p>
              </div>

              <div className="pt-4 border-t border-neutral-900/80 flex items-center justify-between text-xs font-mono">
                <span className="text-neutral-500">{model.confidence}</span>
                <span className={model.statusColor}>{model.state}</span>
              </div>
            </div>
          ))}
        </div>

        {/* VerifAI Synthesis & Evidence Bar */}
        <div className="rounded-2xl bg-neutral-950 border border-emerald-500/30 p-6 sm:p-8 relative overflow-hidden shadow-[0_0_50px_rgba(16,185,129,0.05)]">
          <div className="absolute top-0 right-0 w-96 h-96 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2 max-w-2xl">
              <div className="flex items-center gap-2 text-xs font-mono text-emerald-400">
                <Sparkles className="w-4 h-4" />
                <span>VERIFAI ADJUDICATION ENGINE</span>
              </div>
              <h3 className="text-xl sm:text-2xl text-white font-light">
                Consensus flagged as Incomplete. Independent primary evidence retrieved.
              </h3>
              <p className="text-xs sm:text-sm text-neutral-400 font-light leading-relaxed">
                Primary biology citation: Animal Physiology Journal (PMID: 15482390). Camel humps store triglycerides (fat), not liquid water. VerifAI validates the precise physiology and issues a granular attribution score.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
              <div className="px-5 py-3 rounded-xl bg-neutral-900/90 border border-neutral-800 text-center">
                <span className="text-[11px] text-neutral-500 font-mono block">CONSENSUS SCORE</span>
                <span className="text-lg font-light text-white font-mono">66% DIVERGENT</span>
              </div>
              <div className="px-5 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center">
                <span className="text-[11px] text-emerald-400/80 font-mono block">EVIDENCE STATUS</span>
                <span className="text-lg font-light text-emerald-300 font-mono">CORROBORATED</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
