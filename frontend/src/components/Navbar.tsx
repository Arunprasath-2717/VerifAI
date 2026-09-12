import React from 'react';
import { ShieldCheck, BarChart3, Trophy, LineChart, Sparkles } from 'lucide-react';

interface NavbarProps {
  activeTab: 'dashboard' | 'leaderboard' | 'benchmark';
  setActiveTab: (tab: 'dashboard' | 'leaderboard' | 'benchmark') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-indigo-900/40 shadow-[0_4px_30px_rgba(15,23,42,0.8)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Module Brand */}
          <div className="flex items-center space-x-3.5">
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-65 group-hover:opacity-100 transition duration-300"></div>
              <div className="relative p-2.5 bg-slate-950 rounded-2xl border border-slate-800 flex items-center justify-center">
                <ShieldCheck className="h-7 w-7 text-indigo-400" />
              </div>
            </div>
            
            <div>
              <div className="flex items-center space-x-2.5">
                <span className="font-extrabold text-2xl tracking-tight bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400 bg-clip-text text-transparent">
                  VerifAI
                </span>
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-gradient-to-r from-indigo-950 to-purple-950 text-indigo-300 border border-indigo-700/60 shadow-sm">
                  Trust Analytics Layer
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium tracking-wide">
                Core Verification Telemetry • Leaderboards • Benchmark Intelligence
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-2 bg-slate-900/90 p-1.5 rounded-2xl border border-slate-800/80 shadow-inner">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center space-x-2 px-5 py-2.5 text-xs font-bold rounded-xl transition-all duration-300 ${
                activeTab === 'dashboard'
                  ? 'bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30 scale-[1.02]'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
              }`}
            >
              <BarChart3 className="h-4 w-4" />
              <span>Trust Dashboard</span>
            </button>

            <button
              onClick={() => setActiveTab('leaderboard')}
              className={`flex items-center space-x-2 px-5 py-2.5 text-xs font-bold rounded-xl transition-all duration-300 ${
                activeTab === 'leaderboard'
                  ? 'bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30 scale-[1.02]'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
              }`}
            >
              <Trophy className="h-4 w-4 text-amber-400" />
              <span>Model Leaderboard</span>
            </button>

            <button
              onClick={() => setActiveTab('benchmark')}
              className={`flex items-center space-x-2 px-5 py-2.5 text-xs font-bold rounded-xl transition-all duration-300 ${
                activeTab === 'benchmark'
                  ? 'bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30 scale-[1.02]'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
              }`}
            >
              <LineChart className="h-4 w-4 text-sky-400" />
              <span>Benchmark Analytics</span>
            </button>
          </nav>

          {/* Engine Status Badge */}
          <div className="hidden lg:flex items-center space-x-2 text-xs font-mono bg-emerald-950/60 px-3.5 py-1.5 rounded-xl border border-emerald-800/60 text-emerald-300 shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
            <span className="font-semibold">Engine Synced</span>
          </div>

        </div>
      </div>
    </header>
  );
};
