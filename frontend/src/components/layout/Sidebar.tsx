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
      className={`group h-12 rounded-2xl flex items-center w-full transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] cursor-pointer relative ${
        isActive 
          ? isDark ? 'text-[#181A20]' : 'text-[#800020]' 
          : isDark
            ? 'text-slate-400 hover:text-white hover:bg-white/10'
            : 'text-[#FBF1E3]/80 hover:text-white hover:bg-white/15'
      }`}
    >
      {/* Selected Clean Cream / Ivory Background (No glowing effect) */}
      {isActive && (
        <div className={`absolute inset-0 rounded-2xl pointer-events-none -z-10 animate-in fade-in duration-200 ${
          isDark
            ? 'bg-[#B6FF2E] border border-[#B6FF2E]/40 shadow-md shadow-black/30'
            : 'bg-[#FFFDF5] border border-[#EFE5D8] shadow-md shadow-[#4A0A18]/20'
        }`} />
      )}

      {/* Centered 48px slot with stable alignment */}
      <div className="w-12 h-12 flex items-center justify-center shrink-0">
        <Icon 
          size={20} 
          strokeWidth={isActive ? 2.5 : 2} 
          className={`transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] ${
            isActive 
              ? isDark 
                ? 'text-[#181A20]' 
                : 'text-[#800020]' 
              : isDark 
                ? 'text-slate-400 group-hover:text-white group-hover:scale-105' 
                : 'text-[#FBF1E3]/80 group-hover:text-white group-hover:scale-105'
          }`} 
        />
      </div>
      
      {/* Fluid text label container */}
      <div 
        className={`flex items-center justify-between flex-1 min-w-0 overflow-hidden transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          expanded 
            ? 'opacity-100 max-w-[195px] translate-x-0 pr-3' 
            : 'opacity-0 max-w-0 -translate-x-3 pointer-events-none'
        }`}
      >
        <span className={`whitespace-nowrap text-base truncate font-palatino ${
          isActive 
            ? isDark ? 'text-[#181A20] font-bold' : 'text-[#800020] font-bold' 
            : isDark ? 'text-slate-300 font-semibold' : 'text-[#FBF1E3]/90 font-semibold'
        }`}>
          {label}
        </span>

        {isActive && (
          <span className={`w-2 h-2 rounded-full shrink-0 ml-2 ${
            isDark 
              ? 'bg-[#181A20]' 
              : 'bg-[#800020]'
          }`} />
        )}
      </div>

      {/* Floating Tooltip on collapsed hover */}
      {!expanded && !isMobileDrawer && (
        <div className={`absolute left-[calc(100%+14px)] px-3 py-1.5 text-sm font-semibold rounded-xl whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] shadow-xl border z-50 translate-x-1 group-hover:translate-x-0 font-palatino ${
          isDark
            ? 'bg-[#181A20] text-[#B6FF2E] border-[#333742] shadow-black/50'
            : 'bg-[#4A0A18] text-[#FFFDFA] border-[#800020]/50 shadow-black/40 backdrop-blur-md'
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
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`flex flex-col select-none shadow-2xl transition-[width,box-shadow] duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] will-change-[width] ${
        isDark 
          ? 'bg-[#23262F]/95 backdrop-blur-2xl text-slate-100 border border-[#333742]' 
          : 'bg-[#800020]/95 backdrop-blur-2xl text-[#FBF1E3] border border-[#6E1B33]'
      } ${
        isMobileDrawer
          ? 'w-[280px] h-full p-6 overflow-y-auto'
          : `fixed top-4 left-4 h-[calc(100vh-2rem)] rounded-[2.5rem] p-4 z-40 overflow-hidden ${
              expanded 
                ? 'w-[270px] shadow-[0_25px_60px_-15px_rgba(0,0,0,0.5)]' 
                : 'w-[84px]'
            }`
      }`}
    >
      {/* Static Ambient Gradient Background */}
      <div className="absolute inset-0 overflow-hidden rounded-[2.5rem] pointer-events-none -z-10">
        <div className={`absolute inset-0 ${
          isDark 
            ? 'bg-[#23262F]/95' 
            : 'bg-[#751A30]'
        }`} />

        {/* Static Ambient Glow 1 */}
        <div className={`absolute -top-16 -left-12 w-64 h-72 rounded-full filter blur-3xl pointer-events-none ${
          isDark 
            ? 'bg-[#B6FF2E]/10 mix-blend-screen' 
            : 'bg-[#A64658]/35 mix-blend-screen'
        }`} />

        {/* Static Ambient Glow 2 */}
        <div className={`absolute top-1/3 -right-16 w-60 h-80 rounded-full filter blur-3xl pointer-events-none ${
          isDark 
            ? 'bg-[#76BC09]/10 mix-blend-screen' 
            : 'bg-[#C97B88]/25 mix-blend-screen'
        }`} />

        {/* Static Ambient Glow 3 */}
        <div className={`absolute -bottom-12 left-0 w-56 h-64 rounded-full filter blur-3xl pointer-events-none ${
          isDark 
            ? 'bg-[#A3E823]/08 mix-blend-screen' 
            : 'bg-[#8E2337]/35 mix-blend-screen'
        }`} />

        {/* Shimmer overlay specular light */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/25 via-transparent to-white/10 opacity-70 pointer-events-none" />
      </div>

      {/* Top Specular Rim Reflection */}
      <div className="absolute top-0 inset-x-4 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent pointer-events-none" />

      {/* 1. Brand Header */}
      <div 
        onClick={() => handleNavClick('/dashboard')}
        className="flex items-center w-full mb-6 cursor-pointer group"
      >
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg shrink-0 transition-transform duration-300 group-hover:scale-105 ${
          isDark 
            ? 'bg-[#B6FF2E] text-[#181A20] shadow-[0_0_20px_rgba(182,255,46,0.35)]' 
            : 'bg-[#FBF1E3] text-[#800020] shadow-md shadow-[#6E1B33]/30'
        }`}>
          <svg 
            viewBox="0 0 24 24" 
            className="w-6 h-6 fill-none stroke-current stroke-[2.4]"
            strokeLinecap="round" 
            strokeLinejoin="round"
          >
            <polygon points="12 2 20 7 20 12 12 22 4 12 4 7 12 2" />
            <polyline points="9 12 11 14 15 10" />
          </svg>
        </div>

        <div className={`flex flex-col min-w-0 overflow-hidden transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          expanded 
            ? 'opacity-100 max-w-[170px] translate-x-0 ml-3' 
            : 'opacity-0 max-w-0 -translate-x-3 ml-0 pointer-events-none'
        }`}>
          <span className="text-white font-extrabold text-xl tracking-wider leading-tight whitespace-nowrap font-eternity">
            VerifAI
          </span>
          <span className={`text-xs font-bold tracking-widest uppercase whitespace-nowrap font-adore ${
            isDark ? 'text-[#B6FF2E]' : 'text-[#D8AE9B]'
          }`}>
            Evidence Engine
          </span>
        </div>

        {isMobileDrawer && (
          <button 
            onClick={onCloseMobileDrawer}
            className={`ml-auto w-8 h-8 rounded-xl flex items-center justify-center cursor-pointer ${
              isDark ? 'bg-[#181A20] text-slate-400 hover:text-white' : 'bg-[#6E1B33] text-[#FBF1E3] hover:text-white'
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
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-extrabold text-sm shadow-sm transition-transform duration-300 group-hover:scale-105 font-eternity ${
              isDark 
                ? 'bg-[#181A20] text-[#B6FF2E] ring-2 ring-[#B6FF2E]/30' 
                : 'bg-[#FBF1E3] text-[#800020] ring-2 ring-[#D8AE9B]/50'
            }`}>
              {userSettings.profile.fullName.charAt(0)}
            </div>
          </div>

          <div className={`flex flex-col min-w-0 overflow-hidden transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${
            expanded 
              ? 'opacity-100 max-w-[170px] translate-x-0 pr-2' 
              : 'opacity-0 max-w-0 -translate-x-3 pointer-events-none'
          }`}>
            <span className="text-white text-sm font-bold truncate font-palatino">
              {userSettings.profile.fullName}
            </span>
            <span className={`text-xs font-medium truncate mt-0.5 font-palatino ${isDark ? 'text-slate-400' : 'text-[#FBF1E3]/90'}`}>
              {userSettings.profile.email}
            </span>
          </div>

          {!expanded && !isMobileDrawer && (
            <div className={`absolute left-[calc(100%+14px)] px-3 py-1.5 text-sm font-semibold rounded-xl whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] shadow-xl border z-50 translate-x-1 group-hover:translate-x-0 font-palatino ${
              isDark
                ? 'bg-[#181A20] text-slate-200 border-[#333742] shadow-black/50'
                : 'bg-[#4A0A18] text-[#FFFDFA] border-[#800020]/50 shadow-black/40 backdrop-blur-md'
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
          className={`group h-12 rounded-2xl flex items-center w-full transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] cursor-pointer relative ${
            isDark
              ? 'text-slate-400 hover:text-white hover:bg-white/10'
              : 'text-[#FBF1E3]/80 hover:text-white hover:bg-white/15'
          }`}
        >
          <div className="w-12 h-12 flex items-center justify-center shrink-0">
            <LogOut 
              size={20} 
              strokeWidth={2} 
              className={`transition-all duration-200 group-hover:scale-110 group-hover:-translate-x-0.5 ${
                isDark 
                  ? 'text-slate-400 group-hover:text-white' 
                  : 'text-[#FBF1E3]/80 group-hover:text-white'
              }`} 
            />
          </div>

          <div className={`flex items-center min-w-0 overflow-hidden transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${
            expanded 
              ? 'opacity-100 max-w-[170px] translate-x-0 pr-3' 
              : 'opacity-0 max-w-0 -translate-x-3 pointer-events-none'
          }`}>
            <span className={`whitespace-nowrap text-base font-semibold truncate font-palatino transition-colors duration-200 ${
              isDark 
                ? 'text-slate-300 group-hover:text-white' 
                : 'text-[#FBF1E3]/90 group-hover:text-white'
            }`}>
              Sign Out
            </span>
          </div>

          {!expanded && !isMobileDrawer && (
            <div className={`absolute left-[calc(100%+14px)] px-3 py-1.5 text-sm font-semibold rounded-xl whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] shadow-xl border z-50 translate-x-1 group-hover:translate-x-0 font-palatino ${
              isDark
                ? 'bg-[#181A20] text-rose-400 border-[#333742] shadow-black/50'
                : 'bg-[#4A0A18] text-[#FFFDFA] border-[#800020]/50 shadow-black/40 backdrop-blur-md'
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
