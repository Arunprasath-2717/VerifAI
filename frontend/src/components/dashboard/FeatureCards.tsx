import React from 'react';
import { ShieldCheck, MessageSquare, BookOpen, ArrowUpRight } from 'lucide-react';

interface FeatureCardsProps {
  onOpenVerify: () => void;
  onOpenChat: () => void;
  onOpenKnowledge: () => void;
  onViewAll?: () => void;
}

export const FeatureCards: React.FC<FeatureCardsProps> = ({
  onOpenVerify,
  onOpenChat,
  onOpenKnowledge,
  onViewAll,
}) => {
  return (
    <section className="space-y-4">
      {/* Section Header - Reference Replica */}
      <div className="flex items-center justify-between px-2">
        <h3 className="font-extrabold text-base md:text-lg text-slate-900 tracking-tight">
          Recommended Actions
        </h3>
        <button 
          onClick={onViewAll}
          className="text-xs font-bold text-slate-400 hover:text-slate-900 uppercase tracking-wider transition-colors cursor-pointer"
        >
          View All
        </button>
      </div>

      {/* 3 Horizontal Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Card 1: Paste & Verify (Light) */}
        <div 
          onClick={onOpenVerify}
          className="bg-white p-6 rounded-[2.2rem] border border-slate-200/70 shadow-sm flex flex-col justify-between hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer group"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-slate-900">
                Paste & Verify
              </h4>
              <div className="flex -space-x-1.5 items-center">
                <span className="w-6 h-6 rounded-full bg-emerald-100 border-2 border-white flex items-center justify-center text-[9px] font-bold text-emerald-800">
                  AI
                </span>
                <span className="w-6 h-6 rounded-full bg-blue-100 border-2 border-white flex items-center justify-center text-[9px] font-bold text-blue-800">
                  G
                </span>
                <span className="w-6 h-6 rounded-full bg-slate-100 border-2 border-white flex items-center justify-center text-[8px] font-bold text-slate-600">
                  +3
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed line-clamp-3 mb-6">
              Verify a single AI-generated answer with claim-level evidence, citations, and trust scores.
            </p>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-700 text-xs font-semibold tabular-nums">
              <ShieldCheck size={14} className="text-blue-600" />
              <span>1.5k verifications</span>
            </div>
            <button className="text-blue-600 text-xs font-bold flex items-center gap-0.5 group-hover:translate-x-0.5 transition-transform">
              <span>Verify</span>
              <ArrowUpRight size={13} />
            </button>
          </div>
        </div>

        {/* Card 2: AI Chat (DARK CARD - Signature Reference Replica!) */}
        <div 
          onClick={onOpenChat}
          className="bg-[#111111] text-white p-6 rounded-[2.2rem] shadow-md flex flex-col justify-between hover:bg-black hover:shadow-lg hover:-translate-y-0.5 transition-all cursor-pointer group relative overflow-hidden"
        >
          {/* Subtle glow accent */}
          <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl pointer-events-none" />

          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-white tracking-wide">
                AI Chat
              </h4>
              <div className="flex -space-x-1.5 items-center">
                <span className="w-6 h-6 rounded-full bg-slate-800 border-2 border-slate-900 flex items-center justify-center text-[9px] font-bold text-slate-300">
                  G
                </span>
                <span className="w-6 h-6 rounded-full bg-slate-800 border-2 border-slate-900 flex items-center justify-center text-[9px] font-bold text-slate-300">
                  C
                </span>
                <span className="w-6 h-6 rounded-full bg-slate-800 border-2 border-slate-900 flex items-center justify-center text-[8px] font-bold text-slate-400">
                  +1
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed line-clamp-3 mb-6">
              Compare answers from up to three models and verify claims simultaneously in an interactive workspace.
            </p>
          </div>

          <div className="relative z-10 flex items-center justify-between pt-4 border-t border-white/10">
            <div className="flex items-center gap-1.5 text-slate-300 text-xs font-semibold tabular-nums">
              <MessageSquare size={14} className="text-blue-400" />
              <span>4.2k messages</span>
            </div>
            <button className="text-white text-xs font-bold flex items-center gap-0.5 group-hover:translate-x-0.5 transition-transform">
              <span>Open Chat</span>
              <ArrowUpRight size={13} />
            </button>
          </div>
        </div>

        {/* Card 3: Knowledge Base (Light) */}
        <div 
          onClick={onOpenKnowledge}
          className="bg-white p-6 rounded-[2.2rem] border border-slate-200/70 shadow-sm flex flex-col justify-between hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer group"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-slate-900">
                Knowledge Base
              </h4>
              <div className="flex -space-x-1.5 items-center">
                <span className="w-6 h-6 rounded-full bg-amber-100 border-2 border-white flex items-center justify-center text-[9px] font-bold text-amber-800">
                  KB
                </span>
                <span className="w-6 h-6 rounded-full bg-slate-100 border-2 border-white flex items-center justify-center text-[8px] font-bold text-slate-600">
                  PDF
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed line-clamp-3 mb-6">
              Use your private documents and regulatory guidelines as trusted ground-truth for automated verifications.
            </p>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-700 text-xs font-semibold tabular-nums">
              <BookOpen size={14} className="text-blue-600" />
              <span>128 sources</span>
            </div>
            <button className="text-blue-600 text-xs font-bold flex items-center gap-0.5 group-hover:translate-x-0.5 transition-transform">
              <span>Explore</span>
              <ArrowUpRight size={13} />
            </button>
          </div>
        </div>

      </div>
    </section>
  );
};
