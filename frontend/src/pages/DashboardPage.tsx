import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  MessageSquare, 
  BookOpen, 
  FileText, 
  ChevronRight, 
  TrendingUp, 
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
import { initialLeaderboard } from '../data/mockBackendData';
import { dashboardApi, modelsApi, BackendDashboardStats } from '../api';
import { BorderGlow } from '../components/ui/BorderGlow';
import { BorderGlowButton } from '../components/ui/BorderGlowButton';
import heroCardBg from '../assets/hero_card_bg.png';
import heroCardDarkBg from '../assets/hero_card_dark_bg.png';

interface DashboardPageProps {
  verifications: VerificationRecord[];
  weeklyChartData: ChartPoint[];
  monthlyChartData: ChartPoint[];
  userName: string;
  theme?: 'light' | 'dark';
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  verifications,
  weeklyChartData,
  monthlyChartData,
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

  React.useEffect(() => {
    dashboardApi.getStats()
      .then(stats => setLiveStats(stats))
      .catch(() => {});

    modelsApi.getModelLeaderboard()
      .then(entries => setLiveLeaderboard(entries))
      .catch(() => {});
  }, []);

  const isDark = theme === 'dark';
  const rawChartData = timeframe === '7D'
    ? (liveStats?.weekly_chart_data && liveStats.weekly_chart_data.length > 0 ? liveStats.weekly_chart_data : weeklyChartData)
    : (liveStats?.monthly_chart_data && liveStats.monthly_chart_data.length > 0 ? liveStats.monthly_chart_data : monthlyChartData);
  const chartData = rawChartData;

  const statCards = [
    {
      title: 'Verifications',
      value: liveStats ? liveStats.verifications_count.toLocaleString() : (verifications.length > 0 ? verifications.length.toLocaleString() : '42'),
      trend: '+12%',
      sub: 'This week',
      icon: ShieldCheck,
      link: '/history',
      sparkline: liveStats?.sparklines?.verifications || [35, 45, 60, 40, 75, 55, 80, 65, 95, 75, 100, 85],
    },
    {
      title: 'Claims Analyzed',
      value: liveStats ? liveStats.claims_count.toLocaleString() : '186',
      trend: '+10%',
      sub: 'Atomic facts',
      icon: FileText,
      link: '/history',
      sparkline: liveStats?.sparklines?.claims || [25, 40, 50, 45, 65, 60, 70, 65, 85, 80, 90, 85],
    },
    {
      title: 'Evidence Sources',
      value: liveStats ? liveStats.evidence_sources_count.toLocaleString() : '523',
      trend: '+5%',
      sub: 'Verified vaults',
      icon: BookOpen,
      link: '/knowledge-base',
      sparkline: liveStats?.sparklines?.evidence || [40, 50, 45, 60, 55, 70, 65, 75, 70, 85, 80, 90],
    },
    {
      title: 'Conversations',
      value: liveStats ? liveStats.conversations_count.toLocaleString() : '18',
      trend: '+20%',
      sub: 'Tri-model chats',
      icon: MessageSquare,
      link: '/chat',
      sparkline: liveStats?.sparklines?.conversations || [20, 30, 45, 40, 60, 50, 75, 65, 80, 75, 95, 90],
    },
  ];

  const quickActionItems = [
    {
      id: 'verify',
      title: 'Paste & Verify',
      badge: 'Ground-Truth Pipeline',
      icon: ShieldCheck,
      tagline: 'Deconstruct claims & query evidence',
      description: 'Break down complex paragraphs into atomic propositions and audit each claim against peer-reviewed registries and vaults.',
      path: '/verify',
      ctaText: 'Launch Verification Engine',
      features: [
        'Atomic proposition deconstruction with calibrated confidence scoring',
        'Deep semantic retrieval across private document vaults and web corpus',
        'Real-time contradiction and hallucination risk probability scoring'
      ],
      metricLabel: 'Calibration Accuracy',
      metricValue: '98.4%',
      glowColor: isDark ? '80 100 60' : '128 0 32',
      colors: isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#800020', '#D8AE9B', '#FBF1E3'],
    },
    {
      id: 'chat',
      title: 'Multi-Model Chat',
      badge: 'Parallel Tri-Model',
      icon: MessageSquare,
      tagline: 'Compare 3 LLMs side by side',
      description: 'Dispatch prompts simultaneously across GPT-4o, Claude 3.5, and Gemini 1.5 to compare conflicting claims without model bias.',
      path: '/chat',
      ctaText: 'Open Multi-Model Session',
      features: [
        'Simultaneous prompt dispatch to independent frontier intelligence models',
        'Direct claim contradiction extraction across multiple disparate answers',
        'One-click VerifAI multi-model cross-examination and fact-checking'
      ],
      metricLabel: 'Active Dispatch',
      metricValue: '3 Models Live',
      glowColor: isDark ? '80 100 60' : '128 0 32',
      colors: isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#800020', '#D8AE9B', '#FBF1E3'],
    },
    {
      id: 'leaderboard',
      title: 'Model Leaderboard',
      badge: 'Empirical Benchmark',
      icon: Trophy,
      tagline: 'Observed accuracy & hallucination',
      description: 'Benchmark empirical factual accuracy rankings, hallucination resistance rates, and citation calibration metrics across models.',
      path: '/leaderboard',
      ctaText: 'View Leaderboard Matrix',
      features: [
        'Category-by-category factual accuracy rankings from multi-run tests',
        'Empirical contradiction detection rate across benchmark datasets',
        'Real-world inference latency percentiles and reliability tracking'
      ],
      metricLabel: 'Top Performer',
      metricValue: 'Claude 3.5 (96%)',
      glowColor: isDark ? '80 100 60' : '128 0 32',
      colors: isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#800020', '#D8AE9B', '#FBF1E3'],
    },
    {
      id: 'kb',
      title: 'Knowledge Base',
      badge: 'Private Vault',
      icon: BookOpen,
      tagline: 'Institutional document vault',
      description: 'Ingest enterprise research publications, regulatory PDF guidelines, and corporate technical specifications into vaults.',
      path: '/knowledge-base',
      ctaText: 'Manage Vault Documents',
      features: [
        'Automated document vector chunking and high-density semantic indexing',
        'Zero-retention guarantee: embeddings never train external AI models',
        'Cryptographic audit ledger hashing for regulatory compliance records'
      ],
      metricLabel: 'Vault Documents',
      metricValue: '523 Sources',
      glowColor: isDark ? '80 100 60' : '128 0 32',
      colors: isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#800020', '#D8AE9B', '#FBF1E3'],
    },
  ];

  const activeLeaderboard = liveLeaderboard.length > 0 ? liveLeaderboard : initialLeaderboard;
  const displayedLeaderboard = leaderboardFilter === 'top3' 
    ? activeLeaderboard.slice(0, 3) 
    : activeLeaderboard.slice(0, 5);

  return (
    <div className="space-y-8 pb-12 transition-colors duration-500 max-w-full">
      
      {/* 1. Hero / Welcome Card */}
      <section 
        className={`rounded-[2.5rem] p-6 sm:p-8 md:p-10 border transition-all duration-300 relative overflow-hidden ${
          isDark 
            ? 'bg-[#0B1216] border-[#1C2C30] shadow-2xl shadow-black/50' 
            : 'lt-section-card border-[#E5D3C0] shadow-[0_12px_40px_-15px_rgba(128,0,32,0.08)] bg-[#FFFDF9]'
        }`}
        style={{
          backgroundImage: `url(${isDark ? heroCardDarkBg : heroCardBg})`,
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
            <div className="inline-flex items-center gap-2">
              <span className={`px-3.5 py-1 rounded-full text-xs font-extrabold tracking-wide uppercase flex items-center gap-2 ${
                isDark 
                  ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/30 shadow-[0_0_12px_rgba(182,255,46,0.2)]' 
                  : 'bg-[#FBF1E3]/90 backdrop-blur-xs text-[#800020] border border-[#E9D6C4]'
              }`}>
                <span className={`w-2 h-2 rounded-full animate-pulse ${
                  isDark ? 'bg-[#B6FF2E] shadow-[0_0_6px_#B6FF2E]' : 'bg-[#800020]'
                }`} />
                <span className="font-eternity tracking-wider">VerifAI Intelligence Engine · Live Ground-Truth</span>
              </span>
            </div>

            <h1 className={`text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight leading-tight transition-colors font-palatino ${
              isDark ? 'text-white' : 'text-[#2E0A12]'
            }`}>
              Welcome back, <span className={`font-beloved italic ${isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'}`}>{userName}</span>.
            </h1>

            <p className={`text-sm md:text-base leading-relaxed max-w-xl font-palatino ${
              isDark ? 'text-slate-300' : 'text-[#6C3B45]'
            }`}>
              Audit complex claims across private repositories and peer-reviewed vaults. Benchmark frontier models and eradicate hallucinations with authoritative citations.
            </p>

            {/* Quick Action Navigation Buttons */}
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <BorderGlowButton
                size="md"
                variant="primary"
                onClick={() => navigate('/verify')}
                theme={theme}
                className="transform transition-transform active:scale-95 hover:scale-[1.02]"
              >
                <ShieldCheck size={18} strokeWidth={2.4} />
                <span>Start Verification</span>
                <ArrowRight size={14} />
              </BorderGlowButton>

              <BorderGlowButton
                size="md"
                variant="secondary"
                onClick={() => navigate('/leaderboard')}
                theme={theme}
                className="transform transition-transform active:scale-95 hover:scale-[1.02]"
              >
                <Trophy size={17} />
                <span>Model Leaderboard</span>
              </BorderGlowButton>

              <button
                onClick={() => navigate('/chat')}
                className={`px-4 py-2.5 rounded-2xl text-xs sm:text-sm font-bold transition-all duration-200 transform active:scale-95 hover:scale-[1.02] border flex items-center gap-2 cursor-pointer ${
                  isDark
                    ? 'bg-[#14161C] text-slate-300 hover:text-white border-[#2E3340] hover:border-[#B6FF2E]/40 hover:shadow-[0_0_15px_rgba(182,255,46,0.15)]'
                    : 'bg-[#FBF1E3]/90 backdrop-blur-xs text-[#6C3B45] hover:text-[#2E0A12] border-[#E9D6C4] hover:bg-[#F2E6D6] hover:shadow-xs'
                }`}
              >
                <MessageSquare size={16} className={isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'} />
                <span>Multi-Model Chat</span>
              </button>
            </div>
          </div>

          {/* Right Trust Engine Stat Card */}
          <div className="lg:col-span-4 hidden lg:flex justify-end items-center relative z-10">
            <div className="animate-float-gentle">
              <div className={`w-64 p-5 rounded-2xl border transition-all duration-300 shadow-xl ${
                isDark 
                  ? 'bg-[#14161C]/90 backdrop-blur-md border-[#2E3340] text-white shadow-black/50' 
                  : 'bg-gradient-to-br from-[#750A20]/95 to-[#4E0013]/95 backdrop-blur-md border-white/20 text-[#FFF9F2] shadow-[0_16px_36px_-10px_rgba(78,0,19,0.45)]'
              }`}>
                {/* Header: Title + Pulsing Beacon Dot */}
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-[10px] font-extrabold uppercase tracking-widest font-eternity ${
                    isDark ? 'text-[#B6FF2E]' : 'text-[#E5C4B5]'
                  }`}>
                    TRUST ENGINE
                  </span>
                  <span className={`w-2 h-2 rounded-full animate-pulse ${
                    isDark 
                      ? 'bg-[#B6FF2E] shadow-[0_0_8px_#B6FF2E]' 
                      : 'bg-rose-400 shadow-[0_0_8px_#F43F5E]'
                  }`} />
                </div>

                {/* Score & Confidence Badge */}
                <div className="mb-2">
                  <div className="flex items-center gap-2.5">
                    <p className={`text-3xl font-black font-mono tabular-nums leading-none tracking-tight ${
                      isDark ? 'text-[#B6FF2E]' : 'text-white'
                    }`}>
                      98.4%
                    </p>
                    <span className={`text-[9px] sm:text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full inline-flex items-center gap-1 ${
                      isDark 
                        ? 'bg-[#B6FF2E]/20 text-[#B6FF2E] border border-[#B6FF2E]/35' 
                        : 'bg-white/15 text-white border border-white/25 backdrop-blur-xs'
                    }`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                      <span>HIGH CONFIDENCE</span>
                    </span>
                  </div>
                  <p className={`text-xs font-sans font-medium mt-1.5 leading-snug ${
                    isDark ? 'text-slate-300' : 'text-[#F5E6D8]/90'
                  }`}>
                    Average Evidence Calibration
                  </p>
                </div>

                {/* Metrics Breakdown with Icons */}
                <div className={`text-xs pt-2.5 mt-2.5 border-t space-y-1.5 font-medium font-palatino ${
                  isDark ? 'border-[#2E3340] text-slate-400' : 'border-white/15 text-[#F5E6D8]/85'
                }`}>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-1.5 opacity-85">
                      <Trophy size={12} className={isDark ? 'text-[#B6FF2E]' : 'text-[#E5C4B5]'} />
                      <span>Consensus</span>
                    </span>
                    <span className={isDark ? 'text-[#B6FF2E] font-bold' : 'text-white font-bold'}>Strong</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-1.5 opacity-85">
                      <Cpu size={12} className={isDark ? 'text-[#B6FF2E]' : 'text-[#E5C4B5]'} />
                      <span>Pipeline</span>
                    </span>
                    <span className={isDark ? 'text-[#B6FF2E] font-bold' : 'text-white font-bold'}>Tri-Model Audited</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-1.5 opacity-85">
                      <Clock size={12} className={isDark ? 'text-slate-400' : 'text-[#E5C4B5]'} />
                      <span>Last updated</span>
                    </span>
                    <span className={isDark ? 'text-slate-300' : 'text-white/90'}>2 min ago</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Four Metric Stats Grid */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
        {statCards.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div
              key={idx}
              onClick={() => navigate(stat.link)}
              className={`p-6 border transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] cursor-pointer group flex flex-col justify-between relative overflow-hidden ${
                isDark
                  ? 'rounded-[2rem] bg-[#1E2129] border-[#2E3340] hover:border-[#B6FF2E]/40 hover:-translate-y-1 hover:shadow-[0_12px_28px_rgba(0,0,0,0.4),0_0_20px_rgba(182,255,46,0.15)]'
                  : 'lt-kpi-card lt-card-entrance rounded-[2rem]'
              }`}
            >
              {/* Subtle ambient warm aura */}
              {!isDark && (
                <div className="absolute -top-12 -right-12 w-32 h-32 rounded-full blur-2xl pointer-events-none bg-[#F3E6D5]/60 transition-opacity group-hover:bg-[#EAD7C0]/80" />
              )}

              <div className="flex items-center justify-between mb-4 relative z-10">
                <div className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:scale-105 ${
                  isDark
                    ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/25 shadow-[0_0_12px_rgba(182,255,46,0.15)] group-hover:border-[#B6FF2E]/50'
                    : 'bg-[#FBF1E3] text-[#800020] border border-[#E5D3C0] group-hover:border-[#800020]/40 group-hover:bg-[#F5E6D3]'
                }`}>
                  <Icon size={20} strokeWidth={2.2} />
                </div>

                <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:scale-105 ${
                  isDark
                    ? 'bg-[#B6FF2E]/15 text-[#B6FF2E] border border-[#B6FF2E]/30'
                    : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
                }`}>
                  <TrendingUp size={12} strokeWidth={2.5} />
                  <span>{stat.trend}</span>
                </span>
              </div>

              <div className="relative z-10">
                <p className={`text-xs font-extrabold uppercase tracking-wider mb-2 font-palatino ${
                  isDark ? 'text-slate-400' : 'text-[#6C3B45]'
                }`}>
                  {stat.title}
                </p>

                <div className="flex items-end justify-between">
                  <div>
                    <h4 className={`text-3xl md:text-4xl font-black font-mono tabular-nums leading-none ${
                      isDark ? 'text-white group-hover:text-[#B6FF2E]' : 'text-[#1A060C] group-hover:text-[#800020]'
                    } transition-colors duration-200`}>
                      {stat.value}
                    </h4>
                  </div>

                  <div className="flex flex-col items-end gap-1.5">
                    {/* Mini Sparkline / Histogram Bars matching the reference */}
                    <div className="flex items-end gap-[3px] h-6 px-0.5">
                      {stat.sparkline.map((h: number, sIdx: number) => (
                        <span
                          key={sIdx}
                          className={`w-[3px] rounded-full transition-all duration-300 ${
                            isDark 
                              ? 'bg-[#B6FF2E]/30 group-hover:bg-[#B6FF2E]/70' 
                              : 'bg-[#800020]/25 group-hover:bg-[#800020]/65'
                          }`}
                          style={{ height: `${h}%` }}
                        />
                      ))}
                    </div>
                    <span className={`text-xs font-semibold ${isDark ? 'text-slate-400' : 'text-[#8A6A72]'}`}>
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
      <section className={`p-6 sm:p-8 border transition-all relative overflow-hidden ${
        isDark
          ? 'rounded-[2.5rem] bg-[#1E2129] border-[#2E3340] shadow-xl'
          : 'lt-section-card rounded-[2.5rem]'
      }`}>
        {/* Ambient background glow orbs */}
        {!isDark && (
          <>
            <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full blur-3xl pointer-events-none bg-[#F3E6D5]/70" />
            <div className="absolute -bottom-24 -left-24 w-72 h-72 rounded-full blur-3xl pointer-events-none bg-[#EAD7C0]/40" />
          </>
        )}
        {isDark && (
          <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full blur-3xl pointer-events-none bg-[#B6FF2E]/05" />
        )}

        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E9D6C4] dark:border-[#2E3340]">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                isDark ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/30' : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
              }`}>
                <Trophy size={16} />
              </div>
              <h3 className={`font-extrabold text-lg sm:text-xl tracking-tight font-eternity ${
                isDark ? 'text-white' : 'text-[#2E0A12]'
              }`}>
                Frontier Model Performance Leaderboard
              </h3>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider font-adore ${
                isDark ? 'bg-[#B6FF2E]/15 text-[#B6FF2E]' : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
              }`}>
                Live Benchmarks
              </span>
            </div>
            <p className={`text-sm font-medium font-palatino ${isDark ? 'text-slate-400' : 'text-[#6C3B45]'}`}>
              Empirical factual verification scores, hallucination resistance, and citation accuracy calibrated from multi-run tests.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className={`p-1 rounded-xl border flex items-center gap-1 ${
              isDark ? 'bg-[#14161C] border-[#2E3340]' : 'bg-[#FBF1E3] border-[#E9D6C4]'
            }`}>
              <button
                onClick={() => setLeaderboardFilter('top3')}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-bold transition-all cursor-pointer ${
                  leaderboardFilter === 'top3'
                    ? isDark ? 'bg-[#B6FF2E] text-[#12141A]' : 'bg-[#800020] text-[#FFF9F2] shadow-xs'
                    : isDark ? 'text-slate-400 hover:text-white' : 'text-[#6C3B45] hover:text-[#2E0A12]'
                }`}
              >
                Top 3
              </button>
              <button
                onClick={() => setLeaderboardFilter('all')}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-bold transition-all cursor-pointer ${
                  leaderboardFilter === 'all'
                    ? isDark ? 'bg-[#B6FF2E] text-[#12141A]' : 'bg-[#800020] text-[#FFF9F2] shadow-xs'
                    : isDark ? 'text-slate-400 hover:text-white' : 'text-[#6C3B45] hover:text-[#2E0A12]'
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
                  : 'bg-[#800020] text-[#FFF9F2] hover:bg-[#66001A] shadow-[#800020]/20'
              }`}
            >
              <span>Full Benchmark Matrix</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </div>

        {/* Model Ranking Cards / Responsive Grid */}
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
                    : 'bg-gradient-to-br from-[#FFFDF9] via-[#FAF3EA] to-[#F5E6D3]/60 border-[#E5D3C0] hover:border-[#800020]/40 hover:shadow-xl hover:shadow-[#800020]/10'
                }`}
              >
                {/* Header: Rank + Model Title + Score */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono font-black text-xs transition-transform duration-300 group-hover:scale-105 ${
                        isRank1 
                          ? isDark ? 'bg-[#B6FF2E] text-[#12141A]' : 'bg-[#800020] text-[#FFF9F2]'
                          : isRank2
                          ? isDark ? 'bg-amber-400/20 text-amber-300 border border-amber-400/40' : 'bg-[#E5D3C0] text-[#6C3B45]'
                          : isDark ? 'bg-slate-800 text-slate-300' : 'bg-[#EFE0D1] text-[#6C3B45]'
                      }`}>
                        #{item.rank}
                      </span>
                      <span className={`text-xs font-extrabold uppercase tracking-wider ${
                        isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                      }`}>
                        {item.provider}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className={`text-xl font-black font-mono tabular-nums leading-none ${
                        isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'
                      }`}>
                        {item.overallScore}%
                      </span>
                      <p className={`text-[10px] font-bold uppercase tracking-wider ${
                        isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                      }`}>
                        Score
                      </p>
                    </div>
                  </div>

                  <h4 className={`text-base font-extrabold tracking-tight mb-2 transition-colors ${
                    isDark ? 'text-white group-hover:text-[#B6FF2E]' : 'text-[#2E0A12] group-hover:text-[#800020]'
                  }`}>
                    {item.model}
                  </h4>

                  {/* Key Metrics Mini Bars: Factual Support, Hallucination Resistance, Citation Accuracy */}
                  <div className="space-y-2.5 pt-1 pb-3">
                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1.5">
                        <span className={isDark ? 'text-slate-400' : 'text-[#8A6070]'}>Factual Support</span>
                        <span className={`font-mono ${isDark ? 'text-slate-200' : 'text-[#1E0A10]'}`}>
                          {item.categories.factualSupport}%
                        </span>
                      </div>
                      <div className={`h-2 w-full ${
                        isDark ? 'rounded-full overflow-hidden bg-[#2E3340]' : 'lt-progress-track bg-[#EFE0D1]'
                      }`}>
                        <div 
                          className={isDark
                            ? 'h-full rounded-full bg-[#B6FF2E] transition-all duration-1000 ease-out'
                            : 'h-full rounded-full bg-gradient-to-r from-[#990026] to-[#800020] transition-all duration-1000 ease-out'}
                          style={{ width: `${item.categories.factualSupport}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1.5">
                        <span className={isDark ? 'text-slate-400' : 'text-[#8A6070]'}>Hallucination Resistance</span>
                        <span className={`font-mono ${isDark ? 'text-slate-200' : 'text-[#1E0A10]'}`}>
                          {item.categories.contradictionDetection}%
                        </span>
                      </div>
                      <div className={`h-2 w-full ${
                        isDark ? 'rounded-full overflow-hidden bg-[#2E3340]' : 'lt-progress-track bg-[#EFE0D1]'
                      }`}>
                        <div 
                          className={isDark
                            ? 'h-full rounded-full bg-[#A3E823] transition-all duration-1000 ease-out'
                            : 'h-full rounded-full bg-gradient-to-r from-[#990026] to-[#800020] transition-all duration-1000 ease-out'}
                          style={{ width: `${item.categories.contradictionDetection}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1.5">
                        <span className={isDark ? 'text-slate-400' : 'text-[#8A6070]'}>Citation Accuracy</span>
                        <span className={`font-mono ${isDark ? 'text-slate-200' : 'text-[#1E0A10]'}`}>
                          {item.categories.evidenceSupport}%
                        </span>
                      </div>
                      <div className={`h-2 w-full ${
                        isDark ? 'rounded-full overflow-hidden bg-[#2E3340]' : 'lt-progress-track bg-[#EFE0D1]'
                      }`}>
                        <div 
                          className={isDark
                            ? 'h-full rounded-full bg-[#80C020] transition-all duration-1000 ease-out'
                            : 'h-full rounded-full bg-gradient-to-r from-[#990026] to-[#800020] transition-all duration-1000 ease-out'}
                          style={{ width: `${item.categories.evidenceSupport}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Footer details with circular chevron icon */}
                <div className={`pt-3 border-t flex items-center justify-between text-xs ${
                  isDark ? 'border-[#2E3340] text-slate-400' : 'border-[#E9D6C4] text-[#8A6A72]'
                }`}>
                  <span>{item.evaluationsCount} Evals Tested</span>
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${
                    isDark 
                      ? 'bg-[#1E2129] text-[#B6FF2E] border border-[#2E3340] group-hover:border-[#B6FF2E]/40' 
                      : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4] group-hover:bg-[#800020] group-hover:text-white'
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
            <h3 className={`font-extrabold text-base md:text-lg tracking-tight font-eternity ${
              isDark ? 'text-white' : 'text-[#2E0A12]'
            }`}>
              Quick Actions & Evaluation Engines
            </h3>
            <p className={`text-sm font-palatino ${isDark ? 'text-slate-400' : 'text-[#6C3B45]'}`}>
              Select any pipeline below to scope into capabilities and launch immediate execution.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className={`w-2 h-2 rounded-full ${isDark ? 'bg-[#B6FF2E]' : 'bg-[#800020]'}`} />
            <span className={`font-sans font-semibold text-xs tracking-wide ${isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'}`}>
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
                backgroundColor={isDark ? '#1E2129' : '#FFFDF9'}
                colors={item.colors}
                onClick={() => setScopedActionId(item.id)}
                className={`transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] cursor-pointer h-full ${
                  isScoped 
                    ? isDark 
                      ? 'ring-2 ring-[#B6FF2E] shadow-[0_0_25px_rgba(182,255,46,0.18)] -translate-y-1' 
                      : 'ring-2 ring-[#800020] shadow-lg shadow-[#800020]/10 -translate-y-1'
                    : 'opacity-95 hover:opacity-100 hover:-translate-y-0.5'
                }`}
              >
                <div className={`p-5 flex flex-col justify-between h-full rounded-[24px] transition-all relative overflow-hidden ${
                  isScoped 
                    ? isDark 
                      ? 'bg-[#1E2129]' 
                      : 'bg-gradient-to-br from-[#FBF1E3] to-[#F5E6D3] border border-[#800020]/25' 
                    : isDark 
                      ? 'bg-[#1E2129]' 
                      : 'bg-gradient-to-br from-[#FFFDF9] via-[#FAF3EA] to-[#F3E6D5]/60 border border-[#E5D3C0] hover:border-[#800020]/35'
                }`}>
                  {/* Subtle ambient warm aura */}
                  {!isDark && (
                    <div className={`absolute -top-10 -right-10 w-28 h-28 rounded-full blur-2xl pointer-events-none transition-opacity ${
                      isScoped ? 'bg-[#EAD7C0]/80' : 'bg-[#F3E6D5]/50'
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
                          ? 'bg-[#800020] text-[#FFF9F2] shadow-sm'
                          : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
                      }`}>
                        <Icon size={19} strokeWidth={2.4} />
                      </div>

                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase ${
                        isScoped
                          ? isDark 
                            ? 'bg-[#B6FF2E] text-[#12141A] font-black shadow-[0_0_10px_rgba(182,255,46,0.3)]' 
                            : 'bg-[#800020] text-[#FFF9F2] font-black shadow-xs'
                          : isDark 
                            ? 'bg-[#14161C] text-slate-400 border border-[#2E3340]' 
                            : 'bg-[#FBF1E3] text-[#6C3B45] border border-[#E9D6C4]'
                      }`}>
                        {isScoped ? 'Active Scope' : item.badge}
                      </span>
                    </div>

                    <h4 className={`font-black text-base tracking-tight mb-1 transition-colors font-palatino ${
                      isScoped 
                        ? isDark ? 'text-[#B6FF2E]' : 'text-[#800020]' 
                        : isDark ? 'text-white' : 'text-[#2E0A12]'
                    }`}>
                      {item.title}
                    </h4>

                    <p className={`text-xs font-medium mb-2 font-sans tracking-normal transition-colors ${
                      isDark ? 'text-slate-400' : isScoped ? 'text-[#800020]/90 font-semibold' : 'text-[#8A6A72]'
                    }`}>
                      {item.tagline}
                    </p>

                    <div className="min-h-[64px] mb-4">
                      <p className={`text-xs sm:text-sm leading-relaxed transition-colors font-palatino ${
                        isDark ? 'text-slate-300' : 'text-[#6C3B45]'
                      }`}>
                        {item.description}
                      </p>
                    </div>

                    {/* Metric & Features - Leveled across all 4 cards */}
                    <div className={`pt-3.5 border-t space-y-3 flex-1 flex flex-col justify-between ${
                      isDark ? 'border-[#2E3340]' : 'border-[#E9D6C4]'
                    }`}>
                      <div className="flex items-center justify-between text-xs font-mono font-bold font-palatino">
                        <span className={isDark ? 'text-slate-400' : 'text-[#8A6A72]'}>
                          {item.metricLabel}
                        </span>
                        <span className={`px-2 py-0.5 rounded-md text-xs font-mono font-bold ${
                          isDark 
                            ? 'text-[#B6FF2E] bg-[#B6FF2E]/10' 
                            : isScoped 
                            ? 'text-[#800020] bg-[#800020]/10 font-black' 
                            : 'text-[#800020] bg-[#FBF1E3]'
                        }`}>
                          {item.metricValue}
                        </span>
                      </div>

                      <div className="space-y-2 text-xs font-palatino flex-1">
                        {item.features.map((feat, fIdx) => (
                          <div key={fIdx} className="flex items-start gap-1.5 text-slate-600 dark:text-slate-300 min-h-[32px]">
                            <Check size={13} className={`shrink-0 mt-0.5 ${
                              isDark ? 'text-[#B6FF2E]' : isScoped ? 'text-[#800020]' : 'text-[#A3485E]'
                            }`} />
                            <span className="leading-snug text-[11px] sm:text-xs">{feat}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Card Footer Button */}
                  <div className={`mt-4 pt-3 border-t relative z-10 ${
                    isDark ? 'border-[#2E3340]' : 'border-[#E9D6C4]'
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
                            : 'bg-[#800020] text-[#FFF9F2] hover:bg-[#66001A] shadow-[#800020]/25'
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
                            : 'bg-[#FBF1E3] text-[#6C3B45] hover:text-[#2E0A12] hover:bg-[#F2E6D6] border-[#E9D6C4]'
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
        <section className={`lg:col-span-6 p-6 sm:p-7 border space-y-4 relative overflow-hidden ${
          isDark
            ? 'rounded-[2.5rem] bg-[#1E2129] border-[#2E3340]'
            : 'lt-section-card rounded-[2.5rem]'
        }`}>
          {/* Ambient background glow */}
          {!isDark && (
            <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full blur-3xl pointer-events-none bg-[#F3E6D5]/80" />
          )}

          <div className="flex items-center justify-between relative z-10">
            <div>
              <h3 className={`font-extrabold text-base md:text-lg tracking-tight font-eternity ${
                isDark ? 'text-white' : 'text-[#2E0A12]'
              }`}>
                Recent Verifications
              </h3>
              <p className={`text-sm font-medium font-palatino ${isDark ? 'text-slate-400' : 'text-[#6C3B45]'}`}>
                Last executed truth propositions & evidence audits
              </p>
            </div>

            <button
              onClick={() => navigate('/history')}
              className={`text-sm font-bold transition-colors cursor-pointer font-adore ${
                isDark ? 'text-[#B6FF2E] hover:text-[#A3E823]' : 'text-[#800020] hover:text-[#66001A]'
              }`}
            >
              View All History
            </button>
          </div>

          <div className={`divide-y relative z-10 ${isDark ? 'divide-[#2E3340]' : 'divide-[#E9D6C4]'}`}>
            {verifications.slice(0, 4).map((rec) => (
              <div
                key={rec.id}
                onClick={() => navigate(`/verification/${rec.id}`)}
                className={`py-3.5 first:pt-0 last:pb-0 flex items-center justify-between gap-3 group cursor-pointer -mx-3 px-3 rounded-2xl transition-all duration-400 ease-[cubic-bezier(0.22,1,0.36,1)] hover:translate-x-1 ${
                  isDark ? 'hover:bg-[#14161C]' : 'hover:bg-[#FBF1E3]/80'
                }`}
              >
                <div className="min-w-0 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider font-mono inline-flex items-center gap-1 ${
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
                    <span className={`text-xs font-medium ${isDark ? 'text-slate-500' : 'text-[#8A6A72]'}`}>·</span>
                    <span className={`text-xs font-medium font-mono ${isDark ? 'text-slate-400' : 'text-[#8A6A72]'}`}>{rec.timestamp}</span>
                  </div>

                  <h4 className={`text-sm font-bold truncate transition-colors font-palatino ${
                    isDark ? 'text-slate-200 group-hover:text-[#B6FF2E]' : 'text-[#2E0A12] group-hover:text-[#800020]'
                  }`}>
                    {rec.query}
                  </h4>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-sm font-semibold tabular-nums hidden sm:inline font-palatino ${
                    isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                  }`}>
                    {rec.claimsCount} claims · {rec.evidenceCount} sources
                  </span>
                  <ChevronRight size={16} className={`transition-transform duration-200 group-hover:translate-x-1 ${
                    isDark ? 'text-slate-500 group-hover:text-[#B6FF2E]' : 'text-[#8A6A72] group-hover:text-[#800020]'
                  }`} />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Right: Verification Activity Timeline Curve */}
        <section className={`lg:col-span-6 p-6 sm:p-7 border space-y-4 relative overflow-hidden ${
          isDark
            ? 'rounded-[2.5rem] bg-[#1E2129] border-[#2E3340]'
            : 'lt-section-card rounded-[2.5rem]'
        }`}>
          {/* Ambient background glow */}
          {!isDark && (
            <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full blur-3xl pointer-events-none bg-[#F3E6D5]/80" />
          )}

          <div className="flex items-center justify-between relative z-10">
            <div>
              <h3 className={`font-extrabold text-base md:text-lg tracking-tight font-eternity ${
                isDark ? 'text-white' : 'text-[#2E0A12]'
              }`}>
                Activity Timeline
              </h3>
              <p className={`text-sm font-medium font-palatino ${isDark ? 'text-slate-400' : 'text-[#6C3B45]'}`}>
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
                        : 'bg-[#800020] text-[#FFF9F2] shadow-xs'
                      : isDark
                        ? 'bg-[#14161C] text-slate-400 hover:text-white'
                        : 'bg-[#FBF1E3] text-[#6C3B45] hover:text-[#2E0A12] border border-[#E9D6C4]'
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
                      : 'bg-[#800020] text-[#FFF9F2]'
                    : isDark
                      ? 'text-slate-500 hover:text-slate-300'
                      : 'bg-[#FBF1E3] text-[#6C3B45] hover:text-[#2E0A12] border border-[#E9D6C4]'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Chart View */}
          <div className="h-64 w-full pt-2 relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop 
                      offset="5%" 
                      stopColor={isDark ? '#B6FF2E' : '#800020'} 
                      stopOpacity={isDark ? 0.35 : 0.28} 
                    />
                    <stop 
                      offset="95%" 
                      stopColor={isDark ? '#B6FF2E' : '#D8AE9B'} 
                      stopOpacity={0.0} 
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  vertical={false} 
                  stroke={isDark ? '#2E3340' : '#EAD7C0'} 
                />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: isDark ? '#94A3B8' : '#8A6A72', fontSize: 11 }} 
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: isDark ? '#94A3B8' : '#8A6A72', fontSize: 11 }} 
                />
                <Tooltip 
                  animationDuration={500}
                  animationEasing="ease-out"
                  isAnimationActive={true}
                  cursor={{ 
                    stroke: isDark ? '#B6FF2E' : '#800020', 
                    strokeWidth: 1.5, 
                    strokeDasharray: '4 4', 
                    strokeOpacity: 0.6 
                  }}
                  contentStyle={{ 
                    borderRadius: '16px', 
                    background: isDark ? '#14161C' : '#FFFDF9', 
                    color: isDark ? '#FFFFFF' : '#2E0A12', 
                    border: isDark ? '1px solid #2E3340' : '1px solid #E5D3C0',
                    boxShadow: '0 10px 25px rgba(128,0,32,0.12)',
                    fontSize: '12px',
                    transition: 'all 0.35s cubic-bezier(0.22, 1, 0.36, 1)'
                  }} 
                />
                <Area 
                  type="monotone" 
                  dataKey={chartMetric} 
                  stroke={isDark ? '#B6FF2E' : '#800020'} 
                  strokeWidth={3} 
                  fill="url(#areaGradient)" 
                  dot={{ r: 4, fill: isDark ? '#14161C' : '#FFFDF9', stroke: isDark ? '#B6FF2E' : '#800020', strokeWidth: 2 }}
                  activeDot={{ 
                    r: 6, 
                    fill: isDark ? '#B6FF2E' : '#800020', 
                    stroke: isDark ? '#14161C' : '#FFFDF9', 
                    strokeWidth: 2.5 
                  }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

      </div>
    </div>
  );
};

export default DashboardPage;
