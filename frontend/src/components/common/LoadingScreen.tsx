import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ShieldCheck, Cpu, Terminal, Radio } from 'lucide-react';

interface LoadingScreenProps {
  message?: string;
  submessage?: string;
  fullScreen?: boolean;
  showProgress?: boolean;
  statusLogs?: string[];
}

const DEFAULT_LOGS = [
  'Establishing cryptographic handshake...',
  'Connecting to multi-model consensus cluster...',
  'Synchronizing neural verification graph...',
  'Validating local session integrity...',
  'Mounting enterprise workspace...'
];

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message = 'Initializing VerifAI Console',
  submessage = 'Calibrating multi-model verification engine and consensus graphs',
  fullScreen = true,
  showProgress = true,
  statusLogs = DEFAULT_LOGS,
}) => {
  const [logIndex, setLogIndex] = useState(0);

  useEffect(() => {
    if (!statusLogs || statusLogs.length <= 1) return;
    const interval = setInterval(() => {
      setLogIndex((prev) => (prev + 1) % statusLogs.length);
    }, 1800);
    return () => clearInterval(interval);
  }, [statusLogs]);

  const containerClasses = fullScreen
    ? 'fixed inset-0 z-[9999] min-h-screen w-screen flex flex-col items-center justify-center bg-[#050508] text-white overflow-hidden select-none'
    : 'relative w-full min-h-[400px] py-12 flex flex-col items-center justify-center bg-[#050508] text-white rounded-3xl overflow-hidden select-none';

  return (
    <div className={containerClasses}>
      {/* Ambient glowing fluid background accents */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/3 -translate-x-1/2 -translate-y-1/2 w-[420px] h-[420px] rounded-full bg-fuchsia-600/15 blur-[120px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/3 translate-x-1/2 translate-y-1/2 w-[480px] h-[480px] rounded-full bg-cyan-500/15 blur-[130px] animate-pulse delay-700" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_30%,rgba(5,5,8,0.85)_100%)]" />
      </div>

      <div className="relative z-10 flex flex-col items-center max-w-md w-full px-6 text-center">
        {/* Orbital VerifAI Core Icon */}
        <div className="relative w-24 h-24 mb-7 flex items-center justify-center">
          {/* Outer rotating dashed ring */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-0 rounded-full border border-dashed border-fuchsia-500/40"
          />

          {/* Inner counter-rotating gradient ring */}
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-2 rounded-full border border-transparent border-t-cyan-400 border-r-fuchsia-400/80 border-b-transparent border-l-cyan-400/40"
          />

          {/* Ambient glow behind central node */}
          <div className="absolute inset-4 rounded-full bg-gradient-to-tr from-fuchsia-600/30 to-cyan-500/30 blur-md" />

          {/* Center Nexus Pill */}
          <motion.div
            animate={{ scale: [1, 1.06, 1] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
            className="relative w-12 h-12 rounded-2xl bg-[#0e0f17] border border-white/20 shadow-[0_0_24px_rgba(34,211,238,0.35)] flex items-center justify-center text-cyan-300"
          >
            <ShieldCheck className="w-6 h-6 text-cyan-300 drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
          </motion.div>
        </div>

        {/* Brand Label */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.06] border border-white/10 backdrop-blur-md mb-3.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-[11px] font-semibold tracking-[0.2em] uppercase text-white/90">
            VERIFAI INTELLIGENCE CORE
          </span>
        </div>

        {/* Main Title */}
        <h2 className="text-xl sm:text-2xl font-['Playfair_Display',Georgia,serif] font-medium tracking-tight text-white mb-2">
          {message}
        </h2>

        {/* Subtitle */}
        <p className="text-xs sm:text-[13px] text-white/60 max-w-xs font-normal mb-6 leading-relaxed">
          {submessage}
        </p>

        {/* Shimmering Progress Bar */}
        {showProgress && (
          <div className="w-full max-w-[260px] h-1.5 rounded-full bg-white/10 overflow-hidden relative mb-4">
            <motion.div
              animate={{
                x: ['-100%', '100%'],
              }}
              transition={{
                duration: 1.6,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className="absolute inset-y-0 w-1/2 rounded-full bg-gradient-to-r from-cyan-400 via-fuchsia-500 to-indigo-400 shadow-[0_0_12px_rgba(217,70,239,0.7)]"
            />
          </div>
        )}

        {/* Real-time Telemetry Status */}
        <div className="h-6 flex items-center justify-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={logIndex}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.25 }}
              className="flex items-center gap-2 text-[11px] font-mono text-cyan-300/80"
            >
              <Terminal className="w-3.5 h-3.5 text-fuchsia-400 shrink-0" />
              <span>{statusLogs[logIndex]}</span>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Developer Diagnostics Footer Badges */}
        <div className="mt-8 pt-6 border-t border-white/10 flex items-center gap-4 text-[10px] font-mono text-white/40">
          <span className="flex items-center gap-1.5">
            <Radio className="w-3 h-3 text-emerald-400" /> CLUSTER: STABLE
          </span>
          <span>•</span>
          <span className="flex items-center gap-1.5">
            <Cpu className="w-3 h-3 text-cyan-400" /> ENGINE: v2.4-PROD
          </span>
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;
