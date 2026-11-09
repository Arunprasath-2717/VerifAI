import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  ShieldAlert,
  Cpu,
  Activity,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCw,
  Terminal,
  Layers,
  Lock,
} from 'lucide-react';

interface ChannelData {
  id: string;
  name: string;
  code: string;
  status: string;
  latency: string;
  throughput: string;
  integrity: string;
  targetDescription: string;
  diagnostics: string[];
}

const CHANNELS: ChannelData[] = [
  {
    id: 'ch-1',
    name: 'Multi-LLM Divergence Sensor',
    code: 'CHN-01 // CONSENSUS-DRIFT',
    status: 'OPTIMAL (3/3 Models Calibrated)',
    latency: '7.8ms',
    throughput: '340,000 tokens/sec',
    integrity: '99.98% Coherence',
    targetDescription: 'Cross-examines token emissions in parallel across GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro to isolate semantic divergence before downstream propagation.',
    diagnostics: [
      'Gemini-1.5 emission: Nominal alignment',
      'Claude-3.5 token distribution: Variance < 0.04',
      'GPT-4o confidence threshold: 0.982 corroborated',
      'Consensus vector: Zero deceptive agreement detected',
    ],
  },
  {
    id: 'ch-2',
    name: 'Adversarial Falsification Chamber',
    code: 'CHN-02 // FALSIFICATION-CORE',
    status: 'ACTIVE STRESS-TESTING',
    latency: '9.4ms',
    throughput: '1,200 claims/sec',
    integrity: 'Zero Tolerance',
    targetDescription: 'Proactively generates counter-hypotheses and probes authoritative PubMed, ArXiv, and Federal corpora to disprove synthetic model confidence.',
    diagnostics: [
      'Deconstructing claim clauses: 14 atomic assertions',
      'Querying PubMed/ArXiv index: 4 corroborating papers',
      'Counter-evidence search: 0 invalidating contradictions',
      'Verdict certainty: 98.4% grounded proof',
    ],
  },
  {
    id: 'ch-3',
    name: 'Cryptographic Provenance Ledger',
    code: 'CHN-03 // PROVENANCE-CHAIN',
    status: 'IMMUTABLE RECORDING',
    latency: '4.2ms',
    throughput: '18,500 hashes/sec',
    integrity: 'SHA-256 Tamper-Proof',
    targetDescription: 'Stamps every verified assertion, timestamp, source URL, and extracted statement into a verifiable audit ledger for zero-trust compliance.',
    diagnostics: [
      'Source hash generated: 0x9f4a...e12d',
      'Temporal proof stamped: ISO-8601 atomic sync',
      'Merkle root verified across cluster nodes',
      'Audit export: Ready for enterprise inspection',
    ],
  },
];

export function AutonomousDefenseMatrix() {
  const [activeChannelId, setActiveChannelId] = useState('ch-1');
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStep, setSimulationStep] = useState(0);

  const activeChannel = CHANNELS.find((c) => c.id === activeChannelId) || CHANNELS[0];

  const handleSimulate = () => {
    if (isSimulating) return;
    setIsSimulating(true);
    setSimulationStep(1);

    setTimeout(() => setSimulationStep(2), 900);
    setTimeout(() => setSimulationStep(3), 1900);
    setTimeout(() => {
      setSimulationStep(4);
      setTimeout(() => {
        setIsSimulating(false);
        setSimulationStep(0);
      }, 1400);
    }, 2800);
  };

  return (
    <section className="relative w-full bg-black py-20 sm:py-28 lg:py-32 px-4 sm:px-6 md:px-10 border-t border-neutral-900 overflow-hidden" id="defense-matrix">
      {/* Background Matrix Ambient Grids */}
      <div
        className="absolute inset-0 opacity-[0.04] bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:28px_28px] pointer-events-none"
        aria-hidden="true"
      />
      <div
        className="absolute top-1/3 left-1/4 w-[500px] h-[500px] bg-blue-900/15 rounded-full blur-[140px] pointer-events-none"
        aria-hidden="true"
      />

      <div className="w-full max-w-[1400px] mx-auto relative z-10">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-16 sm:mb-20"
        >
          <div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-mono uppercase tracking-[0.2em] mb-4">
              <Zap className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
              <span>Interactive Telemetry Reactor</span>
            </div>
            <h2
              className="text-white text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-normal tracking-tight"
              style={{ letterSpacing: '-0.04em' }}
            >
              Autonomous Truth &amp;<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-400">
                Defense Matrix.
              </span>
            </h2>
          </div>

          <p className="text-white/70 font-light text-sm sm:text-base md:text-lg max-w-lg leading-relaxed">
            Real-time observational telemetry and falsification chamber. Continuously intercepting hallucinations, synthetic drift, and unverified assertions.
          </p>
        </motion.div>

        {/* Channel Navigation Buttons */}
        <div className="flex flex-wrap gap-3 mb-8">
          {CHANNELS.map((channel) => (
            <button
              key={channel.id}
              type="button"
              onClick={() => setActiveChannelId(channel.id)}
              className={`px-5 py-3 rounded-xl text-xs sm:text-sm font-mono tracking-wider transition-all duration-300 flex items-center gap-3 border ${
                activeChannelId === channel.id
                  ? 'bg-blue-950/40 text-blue-300 border-blue-500/50 shadow-[0_0_25px_rgba(59,130,246,0.25)]'
                  : 'bg-neutral-950 text-white/60 border-neutral-800/80 hover:text-white hover:bg-neutral-900'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  activeChannelId === channel.id ? 'bg-blue-400 animate-ping' : 'bg-neutral-600'
                }`}
              />
              <span>{channel.code}</span>
            </button>
          ))}
        </div>

        {/* Chamber Workspace Panel */}
        <motion.div
          layout
          className="rounded-3xl bg-neutral-950 border border-white/[0.1] p-6 sm:p-8 md:p-12 shadow-[0_20px_60px_rgba(0,0,0,0.8)] relative overflow-hidden"
        >
          {/* Ambient Corner Radiation */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center relative z-10">
            {/* Left Column: Animated Holographic Radar & Oscilloscope */}
            <div className="lg:col-span-5 flex flex-col items-center justify-center">
              <div className="relative w-64 h-64 sm:w-80 sm:h-80 rounded-full border border-blue-500/20 bg-neutral-900/40 flex items-center justify-center p-4 shadow-[inset_0_0_60px_rgba(30,58,138,0.3)]">
                {/* Rotating Sweep Beam */}
                <div
                  className="absolute inset-0 rounded-full pointer-events-none animate-[spin_4s_linear_infinite]"
                  style={{
                    background: 'conic-gradient(from 0deg, rgba(59, 130, 246, 0.4) 0deg, transparent 60deg, transparent 360deg)',
                  }}
                />

                {/* Concentric Radar Rings */}
                <div className="absolute w-3/4 h-3/4 rounded-full border border-blue-500/20" />
                <div className="absolute w-1/2 h-1/2 rounded-full border border-blue-500/25" />
                <div className="absolute w-1/4 h-1/4 rounded-full border border-blue-500/35" />

                {/* Crosshairs */}
                <div className="absolute inset-x-0 top-1/2 h-px bg-blue-500/20" />
                <div className="absolute inset-y-0 left-1/2 w-px bg-blue-500/20" />

                {/* Center Core */}
                <div className="relative z-10 w-14 h-14 rounded-full bg-blue-600/20 border border-blue-400 flex items-center justify-center shadow-[0_0_30px_rgba(59,130,246,0.6)]">
                  <Activity className="w-6 h-6 text-blue-300 animate-pulse" />
                </div>

                {/* Dynamic Blips */}
                <div className="absolute top-16 right-20 w-3 h-3 rounded-full bg-emerald-400 animate-ping opacity-75" />
                <div className="absolute bottom-20 left-16 w-2.5 h-2.5 rounded-full bg-sky-400 animate-pulse" />
                {isSimulating && (
                  <div className="absolute top-24 left-20 w-4 h-4 rounded-full bg-amber-400 animate-ping shadow-[0_0_20px_rgba(245,158,11,0.9)]" />
                )}
              </div>

              {/* Simulation Trigger Button */}
              <button
                type="button"
                onClick={handleSimulate}
                disabled={isSimulating}
                className="mt-8 px-6 py-3 rounded-full bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/40 text-xs font-mono uppercase tracking-widest flex items-center gap-2.5 transition-all shadow-[0_0_20px_rgba(59,130,246,0.2)] hover:scale-105 active:scale-95 disabled:opacity-50"
              >
                {isSimulating ? (
                  <>
                    <RotateCw className="w-3.5 h-3.5 animate-spin text-amber-400" />
                    <span>Stress-Test Simulation Running...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 text-blue-400 fill-blue-400" />
                    <span>Simulate Anomaly Injection</span>
                  </>
                )}
              </button>
            </div>

            {/* Right Column: Live Diagnostics & Channel Telemetry */}
            <div className="lg:col-span-7 flex flex-col justify-between space-y-6">
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] mb-4">
                  <div>
                    <span className="text-xs font-mono text-blue-400 tracking-wider block mb-1">
                      ACTIVE SENTRY PROTOCOL
                    </span>
                    <h3 className="text-2xl sm:text-3xl text-white font-normal tracking-tight">
                      {activeChannel.name}
                    </h3>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
                    {activeChannel.status}
                  </span>
                </div>

                <p className="text-sm sm:text-base text-white/80 font-light leading-relaxed mb-6">
                  {activeChannel.targetDescription}
                </p>

                {/* Live Diagnostic Stream Box */}
                <div className="p-5 rounded-2xl bg-black border border-neutral-800 font-mono text-xs space-y-2.5 relative">
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-800/80 text-neutral-500 text-[11px]">
                    <span className="flex items-center gap-1.5 text-neutral-400">
                      <Terminal className="w-3 h-3 text-blue-400" />
                      LIVE DIAGNOSTIC FEED
                    </span>
                    <span>KERNEL v4.11-PROD</span>
                  </div>

                  {/* Diagnostic lines */}
                  {activeChannel.diagnostics.map((diag, index) => (
                    <div key={index} className="flex items-start gap-2 text-neutral-300">
                      <span className="text-blue-500 select-none">›</span>
                      <span>{diag}</span>
                    </div>
                  ))}

                  {/* Simulation dynamic alert line */}
                  {isSimulating && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-3 rounded-lg bg-amber-500/15 border border-amber-500/40 text-amber-300 flex items-center gap-2 font-mono text-xs"
                    >
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>
                        {simulationStep === 1 && '[!] Injected synthetic assertion: Unverified token cluster'}
                        {simulationStep === 2 && '[!] Parallel model probe: 2/3 LLMs hallucinated source'}
                        {simulationStep === 3 && '[✓] Falsification engine engaged: Counter-proof indexed'}
                        {simulationStep === 4 && '[✓] Anomaly quarantined: Zero drift preserved in 8.1ms'}
                      </span>
                    </motion.div>
                  )}
                </div>
              </div>

              {/* Metrics HUD Row */}
              <div className="grid grid-cols-3 gap-3 pt-4 border-t border-white/[0.08]">
                <div className="p-3.5 rounded-xl bg-neutral-900/60 border border-neutral-800 text-center">
                  <span className="text-[10px] font-mono text-neutral-400 block mb-1">LATENCY</span>
                  <span className="text-base sm:text-lg font-mono text-white">{activeChannel.latency}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-neutral-900/60 border border-neutral-800 text-center">
                  <span className="text-[10px] font-mono text-neutral-400 block mb-1">THROUGHPUT</span>
                  <span className="text-base sm:text-lg font-mono text-white">{activeChannel.throughput}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-neutral-900/60 border border-neutral-800 text-center">
                  <span className="text-[10px] font-mono text-neutral-400 block mb-1">INTEGRITY</span>
                  <span className="text-base sm:text-lg font-mono text-emerald-400">{activeChannel.integrity}</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
