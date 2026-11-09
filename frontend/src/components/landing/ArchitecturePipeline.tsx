import React from 'react';
import { Search, Fingerprint, Scale, ArrowUpRight, CheckCircle2, ShieldCheck } from 'lucide-react';

const PIPELINE_STEPS = [
  {
    step: '01',
    phase: 'DECOMPOSITION',
    title: 'Mine atomic claims from fluent text.',
    description: 'Language models hide inaccuracies behind persuasive sentence structures. VerifAI extracts individual, falsifiable statements rather than relying on an overall confidence guess.',
    tag: 'Falsifiable Assertions',
    icon: Search,
  },
  {
    step: '02',
    phase: 'CORROBORATION',
    title: 'Cross-examine primary & permitted archives.',
    description: 'We query primary journals, verified databases, authoritative documentation, and enterprise private knowledge bases with immutable citation hashes.',
    tag: 'Provenance Graph',
    icon: Fingerprint,
  },
  {
    step: '03',
    phase: 'ADJUDICATION',
    title: 'Refuse consensus when evidence is missing.',
    description: 'If three frontier models make the exact same hallucinated assertion, VerifAI classifies the result as UNKNOWN or CONTRADICTED. Agreement alone is never proof.',
    tag: 'Non-Negotiable Ground Truth',
    icon: Scale,
  },
];

export function ArchitecturePipeline({ onLaunch }: { onLaunch: string }) {
  return (
    <section className="relative w-full bg-black py-20 sm:py-28 px-4 sm:px-6 md:px-10 border-t border-neutral-900" id="pipeline">
      <div className="w-full max-w-[1400px] mx-auto">
        {/* Section Top Heading */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-16 sm:mb-20">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-300 text-xs uppercase tracking-wider mb-4 font-mono">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Evidence-First Architecture
            </div>
            <h2
              className="text-white text-3xl sm:text-4xl md:text-5xl font-light tracking-tight"
              style={{ letterSpacing: '-0.04em' }}
            >
              Trust is a verifiable process.<br />
              <span className="text-white/50">Not a synthetic score.</span>
            </h2>
          </div>
          <p className="text-white/60 font-light text-sm sm:text-base max-w-md leading-relaxed">
            Every verification builds a transparent, human-inspectable audit trail from raw prompt tokens to primary source citations.
          </p>
        </div>

        {/* 3 Step Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PIPELINE_STEPS.map((step) => {
            const Icon = step.icon;
            return (
              <div
                key={step.step}
                className="relative h-[420px] rounded-2xl bg-neutral-950 border border-neutral-800/80 p-8 flex flex-col justify-between hover:border-neutral-700 transition-all duration-300 group"
              >
                <div>
                  <div className="flex items-center justify-between mb-8">
                    <span className="font-mono text-xs text-neutral-400 font-semibold tracking-wider">
                      PHASE {step.step}
                    </span>
                    <div className="w-10 h-10 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center group-hover:border-neutral-600 transition">
                      <Icon className="w-4 h-4 text-emerald-400" />
                    </div>
                  </div>

                  <span className="text-[11px] font-mono uppercase tracking-wider text-emerald-400/90 block mb-2">
                    {step.phase}
                  </span>
                  <h3 className="text-xl sm:text-2xl text-white font-light leading-snug mb-4">
                    {step.title}
                  </h3>
                  <p className="text-[13px] sm:text-[14px] leading-relaxed text-white/70 font-light">
                    {step.description}
                  </p>
                </div>

                <div className="pt-6 border-t border-neutral-900 flex items-center justify-between">
                  <span className="text-xs font-mono text-neutral-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    {step.tag}
                  </span>
                  <ArrowUpRight className="w-4 h-4 text-neutral-500 group-hover:text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition" />
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom Banner */}
        <div className="mt-12 p-8 rounded-2xl bg-gradient-to-r from-neutral-950 via-neutral-900 to-neutral-950 border border-neutral-800/80 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-1 text-center sm:text-left">
            <h4 className="text-white text-lg font-light">Bring your custom corpora or private enterprise database.</h4>
            <p className="text-xs sm:text-sm text-neutral-400 font-light">Zero-storage ephemeral mode available for strictly confidential workflows.</p>
          </div>
          <a
            href={onLaunch}
            className="px-6 py-3 rounded-full bg-white text-black text-xs uppercase tracking-wider font-semibold hover:bg-neutral-200 transition shrink-0"
          >
            Launch Evidence Suite
          </a>
        </div>
      </div>
    </section>
  );
}
