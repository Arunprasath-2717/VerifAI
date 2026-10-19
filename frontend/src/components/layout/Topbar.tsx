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
    <header className="flex items-center justify-between gap-4 mb-8 select-none">
      {/* Mobile Drawer Toggle & Search Bar */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <button
          onClick={onOpenMobileMenu}
          className={`lg:hidden w-10 h-10 rounded-2xl flex items-center justify-center shadow-xs cursor-pointer transition-colors ${
            isDark 
              ? 'bg-[#23262F] border border-[#333742] text-[#B6FF2E]' 
              : 'bg-[#FFFDFA] border border-[#E9D6C4] text-[#800020] hover:bg-[#F2E6D6]'
          }`}
          aria-label="Open Navigation Menu"
        >
          <Menu size={20} />
        </button>

        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search 
            className={`absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none transition-colors ${
              isDark ? 'text-slate-500' : 'text-[#800020]/60'
            }`} 
            size={18} 
          />
          <input 
            type="text" 
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search verified claims & insights..." 
            className={`w-full rounded-2xl py-2.5 pl-11 pr-4 text-sm shadow-xs transition-all outline-none ${
              isDark
                ? 'bg-[#23262F] border border-[#333742] text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-[#B6FF2E]/30 focus:border-[#B6FF2E]'
                : 'bg-[#FFFDFA] border border-[#E9D6C4] text-[#2E0A12] placeholder-[#8A6A72]/60 focus:ring-2 focus:ring-[#800020]/20 focus:border-[#800020]'
            }`}
          />
        </form>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5 sm:gap-4">
        {/* Dynamic Theme Toggle: Sun / Moon */}
        {onToggleTheme && (
          <button
            onClick={onToggleTheme}
            type="button"
            aria-label={isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            title={isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            className={`w-10 h-10 rounded-2xl flex items-center justify-center shadow-xs transition-all cursor-pointer active:scale-95 ${
              isDark
                ? 'bg-[#23262F] hover:bg-[#2A2E38] text-[#B6FF2E] border border-[#333742] shadow-[0_0_15px_rgba(182,255,46,0.18)]'
                : 'bg-[#FFFDFA] hover:bg-[#F2E6D6] text-[#800020] border border-[#E9D6C4] shadow-xs'
            }`}
          >
            {isDark ? (
              <Sun size={18} className="transition-transform duration-300 hover:rotate-45" />
            ) : (
              <Moon size={18} className="transition-transform duration-300 hover:-rotate-12" />
            )}
          </button>
        )}

        {/* Notification Bell */}
        <button 
          onClick={onOpenNotifications}
          aria-label="Notifications"
          className={`relative w-10 h-10 rounded-2xl flex items-center justify-center shadow-xs transition-all cursor-pointer ${
            isDark
              ? 'bg-[#23262F] border border-[#333742] text-slate-300 hover:text-[#B6FF2E] hover:border-[#B6FF2E]/50'
              : 'bg-[#FFFDFA] border border-[#E9D6C4] text-[#800020] hover:bg-[#F2E6D6]'
          }`}
        >
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className={`absolute top-2 right-2 w-2 h-2 rounded-full ring-2 ${
              isDark ? 'bg-[#B6FF2E] ring-[#23262F]' : 'bg-[#800020] ring-[#FFFDFA]'
            }`} />
          )}
        </button>

        {/* User Profile Lockup */}
        <div className="relative">
          <div 
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className={`flex items-center gap-2.5 pl-3 pr-1.5 py-1.5 rounded-2xl border shadow-xs cursor-pointer transition-all group ${
              isDark
                ? 'bg-[#23262F] border-[#333742] hover:border-[#B6FF2E]/50'
                : 'bg-[#FFFDFA] border-[#E9D6C4] hover:border-[#800020]/50'
            }`}
          >
            <div className="text-right hidden sm:block">
              <p className={`text-sm font-bold leading-tight transition-colors ${
                isDark ? 'text-white group-hover:text-[#B6FF2E]' : 'text-[#2E0A12] group-hover:text-[#800020]'
              }`}>
                {userSettings.profile.fullName}
              </p>
              <p className={`text-xs font-semibold leading-tight mt-0.5 ${
                isDark ? 'text-slate-400' : 'text-[#8A6A72]'
              }`}>
                {userSettings.profile.organization}
              </p>
            </div>
            
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm shadow-sm ring-2 ${
              isDark 
                ? 'bg-[#181A20] text-[#B6FF2E] ring-[#B6FF2E]/30' 
                : 'bg-[#800020] text-[#FBF1E3] ring-[#D8AE9B]/50'
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
                    : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#2E0A12] shadow-xl'
                }`}
              >
                <div className={`px-4 py-2.5 border-b ${isDark ? 'border-[#333742]' : 'border-[#E9D6C4]'}`}>
                  <p className="text-sm font-bold">{userSettings.profile.fullName}</p>
                  <p className={`text-xs font-medium truncate mt-0.5 ${isDark ? 'text-slate-400' : 'text-[#8A6A72]'}`}>{userSettings.profile.email}</p>
                </div>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    navigate('/settings/profile');
                  }}
                  className={`w-full text-left px-4 py-2.5 text-sm font-medium flex items-center gap-2.5 transition-colors cursor-pointer ${
                    isDark ? 'hover:bg-[#2A2E38]' : 'hover:bg-[#F2E6D6]'
                  }`}
                >
                  <Settings size={15} className={isDark ? 'text-slate-400' : 'text-[#800020]'} />
                  <span>Account Settings</span>
                </button>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    navigate('/settings/verification');
                  }}
                  className={`w-full text-left px-4 py-2.5 text-sm font-medium flex items-center gap-2.5 transition-colors cursor-pointer ${
                    isDark ? 'hover:bg-[#2A2E38]' : 'hover:bg-[#F2E6D6]'
                  }`}
                >
                  <Sparkles size={15} className={isDark ? 'text-slate-400' : 'text-[#800020]'} />
                  <span>Verification Preferences</span>
                </button>

                <div className={`border-t mt-1 pt-1 ${isDark ? 'border-[#333742]' : 'border-[#E9D6C4]'}`}>
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
    </header>
  );
};
