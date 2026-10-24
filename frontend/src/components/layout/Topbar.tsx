import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { Search, Bell, Menu, Settings, LogOut, Sparkles, Sun, Moon } from 'lucide-react';
import { UserSettings, NotificationItem } from '../../types';

interface TopbarProps {
  userSettings: UserSettings;
  notifications: NotificationItem[];
  onOpenNotifications: () => void;
  onOpenMobileMenu: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
  onLogout?: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({
  userSettings,
  notifications,
  onOpenNotifications,
  onOpenMobileMenu,
  searchQuery,
  onSearchChange,
  theme = 'light',
  onToggleTheme,
  onLogout,
}) => {
  const navigate = useNavigate();
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const unreadCount = notifications.filter(n => !n.read).length;
  const isDark = theme === 'dark';

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/history?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <div className="verifai-topbar flex items-center justify-between gap-2 sm:gap-3 select-none min-w-0 w-full">
      {/* Mobile Drawer Toggle & Search Bar */}
      <div className="flex items-center gap-2 sm:gap-2.5 flex-1 min-w-0 max-w-[460px]">
        <button
          onClick={onOpenMobileMenu}
          className={`lg:hidden w-10 h-10 rounded-xl flex items-center justify-center shadow-xs cursor-pointer transition-colors ${
            isDark
              ? 'bg-[#23262F] border border-[#333742] text-[#B6FF2E]'
              : 'bg-[#FFFFFF] border border-[#74C69D] text-[#1B4332] hover:bg-[#D8F3DC]'
          }`}
          aria-label="Open Navigation Menu"
        >
          <Menu size={17} />
        </button>

        <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-0">
          <Search
            className={`absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none transition-colors ${
              isDark ? 'text-slate-500' : 'text-[#1B4332]/60'
            }`}
            size={15}
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search verified claims & insights..."
            className={`w-full rounded-xl py-2.5 pl-10 pr-3.5 text-sm shadow-sm transition-all outline-none ${
              isDark
                ? 'bg-[#23262F] border border-[#333742] text-slate-100 placeholder-slate-500 focus:ring-1 focus:ring-[#B6FF2E]/30 focus:border-[#B6FF2E]'
                : 'bg-[#FFFFFF] border border-[#74C69D] text-[#1B4332] placeholder-[#356B52]/60 focus:ring-1 focus:ring-[#1B4332]/20 focus:border-[#1B4332]'
            }`}
          />
        </form>
      </div>

      {/* Right Controls */}
      <div className="flex items-center shrink-0 gap-1.5 sm:gap-2.5">
        {/* Dynamic Theme Toggle: Sun / Moon */}
        {onToggleTheme && (
          <button
            onClick={onToggleTheme}
            type="button"
            aria-label={isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            title={isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-xs transition-all cursor-pointer active:scale-95 ${
              isDark
                ? 'bg-[#23262F] hover:bg-[#2A2E38] text-[#B6FF2E] border border-[#333742] shadow-[0_0_12px_rgba(182,255,46,0.15)]'
                : 'bg-[#FFFFFF] hover:bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D] shadow-xs'
            }`}
          >
            {isDark ? (
              <Sun size={15} className="transition-transform duration-300 hover:rotate-45" />
            ) : (
              <Moon size={15} className="transition-transform duration-300 hover:-rotate-12" />
            )}
          </button>
        )}

        {/* Notification Bell */}
        <button
          onClick={onOpenNotifications}
          aria-label="Notifications"
          className={`relative w-10 h-10 rounded-xl flex items-center justify-center shadow-xs transition-all cursor-pointer ${
            isDark
              ? 'bg-[#23262F] border border-[#333742] text-slate-300 hover:text-[#B6FF2E] hover:border-[#B6FF2E]/50'
              : 'bg-[#FFFFFF] border border-[#74C69D] text-[#1B4332] hover:bg-[#D8F3DC]'
          }`}
        >
          <Bell size={15} />
          {unreadCount > 0 && (
            <span className={`absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full ring-2 ${
              isDark ? 'bg-[#B6FF2E] ring-[#23262F]' : 'bg-[#1B4332] ring-[#FFFFFF]'
            }`} />
          )}
        </button>

        {/* User Profile Lockup */}
        <div className="relative">
          <div
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className={`flex items-center gap-2 pl-2.5 pr-1 py-1 rounded-xl border shadow-sm cursor-pointer transition-all group ${
              isDark
                ? 'bg-[#23262F] border-[#333742] hover:border-[#B6FF2E]/50'
                : 'bg-[#FFFFFF] border-[#74C69D] hover:border-[#1B4332]/50'
            }`}
          >
            <div className="text-right hidden sm:block">
              <p className={`text-xs font-bold leading-tight transition-colors ${
                isDark ? 'text-white group-hover:text-[#B6FF2E]' : 'text-[#1B4332] group-hover:text-[#1B4332]'
              }`}>
                {userSettings.profile.fullName}
              </p>
              <p className={`text-[10px] font-semibold leading-tight mt-0.5 ${
                isDark ? 'text-slate-400' : 'text-[#356B52]'
              }`}>
                {userSettings.profile.organization}
              </p>
            </div>

            <div className={`w-7.5 h-7.5 rounded-lg flex items-center justify-center font-bold text-xs shadow-sm ring-1 ${
              isDark
                ? 'bg-[#181A20] text-[#B6FF2E] ring-[#B6FF2E]/30'
                : 'bg-[#74C69D] text-[#1B4332] ring-[#74C69D]/35'
            }`}>
              <span>{userSettings.profile.fullName.charAt(0)}</span>
            </div>
          </div>

          {/* User Dropdown Menu */}
          <AnimatePresence>
            {showProfileMenu && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -6 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -6 }}
                transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                className={`absolute right-0 top-full mt-2 w-60 border rounded-2xl shadow-2xl py-2 z-50 ${
                  isDark
                    ? 'bg-[#23262F] border-[#333742] text-slate-200 shadow-black/60'
                    : 'bg-[#FFFFFF] border-[#74C69D] text-[#1B4332] shadow-xl'
                }`}
              >
                <div className={`px-4 py-2.5 border-b ${isDark ? 'border-[#333742]' : 'border-[#74C69D]'}`}>
                  <p className="text-sm font-bold">{userSettings.profile.fullName}</p>
                  <p className={`text-xs font-medium truncate mt-0.5 ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>{userSettings.profile.email}</p>
                </div>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    navigate('/settings/profile');
                  }}
                  className={`w-full text-left px-4 py-2.5 text-sm font-medium flex items-center gap-2.5 transition-colors cursor-pointer ${
                    isDark ? 'hover:bg-[#2A2E38]' : 'hover:bg-[#D8F3DC]'
                  }`}
                >
                  <Settings size={15} className={isDark ? 'text-slate-400' : 'text-[#1B4332]'} />
                  <span>Account Settings</span>
                </button>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    navigate('/settings/verification');
                  }}
                  className={`w-full text-left px-4 py-2.5 text-sm font-medium flex items-center gap-2.5 transition-colors cursor-pointer ${
                    isDark ? 'hover:bg-[#2A2E38]' : 'hover:bg-[#D8F3DC]'
                  }`}
                >
                  <Sparkles size={15} className={isDark ? 'text-slate-400' : 'text-[#1B4332]'} />
                  <span>Verification Preferences</span>
                </button>

                <div className={`border-t mt-1 pt-1 ${isDark ? 'border-[#333742]' : 'border-[#74C69D]'}`}>
                  <button
                    onClick={() => {
                      setShowProfileMenu(false);
                      if (onLogout) onLogout();
                      navigate('/login');
                    }}
                    className="w-full text-left px-4 py-2.5 text-sm font-semibold text-rose-500 hover:bg-rose-500/10 flex items-center gap-2.5 cursor-pointer transition-colors"
                  >
                    <LogOut size={15} />
                    <span>Sign Out</span>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
