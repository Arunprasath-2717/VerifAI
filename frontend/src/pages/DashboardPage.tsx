import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  MessageSquare,
  BookOpen,
  FileText,
  ChevronRight,
  Sparkles,
  Zap,
  ArrowRight,
  CheckCircle2,
  Trophy,
  Award,
  ExternalLink,
  Check,
  Layers,
  BarChart3,
  Cpu,
  Clock
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { VerificationRecord, ChartPoint, ModelLeaderboardEntry } from '../types';
import { dashboardApi, modelsApi, BackendDashboardStats } from '../api';
import { BorderGlow } from '../components/ui/BorderGlow';
import heroCardDarkBg from '../assets/hero_card_dark_network_globe.webp';
import './DashboardMocha.css';
import heroCardLightBg from '../assets/hero_card_light_network_globe.webp';

interface DashboardPageProps {
  verifications: VerificationRecord[];
  userName: string;
  theme?: 'light' | 'dark';
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  verifications,
  userName,
  theme = 'light',
}) => {
  const navigate = useNavigate();
  const [timeframe, setTimeframe] = useState<'7D' | '30D'>('7D');
  const [chartMetric, setChartMetric] = useState<'verifications' | 'claims' | 'evidence'>('verifications');
  const [scopedActionId, setScopedActionId] = useState<string>('verify');
  const [leaderboardFilter, setLeaderboardFilter] = useState<'all' | 'top3'>('top3');
  const [liveStats, setLiveStats] = useState<BackendDashboardStats | null>(null);
  const [liveLeaderboard, setLiveLeaderboard] = useState<ModelLeaderboardEntry[]>([]);
  const [dataError, setDataError] = useState<string | null>(null);
  const [leaderboardError, setLeaderboardError] = useState<string | null>(null);

  React.useEffect(() => {
    let mounted = true;
    dashboardApi.getStats().then(stats => {
      if (mounted) setLiveStats(stats);
    }).catch(err => {
      if (mounted) setDataError(err instanceof Error ? err.message : 'Dashboard unavailable');
    });
    modelsApi.getModelLeaderboard().then(entries => {
      if (mounted) setLiveLeaderboard(entries);
    }).catch(err => {
      if (mounted) setLeaderboardError(err instanceof Error ? err.message : 'Leaderboard unavailable');
    });
    return () => { mounted = false; };
  }, []);

  const isDark = theme === 'dark';
  const rawChartData = timeframe === '7D'
    ? (liveStats?.weekly_chart_data ?? [])
    : (liveStats?.monthly_chart_data ?? []);
  const chartData = rawChartData.map(point => ({
    ...point,
    name: (point as ChartPoint & { day?: string }).day ?? point.name,
  }));

  const statCards = [
    {
      title: 'Verifications',
      value: liveStats ? liveStats.verifications_count.toLocaleString() : verifications.length.toLocaleString(),
      sub: 'Executed audits',
      icon: ShieldCheck,
      link: '/history',
      sparkline: liveStats?.sparklines?.verifications || [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    },
    {
      title: 'Claims Analyzed',
      value: liveStats ? liveStats.claims_count.toLocaleString() : '0',
      sub: 'Atomic facts',
      icon: FileText,
      link: '/history',
      sparkline: liveStats?.sparklines?.claims || [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    },
    {
      title: 'Evidence Sources',
      value: liveStats ? liveStats.evidence_sources_count.toLocaleString() : '0',
      sub: 'Verified vaults',
      icon: BookOpen,
      link: '/knowledge-base',
      sparkline: liveStats?.sparklines?.evidence || [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    },
    {
      title: 'Conversations',
      value: liveStats ? liveStats.conversations_count.toLocaleString() : '0',
      sub: 'Multi-model chats',
      icon: MessageSquare,
      link: '/chat',
      sparkline: liveStats?.sparklines?.conversations || [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    },
  ];

  const quickActionItems = [
    {
      id: 'verify',
      title: 'Paste & Verify',
      badge: 'EVIDENCE WORKFLOW',
      icon: ShieldCheck,
      tagline: 'Deconstruct claims & query evidence',
      description: 'Break down complex paragraphs into atomic propositions and audit each claim against peer-reviewed registries and vaults.',
      path: '/verify',
      ctaText: 'Launch Verification Engine',
      features: [
        'Extract atomic propositions and report available confidence',
        'Deep semantic retrieval across private document vaults and web corpus',
        'Surface supported, contradicted, and unknown verdicts'
      ],
      metricLabel: 'Calibration Accuracy',
      metricValue: 'Not measured',
      glowColor: isDark ? '80 100 60' : '64 145 108',
      colors: isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#1B4332', '#74C69D', '#D8F3DC'],
    },
    {
      id: 'chat',
      title: 'Multi-Model Chat',
      badge: 'BYOK · COMPARE',
      icon: MessageSquare,
      tagline: 'Compare connected models side by side',
      description: 'Use your connected Groq or OpenRouter models to compare real responses to the same prompt, with your own provider keys.',
      path: '/chat',
      ctaText: 'Open Multi-Model Session',
      features: [
        'Send one prompt to up to three selected connected models',
        'See each model response and generation status independently',
        'One-click VerifAI multi-model cross-examination and fact-checking'
      ],
      metricLabel: 'Active Dispatch',
      metricValue: 'Configure models',
      glowColor: isDark ? '80 100 60' : '64 145 108',
      colors: isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#1B4332', '#74C69D', '#D8F3DC'],
    },
    {
      id: 'leaderboard',
      title: 'Model Leaderboard',
      badge: 'MEASURED RESULTS',
      icon: Trophy,
      tagline: 'Observed accuracy & hallucination',
      description: 'Benchmark empirical factual accuracy rankings, hallucination resistance rates, and citation calibration metrics across models.',
      path: '/leaderboard',
      ctaText: 'View Leaderboard Matrix',
      features: [
        'View measured rankings when enough real evaluations exist',
        'Inspect observed support and contradiction measures',
        'Explore available reliability and latency metrics'
      ],
      metricLabel: 'Top Performer',
      metricValue: 'Awaiting benchmarks',
      glowColor: isDark ? '80 100 60' : '64 145 108',
      colors: isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#1B4332', '#74C69D', '#D8F3DC'],
    },
    {
      id: 'kb',
      title: 'Knowledge Base',
      badge: 'DOCUMENT LIBRARY',
      icon: BookOpen,
      tagline: 'Institutional document vault',
      description: 'Ingest enterprise research publications, regulatory PDF guidelines, and corporate technical specifications into vaults.',
      path: '/knowledge-base',
      ctaText: 'Manage Vault Documents',
      features: [
        'Automated document vector chunking and high-density semantic indexing',
        'Access-controlled document retrieval linked to your account',
        'Review document sources and verification history'
      ],
      metricLabel: 'Vault Documents',
      metricValue: `${liveStats?.evidence_sources_count ?? 0} Sources`,
      glowColor: isDark ? '80 100 60' : '64 145 108',
      colors: isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#1B4332', '#74C69D', '#D8F3DC'],
    },
  ];

  // Both themes share one information architecture and interactive dashboard.
  // Only the light skin is scoped under .mocha-dashboard: dark JSX is unchanged.
  const activeLeaderboard = liveLeaderboard;
  const displayedLeaderboard = leaderboardFilter === 'top3'
    ? activeLeaderboard.slice(0, 3)
    : activeLeaderboard.slice(0, 5);

  return (
    <div className={`space-y-7 pb-14 transition-colors duration-500 max-w-full ${isDark ? '' : 'mocha-dashboard'}`}>
      {dataError && <p role="alert" className="text-sm text-rose-600 dark:text-rose-300">Dashboard data unavailable: {dataError}</p>}
      {leaderboardError && <p role="alert" className="text-sm text-rose-600 dark:text-rose-300">Leaderboard unavailable: {leaderboardError}</p>}

      {/* 1. Hero / Welcome Card */}
      <section
        className={`mocha-dashboard-hero rounded-[28px] p-6 sm:p-8 md:p-9 border transition-all duration-300 relative overflow-hidden ${
          isDark
            ? 'bg-[#0B1216] border-[#1C2C30] shadow-2xl shadow-black/50'
            : 'lt-section-card border-[#74C69D] shadow-[0_20px_48px_-24px_rgba(27, 67, 50,0.45)] bg-[#1B4332]'
        }`}
        style={{
          backgroundImage: isDark ? `url(${heroCardDarkBg})` : `url(${heroCardLightBg})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center right',
          backgroundRepeat: 'no-repeat',
        }}
      >
        {/* Ambient background glow orbs for dark mode */}
        {isDark && (
          <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full blur-3xl pointer-events-none bg-[#B6FF2E]/10 from-[#B6FF2E]/15 to-transparent" />
        )}

        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-center">
          <div className="lg:col-span-8 space-y-4">
            {/* Version & Status Badge */}
            <div className="mocha-hero-kicker inline-flex items-center gap-2">
              <span className={`px-3.5 py-1 rounded-full text-xs font-extrabold tracking-wide uppercase flex items-center gap-2 ${
                isDark
                  ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/30 shadow-[0_0_12px_rgba(182,255,46,0.2)]'
                  : 'bg-[#D8F3DC]/90 backdrop-blur-xs text-[#1B4332] border border-[#74C69D]'
              }`}>
                <span className={`w-2 h-2 rounded-full animate-pulse ${
                  isDark ? 'bg-[#B6FF2E] shadow-[0_0_6px_#B6FF2E]' : 'bg-[#1B4332]'
                }`} />
                <span className="font-semibold tracking-wider">VERIFAI / INTELLIGENCE WORKSPACE</span>
              </span>
            </div>

            <h1 className={`text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight leading-tight transition-colors ${
              isDark ? 'text-white' : 'text-[#1B4332]'
            }`}>
              Welcome back, <span className={isDark ? 'text-[#B6FF2E]' : 'text-[#D8F3DC]'}>{userName}</span>.
            </h1>

            <p className={`mocha-dashboard-intro text-sm md:text-base leading-relaxed max-w-xl font-normal ${
              isDark ? 'text-slate-300' : 'text-[#356B52]'
            }`}>
              A clearer view of what your models say, what the evidence supports, and what still needs to be verified. Your work starts here.
            </p>

            {/* Quick Action Navigation Buttons */}
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => navigate('/verify')}
                className={`mocha-hero-primary inline-flex items-center justify-center gap-2.5 px-5 py-3 rounded-xl text-sm font-extrabold transition-all duration-200 active:scale-[0.98] hover:-translate-y-0.5 ${isDark ? 'bg-[#B6FF2E] text-[#12141A] hover:bg-[#A3E823]' : ''}`}
              >
                <ShieldCheck size={18} strokeWidth={2.3} />
                Start Verification
                <ArrowRight size={16} />
              </button>
              <button
                type="button"
                onClick={() => navigate('/leaderboard')}
                className={`mocha-hero-outline inline-flex items-center justify-center gap-2.5 px-5 py-3 rounded-xl text-sm font-bold transition-all duration-200 active:scale-[0.98] hover:-translate-y-0.5 ${isDark ? 'bg-[#14161C] text-white border border-[#2E3340]' : ''}`}
              >
                <Trophy size={17} />
                Model Leaderboard
              </button>

              <button
                onClick={() => navigate('/chat')}
                className={`mocha-hero-outline px-4 py-3 rounded-xl text-xs sm:text-sm font-bold transition-all duration-200 transform active:scale-95 hover:scale-[1.02] border flex items-center gap-2 cursor-pointer ${
                  isDark
                    ? 'bg-[#14161C] text-slate-300 hover:text-white border-[#2E3340] hover:border-[#B6FF2E]/40 hover:shadow-[0_0_15px_rgba(182,255,46,0.15)]'
                    : 'bg-[#D8F3DC]/90 backdrop-blur-xs text-[#356B52] hover:text-[#1B4332] border-[#74C69D] hover:bg-[#D8F3DC] hover:shadow-xs'
                }`}
              >
                <MessageSquare size={16} className={isDark ? 'text-[#B6FF2E]' : 'text-[#1B4332]'} />
                <span>Multi-Model Chat</span>
              </button>
            </div>
          </div>

          {/* Right Trust Engine Stat Card */}
          <div className="lg:col-span-4 hidden lg:flex justify-end items-center relative z-10">
            <div className={isDark ? 'animate-float-gentle' : 'w-full max-w-[270px]'}>
              <div className={`mocha-trust-panel w-64 p-5 rounded-2xl border transition-all duration-300 shadow-xl ${
                isDark
                  ? 'bg-[#14161C]/90 backdrop-blur-md border-[#2E3340] text-white shadow-black/50'
                  : 'bg-white/10 backdrop-blur-lg border-white/20 text-white shadow-[0_16px_36px_-10px_rgba(21,5,22,0.35)]'
              }`}>
                {/* Header: Title + Pulsing Beacon Dot */}
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-[10px] font-extrabold uppercase tracking-widest ${
                    isDark ? 'text-[#B6FF2E]' : 'text-[#74C69D]'
                  }`}>
                    TRUST ENGINE
                  </span>
                  <span className={`w-2 h-2 rounded-full animate-pulse ${
                    isDark
                      ? 'bg-[#B6FF2E] shadow-[0_0_8px_#B6FF2E]'
                      : 'bg-[#D8F3DC] shadow-[0_0_10px_#D8F3DC]'
                  }`} />
                </div>

                {/* Score & Confidence Badge */}
                <div className="mb-2">
                  <div className="flex items-center gap-2.5">
                    <p className={`text-3xl font-black font-mono tabular-nums leading-none tracking-tight ${
                      isDark ? 'text-[#B6FF2E]' : 'text-white'
                    }`}>
                      —
                    </p>
                    <span className={`text-[9px] sm:text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full inline-flex items-center gap-1 ${
                      isDark
                        ? 'bg-[#B6FF2E]/20 text-[#B6FF2E] border border-[#B6FF2E]/35'
                        : 'bg-white/15 text-white border border-white/25 backdrop-blur-xs'
                    }`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                      <span>NOT MEASURED</span>
                    </span>
                  </div>
                  <p className={`text-xs font-sans font-medium mt-1.5 leading-snug ${
                    isDark ? 'text-slate-300' : 'text-[#D8F3DC]/90'
                  }`}>
                    Calibration not available
                  </p>
                </div>

                {/* Metrics Breakdown with Icons */}
                <div className={`text-xs pt-2.5 mt-2.5 border-t space-y-1.5 font-medium font-palatino ${
                  isDark ? 'border-[#2E3340] text-slate-400' : 'border-white/15 text-[#D8F3DC]/85'
                }`}>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-1.5 opacity-85">
                      <Trophy size={12} className={isDark ? 'text-[#B6FF2E]' : 'text-[#74C69D]'} />
                      <span>Consensus</span>
                    </span>
                    <span className={isDark ? 'text-[#B6FF2E] font-bold' : 'text-white font-bold'}>Not assessed</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-1.5 opacity-85">
                      <Cpu size={12} className={isDark ? 'text-[#B6FF2E]' : 'text-[#74C69D]'} />
                      <span>Pipeline</span>
                    </span>
                    <span className={isDark ? 'text-[#B6FF2E] font-bold' : 'text-white font-bold'}>No live audit status</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-1.5 opacity-85">
                      <Clock size={12} className={isDark ? 'text-slate-400' : 'text-[#74C69D]'} />
                      <span>Last updated</span>
                    </span>
                    <span className={isDark ? 'text-slate-300' : 'text-white/90'}>Unavailable</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Four Metric Stats Grid */}
      <section className="grid grid-cols-1 min-[400px]:grid-cols-2 lg:grid-cols-4 gap-3.5 sm:gap-4">
        {statCards.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div
              key={idx}
              role="link"
              tabIndex={0}
              onClick={() => navigate(stat.link)}
              onKeyDown={event => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  navigate(stat.link);
                }
              }}
              aria-label={`View ${stat.title}`}
              className={`p-4.5 sm:p-5 border cursor-pointer group flex flex-col justify-between relative overflow-hidden dashboard-card-enhanced stagger-reveal animated-border-card ${
                isDark
                  ? 'rounded-2xl bg-[#1E2129] border-[#2E3340] hover:border-[#B6FF2E]/40 hover:shadow-[0_8px_20px_rgba(0,0,0,0.35),0_0_15px_rgba(182,255,46,0.12)]'
                  : 'lt-kpi-card rounded-2xl'
              }`}
            >
              {/* Subtle ambient warm aura */}
              {!isDark && (
                <div className="absolute -top-12 -right-12 w-32 h-32 rounded-full blur-2xl pointer-events-none bg-[#D8F3DC]/60 transition-opacity group-hover:bg-[#74C69D]/80" />
              )}

              <div className="flex items-center justify-between mb-3 relative z-10">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-300 group-hover:scale-105 ${
                  isDark
                    ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/25 shadow-[0_0_12px_rgba(182,255,46,0.15)] group-hover:border-[#B6FF2E]/50'
                    : 'bg-[#1B4332]/40 text-white border border-white/25 group-hover:bg-[#1B4332]/60'
                }`}>
                  <Icon size={17} strokeWidth={2.2} />
                </div>

                <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full transition-transform duration-300 group-hover:scale-105 ${
                  isDark
                    ? 'bg-[#B6FF2E]/15 text-[#B6FF2E] border border-[#B6FF2E]/30'
                    : 'bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D]'
                }`}>
                  <span>Open</span>
                  <ArrowRight size={12} strokeWidth={2.5} />
                </span>
              </div>

              <div className="relative z-10">
                <p className={`text-[11px] font-extrabold uppercase tracking-wider mb-1.5 ${
                  isDark ? 'text-slate-400' : 'text-[#356B52]'
                }`}>
                  {stat.title}
                </p>

                <div className="flex items-end justify-between">
                  <div>
                    <h4 className={`text-2xl sm:text-3xl font-black font-mono tabular-nums leading-none ${
                      isDark ? 'text-white group-hover:text-[#B6FF2E]' : 'text-[#1B4332] group-hover:text-[#1B4332]'
                    } transition-colors duration-200`}>
                      {stat.value}
                    </h4>
                  </div>

                  <div className="flex flex-col items-end gap-1">
                    {/* Mini Sparkline / Histogram Bars matching the reference */}
                    <div className="dashboard-stat-sparkline flex items-end gap-[2.5px] h-5 px-0.5">
                      {stat.sparkline.map((h: number, sIdx: number) => (
                        <span
                          key={sIdx}
                          className={`w-[2.5px] rounded-full transition-all duration-300 ${
                            isDark
                              ? 'bg-[#B6FF2E]/30 group-hover:bg-[#B6FF2E]/70'
                              : 'bg-[#1B4332]/25 group-hover:bg-[#1B4332]/65'
                          }`}
                          style={{ height: `${h}%` }}
                        />
                      ))}
                    </div>
                    <span className={`text-[11px] font-semibold ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>
                      {stat.sub}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </section>

      {/* 3. KEY FEATURE: Model Performance Leaderboard Showcase */}
      <section className={`p-5 sm:p-6 border transition-all relative overflow-hidden ${
        isDark
          ? 'rounded-2xl bg-[#1E2129] border-[#2E3340] shadow-xl'
          : 'lt-section-card rounded-2xl'
      }`}>
        {/* Ambient background glow orbs */}
        {!isDark && (
          <>
            <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full blur-3xl pointer-events-none bg-[#D8F3DC]/70" />
            <div className="absolute -bottom-24 -left-24 w-72 h-72 rounded-full blur-3xl pointer-events-none bg-[#74C69D]/40" />
          </>
        )}
        {isDark && (
          <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full blur-3xl pointer-events-none bg-[#B6FF2E]/05" />
        )}

        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#74C69D] dark:border-[#2E3340]">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                isDark ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/30' : 'bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D]'
              }`}>
                <Trophy size={16} />
              </div>
              <h3 className={`font-extrabold text-lg sm:text-xl tracking-tight ${
                isDark ? 'text-white' : 'text-[#1B4332]'
              }`}>
                Model Performance Leaderboard
              </h3>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                isDark ? 'bg-[#B6FF2E]/15 text-[#B6FF2E]' : 'bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D]'
              }`}>
                Measured Results
              </span>
            </div>
            <p className={`text-sm font-medium font-palatino ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>
              Explore observed model verification scores and evidence-support metrics when measured benchmarks are available.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className={`p-1 rounded-xl border flex items-center gap-1 ${
              isDark ? 'bg-[#14161C] border-[#2E3340]' : 'bg-[#D8F3DC] border-[#74C69D]'
            }`}>
              <button
                onClick={() => setLeaderboardFilter('top3')}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-bold transition-all cursor-pointer ${
                  leaderboardFilter === 'top3'
                    ? isDark ? 'bg-[#B6FF2E] text-[#12141A]' : 'bg-[#1B4332] text-[#FFFFFF] shadow-xs'
                    : isDark ? 'text-slate-400 hover:text-white' : 'text-[#356B52] hover:text-[#1B4332]'
                }`}
              >
                Top 3
              </button>
              <button
                onClick={() => setLeaderboardFilter('all')}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-bold transition-all cursor-pointer ${
                  leaderboardFilter === 'all'
                    ? isDark ? 'bg-[#B6FF2E] text-[#12141A]' : 'bg-[#1B4332] text-[#FFFFFF] shadow-xs'
                    : isDark ? 'text-slate-400 hover:text-white' : 'text-[#356B52] hover:text-[#1B4332]'
                }`}
              >
                All Models
              </button>
            </div>

            <button
              onClick={() => navigate('/leaderboard')}
              className={`px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition-all cursor-pointer shadow-md ${
                isDark
                  ? 'bg-[#B6FF2E] text-[#12141A] hover:bg-[#A3E823]'
                  : 'bg-[#1B4332] text-[#FFFFFF] hover:bg-[#163E2D] shadow-[#1B4332]/20'
              }`}
            >
              <span>Full Benchmark Matrix</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </div>

        {/* Model Ranking Cards / Responsive Grid */}
        {displayedLeaderboard.length === 0 && (
          <div
            role="status"
            className={`mocha-empty-state mt-5 rounded-2xl border px-5 py-6 md:px-7 md:py-7 flex flex-col sm:flex-row items-start sm:items-center gap-4 relative z-10 ${
              isDark ? 'bg-[#14161C] border-[#2E3340]' : 'bg-[#D8F3DC] border-[#74C69D]'
            }`}
          >
            <div className={`mocha-empty-icon shrink-0 h-11 w-11 rounded-2xl flex items-center justify-center ${
              isDark ? 'bg-[#B6FF2E]/10 text-[#B6FF2E]' : 'bg-[#D8F3DC] text-[#1B4332]'
            }`}>
              <Trophy size={21} strokeWidth={1.8} />
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-extrabold ${isDark ? 'text-white' : 'text-[#1B4332]'}`}>
                Your benchmark story starts with real evaluations
              </p>
              <p className={`text-xs sm:text-sm leading-relaxed mt-1 ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>
                No model rankings have been measured yet. Verified scores and comparisons will appear here once available.
              </p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/leaderboard')}
              className={`shrink-0 inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-colors ${
                isDark
                  ? 'border border-[#333742] text-[#B6FF2E] hover:bg-[#242A31]'
                  : 'border border-[#74C69D] text-[#1B4332] hover:bg-[#D8F3DC]'
              }`}
            >
              View leaderboard <ArrowRight size={14} />
            </button>
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 relative z-10">
          {displayedLeaderboard.map((item: ModelLeaderboardEntry) => {
            const isRank1 = item.rank === 1;
            const isRank2 = item.rank === 2;
            const isRank3 = item.rank === 3;

            return (
              <div
                key={item.model}
                onClick={() => navigate('/leaderboard')}
                className={`p-5 rounded-[1.75rem] border transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] cursor-pointer group relative flex flex-col justify-between hover:-translate-y-1 ${
                  isDark
                    ? 'bg-[#14161C] border-[#2E3340] hover:border-[#B6FF2E]/50 hover:shadow-[0_12px_24px_rgba(0,0,0,0.5),0_0_20px_rgba(182,255,46,0.18)]'
                    : 'bg-gradient-to-br from-[#FFFFFF] via-[#FFFFFF] to-[#D8F3DC]/60 border-[#74C69D] hover:border-[#1B4332]/40 hover:shadow-xl hover:shadow-[#1B4332]/10'
                }`}
              >
                {/* Header: Rank + Model Title + Score */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono font-black text-xs transition-transform duration-300 group-hover:scale-105 ${
                        isRank1
                          ? isDark ? 'bg-[#B6FF2E] text-[#12141A]' : 'bg-[#1B4332] text-[#FFFFFF]'
                          : isRank2
                          ? isDark ? 'bg-amber-400/20 text-amber-300 border border-amber-400/40' : 'bg-[#74C69D] text-[#356B52]'
                          : isDark ? 'bg-slate-800 text-slate-300' : 'bg-[#D8F3DC] text-[#356B52]'
                      }`}>
                        #{item.rank}
                      </span>
                      <span className={`text-xs font-extrabold uppercase tracking-wider ${
                        isDark ? 'text-slate-400' : 'text-[#356B52]'
                      }`}>
                        {item.provider}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className={`text-xl font-black font-mono tabular-nums leading-none ${
                        isDark ? 'text-[#B6FF2E]' : 'text-[#1B4332]'
                      }`}>
                        {item.overallScore}%
                      </span>
                      <p className={`text-[10px] font-bold uppercase tracking-wider ${
                        isDark ? 'text-slate-400' : 'text-[#356B52]'
                      }`}>
                        Score
                      </p>
                    </div>
                  </div>

                  <h4 className={`text-base font-extrabold tracking-tight mb-2 transition-colors ${
                    isDark ? 'text-white group-hover:text-[#B6FF2E]' : 'text-[#1B4332] group-hover:text-[#1B4332]'
                  }`}>
                    {item.model}
                  </h4>

                  {/* Key Metrics Mini Bars: Factual Support, Hallucination Resistance, Citation Accuracy */}
                  <div className="space-y-2.5 pt-1 pb-3">
                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1.5">
                        <span className={isDark ? 'text-slate-400' : 'text-[#356B52]'}>Factual Support</span>
                        <span className={`font-mono ${isDark ? 'text-slate-200' : 'text-[#1B4332]'}`}>
                          {item.categories.factualSupport}%
                        </span>
                      </div>
                      <div className={`h-2 w-full ${
                        isDark ? 'rounded-full overflow-hidden bg-[#2E3340]' : 'lt-progress-track bg-[#D8F3DC]'
                      }`}>
                        <div
                          className={isDark
                            ? 'h-full rounded-full bg-[#B6FF2E] transition-all duration-1000 ease-out'
                            : 'h-full rounded-full bg-gradient-to-r from-[#40916C] to-[#1B4332] transition-all duration-1000 ease-out'}
                          style={{ width: `${item.categories.factualSupport}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1.5">
                        <span className={isDark ? 'text-slate-400' : 'text-[#356B52]'}>Hallucination Resistance</span>
                        <span className={`font-mono ${isDark ? 'text-slate-200' : 'text-[#1B4332]'}`}>
                          {item.categories.contradictionDetection}%
                        </span>
                      </div>
                      <div className={`h-2 w-full ${
                        isDark ? 'rounded-full overflow-hidden bg-[#2E3340]' : 'lt-progress-track bg-[#D8F3DC]'
                      }`}>
                        <div
                          className={isDark
                            ? 'h-full rounded-full bg-[#A3E823] transition-all duration-1000 ease-out'
                            : 'h-full rounded-full bg-gradient-to-r from-[#40916C] to-[#1B4332] transition-all duration-1000 ease-out'}
                          style={{ width: `${item.categories.contradictionDetection}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1.5">
                        <span className={isDark ? 'text-slate-400' : 'text-[#356B52]'}>Citation Accuracy</span>
                        <span className={`font-mono ${isDark ? 'text-slate-200' : 'text-[#1B4332]'}`}>
                          {item.categories.evidenceSupport}%
                        </span>
                      </div>
                      <div className={`h-2 w-full ${
                        isDark ? 'rounded-full overflow-hidden bg-[#2E3340]' : 'lt-progress-track bg-[#D8F3DC]'
                      }`}>
                        <div
                          className={isDark
                            ? 'h-full rounded-full bg-[#80C020] transition-all duration-1000 ease-out'
                            : 'h-full rounded-full bg-gradient-to-r from-[#40916C] to-[#1B4332] transition-all duration-1000 ease-out'}
                          style={{ width: `${item.categories.evidenceSupport}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Footer details with circular chevron icon */}
                <div className={`pt-3 border-t flex items-center justify-between text-xs ${
                  isDark ? 'border-[#2E3340] text-slate-400' : 'border-[#74C69D] text-[#356B52]'
                }`}>
                  <span>{item.evaluationsCount} Evals Tested</span>
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${
                    isDark
                      ? 'bg-[#1E2129] text-[#B6FF2E] border border-[#2E3340] group-hover:border-[#B6FF2E]/40'
                      : 'bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D] group-hover:bg-[#1B4332] group-hover:text-white'
                  }`}>
                    <ChevronRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 4. Quick Actions & Evaluation Insights Grid with BorderGlow */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-1">
          <div>
            <h3 className={`font-extrabold text-base md:text-lg tracking-tight ${
              isDark ? 'text-white' : 'text-[#1B4332]'
            }`}>
              Quick Actions & Evaluation Engines
            </h3>
            <p className={`text-xs sm:text-sm font-medium ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>
              Select any pipeline below to scope into capabilities and launch immediate execution.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className={`w-2 h-2 rounded-full ${isDark ? 'bg-[#B6FF2E]' : 'bg-[#1B4332]'}`} />
            <span className={`font-sans font-semibold text-xs tracking-wide ${isDark ? 'text-[#B6FF2E]' : 'text-[#1B4332]'}`}>
              Scoped: {quickActionItems.find(q => q.id === scopedActionId)?.title}
            </span>
          </div>
        </div>

        {/* 4 Aligned Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-stretch">
          {quickActionItems.map((item) => {
            const isScoped = scopedActionId === item.id;
            const Icon = item.icon;

            return (
              <BorderGlow
                key={item.id}
                borderRadius={24}
                glowRadius={32}
                edgeSensitivity={35}
                glowColor={item.glowColor}
                backgroundColor={isDark ? '#1E2129' : '#FFFFFF'}
                colors={item.colors}
                onClick={() => setScopedActionId(item.id)}
                className={`transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] cursor-pointer h-full ${
                  isScoped
                    ? isDark
                      ? 'ring-2 ring-[#B6FF2E] shadow-[0_0_25px_rgba(182,255,46,0.18)] -translate-y-1'
                      : 'ring-2 ring-[#1B4332] shadow-lg shadow-[#1B4332]/10 -translate-y-1'
                    : 'opacity-95 hover:opacity-100 hover:-translate-y-0.5'
                }`}
              >
                <div className={`p-5 flex flex-col justify-between h-full rounded-[24px] transition-all relative overflow-hidden ${
                  isScoped
                    ? isDark
                      ? 'bg-[#1E2129]'
                      : 'bg-gradient-to-br from-[#D8F3DC] to-[#D8F3DC] border border-[#1B4332]/25'
                    : isDark
                      ? 'bg-[#1E2129]'
                      : 'bg-gradient-to-br from-[#FFFFFF] via-[#FFFFFF] to-[#D8F3DC]/60 border border-[#74C69D] hover:border-[#1B4332]/35'
                }`}>
                  {/* Subtle ambient warm aura */}
                  {!isDark && (
                    <div className={`absolute -top-10 -right-10 w-28 h-28 rounded-full blur-2xl pointer-events-none transition-opacity ${
                      isScoped ? 'bg-[#74C69D]/80' : 'bg-[#D8F3DC]/50'
                    }`} />
                  )}

                  {/* Card Content Top + Middle */}
                  <div className="relative z-10 flex-1 flex flex-col">
                    <div className="flex items-center justify-between mb-3">
                      <div className={`w-10 h-10 rounded-2xl flex items-center justify-center transition-transform ${
                        isScoped ? 'scale-105' : ''
                      } ${
                        isDark
                          ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/30 shadow-[0_0_12px_rgba(182,255,46,0.18)]'
                          : isScoped
                          ? 'bg-[#1B4332] text-[#FFFFFF] shadow-sm'
                          : 'bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D]'
                      }`}>
                        <Icon size={19} strokeWidth={2.4} />
                      </div>

                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase ${
                        isScoped
                          ? isDark
                            ? 'bg-[#B6FF2E] text-[#12141A] font-black shadow-[0_0_10px_rgba(182,255,46,0.3)]'
                            : 'bg-[#1B4332] text-[#FFFFFF] font-black shadow-xs'
                          : isDark
                            ? 'bg-[#14161C] text-slate-400 border border-[#2E3340]'
                            : 'bg-[#D8F3DC] text-[#356B52] border border-[#74C69D]'
                      }`}>
                        {isScoped ? 'Active Scope' : item.badge}
                      </span>
                    </div>

                    <h4 className={`font-black text-base tracking-tight mb-1 transition-colors font-palatino ${
                      isScoped
                        ? isDark ? 'text-[#B6FF2E]' : 'text-[#1B4332]'
                        : isDark ? 'text-white' : 'text-[#1B4332]'
                    }`}>
                      {item.title}
                    </h4>

                    <p className={`text-xs font-medium mb-2 font-sans tracking-normal transition-colors ${
                      isDark ? 'text-slate-400' : isScoped ? 'text-[#1B4332]/90 font-semibold' : 'text-[#356B52]'
                    }`}>
                      {item.tagline}
                    </p>

                    <div className="min-h-[64px] mb-4">
                      <p className={`text-xs sm:text-sm leading-relaxed transition-colors font-palatino ${
                        isDark ? 'text-slate-300' : 'text-[#356B52]'
                      }`}>
                        {item.description}
                      </p>
                    </div>

                    {/* Metric & Features - Leveled across all 4 cards */}
                    <div className={`pt-3.5 border-t space-y-3 flex-1 flex flex-col justify-between ${
                      isDark ? 'border-[#2E3340]' : 'border-[#74C69D]'
                    }`}>
                      <div className="flex items-center justify-between text-xs font-mono font-bold font-palatino">
                        <span className={isDark ? 'text-slate-400' : 'text-[#356B52]'}>
                          {item.metricLabel}
                        </span>
                        <span className={`px-2 py-0.5 rounded-md text-xs font-mono font-bold ${
                          isDark
                            ? 'text-[#B6FF2E] bg-[#B6FF2E]/10'
                            : isScoped
                            ? 'text-[#1B4332] bg-[#1B4332]/10 font-black'
                            : 'text-[#1B4332] bg-[#D8F3DC]'
                        }`}>
                          {item.metricValue}
                        </span>
                      </div>

                      <div className="space-y-2 text-xs font-palatino flex-1">
                        {item.features.map((feat, fIdx) => (
                          <div key={fIdx} className="flex items-start gap-1.5 text-slate-600 dark:text-slate-300 min-h-[32px]">
                            <Check size={13} className={`shrink-0 mt-0.5 ${
                              isDark ? 'text-[#B6FF2E]' : isScoped ? 'text-[#1B4332]' : 'text-[#40916C]'
                            }`} />
                            <span className="leading-snug text-[11px] sm:text-xs">{feat}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Card Footer Button */}
                  <div className={`mt-4 pt-3 border-t relative z-10 ${
                    isDark ? 'border-[#2E3340]' : 'border-[#74C69D]'
                  }`}>
                    {isScoped ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(item.path);
                        }}
                        className={`w-full h-10 px-4 rounded-xl text-xs font-bold tracking-wide transition-all duration-200 transform active:scale-95 flex items-center justify-center gap-2 cursor-pointer shadow-md ${
                          isDark
                            ? 'bg-[#B6FF2E] text-[#12141A] hover:bg-[#A3E823] shadow-[0_0_15px_rgba(182,255,46,0.3)]'
                            : 'bg-[#1B4332] text-[#FFFFFF] hover:bg-[#163E2D] shadow-[#1B4332]/25'
                        }`}
                      >
                        <span className="font-palatino font-bold">{item.ctaText}</span>
                        <ArrowRight size={14} />
                      </button>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(item.path);
                        }}
                        className={`w-full h-10 px-4 rounded-xl text-xs font-bold transition-all duration-200 transform active:scale-95 flex items-center justify-between cursor-pointer border ${
                          isDark
                            ? 'bg-[#14161C] text-slate-300 hover:text-white border-[#2E3340] hover:border-[#B6FF2E]/40'
                            : 'bg-[#D8F3DC] text-[#356B52] hover:text-[#1B4332] hover:bg-[#D8F3DC] border-[#74C69D]'
                        }`}
                      >
                        <span className="font-palatino">{item.ctaText}</span>
                        <ChevronRight size={14} className="opacity-70 group-hover:translate-x-0.5 transition-transform" />
                      </button>
                    )}
                  </div>

                </div>
              </BorderGlow>
            );
          })}
        </div>
      </section>

      {/* 5. Bottom Row: Recent Verifications + Activity Timeline Curve */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

        {/* Left: Recent Verifications List */}
        <section className={`lg:col-span-6 p-5 sm:p-6 border space-y-4 relative overflow-hidden chart-section-entrance ${
          isDark
            ? 'rounded-2xl bg-[#1E2129] border-[#2E3340]'
            : 'lt-section-card rounded-2xl'
        }`}>
          {/* Ambient background glow */}
          {!isDark && (
            <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full blur-3xl pointer-events-none bg-[#D8F3DC]/80" />
          )}

          <div className="flex items-center justify-between relative z-10">
            <div>
              <h3 className={`font-extrabold text-base md:text-lg tracking-tight ${
                isDark ? 'text-white' : 'text-[#1B4332]'
              }`}>
                Recent Verifications
              </h3>
              <p className={`text-xs sm:text-sm font-medium ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>
                Last executed truth propositions & evidence audits
              </p>
            </div>

            <button
              onClick={() => navigate('/history')}
              className={`text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
                isDark ? 'text-[#B6FF2E] hover:text-[#A3E823]' : 'text-[#1B4332] hover:text-[#163E2D]'
              }`}
            >
              View All History
            </button>
          </div>

          <div className="relative z-10">
            {verifications.length === 0 ? (
              <div className="py-8 text-center space-y-3">
                <div className={`w-10 h-10 rounded-xl mx-auto flex items-center justify-center ${
                  isDark ? 'bg-[#14161C] text-slate-400 border border-[#2E3340]' : 'bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D]'
                }`}>
                  <ShieldCheck size={20} strokeWidth={2.2} />
                </div>
                <div className="space-y-1">
                  <h4 className={`text-sm font-bold ${isDark ? 'text-slate-200' : 'text-[#1B4332]'}`}>
                    No verifications recorded yet
                  </h4>
                  <p className={`text-xs max-w-sm mx-auto ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>
                    Verify propositions and audit claims across ground-truth vaults.
                  </p>
                </div>
                <button
                  onClick={() => navigate('/verify')}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition-all active:scale-95 shadow-xs ${
                    isDark ? 'bg-[#B6FF2E] text-[#12141A] hover:bg-[#A3E823]' : 'bg-[#1B4332] text-[#D8F3DC] hover:bg-[#163E2D]'
                  }`}
                >
                  <ShieldCheck size={13} />
                  <span>Audit First Claim</span>
                  <ArrowRight size={12} />
                </button>
              </div>
            ) : (
              <div className={`divide-y ${isDark ? 'divide-[#2E3340]' : 'divide-[#74C69D]'}`}>
                {verifications.slice(0, 4).map((rec) => (
                  <div
                    key={rec.id}
                    onClick={() => navigate(`/verification/${rec.id}`)}
                    className={`py-3 first:pt-0 last:pb-0 flex items-center justify-between gap-3 group cursor-pointer -mx-2 px-2 rounded-xl transition-all duration-300 hover:translate-x-1 ${
                      isDark ? 'hover:bg-[#14161C]' : 'hover:bg-[#D8F3DC]/80'
                    }`}
                  >
                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider font-mono inline-flex items-center gap-1 ${
                          rec.status === 'SUPPORTED'
                            ? isDark
                              ? 'bg-[#B6FF2E]/15 text-[#B6FF2E] border border-[#B6FF2E]/30'
                              : 'bg-[#EDF7F0] text-[#1D6A42] border border-[#BDE3CC]'
                            : rec.status === 'CONTRADICTED'
                            ? isDark
                              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                              : 'bg-[#FDECEE] text-[#9E1B28] border border-[#F5C2C7]'
                            : isDark
                            ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                            : 'bg-[#FEF6EC] text-[#8F5A0C] border border-[#F5DCB4]'
                        }`}>
                          {rec.status}
                        </span>
                        <span className={`text-xs font-medium ${isDark ? 'text-slate-500' : 'text-[#356B52]'}`}>·</span>
                        <span className={`text-xs font-medium font-mono ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>{rec.timestamp}</span>
                      </div>

                      <h4 className={`text-sm font-bold truncate transition-colors ${
                        isDark ? 'text-slate-200 group-hover:text-[#B6FF2E]' : 'text-[#1B4332] group-hover:text-[#1B4332]'
                      }`}>
                        {rec.query}
                      </h4>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className={`text-xs font-semibold tabular-nums hidden sm:inline ${
                        isDark ? 'text-slate-400' : 'text-[#356B52]'
                      }`}>
                        {rec.claimsCount} claims · {rec.evidenceCount} sources
                      </span>
                      <ChevronRight size={15} className={`transition-transform duration-200 group-hover:translate-x-1 ${
                        isDark ? 'text-slate-500 group-hover:text-[#B6FF2E]' : 'text-[#356B52] group-hover:text-[#1B4332]'
                      }`} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Right: Verification Activity Timeline Curve */}
        <section className={`lg:col-span-6 p-5 sm:p-6 border space-y-4 relative overflow-hidden chart-section-entrance ${
          isDark
            ? 'rounded-2xl bg-[#1E2129] border-[#2E3340]'
            : 'lt-section-card rounded-2xl'
        }`}>
          {/* Ambient background glow */}
          {!isDark && (
            <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full blur-3xl pointer-events-none bg-[#D8F3DC]/80" />
          )}

          <div className="flex items-center justify-between relative z-10">
            <div>
              <h3 className={`font-extrabold text-base md:text-lg tracking-tight ${
                isDark ? 'text-white' : 'text-[#1B4332]'
              }`}>
                Activity Timeline
              </h3>
              <p className={`text-xs sm:text-sm font-medium ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>
                Verified propositions and evidence retrieval throughput
              </p>
            </div>

            <div className="flex items-center gap-1.5">
              {(['7D', '30D'] as const).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`px-3 py-1 rounded-xl text-xs font-bold transition-all duration-200 transform active:scale-95 cursor-pointer ${
                    timeframe === tf
                      ? isDark
                        ? 'bg-[#B6FF2E] text-[#12141A] font-black shadow-xs'
                        : 'bg-[#1B4332] text-[#FFFFFF] shadow-xs'
                      : isDark
                        ? 'bg-[#14161C] text-slate-400 hover:text-white'
                        : 'bg-[#D8F3DC] text-[#356B52] hover:text-[#1B4332] border border-[#74C69D]'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {/* Metric Selector Tabs */}
          <div className="flex gap-2 pt-1 relative z-10">
            {[
              { id: 'verifications', label: 'Verifications' },
              { id: 'claims', label: 'Claims Analyzed' },
              { id: 'evidence', label: 'Evidence Citations' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setChartMetric(m.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                  chartMetric === m.id
                    ? isDark
                      ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/30'
                      : 'bg-[#1B4332] text-[#FFFFFF]'
                    : isDark
                      ? 'text-slate-500 hover:text-slate-300'
                      : 'bg-[#D8F3DC] text-[#356B52] hover:text-[#1B4332] border border-[#74C69D]'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Chart View. Never imply a historical trend when there are no data points. */}
          <div className="h-64 w-full pt-2 relative z-10">
            {chartData.length === 0 ? (
              <div
                role="status"
                className={`mocha-empty-state h-full rounded-2xl border flex flex-col justify-center items-center text-center px-5 ${
                  isDark ? 'bg-[#14161C] border-[#2E3340]' : 'bg-[#D8F3DC] border-[#74C69D]'
                }`}
              >
                <div className={`mocha-empty-icon h-11 w-11 rounded-2xl flex items-center justify-center mb-3 ${
                  isDark ? 'bg-[#B6FF2E]/10 text-[#B6FF2E]' : 'bg-[#D8F3DC] text-[#1B4332]'
                }`}>
                  <BarChart3 size={21} strokeWidth={1.8} />
                </div>
                <p className={`text-sm font-extrabold ${isDark ? 'text-white' : 'text-[#1B4332]'}`}>
                  No activity to chart yet
                </p>
                <p className={`text-xs leading-relaxed mt-1 max-w-[320px] ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>
                  Once you verify claims, measured activity for this period will appear here.
                </p>
                <button type="button" onClick={() => navigate('/verify')}
                  className={`mt-3 inline-flex items-center gap-1.5 text-xs font-bold hover:underline ${
                    isDark ? 'text-[#B6FF2E]' : 'text-[#1B4332]'
                  }`}>
                  Verify a claim <ArrowRight size={13} />
                </button>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop
                      offset="5%"
                      stopColor={isDark ? '#B6FF2E' : '#1B4332'}
                      stopOpacity={isDark ? 0.35 : 0.28}
                    />
                    <stop
                      offset="95%"
                      stopColor={isDark ? '#B6FF2E' : '#74C69D'}
                      stopOpacity={0.0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke={isDark ? '#2E3340' : '#74C69D'}
                />
                <XAxis
                  dataKey="name"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: isDark ? '#94A3B8' : '#356B52', fontSize: 11 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: isDark ? '#94A3B8' : '#356B52', fontSize: 11 }}
                />
                <Tooltip
                  animationDuration={500}
                  animationEasing="ease-out"
                  isAnimationActive={true}
                  cursor={{
                    stroke: isDark ? '#B6FF2E' : '#1B4332',
                    strokeWidth: 1.5,
                    strokeDasharray: '4 4',
                    strokeOpacity: 0.6
                  }}
                  contentStyle={{
                    borderRadius: '16px',
                    background: isDark ? '#14161C' : '#FFFFFF',
                    color: isDark ? '#FFFFFF' : '#1B4332',
                    border: isDark ? '1px solid #2E3340' : '1px solid #74C69D',
                    boxShadow: '0 10px 25px rgba(27, 67, 50,0.12)',
                    fontSize: '12px',
                    transition: 'all 0.35s cubic-bezier(0.22, 1, 0.36, 1)'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey={chartMetric}
                  stroke={isDark ? '#B6FF2E' : '#1B4332'}
                  strokeWidth={3}
                  fill="url(#areaGradient)"
                  dot={{ r: 4, fill: isDark ? '#14161C' : '#FFFFFF', stroke: isDark ? '#B6FF2E' : '#1B4332', strokeWidth: 2 }}
                  activeDot={{
                    r: 6,
                    fill: isDark ? '#B6FF2E' : '#1B4332',
                    stroke: isDark ? '#14161C' : '#FFFFFF',
                    strokeWidth: 2.5
                  }}
                />
              </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>

      </div>
    </div>
  );
};

export default DashboardPage;
