import React, { useState } from 'react';
import { ArrowRight, ChevronRight } from 'lucide-react';

interface ExpandableCardProps {
  title: string;
  description: string;
  icon: React.ElementType;
  iconBg?: string;
  iconColor?: string;
  ctaText?: string;
  onClickCta?: () => void;
  features?: string[];
  badge?: string;
  className?: string;
  theme?: 'light' | 'dark';
}

export const ExpandableCard: React.FC<ExpandableCardProps> = ({
  title,
  description,
  icon: Icon,
  iconBg,
  iconColor,
  ctaText = 'Open',
  onClickCta,
  features = [],
  badge,
  className = '',
  theme = 'light',
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const isDark = theme === 'dark';

  const active = isHovered || isFocused;

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      tabIndex={0}
      className={`rounded-[2.2rem] border p-6 transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] cursor-pointer group outline-none relative overflow-hidden flex flex-col justify-between ${
        isDark
          ? `bg-[#23262F] border-[#333742] ${
              active 
                ? 'shadow-xl border-[#B6FF2E]/50 -translate-y-0.5 shadow-[0_0_25px_rgba(182,255,46,0.12)]' 
                : 'shadow-xs hover:border-[#B6FF2E]/30'
            }`
          : `bg-[#FFFDFA] border-[#E9D6C4] ${
              active 
                ? 'shadow-lg border-[#800020]/40 -translate-y-0.5 bg-white' 
                : 'shadow-xs hover:border-[#800020]/40'
            }`
      } ${className}`}
    >
      <div>
        {/* Top Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div 
              className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-transform duration-200 group-hover:scale-105 ${
                iconBg && iconColor 
                  ? `${iconBg} ${iconColor}`
                  : isDark 
                    ? 'bg-[#181A20] text-[#B6FF2E] border border-[#B6FF2E]/25 shadow-[0_0_10px_rgba(182,255,46,0.15)]' 
                    : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
              }`}
            >
              <Icon size={20} strokeWidth={2.2} />
            </div>
            <div>
              <h4 className={`font-extrabold text-sm md:text-base tracking-tight transition-colors ${
                isDark ? 'text-white group-hover:text-[#B6FF2E]' : 'text-[#2E0A12] group-hover:text-[#800020]'
              }`}>
                {title}
              </h4>
              {badge && (
                <span className={`text-[10px] font-bold uppercase tracking-wider ${
                  isDark ? 'text-slate-400' : 'text-[#800020]'
                }`}>
                  {badge}
                </span>
              )}
            </div>
          </div>

          <div className={`transition-colors ${
            isDark ? 'text-slate-400 group-hover:text-[#B6FF2E]' : 'text-[#800020]/50 group-hover:text-[#800020]'
          }`}>
            <ChevronRight 
              size={18} 
              className="transition-transform duration-200 group-hover:translate-x-1" 
            />
          </div>
        </div>

        {/* Short description */}
        <p className={`text-xs leading-relaxed mb-3 ${
          isDark ? 'text-slate-300' : 'text-[#4D5745]'
        }`}>
          {description}
        </p>

        {/* Supporting content that gently reveals on hover/focus */}
        {features.length > 0 && (
          <div 
            className={`transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] overflow-hidden ${
              active 
                ? `max-h-36 opacity-100 mt-3 pt-3 border-t ${isDark ? 'border-[#333742]' : 'border-[#E9D6C4]'}` 
                : 'max-h-0 opacity-0 mt-0 pt-0'
            }`}
          >
            <ul className="space-y-1.5 text-[11px] font-medium">
              {features.map((feat, idx) => (
                <li key={idx} className={`flex items-center gap-2 ${
                  isDark ? 'text-slate-300' : 'text-[#4D5745]'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    isDark ? 'bg-[#B6FF2E]' : 'bg-[#800020]'
                  }`} />
                  <span>{feat}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className={`mt-5 pt-3 border-t flex items-center justify-between ${
        isDark ? 'border-[#333742]' : 'border-[#E9D6C4]'
      }`}>
        <span className={`text-[11px] font-semibold ${
          isDark ? 'text-slate-400' : 'text-[#800020]/70'
        }`}>
          Workspace
        </span>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onClickCta?.();
          }}
          className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer active:scale-95 ${
            isDark
              ? 'bg-[#B6FF2E] hover:bg-[#A3E823] text-[#181A20] shadow-[0_0_12px_rgba(182,255,46,0.3)]'
              : 'bg-[#800020] hover:bg-[#711C32] text-[#FBF1E3] shadow-xs'
          }`}
        >
          <span>{ctaText}</span>
          <ArrowRight size={13} />
        </button>
      </div>
    </div>
  );
};
