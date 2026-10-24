import React from 'react';
import { ShieldCheck, ArrowRight, Sparkles, MessageSquare } from 'lucide-react';
import { HaloButton } from '../ui/halo-button';

interface WelcomeCardProps {
  userName: string;
  onStartVerification: () => void;
  onOpenChat: () => void;
}

export const WelcomeCard: React.FC<WelcomeCardProps> = ({
  userName,
  onStartVerification,
  onOpenChat,
}) => {
  return (
    <section className="bg-white rounded-[2.8rem] p-8 md:p-10 border border-slate-200/60 shadow-sm relative overflow-hidden group">
      {/* Subtle background ambient mesh */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-blue-50/60 via-slate-50/30 to-transparent rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Copy & Actions */}
        <div className="lg:col-span-7 xl:col-span-7 space-y-4">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 tracking-wide">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>VerifAI Engine v2.6 · Online</span>
          </div>

          <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Hi {userName}.
          </h1>

          <p className="text-slate-500 text-sm md:text-base leading-relaxed max-w-xl">
            Verify AI answers with evidence, compare independent model judgments, and understand what you can trust.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <HaloButton
              onClick={onStartVerification}
              type="button"
            >
              <ShieldCheck size={18} strokeWidth={2.2} className="text-blue-600" />
              <span>Start Verification</span>
            </HaloButton>

            <button
              onClick={onOpenChat}
              className="bg-slate-100 hover:bg-slate-200/80 text-slate-800 px-5 py-3 rounded-full font-semibold text-sm transition-all flex items-center gap-2 cursor-pointer"
            >
              <MessageSquare size={17} />
              <span>Open AI Chat</span>
            </button>
          </div>
        </div>

        {/* Right Restrained Geometric Evidence Illustration */}
        <div className="lg:col-span-5 xl:col-span-5 flex items-center justify-center lg:justify-end">
          <div className="relative w-64 h-56 md:w-72 md:h-64 flex items-center justify-center select-none">
            {/* Soft backdrop blur shapes */}
            <div className="absolute w-44 h-44 bg-blue-500/10 rounded-full blur-2xl" />
            <div className="absolute bottom-2 right-4 w-32 h-32 bg-emerald-500/10 rounded-full blur-xl" />

            {/* Geometric VerifAI Evidence Network SVG */}
            <svg viewBox="0 0 280 240" className="w-full h-full relative z-10">
              <defs>
                <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#1E293B" />
                  <stop offset="100%" stopColor="#0F172A" />
                </linearGradient>
                <linearGradient id="evidenceBeam" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#10B981" stopOpacity="0.6" />
                </linearGradient>
              </defs>

              {/* Connecting Evidence Rays */}
              <line x1="140" y1="120" x2="60" y2="70" stroke="#CBD5E1" strokeWidth="1.5" strokeDasharray="4 4" />
              <line x1="140" y1="120" x2="220" y2="60" stroke="#CBD5E1" strokeWidth="1.5" strokeDasharray="4 4" />
              <line x1="140" y1="120" x2="80" y2="185" stroke="#CBD5E1" strokeWidth="1.5" strokeDasharray="4 4" />
              <line x1="140" y1="120" x2="215" y2="175" stroke="#CBD5E1" strokeWidth="1.5" strokeDasharray="4 4" />

              {/* Ground Truth Citation Card 1 (Top Left) */}
              <g className="transition-transform duration-300 hover:scale-105">
                <rect x="25" y="45" width="80" height="42" rx="12" fill="#FFFFFF" stroke="#E2E8F0" strokeWidth="1.5" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.04))" />
                <circle cx="43" cy="66" r="6" fill="#10B981" />
                <path d="M40.5 66L42.5 68L46 64.5" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <rect x="55" y="59" width="38" height="5" rx="2.5" fill="#64748B" />
                <rect x="55" y="68" width="24" height="4" rx="2" fill="#94A3B8" />
              </g>

              {/* Ground Truth Citation Card 2 (Top Right) */}
              <g className="transition-transform duration-300 hover:scale-105">
                <rect x="180" y="35" width="85" height="44" rx="12" fill="#FFFFFF" stroke="#E2E8F0" strokeWidth="1.5" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.04))" />
                <circle cx="198" cy="57" r="6" fill="#3B82F6" />
                <rect x="210" y="50" width="42" height="5" rx="2.5" fill="#0F172A" />
                <rect x="210" y="60" width="30" height="4" rx="2" fill="#94A3B8" />
              </g>

              {/* Contradiction Flag Card (Bottom Left) */}
              <g className="transition-transform duration-300 hover:scale-105">
                <rect x="40" y="165" width="82" height="42" rx="12" fill="#FFFFFF" stroke="#FEE2E2" strokeWidth="1.5" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.04))" />
                <circle cx="58" cy="186" r="6" fill="#EF4444" />
                <line x1="56" y1="184" x2="60" y2="188" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" />
                <line x1="60" y1="184" x2="56" y2="188" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" />
                <rect x="70" y="179" width="38" height="5" rx="2.5" fill="#64748B" />
                <rect x="70" y="188" width="22" height="4" rx="2" fill="#94A3B8" />
              </g>

              {/* Verification Node (Bottom Right) */}
              <g className="transition-transform duration-300 hover:scale-105">
                <rect x="175" y="155" width="84" height="42" rx="12" fill="#FFFFFF" stroke="#E2E8F0" strokeWidth="1.5" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.04))" />
                <circle cx="193" cy="176" r="6" fill="#F59E0B" />
                <circle cx="193" cy="176" r="1.5" fill="#FFFFFF" />
                <rect x="205" y="169" width="40" height="5" rx="2.5" fill="#0F172A" />
                <rect x="205" y="178" width="26" height="4" rx="2" fill="#94A3B8" />
              </g>

              {/* Central VerifAI Shield Diamond */}
              <g className="transition-transform duration-500 group-hover:scale-110" style={{ transformOrigin: '140px 120px' }}>
                <circle cx="140" cy="120" r="34" fill="#F1F5F9" />
                <circle cx="140" cy="120" r="28" fill="url(#shieldGrad)" />
                <circle cx="140" cy="120" r="28" stroke="#3B82F6" strokeWidth="2" strokeDasharray="3 3" />
                
                {/* Shield Icon in Center */}
                <path 
                  d="M140 106L152 112V121C152 128.5 147 134 140 137C133 134 128 128.5 128 121V112L140 106Z" 
                  fill="none" 
                  stroke="#FFFFFF" 
                  strokeWidth="2.2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                />
                <path 
                  d="M136 120L139 123L145 117" 
                  stroke="#60A5FA" 
                  strokeWidth="2.2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                />
              </g>
            </svg>
          </div>
        </div>
      </div>
    </section>
  );
};
