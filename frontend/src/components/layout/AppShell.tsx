"use client";

import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence, useScroll, useSpring, useReducedMotion } from 'motion/react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { NotificationDrawer } from '../modals/NotificationDrawer';
import { UserSettings, NotificationItem } from '../../types';

// ============================================================================
// MOTION SYSTEM SPECIFICATION & DESIGN TOKENS
// ============================================================================
/**
 * 1. Durations:
 *    - fast (180ms): Micro-interactions, button presses, tooltips
 *    - base (350ms): Card reveals, drawer springs, route transitions
 *    - slow (750ms): Ambient lighting shifts, aura pulses, page loading
 */
export const MOTION_DURATIONS = {
  fast: 0.22,
  base: 0.45,
  slow: 0.75,
} as const;

/**
 * 2. Easing Curves:
 *    - entrance: cubic-bezier(0.22, 1, 0.36, 1) - Natural deceleration with slight overshoot
 *    - exit:     cubic-bezier(0.4, 0, 0.2, 1)   - Crisp responsive acceleration
 *    - spring:   Physical bounce (stiffness: 380, damping: 28, bounce: 0.12)
 */
export const MOTION_EASINGS = {
  entrance: [0.22, 1, 0.36, 1] as const,
  exit: [0.4, 0, 0.2, 1] as const,
  spring: { type: 'spring' as const, stiffness: 380, damping: 28, bounce: 0.12 },
  gentleSpring: { type: 'spring' as const, stiffness: 220, damping: 24 },
} as const;

/** 3. Stagger increment rule (40ms per sequential item) */
export const MOTION_STAGGER = 0.04;

interface AppShellProps {
  userSettings: UserSettings;
  notifications: NotificationItem[];
  onMarkAllNotificationsRead: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
  onLogout?: () => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  userSettings,
  notifications,
  onMarkAllNotificationsRead,
  searchQuery,
  onSearchChange,
  theme = 'light',
  onToggleTheme,
  onLogout,
}) => {
  const [isSidebarHovered, setIsSidebarHovered] = useState(false);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  const location = useLocation();
  const shouldReduceMotion = useReducedMotion();
  const isDark = theme === 'dark';
  const isDashboard = location.pathname === '/dashboard' || location.pathname === '/dashboard/';

  // --------------------------------------------------------------------------
  // 1. SCROLL PROGRESS INDICATOR (Kinetic Spring Smoothing)
  // --------------------------------------------------------------------------
  const { scrollYProgress, scrollY } = useScroll();
  const smoothScrollProgress = useSpring(scrollYProgress, {
    stiffness: 380,
    damping: 32,
    restDelta: 0.001,
  });

  // Track scroll position to dynamically elevate top navigation chrome
  useEffect(() => {
    return scrollY.on('change', (latest) => {
      setIsScrolled(latest > 20);
    });
  }, [scrollY]);

  // --------------------------------------------------------------------------
  // 2. AMBIENT CURSOR-FOLLOW SPOTLIGHT GLOW (Pointer Fine Only)
  // --------------------------------------------------------------------------
  const [mousePos, setMousePos] = useState({ x: -1000, y: -1000 });
  const [isFinePointer, setIsFinePointer] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(hover: hover) and (pointer: fine)');
    setIsFinePointer(mediaQuery.matches);

    const handlePointerMove = (e: PointerEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
    };

    if (mediaQuery.matches && !shouldReduceMotion) {
      window.addEventListener('pointermove', handlePointerMove, { passive: true });
    }

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
    };
  }, [shouldReduceMotion]);

  const smoothMouseX = useSpring(mousePos.x, { damping: 28, stiffness: 180, mass: 0.4 });
  const smoothMouseY = useSpring(mousePos.y, { damping: 28, stiffness: 180, mass: 0.4 });

  useEffect(() => {
    if (isFinePointer) {
      smoothMouseX.set(mousePos.x);
      smoothMouseY.set(mousePos.y);
    }
  }, [mousePos.x, mousePos.y, isFinePointer, smoothMouseX, smoothMouseY]);

  return (
    <div
      className={`min-h-screen flex font-sans antialiased overflow-x-hidden transition-colors duration-500 relative ${
        isDark
          ? 'bg-[#181A20] text-slate-100 selection:bg-[#B6FF2E] selection:text-[#181A20]'
          : 'bg-[#FFF9F2] text-[#2E0A12] selection:bg-[#800020] selection:text-[#FFF9F2]'
      }`}
    >
      {/* ───────────────────────────────────────────────────────────────────
          SCENE 1: Reading/Scroll Progress Bar with Glow Rim
          ─────────────────────────────────────────────────────────────────── */}
      <motion.div
        aria-hidden="true"
        className="fixed top-0 left-0 right-0 h-[2.5px] z-50 origin-left pointer-events-none"
        style={{
          scaleX: shouldReduceMotion ? 1 : smoothScrollProgress,
          background: isDark
            ? 'linear-gradient(90deg, #B6FF2E 0%, #A3E823 50%, #B6FF2E 100%)'
            : 'linear-gradient(90deg, #800020 0%, #D45060 50%, #800020 100%)',
          boxShadow: isDark
            ? '0 0 12px rgba(182, 255, 46, 0.65)'
            : '0 0 10px rgba(128, 0, 32, 0.45)',
        }}
      />

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 2: Ambient Cursor-Follow Spotlight (Disabled on touch / reduced motion)
          ─────────────────────────────────────────────────────────────────── */}
      {isFinePointer && !shouldReduceMotion && (
        <motion.div
          aria-hidden="true"
          className="fixed pointer-events-none rounded-full -z-10 blur-3xl will-change-transform"
          style={{
            x: smoothMouseX,
            y: smoothMouseY,
            translateX: '-50%',
            translateY: '-50%',
            width: 520,
            height: 520,
            background: isDark
              ? 'radial-gradient(circle, rgba(182, 255, 46, 0.045) 0%, rgba(182, 255, 46, 0) 70%)'
              : 'radial-gradient(circle, rgba(128, 0, 32, 0.035) 0%, rgba(128, 0, 32, 0) 70%)',
          }}
        />
      )}

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 3: Desktop Fixed Sidebar Dock (Kinetic Spring Expansion)
          ─────────────────────────────────────────────────────────────────── */}
      <motion.div
        className="hidden lg:block shrink-0 ml-4"
        animate={{ width: isSidebarHovered ? 270 : 84 }}
        transition={
          shouldReduceMotion
            ? { duration: 0.1 }
            : { duration: 1.0, ease: [0.16, 1, 0.3, 1] }
        }
      >
        <Sidebar
          userSettings={userSettings}
          onHoverChange={setIsSidebarHovered}
          theme={theme}
          onLogout={onLogout}
        />
      </motion.div>

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 4: Mobile Navigation Drawer (Spring Physics & Blur Crossfade)
          ─────────────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {isMobileDrawerOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: MOTION_DURATIONS.fast, ease: MOTION_EASINGS.exit }}
              onClick={() => setIsMobileDrawerOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-xs cursor-pointer"
            />
            <motion.div
              initial={shouldReduceMotion ? { opacity: 0 } : { x: '-100%' }}
              animate={shouldReduceMotion ? { opacity: 1 } : { x: 0 }}
              exit={shouldReduceMotion ? { opacity: 0 } : { x: '-100%' }}
              transition={
                shouldReduceMotion
                  ? { duration: MOTION_DURATIONS.fast }
                  : { ...MOTION_EASINGS.spring, stiffness: 320, damping: 30 }
              }
              className="relative z-50 h-full w-[280px] shadow-2xl"
            >
              <Sidebar
                userSettings={userSettings}
                isMobileDrawer={true}
                onCloseMobileDrawer={() => setIsMobileDrawerOpen(false)}
                theme={theme}
                onLogout={onLogout}
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 5: Main Workspace Container & Dynamic Sticky Header
          ─────────────────────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col px-4 sm:px-8 py-6 max-w-[1600px] mx-auto w-full min-w-0 transition-all duration-500">
        <header
          className={`sticky top-0 z-30 transition-all duration-300 -mx-4 sm:-mx-8 px-4 sm:px-8 pt-2 pb-4 ${
            isScrolled
              ? isDark
                ? 'bg-[#181A20]/80 backdrop-blur-md border-b border-[#333742]/60 shadow-lg shadow-black/20'
                : 'bg-[#FFF9F2]/80 backdrop-blur-md border-b border-[#E9D6C4]/60 shadow-md shadow-[#800020]/05'
              : 'bg-transparent'
          }`}
        >
          <Topbar
            userSettings={userSettings}
            notifications={notifications}
            onOpenNotifications={() => setIsNotificationsOpen(true)}
            onOpenMobileMenu={() => setIsMobileDrawerOpen(true)}
            searchQuery={searchQuery}
            onSearchChange={onSearchChange}
            theme={theme}
            onToggleTheme={onToggleTheme}
            onLogout={onLogout}
          />
        </header>

        {/* ─────────────────────────────────────────────────────────────────
            SCENE 6: Dynamic Page Content (Kinetic Route Transitions)
            ───────────────────────────────────────────────────────────────── */}
        <main
          className={`flex-1 w-full min-w-0 mt-2 ${!isDashboard ? 'non-dashboard-workspace' : ''}`}
        >
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={location.pathname}
              initial={
                shouldReduceMotion
                  ? { opacity: 0 }
                  : { opacity: 0, y: 12, filter: 'blur(4px)', scale: 0.996 }
              }
              animate={
                shouldReduceMotion
                  ? { opacity: 1 }
                  : { opacity: 1, y: 0, filter: 'blur(0px)', scale: 1 }
              }
              exit={
                shouldReduceMotion
                  ? { opacity: 0 }
                  : { opacity: 0, y: -8, filter: 'blur(2px)', scale: 0.998 }
              }
              transition={{
                duration: MOTION_DURATIONS.base,
                ease: MOTION_EASINGS.entrance,
              }}
              className="w-full min-w-0"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 7: Slide-over Notifications Drawer (Spring Physics & Stagger)
          ─────────────────────────────────────────────────────────────────── */}
      <NotificationDrawer
        isOpen={isNotificationsOpen}
        onClose={() => setIsNotificationsOpen(false)}
        notifications={notifications}
        onMarkAllAsRead={onMarkAllNotificationsRead}
      />
    </div>
  );
};

export default AppShell;
