import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, ArrowRight, BarChart3, BookOpen, CalendarDays, ChevronRight,
  CircleHelp, Clock3, FileCheck2, Files, Link2, MessageSquare, ShieldCheck,
  Sparkles, Trophy } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { BackendDashboardStats } from '../api/dashboard';
import { modelsApi, type PublicLeaderboardSnapshot } from '../api/models';
import type { ChartPoint, VerificationRecord, VerificationStatus } from '../types';
import './DashboardLightPage.css';

interface DashboardLightPageProps {
  userName: string;
  verifications: VerificationRecord[];
  stats: BackendDashboardStats | null;
  dataError: string | null;
}

type WindowSize = '7D' | '30D';
type Metric = 'verifications' | 'claims' | 'evidence';

const pointsFor = (items: ChartPoint[]) => items.map(point => ({
  name: (point as ChartPoint & { day?: string }).day || point.name,
  verifications: point.verifications || 0,
  claims: point.claims || 0,
  evidence: point.evidence || 0,
}));

const formatCount = (value: number) => value.toLocaleString('en-US');

const timeLabel = (timestamp: string) => {
  const date = new Date(timestamp);
  return Number.isFinite(date.getTime())
    ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    : timestamp;
};

const STATUS_COPY: Record<VerificationStatus, string> = {
  SUPPORTED: 'Supported',
  CONTRADICTED: 'Contradicted',
  UNKNOWN: 'Unknown',
  UNAVAILABLE: 'Unavailable',
  FAILED: 'Failed',
};

const ICON_SIZE = 20;

export const DashboardLightPage: React.FC<DashboardLightPageProps> = ({
  userName, verifications, stats, dataError,
}) => {
  const navigate = useNavigate();
  const [timeframe, setTimeframe] = useState<WindowSize>('7D');
  const [metric, setMetric] = useState<Metric>('verifications');
  const [publicBenchmarks, setPublicBenchmarks] = useState<PublicLeaderboardSnapshot | null>(null);
  const [benchmarkError, setBenchmarkError] = useState(false);

  useEffect(() => {
    let active = true;
    modelsApi.getPublicLeaderboard().then(data => {
      if (active) setPublicBenchmarks(data);
    }).catch(() => {
      if (active) setBenchmarkError(true);
    });
    return () => { active = false; };
  }, []);

  const data = useMemo(() =>
    pointsFor(timeframe === '7D' ? stats?.weekly_chart_data ?? [] : stats?.monthly_chart_data ?? []),
    [timeframe, stats]);
  const ticks = useMemo(() => {
    if (!data.length) return [];
    const every = Math.max(1, Math.ceil((data.length - 1) / 5));
    return data.filter((_, index) => index % every === 0 || index === data.length - 1)
      .map(item => item.name);
  }, [data]);
  const hasActivity = data.some(point => point[metric] > 0);

  const overview = [
    { label: 'Verifications', value: stats?.verifications_count ?? verifications.length,
      description: 'Recorded reviews', icon: ShieldCheck, destination: '/history' },
    { label: 'Claims analyzed', value: stats?.claims_count ?? 0,
      description: 'Individual propositions', icon: FileCheck2, destination: '/history' },
    { label: 'Evidence sources', value: stats?.evidence_sources_count ?? 0,
      description: 'Referenced sources', icon: Files, destination: '/knowledge-base' },
    { label: 'Conversations', value: stats?.conversations_count ?? 0,
      description: 'Multi-model sessions', icon: MessageSquare, destination: '/chat' },
  ];

  const actions = [
    { name: 'Verify a claim', description: 'Check statements against available evidence.',
      icon: ShieldCheck, path: '/verify' },
    { name: 'Compare AI models', description: 'Run one prompt through connected models.',
      icon: MessageSquare, path: '/chat' },
    { name: 'Your knowledge base', description: 'Manage documents and evidence collections.',
      icon: BookOpen, path: '/knowledge-base' },
    { name: 'Review analytics', description: 'Investigate activity and claim outcomes.',
      icon: BarChart3, path: '/reports' },
  ];

  const metrics: { key: Metric; label: string }[] = [
    { key: 'verifications', label: 'Verifications' },
    { key: 'claims', label: 'Claims' },
    { key: 'evidence', label: 'Evidence' },
  ];

  const recent = [...verifications].sort((a, b) =>
    (Date.parse(b.timestamp) || 0) - (Date.parse(a.timestamp) || 0)).slice(0, 5);

  return (
    <div className="command-dashboard" data-testid="light-dashboard">
      {dataError && <div className="command-error" role="alert">
        <CircleHelp size={16}/> Dashboard data unavailable: {dataError}. Existing records remain accessible.
      </div>}

      <section className="command-dashboard-hero" aria-labelledby="dashboard-main-title">
        <div className="command-hero-copy">
          <h1 id="dashboard-main-title">Welcome back, <span>{userName}</span>.</h1>
          <p>One place to review what you've verified, continue your research, and compare model outputs.</p>
          <div className="command-hero-actions">
            <button type="button" className="command-primary" onClick={() => navigate('/verify')}>
              <ShieldCheck size={17}/> Start a verification <ArrowRight size={16}/>
            </button>
            <button type="button" className="command-secondary" onClick={() => navigate('/chat')}>
              <MessageSquare size={17}/> Open model chat
            </button>
          </div>
        </div>
        <div className="command-hero-note" aria-label="Verification workspace information">
          <span className="command-note-icon"><Sparkles size={19}/></span>
          <div>
            <strong>Evidence comes first.</strong>
            <p>Model agreement alone isn't proof. Inspect sources and unresolved claims before relying on an answer.</p>
          </div>
        </div>
      </section>

      <section className="command-stats" aria-label="Workspace totals">
        {overview.map((item, index) => {
          const Icon = item.icon;
          return <button type="button" className="command-stat" key={item.label}
            onClick={() => navigate(item.destination)} aria-label={'View ' + item.label}>
            <div className="command-stat-top">
              <span className="command-stat-label">{item.label}</span>
              <Icon size={ICON_SIZE} strokeWidth={1.8}/>
            </div>
            <strong>{formatCount(item.value)}</strong>
            <div className="command-stat-bottom"><span>{item.description}</span>
              <ArrowRight size={15}/></div>
            <span className="command-stat-number">{String(index + 1).padStart(2,'0')}</span>
          </button>;
        })}
      </section>

      <div className="command-main-grid">
        <section className="command-panel command-activity" aria-label="Workspace activity">
          <div className="command-panel-heading">
            <div><h2>Activity overview</h2><p>Recorded usage, not projected trends</p></div>
            <div className="command-window" role="group" aria-label="Activity period">
              {(['7D', '30D'] as const).map(window => (
                <button type="button" key={window} aria-pressed={timeframe === window}
                  onClick={() => setTimeframe(window)}>{window === '7D' ? '7 days' : '30 days'}</button>
              ))}
            </div>
          </div>
          <div className="command-metric-options" role="group" aria-label="Activity metric">
            {metrics.map(item => (
              <button key={item.key} type="button" aria-pressed={metric === item.key}
                onClick={() => setMetric(item.key)}>{item.label}</button>
            ))}
          </div>
          {!hasActivity ? <div className="command-activity-empty" role="status">
            <div className="command-empty-symbol"><Activity size={21}/></div>
            <strong>No activity to chart yet</strong>
            <p>New reviews and evidence activity will appear here as you use VerifAI.</p>
            <button type="button" onClick={() => navigate('/verify')}>Verify a claim <ArrowRight size={14}/></button>
          </div> : <div className="command-area" role="img" aria-label={metric + ' over ' + timeframe}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 17, right: 12, left: 3, bottom: 6 }}>
                <defs><linearGradient id="commandActivityArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#40916C" stopOpacity={.25}/>
                  <stop offset="100%" stopColor="#74C69D" stopOpacity={0}/>
                </linearGradient></defs>
                <CartesianGrid vertical={false} strokeDasharray="3 5" stroke="#DBEBDD"/>
                <XAxis dataKey="name" ticks={ticks} interval="preserveStartEnd" minTickGap={15}
                  tickMargin={11} tickLine={false} axisLine={false}
                  tick={{ fill:'#2B4A36', fontSize:11 }}/>
                <YAxis axisLine={false} tickLine={false} allowDecimals={false} width={35}
                  tickMargin={8} tick={{ fill:'#2B4A36', fontSize:11 }}/>
                <Tooltip contentStyle={{ background:'#FFF',color:'#000',fontSize:12,border:'1px solid #B3DCC0',borderRadius:12 }}
                  cursor={{stroke:'#40916C',strokeDasharray:'4 4'}}/>
                <Area dataKey={metric} type="monotone" fill="url(#commandActivityArea)"
                  stroke="#1B4332" strokeWidth={2.6} dot={false}
                  activeDot={{r:5, stroke:'#FFF',strokeWidth:2}} isAnimationActive={false}/>
              </AreaChart>
            </ResponsiveContainer>
          </div>}
          <div className="command-panel-foot"><span><i/> {metrics.find(item => item.key === metric)?.label}</span><span>Daily records · {timeframe}</span></div>
        </section>

        <section className="command-panel command-benchmark" aria-label="Public model performance">
          <div className="command-panel-heading">
            <div><h2>Model benchmarks</h2><p>Independent performance snapshot</p></div>
            <Trophy size={20}/>
          </div>
          {publicBenchmarks?.models.length ? (
            <>
              <div className="command-benchmark-source">
                <span>LiveBench 2.0</span>
                <span>Updated {timeLabel(publicBenchmarks.source_updated_at)}</span>
              </div>
              <div className="command-benchmark-list">
                {publicBenchmarks.models.slice(0, 3).map(item => (
                  <div className="command-benchmark-row" key={item.id}>
                    <span className="command-benchmark-rank">{String(item.rank).padStart(2, '0')}</span>
                    <div className="command-benchmark-detail">
                      <strong>{item.name}</strong>
                      <span>{item.organization}</span>
                    </div>
                    <span className="command-benchmark-score">{item.overall_score.toFixed(1)}</span>
                  </div>
                ))}
              </div>
              <p className="command-benchmark-disclaimer">Task-suite scores /100, not VerifAI verification accuracy.</p>
            </>
          ) : <div className="command-benchmark-pending" role="status">
            <Trophy size={22}/>
            <strong>Your benchmark story starts with real evaluations</strong>
            <p>{benchmarkError ? 'Public benchmark data could not be loaded.' : 'Loading attributed public benchmark results…'}</p>
          </div>}
          <button className="command-panel-link" type="button" onClick={() => navigate('/leaderboard')}>
            Explore model leaderboard <ArrowRight size={16}/>
          </button>
        </section>
      </div>

      <div className="command-bottom-grid">
        <section className="command-panel command-history" aria-label="Recent verifications">
          <div className="command-panel-heading">
            <div><h2>Recent verifications</h2><p>Continue where you left off</p></div>
            <button type="button" className="command-inline-link" onClick={() => navigate('/history')}>
              View history <ArrowRight size={14}/>
            </button>
          </div>
          {recent.length ? <div className="command-history-list">
            {recent.map(item => (
              <button type="button" key={item.id} className="command-history-item"
                onClick={() => navigate('/verification/' + item.id)}>
                <span className={'command-history-icon command-status-' + item.status.toLowerCase()}>
                  <ShieldCheck size={17}/>
                </span>
                <div className="command-history-copy">
                  <strong>{item.query}</strong>
                  <span>{timeLabel(item.timestamp)} · {formatCount(item.claimsCount)} claims · {formatCount(item.evidenceCount)} sources</span>
                </div>
                <div className="command-history-end">
                  <span className={'command-status-label command-status-' + item.status.toLowerCase()}>
                    {STATUS_COPY[item.status]}
                  </span>
                  <ChevronRight size={17}/>
                </div>
              </button>
            ))}
          </div> : <div className="command-history-empty" role="status">
            <CalendarDays size={22}/>
            <strong>No verifications recorded yet</strong>
            <p>Once a check finishes, you'll be able to revisit its claims, verdicts and evidence here.</p>
          </div>}
        </section>

        <section className="command-panel command-workflows" aria-label="Workspace actions">
          <div className="command-panel-heading"><div>
            <h2>Your workflows</h2><p>Open a focused workspace</p>
          </div><Link2 size={19}/></div>
          <div className="command-action-list">
            {actions.map(action => {
              const Icon = action.icon;
              return <button type="button" key={action.name} className="command-action"
                onClick={() => navigate(action.path)}>
                <span className="command-action-icon"><Icon size={18}/></span>
                <span className="command-action-text"><strong>{action.name}</strong>
                  <small>{action.description}</small></span>
                <ArrowRight size={16}/>
              </button>;
            })}
          </div>
          <div className="command-action-note"><Clock3 size={14}/> Built from your recorded activity, not illustrative counts.</div>
        </section>
      </div>
    </div>
  );
};

export default DashboardLightPage;
