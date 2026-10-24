import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutGrid,
  ShieldCheck,
  MessageSquare,
  BookOpen,
  Clock3,
  BarChart3,
  Settings,
  LogOut,
  X,
  Trophy
} from 'lucide-react';
import { UserSettings } from '../../types';

interface SidebarProps {
  userSettings: UserSettings;
  onHoverChange?: (hovered: boolean) => void;
  isMobileDrawer?: boolean;
  onCloseMobileDrawer?: () => void;
  theme?: 'light' | 'dark';
  onLogout?: () => void;
}

interface SidebarDockItemProps {
  path: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string; strokeWidth?: number }>;
  isActive: boolean;
  expanded: boolean;
  isMobileDrawer: boolean;
  onClick: () => void;
  theme?: 'light' | 'dark';
}

const SidebarDockItem: React.FC<SidebarDockItemProps> = ({
  path,
  label,
  icon: Icon,
  isActive,
  expanded,
  isMobileDrawer,
  onClick,
  theme = 'light',
}) => {
  const isDark = theme === 'dark';

  return (
    <button
      key={path}
      onClick={onClick}
      title={!expanded ? label : undefined}
      className={`group min-h-11 rounded-xl flex items-center w-full cursor-pointer relative sidebar-nav-hover ${
        isActive
          ? `sidebar-nav-active-glow ${isDark ? 'text-[#181A20]' : 'text-[#1B4332]'}`
          : isDark
            ? 'text-slate-400 hover:text-white hover:bg-white/10'
            : 'text-white/90 hover:text-white hover:bg-white/10'
      }`}
    >
      {/* Selected Background */}
      {isActive && (
        <div className={`absolute inset-0 rounded-xl pointer-events-none -z-10 transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
          isDark
            ? 'bg-[#B6FF2E] border border-[#B6FF2E]/40 shadow-[0_0_16px_rgba(182,255,46,0.25)]'
            : 'bg-[#D8F3DC] border border-[#D8F3DC] shadow-[0_0_12px_rgba(116,198,157,0.35)]'
        }`} />
      )}

      {/* Centered slot */}
      <div className="w-10 h-11 flex items-center justify-center shrink-0">
        <Icon
          size={19}
          strokeWidth={isActive ? 2.5 : 2}
          className={`transition-all duration-200 ${
            isActive
              ? isDark
                ? 'text-[#181A20]'
                : 'text-[#1B4332]'
              : isDark
                ? 'text-slate-400 group-hover:text-white'
                : 'text-white/85 group-hover:text-white'
          }`}
        />
      </div>

      {/* Fluid text label container */}
      <div
        className={`verifai-sidebar-reveal flex items-center justify-between flex-1 min-w-0 overflow-hidden ${
          expanded
            ? 'opacity-100 max-w-[200px] translate-x-0 pr-2.5'
            : 'opacity-0 max-w-0 -translate-x-2 pointer-events-none'
        }`}
      >
        <span className={`whitespace-nowrap text-[15px] leading-5 truncate ${
          isActive
            ? isDark ? 'text-[#181A20] font-bold' : 'text-[#1B4332] font-bold'
            : isDark ? 'text-slate-300 font-semibold' : 'text-white/90 font-semibold'
        }`}>
          {label}
        </span>

        {isActive && (
          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ml-1.5 ${
            isDark
              ? 'bg-[#181A20]'
              : 'bg-[#1B4332]'
          }`} />
        )}
      </div>

      {/* Floating Tooltip on collapsed hover */}
      {!expanded && !isMobileDrawer && (
        <div className={`absolute left-[calc(100%+8px)] px-2.5 py-1 text-[15px] font-semibold rounded-lg whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 shadow-lg border z-50 translate-x-1 group-hover:translate-x-0 ${
          isDark
            ? 'bg-[#181A20] text-[#B6FF2E] border-[#333742] shadow-black/50'
            : 'bg-[#163E2D] text-[#FFFFFF] border-[#1B4332]/50 shadow-black/40 backdrop-blur-md'
        }`}>
          {label}
        </div>
      )}
    </button>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({
  userSettings,
  onHoverChange,
  isMobileDrawer = false,
  onCloseMobileDrawer,
  theme = 'light',
  onLogout,
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isHovered, setIsHovered] = useState(false);
  const isDark = theme === 'dark';
  const pathname = location.pathname;

  const handleMouseEnter = () => {
    if (!isMobileDrawer) {
      setIsHovered(true);
      onHoverChange?.(true);
    }
  };

  const handleMouseLeave = () => {
    if (!isMobileDrawer) {
      setIsHovered(false);
      onHoverChange?.(false);
    }
  };

  const expanded = isMobileDrawer || isHovered;

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutGrid },
    { path: '/verify', label: 'Verify', icon: ShieldCheck },
    { path: '/chat', label: 'AI Chat', icon: MessageSquare },
    { path: '/leaderboard', label: 'Leaderboard', icon: Trophy },
    { path: '/knowledge-base', label: 'Knowledge Base', icon: BookOpen },
    { path: '/history', label: 'History', icon: Clock3 },
    { path: '/reports', label: 'Reports', icon: BarChart3 },
  ];

  const handleNavClick = (path: string) => {
    navigate(path);
    if (isMobileDrawer && onCloseMobileDrawer) {
      onCloseMobileDrawer();
    }
  };

  return (
    <aside
      aria-label="Main Navigation"
      data-expanded={expanded}
      data-mobile={isMobileDrawer}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`verifai-sidebar flex flex-col select-none shadow-2xl transition-shadow duration-500 ${
        isDark
          ? 'backdrop-blur-2xl text-slate-100 border border-[#333742]'
          : 'backdrop-blur-2xl text-[#D8F3DC] border border-[#40916C]'
      } verifai-sidebar-gradient ${
        isMobileDrawer
          ? 'w-full h-full p-4 overflow-y-auto'
          : 'relative w-full h-full rounded-2xl p-2.5 z-40 overflow-hidden'
      }`}
    >
      {/* Animated Aurora Gradient Background */}
      <div className="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none -z-10">

        {/* Drifting Aurora Orb 1 */}
        <div className={`absolute -top-16 -left-12 w-64 h-72 rounded-full filter blur-3xl pointer-events-none sidebar-aurora-orb-1 morph-blob ${
          isDark
            ? 'bg-[#B6FF2E]/12 mix-blend-screen'
            : 'bg-[#74C69D]/20 mix-blend-screen'
        }`} />

        {/* Drifting Aurora Orb 2 */}
        <div className={`absolute top-1/3 -right-16 w-60 h-80 rounded-full filter blur-3xl pointer-events-none sidebar-aurora-orb-2 morph-blob ${
          isDark
            ? 'bg-[#76BC09]/12 mix-blend-screen'
            : 'bg-[#74C69D]/25 mix-blend-screen'
        }`} />

        {/* Drifting Aurora Orb 3 */}
        <div className={`absolute -bottom-12 left-4 w-56 h-64 rounded-full filter blur-3xl pointer-events-none sidebar-aurora-orb-3 morph-blob ${
          isDark
            ? 'bg-[#A3E823]/10 mix-blend-screen'
            : 'bg-[#40916C]/22 mix-blend-screen'
        }`} />

        {/* Shimmer overlay specular light */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/25 via-transparent to-white/10 opacity-70 pointer-events-none" />

        {/* Vertical shimmer line */}
        <div className="sidebar-shimmer-line" />
        <div className="sidebar-shimmer-line" style={{ left: '30%', animationDelay: '2s' }} />
        <div className="sidebar-shimmer-line" style={{ left: '70%', animationDelay: '4s' }} />
      </div>

      {/* Top Specular Rim Reflection */}
      <div className="absolute top-0 inset-x-4 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent pointer-events-none" />

      {/* 1. Brand Header */}
      <div
        onClick={() => handleNavClick('/dashboard')}
        className="flex items-center w-full mb-4 cursor-pointer group"
      >
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-md shrink-0 transition-transform duration-200 group-hover:scale-105 ${
          isDark
            ? 'bg-[#B6FF2E] text-[#181A20] shadow-[0_0_12px_rgba(182,255,46,0.3)]'
            : 'bg-[#D8F3DC] text-[#1B4332] shadow-sm shadow-[#40916C]/20'
        }`}>
          <svg
            viewBox="0 0 24 24"
            className="w-5 h-5 fill-none stroke-current stroke-[2.2]"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polygon points="12 2 20 7 20 12 12 22 4 12 4 7 12 2" />
            <polyline points="9 12 11 14 15 10" />
          </svg>
        </div>

        <div className={`verifai-sidebar-reveal flex flex-col min-w-0 overflow-hidden ${
          expanded
            ? 'opacity-100 max-w-[195px] translate-x-0 ml-2.5'
            : 'opacity-0 max-w-0 -translate-x-2 ml-0 pointer-events-none'
        }`}>
          <span className="text-white font-bold text-base tracking-tight leading-tight whitespace-nowrap">
            VerifAI
          </span>
          <span className={`text-xs font-semibold tracking-wider uppercase whitespace-nowrap ${
            isDark ? 'text-[#B6FF2E]' : 'text-[#D8F3DC]'
          }`}>
            Truth Engine
          </span>
        </div>

        {isMobileDrawer && (
          <button
            type="button"
            aria-label="Close Navigation Menu"
            onClick={onCloseMobileDrawer}
            className={`ml-auto w-8 h-8 rounded-xl flex items-center justify-center cursor-pointer ${
              isDark ? 'bg-[#181A20] text-slate-400 hover:text-white' : 'bg-[#40916C] text-[#D8F3DC] hover:text-white'
            }`}
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* 2. Main Navigation Items */}
      <nav className="flex-1 flex flex-col gap-2 w-full overflow-y-auto no-scrollbar py-1">
        {navItems.map((item) => {
          const isActive = pathname === item.path || (item.path !== '/dashboard' && pathname.startsWith(item.path));

          return (
            <SidebarDockItem
              key={item.path}
              path={item.path}
              label={item.label}
              icon={item.icon}
              isActive={isActive}
              expanded={expanded}
              isMobileDrawer={isMobileDrawer}
              onClick={() => handleNavClick(item.path)}
              theme={theme}
            />
          );
        })}
      </nav>

      {/* 3. Divider */}
      <div className="w-full my-3 flex items-center justify-center">
        <div className="w-full h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" />
      </div>

      {/* 4. Bottom Controls */}
      <div className="flex flex-col gap-2 w-full">

        {/* Settings Action */}
        <SidebarDockItem
          path="/settings"
          label="Settings"
          icon={Settings}
          isActive={pathname.startsWith('/settings')}
          expanded={expanded}
          isMobileDrawer={isMobileDrawer}
          onClick={() => handleNavClick('/settings')}
          theme={theme}
        />

        {/* User Profile Lockup */}
        <div
          onClick={() => handleNavClick('/settings/profile')}
          title={!expanded ? userSettings.profile.fullName : undefined}
          className="group h-12 rounded-2xl flex items-center w-full cursor-pointer hover:bg-white/10 transition-colors relative"
        >
          <div className="w-12 h-12 flex items-center justify-center shrink-0">
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-extrabold text-sm shadow-sm transition-transform duration-300 group-hover:scale-105 ${
              isDark
                ? 'bg-[#181A20] text-[#B6FF2E] ring-2 ring-[#B6FF2E]/30'
                : 'bg-[#D8F3DC] text-[#1B4332] ring-2 ring-[#D8F3DC]/50'
            }`}>
              {userSettings.profile.fullName.charAt(0)}
            </div>
          </div>

          <div className={`verifai-sidebar-reveal flex flex-col min-w-0 overflow-hidden ${
            expanded
              ? 'opacity-100 max-w-[200px] translate-x-0 pr-2'
              : 'opacity-0 max-w-0 -translate-x-3 pointer-events-none'
          }`}>
            <span className="text-white text-base font-bold truncate font-palatino">
              {userSettings.profile.fullName}
            </span>
            <span className={`text-[13px] font-medium truncate mt-0.5 font-palatino ${isDark ? 'text-slate-400' : 'text-white/90'}`}>
              {userSettings.profile.email}
            </span>
          </div>

          {!expanded && !isMobileDrawer && (
            <div className={`absolute left-[calc(100%+14px)] px-3 py-1.5 text-sm font-semibold rounded-xl whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] shadow-xl border z-50 translate-x-1 group-hover:translate-x-0 font-palatino ${
              isDark
                ? 'bg-[#181A20] text-slate-200 border-[#333742] shadow-black/50'
                : 'bg-[#163E2D] text-[#FFFFFF] border-[#1B4332]/50 shadow-black/40 backdrop-blur-md'
            }`}>
              {userSettings.profile.fullName}
            </div>
          )}
        </div>

        {/* Sign Out Action */}
        <button
          onClick={() => {
            if (onLogout) onLogout();
            handleNavClick('/login');
          }}
          title={!expanded ? 'Sign Out' : undefined}
          className={`group min-h-11 rounded-xl flex items-center w-full cursor-pointer relative sidebar-nav-hover ${
            isDark
              ? 'text-slate-400 hover:text-white hover:bg-white/10'
              : 'text-white/90 hover:text-white hover:bg-white/10'
          }`}
        >
          <div className="w-10 h-11 flex items-center justify-center shrink-0">
            <LogOut
              size={19}
              strokeWidth={2}
              className={`transition-all duration-200 ${
                isDark
                  ? 'text-slate-400 group-hover:text-white'
                  : 'text-white/85 group-hover:text-white'
              }`}
            />
          </div>

          <div className={`verifai-sidebar-reveal flex items-center min-w-0 overflow-hidden ${
            expanded
              ? 'opacity-100 max-w-[200px] translate-x-0 pr-2.5'
              : 'opacity-0 max-w-0 -translate-x-2 pointer-events-none'
          }`}>
            <span className={`whitespace-nowrap text-[15px] font-semibold truncate transition-colors duration-200 ${
              isDark
                ? 'text-slate-300 group-hover:text-white'
                : 'text-white/90 group-hover:text-white'
            }`}>
              Sign Out
            </span>
          </div>

          {!expanded && !isMobileDrawer && (
            <div className={`absolute left-[calc(100%+8px)] px-2.5 py-1 text-[15px] font-semibold rounded-lg whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 shadow-xl border z-50 translate-x-1 group-hover:translate-x-0 ${
              isDark
                ? 'bg-[#181A20] text-rose-400 border-[#333742] shadow-black/50'
                : 'bg-[#163E2D] text-[#FFFFFF] border-[#1B4332]/50 shadow-black/40 backdrop-blur-md'
            }`}>
              Sign Out
            </div>
          )}
        </button>

      </div>
    </aside>
  );
};

export default Sidebar;
