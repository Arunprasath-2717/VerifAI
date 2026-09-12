'use client';

import React, { useRef, useState } from 'react';
import Link from 'next/link';
import { ArrowUpRight } from 'lucide-react';

interface FeatureCardProps {
  icon: React.ReactNode;
  iconBgColor?: string;
  iconTextColor?: string;
  title: string;
  description: string;
  tag?: string;
  link?: string;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  iconBgColor = 'bg-pastel-lavender-light dark:bg-purple-950/40',
  iconTextColor = 'text-purple-700 dark:text-purple-300',
  title,
  description,
  tag,
  link,
}) => {
  const [tilt, setTilt] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState<boolean>(false);
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion || !cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -4;
    const rotateY = ((x - centerX) / centerX) * 4;

    setTilt({ x: rotateX, y: rotateY });
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    setTilt({ x: 0, y: 0 });
  };

  const cardContent = (
    <div
      ref={cardRef}
      onMouseEnter={() => setIsHovered(true)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative bg-white dark:bg-pastel-surface-dark border border-pastel-border dark:border-pastel-border-dark rounded-3xl p-6 sm:p-7 shadow-pastel-card hover:border-pastel-lavender dark:hover:border-pastel-lavender transition-all duration-200 ease-out flex flex-col justify-between h-full group overflow-hidden [perspective:1000px] [transform-style:preserve-3d]"
      style={{
        transform: `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) translateY(${isHovered ? '-4px' : '0px'})`,
        boxShadow: isHovered
          ? '0 16px 32px -8px rgba(167, 139, 250, 0.18), 0 6px 12px -3px rgba(37, 35, 52, 0.05)'
          : '0 2px 10px -2px rgba(37, 35, 52, 0.04)',
      }}
    >
      {/* Subtle Specular Sheen on Hover */}
      <div
        className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-pastel-lavender/10 pointer-events-none transition-opacity duration-300"
        style={{ opacity: isHovered ? 1 : 0 }}
      />

      <div>
        <div className="flex items-center justify-between mb-4">
          <div
            className={`w-11 h-11 rounded-2xl ${iconBgColor} ${iconTextColor} flex items-center justify-center transition-transform duration-300 group-hover:scale-110 shadow-2xs`}
          >
            {icon}
          </div>
          {tag && (
            <span className="text-[10px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-pastel-bg dark:bg-pastel-surface-elevated text-pastel-slate dark:text-pastel-slate-light border border-pastel-border/60">
              {tag}
            </span>
          )}
        </div>

        <h4 className="text-base sm:text-lg font-bold text-pastel-charcoal dark:text-pastel-charcoal-light mb-2 group-hover:text-purple-700 dark:group-hover:text-purple-300 transition-colors">
          {title}
        </h4>

        <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light leading-relaxed">
          {description}
        </p>
      </div>

      {link && (
        <div className="pt-4 mt-4 border-t border-pastel-border/60 dark:border-pastel-border-dark/60 flex items-center text-xs font-semibold text-purple-600 dark:text-purple-300 space-x-1">
          <span>Explore feature</span>
          <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </div>
      )}
    </div>
  );

  if (link) {
    return <Link href={link} className="block h-full">{cardContent}</Link>;
  }

  return cardContent;
};
