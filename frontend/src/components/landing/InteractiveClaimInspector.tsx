import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, ArrowRight, Database, ExternalLink, ShieldAlert, Sparkles } from 'lucide-react';

interface SampleClaim {
  id: string;
  category: string;
  input: string;
  claim: string;
  status: 'SUPPORTED' | 'CONTRADICTED' | 'UNKNOWN';
  confidence: number;
  sources: { title: string; domain: string; snippet: string }[];
  consensusAgreement: string;
  verdictNote: string;
}

const SAMPLE_CLAIMS: SampleClaim[] = [
  {
    id: 'claim-1',
    category: 'Astrophysics & Space',
    input: "According to recent spectrographic observations from NASA's James Webb Space Telescope, exoplanet WASP-39b exhibits unambiguous evidence of atmospheric carbon dioxide and sulfur dioxide photochemistry.",
    claim: 'WASP-39b contains atmospheric sulfur dioxide produced via photochemistry.',
    status: 'SUPPORTED',
    confidence: 97.4,
    consensusAgreement: 'High (3 of 3 models agree)',
    verdictNote: 'Corroborated by independent peer-reviewed transmission spectroscopy data (Nature 2023, DOI:10.1038/s41586-022-05269-w).',
    sources: [
      {
        title: 'Direct photochemical production of SO2 in WASP-39b atmosphere',
        domain: 'nature.com',
        snippet: 'JWST NIRSpec observations reveal prominent 4.05-micron SO2 absorption created by stellar UV photolysis.',
      },
      {
        title: 'NASA Exoplanet Archive: WASP-39 Atmospheric Chemistry',
        domain: 'nasa.gov',
        snippet: 'Confirmed molecular inventory includes CO2, SO2, and H2O spectral fingerprints at >5-sigma confidence.',
      },
    ],
  },
  {
    id: 'claim-2',
    category: 'Physics & Optics',
    input: 'The Great Wall of China is easily visible to the unaided human eye from low Earth orbit during daylight passes.',
    claim: 'The Great Wall of China is visible to the naked human eye from low Earth orbit.',
    status: 'CONTRADICTED',
    confidence: 96.1,
    consensusAgreement: 'Split (2 models repeated myth, 1 flagged caveat)',
    verdictNote: 'Optical resolution limit of human eye (~1 arcminute) requires minimum width of tens of meters from 350km altitude. The wall is 5-9 meters wide and blends with surrounding topography.',
    sources: [
      {
        title: 'NASA Earth Observatory: Is the Great Wall Visible from Orbit?',
        domain: 'earthobservatory.nasa.gov',
        snippet: 'Astronaut photographic records and optical physics confirm the wall is indistinguishable without telephoto lenses.',
      },
      {
        title: 'Scientific American: The Great Wall Orbit Myth',
        domain: 'scientificamerican.com',
        snippet: 'Contrast with soil and human retinal angular resolution make unaided space visibility physically impossible.',
      },
    ],
  },
  {
    id: 'claim-3',
    category: 'Quantum Computing',
    input: 'Recent fault-tolerant superconducting quantum processors have proven polynomial-time algorithms that unconditionally solve generic NP-complete combinatorial benchmarks.',
    claim: 'Quantum computers have unconditionally solved generic NP-complete problems in polynomial time.',
    status: 'UNKNOWN',
    confidence: 89.2,
    consensusAgreement: 'Model Hallucination Detected (Model invented benchmark paper)',
    verdictNote: 'No verifiable mathematical proof or experimental quantum computation demonstrates NP ⊆ BQP. Current consensus remains that quantum computers cannot solve NP-complete problems in polynomial time.',
    sources: [
      {
        title: 'Complexity Zoo: BQP vs NP Status Report',
        domain: 'complexityzoo.net',
        snippet: 'Widely believed BQP and NP are incomparable; no known polynomial quantum algorithm exists for NP-complete problems.',
      },
      {
        title: 'IEEE Quantum Computing Survey on Complexity Bounds',
        domain: 'ieee.org',
        snippet: 'Unconditional polynomial speedup for generic NP-complete problems remains an unproven theoretical conjecture.',
      },
    ],
  },
];

export function InteractiveClaimInspector() {
  const [activeTab, setActiveTab] = useState<string>('claim-1');
  const activeClaim = SAMPLE_CLAIMS.find((c) => c.id === activeTab) || SAMPLE_CLAIMS[0];

  return (
    <section className="relative w-full bg-black py-16 sm:py-24 px-4 sm:px-6 md:px-10 border-t border-neutral-900" id="inspector">
      <div className="w-full max-w-[1400px] mx-auto">
        {/* Header */}
        <div className="max-w-3xl mb-12 sm:mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs uppercase tracking-wider mb-4 font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            Live Inspection Simulator
          </div>
          <h2
            className="text-white text-3xl sm:text-4xl md:text-5xl font-light tracking-tight mb-4"
            style={{ letterSpacing: '-0.04em' }}
          >
            Don't trust confidence.<br />
            <span className="text-white/50">Inspect the evidence trail.</span>
          </h2>
          <p className="text-white/70 text-sm sm:text-base font-light max-w-2xl leading-relaxed">
            See how VerifAI deconstructs generative model text, isolates atomic propositions, queries verified datasets, and exposes the ground truth behind deceptive consensus.
          </p>
        </div>

        {/* Claim Selector Pills */}
        <div className="flex flex-wrap gap-2.5 mb-8">
          {SAMPLE_CLAIMS.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setActiveTab(c.id)}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-light transition-all flex items-center gap-2 border ${
                activeTab === c.id
                  ? 'bg-neutral-800 text-white border-neutral-600 shadow-[0_0_20px_rgba(255,255,255,0.08)]'
                  : 'bg-neutral-950 text-white/60 border-neutral-800/80 hover:text-white hover:bg-neutral-900'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-neutral-400" />
              <span>{c.category}</span>
            </button>
          ))}
        </div>

        {/* Interactive Inspection Workspace Card */}
        <div className="rounded-2xl bg-neutral-950 border border-neutral-800/80 p-6 sm:p-8 md:p-10 shadow-2xl relative overflow-hidden">
          {/* Subtle background ambient blob */}
          <div
            className={`absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl opacity-15 pointer-events-none transition-all duration-700 ${
              activeClaim.status === 'SUPPORTED'
                ? 'bg-emerald-500'
                : activeClaim.status === 'CONTRADICTED'
                ? 'bg-rose-500'
                : 'bg-amber-500'
            }`}
          />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 relative z-10">
            {/* Left Column: Raw Input & Decomposed Claim */}
            <div className="lg:col-span-7 flex flex-col justify-between space-y-6">
              {/* Raw Prompt Input */}
              <div>
                <div className="flex items-center justify-between text-xs text-neutral-400 uppercase tracking-wider mb-2 font-mono">
                  <span>Step 01: Raw LLM Output</span>
                  <span className="text-neutral-500">Unverified Text</span>
                </div>
                <div className="p-4 sm:p-5 rounded-xl bg-neutral-900/80 border border-neutral-800 text-neutral-200 text-sm leading-relaxed font-light">
                  "{activeClaim.input}"
                </div>
              </div>

              {/* Extracted Atomic Proposition */}
              <div>
                <div className="flex items-center justify-between text-xs text-neutral-400 uppercase tracking-wider mb-2 font-mono">
                  <span>Step 02: Extracted Atomic Assertion</span>
                  <span className="text-emerald-400">Target Claim</span>
                </div>
                <div className="p-4 sm:p-5 rounded-xl bg-black border border-neutral-800 text-white text-base font-light leading-relaxed flex items-start gap-3">
                  <ArrowRight className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-normal text-white">{activeClaim.claim}</span>
                  </div>
                </div>
              </div>

              {/* Corroborating Evidence Sources */}
              <div>
                <div className="flex items-center justify-between text-xs text-neutral-400 uppercase tracking-wider mb-2 font-mono">
                  <span>Step 03: Primary Sources Corroborated</span>
                  <span className="text-neutral-400">2 Verified Citations</span>
                </div>
                <div className="space-y-2.5">
                  {activeClaim.sources.map((s, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-lg bg-neutral-900/60 border border-neutral-800/80 hover:border-neutral-700 transition"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-white flex items-center gap-1.5">
                          <Database className="w-3.5 h-3.5 text-neutral-400" />
                          {s.title}
                        </span>
                        <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                          {s.domain}
                          <ExternalLink className="w-3 h-3 text-neutral-500" />
                        </span>
                      </div>
                      <p className="text-xs text-neutral-400 font-light leading-relaxed">
                        "{s.snippet}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Independent Verdict & Truth Score */}
            <div className="lg:col-span-5 flex flex-col justify-between bg-black/50 border border-neutral-800 rounded-xl p-6 sm:p-8">
              <div>
                <div className="flex items-center justify-between text-xs text-neutral-400 font-mono tracking-wider mb-6">
                  <span>VERIFICATION OUTCOME</span>
                  <span>IMMUTABLE TRACE</span>
                </div>

                {/* Verdict Badge */}
                <div className="mb-6">
                  {activeClaim.status === 'SUPPORTED' && (
                    <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium text-sm">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      <span>EVIDENCE SUPPORTED</span>
                    </div>
                  )}
                  {activeClaim.status === 'CONTRADICTED' && (
                    <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 font-medium text-sm">
                      <XCircle className="w-5 h-5 text-rose-400" />
                      <span>CLAIM CONTRADICTED</span>
                    </div>
                  )}
                  {activeClaim.status === 'UNKNOWN' && (
                    <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 font-medium text-sm">
                      <HelpCircle className="w-5 h-5 text-amber-400" />
                      <span>INSUFFICIENT PROOF (UNKNOWN)</span>
                    </div>
                  )}
                </div>

                {/* Confidence Bar */}
                <div className="space-y-2 mb-6">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-neutral-400">Provenance Confidence</span>
                    <span className="text-white font-medium">{activeClaim.confidence}%</span>
                  </div>
                  <div className="h-2 w-full bg-neutral-900 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-700 ${
                        activeClaim.status === 'SUPPORTED'
                          ? 'bg-emerald-400'
                          : activeClaim.status === 'CONTRADICTED'
                          ? 'bg-rose-400'
                          : 'bg-amber-400'
                      }`}
                      style={{ width: `${activeClaim.confidence}%` }}
                    />
                  </div>
                </div>

                {/* Consensus Warning vs Ground Truth */}
                <div className="p-4 rounded-lg bg-neutral-900/60 border border-neutral-800/80 mb-6">
                  <div className="flex items-center gap-2 text-xs font-mono text-neutral-300 mb-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-neutral-400" />
                    <span>LLM Consensus State</span>
                  </div>
                  <p className="text-xs text-neutral-400 font-light">
                    {activeClaim.consensusAgreement}
                  </p>
                </div>

                {/* Adjudication Summary */}
                <div>
                  <span className="text-xs font-mono uppercase tracking-wider text-neutral-500 block mb-2">
                    Adjudication Reasoning
                  </span>
                  <p className="text-xs sm:text-sm text-neutral-300 font-light leading-relaxed">
                    {activeClaim.verdictNote}
                  </p>
                </div>
              </div>

              {/* Footer Note */}
              <div className="pt-6 mt-6 border-t border-neutral-800/60 flex items-center justify-between text-[11px] text-neutral-500 font-mono">
                <span>VERIFAI CORE ADJUDICATOR</span>
                <span>CRYPTOGRAPHIC HASH: VERIFIED</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
