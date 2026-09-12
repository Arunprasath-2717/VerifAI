'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ShieldCheck, CheckCircle, Search, ExternalLink, Sparkles, FileText, ArrowRight, Activity } from 'lucide-react';
import Link from 'next/link';

export const HeroPreviewMockup: React.FC = () => {
  const [activePhase, setActivePhase] = useState<number>(0);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState<boolean>(false);

  const phases = [
    { id: 0, name: 'AI Response', duration: 4500 },
    { id: 1, name: 'Claim Detection', duration: 4500 },
    { id: 2, name: 'Verification Progress', duration: 3500 },
    { id: 3, name: 'Evidence Result', duration: 5500 },
  ];

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion || isPaused) return;

    const timer = setTimeout(() => {
      setActivePhase((prev) => (prev + 1) % phases.length);
    }, phases[activePhase].duration);

    return () => clearTimeout(timer);
  }, [activePhase, isPaused]);

  // Interactive 3D Perspective Tilt on Mouse Move
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion || !cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    // Subtle 3D angle (maximum ~6 degrees for elegant minimalism)
    const rotateX = ((y - centerY) / centerY) * -5;
    const rotateY = ((x - centerX) / centerX) * 5;

    setTilt({ x: rotateX, y: rotateY });
  };

  const handleMouseLeave = () => {
    setIsPaused(false);
    setIsHovered(false);
    setTilt({ x: 0, y: 0 });
  };

  return (
    <div
      className="relative w-full max-w-xl mx-auto [perspective:1200px]"
      onMouseEnter={() => {
        setIsPaused(true);
        setIsHovered(true);
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* 3D Decorative Pastel Floating Layers behind mockup */}
      <div
        className="absolute -top-10 -left-10 w-44 h-44 rounded-full bg-gradient-to-br from-pastel-lavender/30 to-purple-200/20 dark:from-pastel-lavender/15 blur-2xl -z-10 pointer-events-none transition-transform duration-700 ease-out"
        style={{
          transform: `translate3d(${tilt.y * -2}px, ${tilt.x * -2}px, 0)`,
        }}
      />
      <div
        className="absolute -bottom-10 -right-10 w-52 h-52 rounded-full bg-gradient-to-br from-pastel-blue/30 to-blue-200/20 dark:from-pastel-blue/15 blur-2xl -z-10 pointer-events-none transition-transform duration-700 ease-out"
        style={{
          transform: `translate3d(${tilt.y * 2.5}px, ${tilt.x * 2.5}px, 0)`,
        }}
      />

      {/* Floating 3D Badge Overlay (Translates in Z space) */}
      <div
        className="absolute -top-3 -right-3 sm:-right-4 z-20 px-3.5 py-1.5 rounded-2xl bg-white/95 dark:bg-pastel-surface-elevated/95 backdrop-blur-md border border-pastel-mint-border shadow-pastel flex items-center space-x-2 text-[11px] font-semibold text-emerald-800 dark:text-emerald-300 transition-all duration-300 pointer-events-none"
        style={{
          transform: isHovered
            ? `translate3d(${tilt.y * 1.5}px, ${tilt.x * 1.5}px, 30px)`
            : 'translate3d(0, 0, 0)',
        }}
      >
        <span className="w-2 h-2 rounded-full bg-pastel-mint animate-ping" />
        <span className="font-mono">94% Confidence</span>
      </div>

      {/* Main 3D Card Container */}
      <div
        ref={cardRef}
        className="relative bg-white dark:bg-pastel-surface-dark border border-pastel-border dark:border-pastel-border-dark rounded-3xl shadow-pastel overflow-hidden transition-transform duration-200 ease-out [transform-style:preserve-3d]"
        style={{
          transform: `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
          boxShadow: isHovered
            ? '0 20px 40px -10px rgba(167, 139, 250, 0.2), 0 10px 20px -5px rgba(37, 35, 52, 0.08)'
            : '0 8px 30px -4px rgba(167, 139, 250, 0.1), 0 4px 10px -2px rgba(37, 35, 52, 0.04)',
        }}
      >
        {/* Specular Light Sheen Highlight */}
        <div
          className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-white/25 pointer-events-none transition-opacity duration-300"
          style={{ opacity: isHovered ? 1 : 0 }}
        />

        {/* Mockup Window Header */}
        <div className="px-4 py-3 bg-pastel-lavender-light/50 dark:bg-pastel-surface-elevated border-b border-pastel-border dark:border-pastel-border-dark flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-2.5 h-2.5 rounded-full bg-pastel-rose dark:bg-rose-400" />
            <div className="w-2.5 h-2.5 rounded-full bg-pastel-peach dark:bg-amber-400" />
            <div className="w-2.5 h-2.5 rounded-full bg-pastel-mint dark:bg-emerald-400" />
            <span className="text-[11px] font-semibold text-pastel-charcoal dark:text-pastel-charcoal-light ml-2">
              Credence Studio
            </span>
          </div>

          <div className="flex items-center space-x-1.5">
            <Activity className="w-3 h-3 text-purple-600 dark:text-purple-300" />
            <span className="text-[10px] text-pastel-slate dark:text-pastel-slate-light font-mono font-medium">
              Multi-Source Index
            </span>
          </div>
        </div>

        {/* Phase Navigation Tabs */}
        <div className="flex items-center border-b border-pastel-border/60 dark:border-pastel-border-dark/60 bg-pastel-bg/50 dark:bg-pastel-surface-dark px-3 py-1.5 gap-1 overflow-x-auto text-[11px]">
          {phases.map((p, idx) => (
            <button
              key={p.id}
              onClick={() => setActivePhase(idx)}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all flex items-center space-x-1.5 whitespace-nowrap ${
                activePhase === idx
                  ? 'bg-pastel-lavender text-white shadow-2xs'
                  : 'text-pastel-slate dark:text-pastel-slate-light hover:bg-pastel-lavender-light/60 dark:hover:bg-pastel-surface-elevated'
              }`}
            >
              <span>{idx + 1}.</span>
              <span>{p.name}</span>
            </button>
          ))}
        </div>

        {/* Mockup Workspace Body */}
        <div className="p-4 sm:p-5 min-h-[340px] flex flex-col justify-between">
          {/* Top User Query */}
          <div className="bg-pastel-bg dark:bg-pastel-surface-elevated/40 rounded-xl p-3 border border-pastel-border/60 dark:border-pastel-border-dark/60 text-xs mb-3">
            <div className="flex items-center space-x-2 text-pastel-slate dark:text-pastel-slate-light mb-1 text-[10px] font-semibold uppercase tracking-wider">
              <span>Researcher Query</span>
            </div>
            <p className="text-pastel-charcoal dark:text-pastel-charcoal-light font-medium">
              "How significant is the global sea ice reduction and what peer-reviewed measurements verify this trend?"
            </p>
          </div>

          {/* Dynamic Phase Transition Container with 3D depth */}
          <div className="relative flex-1">
            {/* Phase 0: Standard AI Response */}
            {activePhase === 0 && (
              <div className="transition-all duration-500 animate-fade-in-up space-y-3">
                <div className="flex items-center space-x-2 text-[11px] text-pastel-lavender-dark dark:text-pastel-lavender font-medium">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Assistant Response Generated</span>
                </div>
                <div className="p-3.5 rounded-xl bg-white dark:bg-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark text-xs text-pastel-charcoal dark:text-pastel-charcoal-light leading-relaxed shadow-2xs">
                  According to satellite observations from NASA and the National Snow and Ice Data Center (NSIDC), Arctic sea ice minimum extent has declined at a rate of approximately 12.6% per decade since 1979 relative to the 1981–2010 average.
                </div>
                <div className="text-[11px] text-pastel-slate dark:text-pastel-slate-light flex items-center space-x-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-pastel-lavender" />
                  <span>Ready for factual claim segmentation...</span>
                </div>
              </div>
            )}

            {/* Phase 1: Claim Detection */}
            {activePhase === 1 && (
              <div className="transition-all duration-500 animate-fade-in-up space-y-3">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-purple-700 dark:text-purple-300 font-semibold flex items-center space-x-1.5">
                    <FileText className="w-3.5 h-3.5" />
                    <span>2 Factual Claims Detected</span>
                  </span>
                  <span className="text-[10px] bg-pastel-lavender-light dark:bg-pastel-surface-elevated text-purple-800 dark:text-purple-200 px-2 py-0.5 rounded-md border border-pastel-lavender-border">
                    Segmented
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white dark:bg-pastel-surface-elevated border border-pastel-lavender-border text-xs text-pastel-charcoal dark:text-pastel-charcoal-light leading-relaxed shadow-2xs">
                  According to{' '}
                  <span className="bg-pastel-blue-light/80 dark:bg-blue-950/60 text-blue-900 dark:text-blue-200 border-b-2 border-pastel-blue px-1 py-0.5 rounded font-medium">
                    satellite observations from NASA and NSIDC
                  </span>
                  , Arctic sea ice minimum extent has declined at a{' '}
                  <span className="bg-pastel-mint-light/80 dark:bg-emerald-950/60 text-emerald-900 dark:text-emerald-200 border-b-2 border-pastel-mint px-1 py-0.5 rounded font-medium">
                    rate of 12.6% per decade since 1979
                  </span>
                  .
                </div>

                <div className="space-y-1 text-[11px]">
                  <div className="flex items-center justify-between p-2 rounded-lg bg-pastel-bg dark:bg-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark">
                    <span className="font-mono text-pastel-slate dark:text-pastel-slate-light">Claim 01: NASA & NSIDC satellite dataset</span>
                    <span className="text-pastel-blue-dark dark:text-blue-300 font-medium">Pending match</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-pastel-bg dark:bg-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark">
                    <span className="font-mono text-pastel-slate dark:text-pastel-slate-light">Claim 02: 12.6% decadal reduction standard</span>
                    <span className="text-pastel-mint-dark dark:text-emerald-300 font-medium">Pending match</span>
                  </div>
                </div>
              </div>
            )}

            {/* Phase 2: Verification Progress */}
            {activePhase === 2 && (
              <div className="transition-all duration-500 animate-fade-in-up space-y-3">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-blue-700 dark:text-blue-300 font-semibold flex items-center space-x-1.5">
                    <Search className="w-3.5 h-3.5 animate-spin" />
                    <span>Cross-referencing Academic Index...</span>
                  </span>
                  <span className="font-mono text-xs font-semibold text-pastel-charcoal dark:text-white">78%</span>
                </div>

                {/* Animated Progress Bar */}
                <div className="w-full bg-pastel-border/60 dark:bg-pastel-surface-elevated h-2.5 rounded-full overflow-hidden p-0.5">
                  <div className="bg-pastel-lavender h-full rounded-full w-4/5 transition-all duration-700" />
                </div>

                <div className="space-y-1.5 text-[11px] pt-1">
                  <div className="flex items-center space-x-2 text-pastel-charcoal dark:text-pastel-charcoal-light">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    <span>Segmenting statement into testable assertions</span>
                  </div>
                  <div className="flex items-center space-x-2 text-pastel-charcoal dark:text-pastel-charcoal-light">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    <span>Querying NASA Earth Observatory & NOAA indices</span>
                  </div>
                  <div className="flex items-center space-x-2 text-purple-700 dark:text-purple-300 font-medium">
                    <div className="w-3.5 h-3.5 flex items-center justify-center">
                      <span className="w-2 h-2 rounded-full bg-pastel-lavender animate-ping" />
                    </div>
                    <span>Synthesizing evidence relevance & trust scores</span>
                  </div>
                </div>
              </div>
            )}

            {/* Phase 3: Evidence Result */}
            {activePhase === 3 && (
              <div className="transition-all duration-500 animate-fade-in-up space-y-3">
                {/* Result Header Badge */}
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-pastel-mint-light/70 dark:bg-emerald-950/40 border border-pastel-mint-border">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-lg bg-emerald-600 text-white flex items-center justify-center">
                      <CheckCircle className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-emerald-900 dark:text-emerald-200">
                        VERIFIED (94% Trust Score)
                      </span>
                      <p className="text-[10px] text-emerald-800 dark:text-emerald-300">
                        Corroborated by 2 peer-reviewed sources
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white dark:bg-pastel-surface-dark text-emerald-800 dark:text-emerald-200 border border-pastel-mint-border">
                    High Confidence
                  </span>
                </div>

                {/* Evidence Item */}
                <div className="p-3 rounded-xl bg-white dark:bg-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark space-y-1.5 shadow-2xs">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-semibold text-purple-700 dark:text-purple-300 flex items-center space-x-1">
                      <span>NASA Earth Observatory (2024 Report)</span>
                      <ExternalLink className="w-3 h-3 text-purple-500" />
                    </span>
                    <span className="text-[10px] bg-pastel-mint-light text-emerald-800 dark:text-emerald-300 px-1.5 py-0.5 rounded font-medium">
                      Relevance: 96%
                    </span>
                  </div>
                  <p className="text-[11px] text-pastel-slate dark:text-pastel-slate-light leading-normal italic">
                    "Satellite observations confirm Arctic sea ice extent decline at 12.6% per decade relative to 1981–2010..."
                  </p>
                </div>

                <div className="flex items-center justify-between text-[11px] pt-1">
                  <span className="text-pastel-slate dark:text-pastel-slate-light">
                    Source corroboration confirmed
                  </span>
                  <Link
                    href="/chat"
                    className="text-purple-600 dark:text-purple-300 font-semibold hover:underline flex items-center space-x-1"
                  >
                    <span>Open in workspace</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Mockup Bottom Controls */}
          <div className="mt-4 pt-3 border-t border-pastel-border/60 dark:border-pastel-border-dark/60 flex items-center justify-between text-[11px] text-pastel-slate dark:text-pastel-slate-light">
            <span>Cycle auto-advancing</span>
            <div className="flex items-center space-x-1.5">
              {phases.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setActivePhase(idx)}
                  className={`h-1.5 rounded-full transition-all ${
                    activePhase === idx ? 'w-5 bg-pastel-lavender' : 'w-1.5 bg-pastel-border dark:bg-pastel-border-dark'
                  }`}
                  aria-label={`View step ${idx + 1}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
