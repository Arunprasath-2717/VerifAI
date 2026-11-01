import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowDownUp, ArrowLeft, ArrowUpRight, BarChart3, CalendarDays,
  Check, ChevronRight, CircleAlert, Clock3, ExternalLink, Info,
  Medal, RefreshCw, Search, ShieldCheck, Sparkles, Trophy, X,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import {
  modelsApi, type LiveBenchSuiteKey, type PublicLeaderboardModel,
  type PublicLeaderboardSnapshot,
} from '../api/models';
import type { ModelLeaderboardEntry } from '../types';

interface ModelLeaderboardPageProps {
  theme?: 'light' | 'dark';
}

type Metric = 'overall' | LiveBenchSuiteKey;
type LeaderboardMode = 'public' | 'verifai';

const SUITES: { key: LiveBenchSuiteKey; label: string; shortLabel: string; description: string }[] = [
  { key: 'agentic', label: 'Agentic tasks', shortLabel: 'Agentic', description: 'Long-running, multi-stage applications and operational tasks' },
  { key: 'reasoning', label: 'Reasoning', shortLabel: 'Reasoning', description: 'Single-answer reasoning tasks with measurable outcomes' },
  { key: 'coding', label: 'Coding', shortLabel: 'Coding', description: 'Repository bug fixes graded by deterministic tests' },
  { key: 'browser', label: 'Browser use', shortLabel: 'Browser', description: 'Multi-step work in interactive browser applications' },
  { key: 'data_analysis', label: 'Data analysis', shortLabel: 'Data', description: 'Short data-analysis and numerical reasoning problems' },
  { key: 'research', label: 'Research', shortLabel: 'Research', description: 'Research reports evaluated against a task-specific rubric' },
  { key: 'design', label: 'Design', shortLabel: 'Design', description: 'Presentation, document, and visual layout deliverables' },
];

const scoreLabel = (value: number | null | undefined): string =>
  typeof value === 'number' && Number.isFinite(value) ? value.toFixed(1) : '—';

const scoreFor = (model: PublicLeaderboardModel, metric: Metric): number | null =>
  metric === 'overall' ? model.overall_score : model.suite_scores[metric];

const dateLabel = (date: string): string => {
  const parsed = new Date(date + 'T00:00:00Z');
  return Number.isNaN(parsed.getTime())
    ? date
    : parsed.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' });
};

const scoreBar = (score: number | null, dark: boolean) => (
  <div className={'h-1.5 rounded-full overflow-hidden w-full ' + (dark ? 'bg-[#343B47]' : 'bg-[#D8F3DC]')}>
    {score !== null && (
      <div className={'h-full rounded-full ' + (dark ? 'bg-[#B6FF2E]' : 'bg-[#40916C]')}
        style={{ width: Math.min(100, Math.max(0, score)) + '%' }} />
    )}
  </div>
);

export const ModelLeaderboardPage: React.FC<ModelLeaderboardPageProps> = ({ theme = 'light' }) => {
  const dark = theme === 'dark';
  const [mode, setMode] = useState<LeaderboardMode>('public');
  const [snapshot, setSnapshot] = useState<PublicLeaderboardSnapshot | null>(null);
  const [empirical, setEmpirical] = useState<ModelLeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [empiricalError, setEmpiricalError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [provider, setProvider] = useState('all');
  const [metric, setMetric] = useState<Metric>('overall');
  const [inspected, setInspected] = useState<PublicLeaderboardModel | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [official, local] = await Promise.allSettled([
      modelsApi.getPublicLeaderboard(),
      modelsApi.getModelLeaderboard(),
    ]);
    if (official.status === 'fulfilled') setSnapshot(official.value);
    else setError(official.reason instanceof Error ? official.reason.message : 'Unable to load the public benchmark snapshot.');
    if (local.status === 'fulfilled') {
      setEmpirical(local.value);
      setEmpiricalError(null);
    } else {
      setEmpiricalError(local.reason instanceof Error ? local.reason.message : 'Private evaluation data unavailable.');
    }
    setLoading(false);
  }, []);

  useEffect(() => { void reload(); }, [reload]);
  useEffect(() => {
    if (!inspected) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setInspected(null);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [inspected]);

  const organizations = useMemo(() => [...new Set(snapshot?.models.map(item => item.organization) || [])].sort(), [snapshot]);
  const entries = useMemo(() => {
    const q = search.toLowerCase().trim();
    return (snapshot?.models || [])
      .filter(item => (
        (provider === 'all' || item.organization === provider) &&
        (!q || (item.name + ' ' + item.organization).toLowerCase().includes(q))
      ))
      .sort((a, b) => {
        const av = scoreFor(a, metric);
        const bv = scoreFor(b, metric);
        if (av === null && bv !== null) return 1;
        if (bv === null && av !== null) return -1;
        return (bv ?? -1) - (av ?? -1) || a.rank - b.rank;
      });
  }, [snapshot, search, provider, metric]);
  const topModels = useMemo(() => snapshot?.models.slice(0, 3) || [], [snapshot]);
  const scoreTitle = metric === 'overall' ? 'Overall' : SUITES.find(s => s.key === metric)?.label || 'Overall';

  const surface = dark ? 'bg-[#1E2129] border-[#333742]' : 'bg-white border-[#D8F3DC]';
  const pale = dark ? 'bg-[#232833] border-[#414653]' : 'bg-[#D8F3DC] border-[#74C69D]';
  const muted = dark ? 'text-slate-300' : 'text-black';
  const heading = dark ? 'text-white' : 'text-black';
  const field = dark
    ? 'bg-[#151820] text-white border-[#414653] focus:border-[#B6FF2E]'
    : 'bg-white text-black border-[#74C69D] focus:border-[#40916C]';

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32 }} className="w-full min-w-0 pb-12 space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1.5">
          <Link to="/reports" className={'inline-flex items-center gap-1.5 text-xs font-semibold hover:underline ' + muted}>
            <ArrowLeft size={14}/> Back to reports
          </Link>
          <h1 className={'text-2xl md:text-3xl font-black tracking-tight ' + heading}>AI Model Leaderboard</h1>
          <p className={'text-xs sm:text-sm max-w-2xl leading-relaxed ' + muted}>
            Compare newly evaluated frontier and open-weight models using real, attributed benchmark scores.
          </p>
        </div>
        <button type="button" onClick={() => void reload()} disabled={loading}
          className={'inline-flex items-center gap-2 rounded-xl border px-3.5 py-2.5 text-xs font-bold disabled:opacity-60 ' + surface}>
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          Reload published results
        </button>
      </div>

      <div className={'flex flex-wrap items-center gap-2 rounded-2xl border p-2 ' + surface}
        role="tablist" aria-label="Benchmark data source">
        <button type="button" role="tab" aria-selected={mode === 'public'} onClick={() => setMode('public')}
          className={'rounded-xl px-3.5 py-2.5 text-xs font-bold inline-flex items-center gap-2 transition-colors ' +
            (mode === 'public' ? dark ? 'bg-[#B6FF2E] text-[#181A20]' : 'bg-[#74C69D] text-black'
              : dark ? 'text-slate-300 hover:bg-[#323846]' : 'text-black hover:bg-[#D8F3DC]')}>
          <Trophy size={15}/> Public benchmarks
        </button>
        <button type="button" role="tab" aria-selected={mode === 'verifai'} onClick={() => setMode('verifai')}
          className={'rounded-xl px-3.5 py-2.5 text-xs font-bold inline-flex items-center gap-2 transition-colors ' +
            (mode === 'verifai' ? dark ? 'bg-[#B6FF2E] text-[#181A20]' : 'bg-[#74C69D] text-black'
              : dark ? 'text-slate-300 hover:bg-[#323846]' : 'text-black hover:bg-[#D8F3DC]')}>
          <ShieldCheck size={15}/> VerifAI evaluations
          {empirical.length > 0 && <span className="text-xs font-mono">({empirical.length})</span>}
        </button>
      </div>

      {mode === 'public' ? (
        <>
          <section className={'rounded-2xl border p-4 sm:p-5 ' + surface} aria-label="Benchmark source and methodology">
            <div className="flex flex-wrap items-start gap-3 justify-between">
              <div className="min-w-0 flex-1">
                <div className="flex items-center flex-wrap gap-2 mb-2">
                  <span className={'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider ' +
                    (dark ? 'bg-[#B6FF2E]/15 text-[#B6FF2E]' : 'bg-[#D8F3DC] text-black')}>
                    <Check size={13}/> Independent benchmark data
                  </span>
                  <span className={'inline-flex items-center gap-1 text-[11px] ' + muted}>
                    <CalendarDays size={12}/> Weekly refresh
                  </span>
                </div>
                <h2 className={'text-base font-extrabold ' + heading}>LiveBench 2.0 · benchmark release {snapshot?.benchmark_release || '—'}</h2>
                <p className={'mt-1 text-xs leading-relaxed max-w-3xl ' + muted}>
                  Overall is the source’s mean of measured task-suite scores (0–100). These are <strong>not</strong> VerifAI hallucination,
                  citation, evidence-grounding, or availability scores. Missing benchmark scores remain blank.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 text-xs font-bold">
                <a href={snapshot?.source_url || 'https://livebench.ai/'} target="_blank" rel="noopener noreferrer"
                  className={'inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 ' + pale}>
                  Original leaderboard <ExternalLink size={13}/>
                </a>
                {snapshot && <a href={snapshot.methodology_url} target="_blank" rel="noopener noreferrer"
                  className={'inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 ' + surface}>
                  Methodology <ArrowUpRight size={13}/>
                </a>}
              </div>
            </div>
          </section>

          {error && <p role="alert" className="rounded-xl border border-rose-400/50 p-3 text-sm flex gap-2 items-center">
            <CircleAlert size={17}/> Public benchmark unavailable: {error}
          </p>}
          {loading && !snapshot ? <div role="status" className={'rounded-2xl border p-8 text-sm ' + surface}>
            Loading official benchmark results…
          </div> : snapshot && <>
            <section className="grid grid-cols-2 xl:grid-cols-4 gap-3" aria-label="Leaderboard summary">
              {[
                { title: 'Models evaluated', value: String(snapshot.total_models), caption: 'Source-listed models', icon: <BarChart3 size={18}/> },
                { title: 'Highest overall', value: scoreLabel(snapshot.models[0]?.overall_score) + ' /100',
                  caption: snapshot.models[0]?.name || '—', icon: <Trophy size={18}/> },
                { title: 'Source updated', value: dateLabel(snapshot.source_updated_at),
                  caption: 'Published by LiveBench', icon: <Clock3 size={18}/> },
                { title: 'Measured suites', value: '7', caption: 'Distinct task areas', icon: <Sparkles size={18}/> },
              ].map(card => (
                <div key={card.title} className={'rounded-2xl border p-3 sm:p-4 min-w-0 ' + surface}>
                  <span className={'flex items-center justify-between gap-2 text-[11px] font-bold ' + muted}>
                    {card.title}{card.icon}
                  </span>
                  <p className={'text-lg sm:text-xl font-black mt-3 tracking-tight break-words ' + heading}>{card.value}</p>
                  <p className={'mt-1 text-[11px] truncate ' + muted} title={card.caption}>{card.caption}</p>
                </div>
              ))}
            </section>

            <section className="grid gap-3 md:grid-cols-3" aria-label="Top three overall models">
              {topModels.map((item, index) => (
                <button type="button" key={item.id} onClick={() => setInspected(item)}
                  className={'text-left rounded-2xl border p-4 hover:-translate-y-0.5 transition-transform min-w-0 ' +
                    (index === 0 && !dark ? 'bg-gradient-to-br from-[#D8F3DC] to-white border-[#74C69D]'
                      : surface)}>
                  <div className="flex justify-between items-center gap-2">
                    <span className={'text-[10px] font-black uppercase tracking-wider ' + muted}>
                      #{item.rank} overall
                    </span>
                    <Medal size={18} className={dark ? 'text-[#B6FF2E]' : 'text-[#40916C]'}/>
                  </div>
                  <h3 className={'text-base font-extrabold mt-2 truncate ' + heading} title={item.name}>{item.name}</h3>
                  <p className={'text-xs mt-1 ' + muted}>{item.organization}</p>
                  <p className={'text-2xl font-black mt-3 tabular-nums ' + heading}>{scoreLabel(item.overall_score)}
                    <span className={'text-xs ml-1 font-semibold ' + muted}>/ 100</span>
                  </p>
                  <div className="mt-2">{scoreBar(item.overall_score, dark)}</div>
                </button>
              ))}
            </section>

            <section className={'rounded-2xl border p-3 sm:p-4 space-y-3 ' + surface}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className={'text-base font-extrabold ' + heading}>All published model scores</h2>
                  <p className={'text-xs ' + muted}>{entries.length} matching models · filter or sort by task suite</p>
                </div>
                <span className={'inline-flex gap-1.5 items-center text-[11px] ' + muted}>
                  <ArrowDownUp size={13}/> Sorted by {scoreTitle.toLowerCase()}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                <div className="relative min-w-[170px] flex-1">
                  <Search size={15} className={'absolute top-1/2 -translate-y-1/2 left-3 ' + muted}/>
                  <input aria-label="Search AI models" value={search} onChange={e => setSearch(e.target.value)}
                    placeholder="Search model or lab…"
                    className={'w-full rounded-xl border pl-9 pr-3 py-2.5 text-xs outline-none ' + field}/>
                </div>
                <select aria-label="Filter model organization" value={provider} onChange={e => setProvider(e.target.value)}
                  className={'rounded-xl border px-3 py-2.5 text-xs font-semibold outline-none max-w-full ' + field}>
                  <option value="all">All providers</option>
                  {organizations.map(org => <option key={org} value={org}>{org}</option>)}
                </select>
                <select aria-label="Sort models by benchmark" value={metric} onChange={e => setMetric(e.target.value as Metric)}
                  className={'rounded-xl border px-3 py-2.5 text-xs font-semibold outline-none max-w-full ' + field}>
                  <option value="overall">Overall score</option>
                  {SUITES.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
                </select>
              </div>
              {entries.length === 0 ? <p className={'rounded-xl border p-6 text-center text-sm ' + pale}>No models match your search.</p> : <>
                <div className="md:hidden space-y-2" aria-label="Mobile model leaderboard">
                  {entries.map((model, index) => (
                    <button type="button" key={model.id} onClick={() => setInspected(model)}
                      className={'w-full text-left rounded-xl border px-3 py-3 space-y-2 ' + pale}
                      aria-label={'Details for ' + model.name}>
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <span className={'text-[10px] font-bold ' + muted}>#{metric === 'overall' ? model.rank : index + 1} · {model.organization}</span>
                          <p className={'font-extrabold text-sm break-words ' + heading}>{model.name}</p>
                        </div>
                        <span className={'font-black text-base tabular-nums shrink-0 ' + heading}>{scoreLabel(scoreFor(model, metric))}</span>
                      </div>
                      {scoreBar(scoreFor(model, metric), dark)}
                      <div className={'flex justify-between items-center text-[10px] ' + muted}>
                        <span>{scoreTitle} · {model.suite_coverage}/7 suites measured</span>
                        <span className="flex items-center gap-1">Breakdown <ChevronRight size={12}/></span>
                      </div>
                    </button>
                  ))}
                </div>
                <div className="hidden md:block w-full overflow-x-auto" role="region" aria-label="Detailed benchmark score table" tabIndex={0}>
                  <table className="text-xs text-left w-full min-w-[1020px] border-collapse">
                    <thead>
                      <tr className={'border-b ' + (dark ? 'border-[#414653]' : 'border-[#D8F3DC]')}>
                        <th scope="col" className="p-3 text-[11px]">Rank</th>
                        <th scope="col" className="p-3 text-[11px] min-w-[190px]">Model</th>
                        <th scope="col" className="p-3 text-[11px]">Organization</th>
                        <th scope="col" className="p-3 text-[11px] text-right">Overall</th>
                        {SUITES.map(suite => <th scope="col" key={suite.key} className="p-3 text-[11px] text-right" title={suite.description}>{suite.shortLabel}</th>)}
                        <th scope="col" className="p-3">Details</th>
                      </tr>
                    </thead>
                    <tbody className={dark ? 'divide-y divide-[#323846]' : 'divide-y divide-[#ECF7EE]'}>
                      {entries.map((model, index) => (
                        <tr key={model.id} className={dark ? 'hover:bg-[#232833]' : 'hover:bg-[#F1FBF4]'}>
                          <td className={'p-3 font-mono font-bold ' + heading}>#{metric === 'overall' ? model.rank : index + 1}</td>
                          <td className={'p-3 font-bold ' + heading}>{model.name}</td>
                          <td className={'p-3 ' + muted}>{model.organization}</td>
                          <td className={'p-3 font-black text-right tabular-nums ' + heading}>{scoreLabel(model.overall_score)}</td>
                          {SUITES.map(suite => (
                            <td key={suite.key} className={'p-3 text-right font-mono tabular-nums ' +
                              (metric === suite.key ? 'font-black ' + heading : muted)}>
                              {scoreLabel(model.suite_scores[suite.key])}
                            </td>
                          ))}
                          <td className="p-3">
                            <button type="button" onClick={() => setInspected(model)}
                              aria-label={'View benchmark details for ' + model.name}
                              className={'rounded-lg border p-2 hover:opacity-80 ' + pale}>
                              <ChevronRight size={15}/>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>}
            </section>
            <p className={'text-[11px] flex items-start gap-2 leading-relaxed ' + muted}>
              <Info size={14} className="shrink-0 mt-0.5"/>
              Values are published model evaluation scores, not real-time API availability or a guarantee of performance.
              Source measurements may have missing categories; each model's coverage is shown in its details.
              Weekly refresh keeps the last valid snapshot if the source becomes unavailable.
            </p>
          </>}
        </>
      ) : (
        <section className={'rounded-2xl border p-5 sm:p-8 space-y-3 ' + surface} aria-label="VerifAI first-party model evaluations">
          <div className="flex gap-3 items-center">
            <ShieldCheck size={24} className={dark ? 'text-[#B6FF2E]' : 'text-[#40916C]'}/>
            <h2 className={'text-lg font-extrabold ' + heading}>VerifAI's own measured evaluations</h2>
          </div>
          <p className={'text-sm leading-relaxed max-w-3xl ' + muted}>
            These are separate from public LiveBench scores. VerifAI will only list factual support, contradiction
            detection, and citation metrics after evaluating real models on its own labeled dataset.
          </p>
          {empiricalError && <p role="alert" className="text-xs">{empiricalError}</p>}
          {!empirical.length ? (
            <div className={'rounded-xl border p-5 text-sm ' + pale}>
              No internally measured model rankings yet. Public benchmark results are available in the other tab;
              fabricated verification scores are never shown here.
            </div>
          ) : (
            <div className="grid gap-2">
              {empirical.map(row => (
                <div key={row.model} className={'rounded-xl border p-3 flex flex-wrap justify-between items-center gap-2 ' + pale}>
                  <div>
                    <strong className={'text-sm ' + heading}>#{row.rank} · {row.model}</strong>
                    <p className={'text-xs ' + muted}>{row.provider} · {row.evaluationsCount} evaluated cases</p>
                  </div>
                  <strong className={'text-base tabular-nums ' + heading}>{scoreLabel(row.overallScore)}%</strong>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <AnimatePresence>
        {inspected && mode === 'public' && snapshot && (
          <motion.div
            key={inspected.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onMouseDown={event => { if (event.target === event.currentTarget) setInspected(null); }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/65 backdrop-blur-sm p-3 sm:p-5">
            <motion.section role="dialog" aria-modal="true" aria-labelledby="public-model-dialog-title"
              initial={{ y: 14, scale: 0.98 }} animate={{ y: 0, scale: 1 }} exit={{ y: 14, scale: 0.98 }}
              className={'w-full max-w-xl max-h-[88dvh] overflow-y-auto rounded-2xl border shadow-2xl p-4 sm:p-6 space-y-4 ' + surface}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className={'text-xs font-bold ' + muted}>PUBLIC BENCHMARK · RANK #{inspected.rank}</p>
                  <h2 id="public-model-dialog-title" className={'text-xl font-black mt-1 ' + heading}>{inspected.name}</h2>
                  <p className={'text-sm ' + muted}>{inspected.organization} · LiveBench 2.0</p>
                </div>
                <button type="button" onClick={() => setInspected(null)} aria-label="Close model details"
                  className={'p-2 rounded-lg border ' + pale}><X size={17}/></button>
              </div>
              <div className={'rounded-xl border p-4 ' + pale}>
                <div className="flex items-end justify-between gap-3">
                  <div>
                    <p className={'text-xs font-bold ' + muted}>Official overall score</p>
                    <p className={'text-3xl font-black tabular-nums ' + heading}>{scoreLabel(inspected.overall_score)}<span className="text-sm font-semibold"> / 100</span></p>
                  </div>
                  <span className={'text-xs font-bold ' + muted}>{inspected.suite_coverage} / 7 suites</span>
                </div>
                <div className="mt-3">{scoreBar(inspected.overall_score, dark)}</div>
              </div>
              <div className="space-y-3">
                {SUITES.map(suite => (
                  <div key={suite.key} className="space-y-1.5">
                    <div className="flex justify-between gap-3 items-baseline">
                      <span className={'text-sm font-semibold ' + heading}>{suite.label}</span>
                      <span className={'font-mono text-sm font-bold tabular-nums ' + heading}>{scoreLabel(inspected.suite_scores[suite.key])}</span>
                    </div>
                    {scoreBar(inspected.suite_scores[suite.key], dark)}
                    <p className={'text-[11px] ' + muted}>{suite.description}</p>
                  </div>
                ))}
              </div>
              <div className={'rounded-xl border p-3 text-xs space-y-2 ' + pale}>
                <p className="font-bold">Evidence and interpretation</p>
                <p>Published source updated {dateLabel(snapshot.source_updated_at)} · benchmark release {dateLabel(snapshot.benchmark_release)}.</p>
                <p>These task scores cannot establish citation accuracy, factual reliability in your domain, or provider availability.</p>
                <a href={snapshot.data_url} target="_blank" rel="noopener noreferrer"
                  className={'inline-flex gap-1 font-bold items-center underline underline-offset-2 ' + heading}>
                  View source CSV <ExternalLink size={12}/>
                </a>
              </div>
              <div className="flex justify-end gap-2 flex-wrap">
                <Link to="/chat" onClick={() => setInspected(null)}
                  className={'rounded-xl border px-3 py-2 text-xs font-bold ' + pale}>
                  Try an available model in Chat
                </Link>
                <button type="button" onClick={() => setInspected(null)}
                  className={'rounded-xl px-4 py-2 text-xs font-bold ' +
                    (dark ? 'bg-[#B6FF2E] text-[#181A20]' : 'bg-[#74C69D] text-black')}>
                  Close
                </button>
              </div>
            </motion.section>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
export default ModelLeaderboardPage;
