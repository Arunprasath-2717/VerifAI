import React from 'react';
import { BorderGlow } from './BorderGlow';
import { useTheme } from '../../context/ThemeContext';

export interface BorderGlowButtonProps {
  children: React.ReactNode;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
  className?: string;
  theme?: 'light' | 'dark';
  variant?: 'primary' | 'secondary' | 'accent';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  glowColor?: string;
  colors?: string[];
}

export const BorderGlowButton: React.FC<BorderGlowButtonProps> = ({
  children,
  onClick,
  type = 'button',
  disabled = false,
  className = '',
  theme: propTheme,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  glowColor,
  colors,
}) => {
  const context = useTheme();
  const isDark = (propTheme || context.theme) === 'dark';

  // Theme-aware HSL and mesh gradient palettes
  const defaultDarkGlow = '80 100 60'; // Electric Lime Spark
  const defaultLightGlow = '348 100 25'; // Deep Burgundy
  const resolvedGlowColor = glowColor || (isDark ? defaultDarkGlow : defaultLightGlow);

  const defaultDarkColors = ['#B6FF2E', '#A3E823', '#2E3340'];
  const defaultLightColors = ['#800020', '#D45060', '#F3E6D5'];
  const resolvedColors = colors || (isDark ? defaultDarkColors : defaultLightColors);

  // Background and text styling based on variant & theme
  const getButtonStyles = () => {
    if (variant === 'primary') {
      if (isDark) {
        return {
          bg: '#B6FF2E',
          textClass: 'text-[#12141A] font-black',
          borderClass: 'border-[#B6FF2E]/60 shadow-[0_0_20px_rgba(182,255,46,0.3)]',
        };
      } else {
        return {
          bg: '#800020',
          textClass: 'text-[#FFF9F2] font-bold',
          borderClass: 'border-[#6E001A] shadow-md shadow-[#800020]/25',
        };
      }
    } else if (variant === 'accent') {
      if (isDark) {
        return {
          bg: '#1E2129',
          textClass: 'text-[#B6FF2E] font-extrabold',
          borderClass: 'border-[#333742] shadow-[0_0_15px_rgba(182,255,46,0.15)]',
        };
      } else {
        return {
          bg: '#F3E6D5',
          textClass: 'text-[#4A0A18] font-extrabold',
          borderClass: 'border-[#D4B8A4] shadow-xs',
        };
      }
    } else {
      // Secondary
      if (isDark) {
        return {
          bg: '#1E2129',
          textClass: 'text-slate-100 hover:text-white font-bold',
          borderClass: 'border-[#2E3340]',
        };
      } else {
        return {
          bg: '#FFFFFF',
          textClass: 'text-[#5C3040] hover:text-[#1E0A10] font-bold',
          borderClass: 'border-[#E5D3C0]',
        };
      }
    }
  };

  const { bg, textClass, borderClass } = getButtonStyles();

  const sizeClasses = {
    sm: 'px-3.5 py-1.5 text-xs',
    md: 'px-5 py-2.5 text-xs md:text-sm',
    lg: 'px-7 py-3 text-sm md:text-base font-bold',
  }[size];

  const radius = size === 'sm' ? 14 : size === 'lg' ? 20 : 16;

  return (
    <BorderGlow
      edgeSensitivity={45}
      glowColor={resolvedGlowColor}
      backgroundColor={bg}
      borderRadius={radius}
      glowRadius={24}
      glowIntensity={1.3}
      coneSpread={30}
      colors={resolvedColors}
      className={`inline-block ${fullWidth ? 'w-full' : ''} ${disabled ? 'opacity-50 pointer-events-none cursor-not-allowed' : 'cursor-pointer active:scale-95 transition-transform'}`}
    >
      <button
        type={type}
        disabled={disabled}
        onClick={onClick}
        className={`w-full flex items-center justify-center gap-2 rounded-[inherit] transition-all outline-none ${sizeClasses} ${textClass} ${borderClass} ${className}`}
      >
        {children}
      </button>
    </BorderGlow>
  );
};

export default BorderGlowButton;
