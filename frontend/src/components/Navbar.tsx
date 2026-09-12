'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from './ThemeProvider';
import { ShieldCheck, Moon, Sun, Menu, X, ArrowRight } from 'lucide-react';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Home', href: '/' },
    { name: 'Chat', href: '/chat' },
    { name: 'Verification', href: '/verification' },
    { name: 'Extension', href: '/extension' },
    { name: 'About', href: '/about' },
  ];

  return (
    <header
      className={`sticky top-0 z-40 transition-all duration-300 w-full ${
        scrolled
          ? 'py-2.5 bg-white/90 dark:bg-pastel-surface-dark/90 backdrop-blur-md shadow-xs border-b border-pastel-border dark:border-pastel-border-dark'
          : 'py-4 bg-transparent border-b border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center space-x-2.5 group focus:outline-none">
          <div className="w-9 h-9 rounded-xl bg-pastel-lavender/20 dark:bg-pastel-lavender/30 border border-pastel-lavender flex items-center justify-center text-pastel-lavender-dark dark:text-pastel-lavender transition-transform group-hover:scale-105">
            <ShieldCheck className="w-5 h-5 text-purple-600 dark:text-purple-300" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-base tracking-tight text-pastel-charcoal dark:text-pastel-charcoal-light">
              Credence
            </span>
            <span className="text-[10px] text-pastel-slate dark:text-pastel-slate-light font-medium tracking-wide uppercase">
              AI Verification
            </span>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center space-x-1 bg-pastel-lavender-light/60 dark:bg-pastel-surface-dark/60 p-1 rounded-full border border-pastel-border dark:border-pastel-border-dark">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-white dark:bg-pastel-surface-elevated text-pastel-charcoal dark:text-white shadow-2xs'
                    : 'text-pastel-slate dark:text-pastel-slate-light hover:text-pastel-charcoal dark:hover:text-white'
                }`}
              >
                {link.name}
              </Link>
            );
          })}
        </nav>

        {/* Actions (Theme toggle + CTA) */}
        <div className="hidden md:flex items-center space-x-3">
          <button
            onClick={toggleTheme}
            aria-label="Toggle color theme"
            className="p-2 rounded-xl text-pastel-slate hover:text-pastel-charcoal dark:text-pastel-slate-light dark:hover:text-white hover:bg-pastel-lavender-light dark:hover:bg-pastel-surface-elevated transition-colors"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-300" /> : <Moon className="w-4 h-4" />}
          </button>

          <Link
            href="/chat"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-medium bg-pastel-lavender hover:bg-pastel-lavender-hover text-white shadow-pastel hover:shadow-pastel-hover transition-all transform active:scale-95"
          >
            <span>Start verifying</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Mobile menu toggle */}
        <div className="flex items-center space-x-2 md:hidden">
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="p-2 rounded-lg text-pastel-slate dark:text-pastel-slate-light"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-300" /> : <Moon className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Open menu"
            className="p-2 rounded-lg text-pastel-charcoal dark:text-white hover:bg-pastel-lavender-light dark:hover:bg-pastel-surface-elevated transition-colors"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden px-4 pt-3 pb-5 bg-white dark:bg-pastel-surface-dark border-b border-pastel-border dark:border-pastel-border-dark space-y-2">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm font-medium ${
                pathname === link.href
                  ? 'bg-pastel-lavender-light dark:bg-pastel-surface-elevated text-purple-700 dark:text-purple-300 font-semibold'
                  : 'text-pastel-slate dark:text-pastel-slate-light'
              }`}
            >
              {link.name}
            </Link>
          ))}
          <div className="pt-2">
            <Link
              href="/chat"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-pastel-lavender hover:bg-pastel-lavender-hover text-white shadow-pastel"
            >
              <span>Start verifying</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
