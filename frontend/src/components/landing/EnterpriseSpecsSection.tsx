import React from 'react';
import { Lock, Cpu, Database, ShieldCheck, FileText, CheckCircle2 } from 'lucide-react';

const SPECS = [
  {
    title: 'Private Knowledge Vaults',
    desc: 'Connect internal documentation, PDF whitepapers, and proprietary databases via encrypted vector embeddings. Your data never trains public models.',
    icon: Database,
  },
  {
    title: 'Tamper-Evident Audit Trails',
    desc: 'Every verification run records immutable cryptographic hashes of extracted claims, queried URLs, timestamps, and model responses for compliance.',
    icon: Lock,
  },
  {
    title: 'Multi-Frontier LLM Integration',
    desc: 'Query Claude 3.5, GPT-4o, and Gemini 1.5 simultaneously or connect custom fine-tuned weights using your own enterprise API keys.',
    icon: Cpu,
  },
  {
    title: 'Strict Ground-Truth Governance',
    desc: 'Zero fabrication tolerance. Missing citations trigger UNKNOWN outcomes rather than synthetic extrapolation.',
    icon: ShieldCheck,
  },
];

export function EnterpriseSpecsSection() {
  return (
    <section className="relative w-full bg-black py-20 sm:py-28 px-4 sm:px-6 md:px-10 border-t border-neutral-900" id="specs">
      <div className="w-full max-w-[1400px] mx-auto">
        <div className="max-w-3xl mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-300 text-xs uppercase tracking-wider mb-4 font-mono">
            <FileText className="w-3.5 h-3.5 text-emerald-400" />
            Enterprise Infrastructure
          </div>
          <h2
            className="text-white text-3xl sm:text-4xl md:text-5xl font-light tracking-tight mb-4"
            style={{ letterSpacing: '-0.04em' }}
          >
            Engineered for high-stakes<br />
            <span className="text-white/50">verification workflows.</span>
          </h2>
          <p className="text-white/70 text-sm sm:text-base font-light max-w-2xl leading-relaxed">
            From legal discovery and biomedical literature synthesis to financial diligence, VerifAI guarantees complete traceability and zero unverified assumptions.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {SPECS.map((spec, idx) => {
            const Icon = spec.icon;
            return (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-neutral-950 border border-neutral-800/80 flex flex-col justify-between hover:border-neutral-700 transition"
              >
                <div>
                  <div className="w-10 h-10 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center mb-6">
                    <Icon className="w-5 h-5 text-emerald-400" />
                  </div>
                  <h3 className="text-lg font-normal text-white mb-2">{spec.title}</h3>
                  <p className="text-xs sm:text-[13px] text-white/60 font-light leading-relaxed">
                    {spec.desc}
                  </p>
                </div>
                <div className="mt-6 pt-4 border-t border-neutral-900 flex items-center gap-1.5 text-xs font-mono text-neutral-500">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Production Ready</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
