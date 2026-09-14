import React from 'react';
import { ShieldCheck, BarChart3, Trophy, LineChart, Sparkles, History, ListChecks, FileText } from 'lucide-react';

interface NavbarProps {
  activeTab: 'dashboard' | 'leaderboard' | 'benchmark' | 'history' | 'audit' | 'reports';
  setActiveTab: (tab: 'dashboard' | 'leaderboard' | 'benchmark' | 'history' | 'audit' | 'reports') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'leaderboard', label: 'Leaderboard', icon: Trophy },
    { id: 'benchmark', label: 'Benchmarks', icon: LineChart },
    { id: 'history', label: 'History', icon: History },
    { id: 'audit', label: 'Audit', icon: ListChecks },
    { id: 'reports', label: 'Reports', icon: FileText },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/40 backdrop-blur-2xl border-b border-white/60 shadow-lg shadow-sky-500/5 transition-colors duration-300">
      <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Brand */}
          <div 
            className="flex-shrink-0 flex items-center group cursor-pointer" 
            onClick={() => setActiveTab('dashboard')}
          >
            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-sky-500 via-purple-500 to-blue-500 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-500"></div>
              <div className="relative w-11 h-11 rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center shadow-lg shadow-sky-500/30 group-hover:scale-105 transition-transform duration-300">
                <ShieldCheck className="h-6 w-6 text-white" />
              </div>
            </div>
            
            <div className="ml-3.5 flex flex-col justify-center">
              <span className="text-xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-sky-900 to-blue-700">
                VerifAI
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider text-sky-500/70">
                Premium Glass UI
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1.5 bg-white/30 backdrop-blur-md p-1.5 rounded-2xl border border-white/50 shadow-inner overflow-x-auto hide-scrollbar">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`
                    flex items-center space-x-2 px-5 py-2.5 text-xs font-bold rounded-xl transition-all duration-300 relative
                    ${isActive 
                      ? 'text-white shadow-md shadow-sky-500/25 scale-105 group' 
                      : 'text-slate-700 hover:bg-white/60 hover:text-sky-700 hover:shadow-sm'
                    }
                  `}
                >
                  {isActive && (
                    <div className="absolute inset-0 bg-gradient-to-r from-sky-500 to-blue-500 rounded-xl -z-10 animate-in zoom-in-95 duration-300" />
                  )}
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Engine Status Badge */}
          <div className="hidden lg:flex items-center space-x-2 text-xs font-mono bg-sky-50/50 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-sky-200/50 text-sky-700 shadow-sm hover:shadow-md transition-shadow cursor-pointer group">
            <Sparkles className="h-3.5 w-3.5 text-sky-500 group-hover:animate-spin" />
            <span className="font-bold">Mock Active</span>
          </div>

        </div>
      </div>
    </header>
  );
};
