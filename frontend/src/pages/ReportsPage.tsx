import React, { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowDownRight, ArrowRight, BarChart3, CheckCheck, CircleHelp,
  FileCheck2, Link2, RefreshCw, ShieldCheck, TrendingUp } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { reportsApi, type AnalyticsReportResponse } from '../api';
import { useTheme } from '../context/ThemeContext';
import './ReportsRedesign.css';

interface ReportsPageProps {
  theme?: 'light' | 'dark';
}

type Period = '7D' | '30D' | '90D' | '1Y';
type ActivityPoint = {
  date: string;
  name: string;
  claims: number;
  evidence: number;
  verifications: number;
};

const PERIODS: { value: Period; label: string }[] = [
  { value: '7D', label: '7 days' },
  { value: '30D', label: '30 days' },
  { value: '90D', label: '90 days' },
  { value: '1Y', label: '1 year' },
];

const formatNumber = (n: number) => n.toLocaleString('en-US');
const percent = (n: number) => Number.isFinite(n) ? n.toFixed(1) + '%' : '—';

const dateLabel = (date: string, compact = false) => {
  const parsed = new Date(date + 'T00:00:00Z');
  if (!Number.isFinite(parsed.getTime())) return date;
  return parsed.toLocaleDateString('en-US', {
    timeZone: 'UTC',
    month: compact ? 'short' : 'long',
    day: 'numeric',
    ...(compact ? {} : { year: 'numeric' }),
  });
};

const RangeEmpty = ({ title, detail }: { title: string; detail: string }) => (
  <div className="rpt-empty" role="status">
    <div className="rpt-empty-icon"><Activity size={22} strokeWidth={1.8}/></div>
    <strong>{title}</strong>
    <p>{detail}</p>
  </div>
);

const RankingRows = ({ rows, accent }: {
  rows: { name: string; value: number; share?: number }[];
  accent: 'olive' | 'mint';
}) => {
  const max = Math.max(1, ...rows.map(row => row.value));
  return <div className="rpt-rank-list">
    {rows.map((row, index) => (
      <div key={row.name + index} className="rpt-rank-item" title={row.name}>
        <div className="rpt-rank-copy">
          <span className="rpt-rank-index">{String(index + 1).padStart(2, '0')}</span>
          <span className="rpt-rank-name">{row.name}</span>
          <strong className="rpt-rank-count">{formatNumber(row.value)}
            {row.share !== undefined && <small> · {percent(row.share)}</small>}
          </strong>
        </div>
        <div className="rpt-rank-track" aria-label={row.name + ': ' + row.value}>
          <div className={'rpt-rank-fill rpt-rank-fill--' + accent}
            style={{ width: (row.value > 0 ? Math.max(2, row.value / max * 100) : 0) + '%' }}/>
        </div>
      </div>
    ))}
  </div>;
};

export const ReportsPage: React.FC<ReportsPageProps> = ({ theme: propTheme }) => {
  const context = useTheme();
  const dark = (propTheme || context.theme) === 'dark';
  const [timeframe, setTimeframe] = useState<Period>('30D');
  const [analytics, setAnalytics] = useState<AnalyticsReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadError(null);
    reportsApi.getAnalytics(timeframe).then(report => {
      if (active) setAnalytics(report);
    }).catch(err => {
      if (active) { setAnalytics(null); setLoadError(err instanceof Error ? err.message : 'Analytics unavailable'); }
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [timeframe, reload]);

  const series = useMemo<ActivityPoint[]>(() =>
    (analytics?.chart_data ?? []).map((point, index) => ({
      date: String(point.date || point.day || index),
      name: String(point.day || point.date || index),
      claims: Number(point.claims) || 0,
      evidence: Number(point.evidence) || 0,
      verifications: Number(point.verifications) || 0,
    })), [analytics]);

  const tickDates = useMemo(() => {
    if (series.length === 0) return [];
    const step = Math.max(1, Math.ceil((series.length - 1) / 5));
    return series.filter((_, index) => index % step === 0 || index === series.length - 1)
      .map(item => item.date);
  }, [series]);

  const totalClaims = analytics?.total_claims ?? 0;
  const totalVerifications = analytics?.total_verifications ?? 0;
  const support = analytics?.supported_rate ?? 0;
  const contradiction = analytics?.contradicted_rate ?? 0;
  const unknown = analytics?.unknown_rate ?? 0;
  const remainder = Math.max(0, 100 - support - contradiction - unknown);
  const outcomes = [
    { id: 'supported', label: 'Supported', pct: support },
    { id: 'contradicted', label: 'Contradicted', pct: contradiction },
    { id: 'unknown', label: 'Unknown', pct: unknown },
    // Non-factual or otherwise unclassified claims need an honest fourth
    // segment; never quietly assign missing percent to the Unknown category.
    ...(totalClaims > 0 && remainder > 0.15
      ? [{ id: 'other', label: 'Other / unclassified', pct: remainder }]
      : []),
  ];
  const modelRows = (analytics?.model_usage ?? [])
    .map(row => ({ name: String(row.model), value: Number(row.usage) || 0 }))
    .filter(row => row.value > 0);
  const sourceRows = (analytics?.evidence_sources ?? [])
    .map(row => ({ name: String(row.domain), value: Number(row.count) || 0 }))
    .filter(row => row.value > 0);
  const sourceTotal = sourceRows.reduce((sum, source) => sum + source.value, 0);
  const peak = series.reduce((best, point) => point.claims > best.claims ? point : best,
    { date: '', name: '', claims: 0, evidence: 0, verifications: 0 });
  const observed = series.some(item => item.claims > 0 || item.verifications > 0);
  const fmtAxisDate = (value: string) =>
    timeframe === '7D'
      ? (Number.isFinite(Date.parse(value)) ? new Date(value + 'T00:00:00Z').toLocaleDateString('en-US', { weekday: 'short', timeZone: 'UTC' }) : value)
      : dateLabel(value, true);
  const periodLabel = PERIODS.find(period => period.value === timeframe)?.label || timeframe;

  return (
    <div className={'reports-redesign reports-redesign--' + (dark ? 'dark' : 'light')}>
      <div className="rpt-head">
        <div>
          <h1>Reports &amp; Insights</h1>
          <p>Understand the activity behind your verified claims.</p>
        </div>
        <div className="rpt-period" role="group" aria-label="Report time period">
          {PERIODS.map(period => (
            <button key={period.value} type="button" aria-pressed={timeframe === period.value}
              onClick={() => setTimeframe(period.value)}>{period.label}</button>
          ))}
        </div>
      </div>

      {loadError && <div className="rpt-error" role="alert">
        <span><CircleHelp size={18}/> Report data could not be loaded: {loadError}</span>
        <button type="button" onClick={() => setReload(n => n + 1)}>Retry <RefreshCw size={14}/></button>
      </div>}

      <div className="rpt-metrics" aria-label="Analytics summary">
        {[
          { label: 'Verifications', value: formatNumber(totalVerifications), unit: 'completed runs', icon: <FileCheck2 size={20}/> },
          { label: 'Claims analyzed', value: formatNumber(totalClaims), unit: 'across audits', icon: <BarChart3 size={20}/> },
          { label: 'Supported claims', value: totalClaims ? percent(support) : '—', unit: 'of measured claims', icon: <CheckCheck size={20}/> },
          { label: 'Unknown outcomes', value: totalClaims ? percent(unknown) : '—', unit: 'awaiting evidence', icon: <CircleHelp size={20}/> },
        ].map((item, index) => (
          <div className="rpt-metric" key={item.label}>
            <div className="rpt-metric-top"><span>{item.label}</span>{item.icon}</div>
            <div className="rpt-metric-value">{loading ? <span className="rpt-skeleton"/> : item.value}</div>
            <div className="rpt-metric-foot"><span>{item.unit}</span><span className="rpt-metric-index">0{index + 1}</span></div>
          </div>
        ))}
      </div>

      <div className="rpt-top-grid">
        <section className="rpt-panel rpt-trend" aria-label="Verification activity">
          <div className="rpt-panel-head">
            <div>
              <div className="rpt-title-icon"><Activity size={18}/></div>
              <h2>Verification activity</h2>
              <p>Claims analyzed over the last {periodLabel.toLowerCase()} · UTC</p>
            </div>
            <div className="rpt-live-detail">
              <span className="rpt-status-dot"/>
              {peak.claims > 0 ? 'Peak ' + formatNumber(peak.claims) + ' · ' + dateLabel(peak.date, true) : 'No activity yet'}
            </div>
          </div>
          {loading ? <div className="rpt-trend-loading" role="status" aria-label="Loading activity chart"/> :
            observed ? <div className="rpt-activity-chart" role="img" aria-label="Daily claims analyzed chart; hover or focus points for detail">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={series} margin={{ top: 16, right: 14, left: 2, bottom: 6 }}>
                  <defs>
                    <linearGradient id="reportAreaMint" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={dark ? '#B6FF2E' : '#40916C'} stopOpacity={0.24}/>
                      <stop offset="100%" stopColor={dark ? '#B6FF2E' : '#74C69D'} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid vertical={false} strokeDasharray="3 5" stroke={dark ? '#333C42' : '#D8E8DD'}/>
                  <XAxis dataKey="date" ticks={tickDates} interval="preserveStartEnd"
                    axisLine={false} tickLine={false} minTickGap={16} tickMargin={12}
                    tick={{ fill: dark ? '#A4B5AA' : '#2B4437', fontSize: 11 }}
                    tickFormatter={fmtAxisDate} />
                  <YAxis axisLine={false} tickLine={false} allowDecimals={false}
                    width={35} tickMargin={8}
                    tick={{ fill: dark ? '#A4B5AA' : '#2B4437', fontSize: 11 }}/>
                  <Tooltip labelFormatter={label => dateLabel(String(label))}
                    formatter={(value, name) => [formatNumber(Number(value) || 0),
                      name === 'claims' ? 'Claims' : String(name)]}
                    cursor={{ stroke: dark ? '#B6FF2E' : '#40916C', strokeDasharray: '4 4' }}
                    contentStyle={{ background: dark ? '#1E2728' : '#FFFFFF',
                      color: dark ? '#FFFFFF' : '#000000',
                      border: '1px solid ' + (dark ? '#384843' : '#9ED4B0'),
                      borderRadius: 12, fontSize: 12, boxShadow: '0 12px 30px -16px rgba(0,0,0,.25)' }}
                    labelStyle={{ color: dark ? '#FFFFFF' : '#000000', fontWeight: 700 }} />
                  <Area type="monotone" dataKey="claims" stroke={dark ? '#B6FF2E' : '#1B4332'}
                    strokeWidth={2.6} fill="url(#reportAreaMint)" dot={false}
                    activeDot={{ r: 5, strokeWidth: 2, stroke: dark ? '#1E2129' : '#FFFFFF' }}
                    isAnimationActive={false}/>
                </AreaChart>
              </ResponsiveContainer>
            </div> :
              <RangeEmpty title="No activity in this period" detail="When you verify claims, your daily volume appears here. Try a wider date range."/ >
          }
          <div className="rpt-trend-footer">
            <span><span className="rpt-chart-legend"/> Claims analyzed</span>
            <span>Daily totals · {periodLabel} selected</span>
          </div>
        </section>

        <section className="rpt-panel rpt-outcomes" aria-label="Claim outcomes">
          <div className="rpt-panel-head">
            <div>
              <div className="rpt-title-icon"><ShieldCheck size={18}/></div>
              <h2>Claim outcomes</h2>
              <p>How claims were classified</p>
            </div>
          </div>
          <div className="rpt-outcome-graphic">
            <div className="rpt-donut" role="img"
              aria-label={totalClaims ? outcomes.map(item => percent(item.pct) + ' ' + item.label.toLowerCase()).join(', ') : 'No claim outcomes'}
              style={{ background: totalClaims > 0
                ? `conic-gradient(#40916C 0% ${support}%, #F06476 ${support}% ${support + contradiction}%, #E5A72F ${support + contradiction}% ${Math.min(100, support + contradiction + unknown)}%, #ABBDB0 ${Math.min(100, support + contradiction + unknown)}% 100%)`
                : dark ? '#343D43' : '#E1EDE4' }}>
              <div className="rpt-donut-center">
                <strong>{loading ? '—' : formatNumber(totalClaims)}</strong>
                <span>Total claims</span>
              </div>
            </div>
          </div>
          <div className="rpt-outcome-rows">
            {outcomes.map(outcome => (
              <div className="rpt-outcome-row" key={outcome.id}>
                <span className="rpt-outcome-label"><i className={'rpt-outcome-dot rpt-outcome-dot--' + outcome.id}/>{outcome.label}</span>
                <span className="rpt-outcome-amount">{totalClaims ? percent(outcome.pct) : '—'}</span>
              </div>
            ))}
          </div>
          <p className="rpt-outcome-note">Percent of recorded claims, not a model accuracy benchmark.</p>
        </section>
      </div>

      <div className="rpt-bottom-grid">
        <section className="rpt-panel rpt-rank-panel" aria-label="Model usage">
          <div className="rpt-panel-head">
            <div>
              <div className="rpt-title-icon"><TrendingUp size={18}/></div>
              <h2>Model usage</h2>
              <p>Completed model responses in the reporting window</p>
            </div>
            <span className="rpt-mini-total">{modelRows.reduce((sum, row) => sum + row.value, 0)} runs</span>
          </div>
          {loading ? <div className="rpt-rank-loading"/> :
            modelRows.length ? <RankingRows rows={modelRows} accent="olive"/> :
            <RangeEmpty title="No model calls recorded" detail="Start a multi-model chat to see which models are used."/ >
          }
        </section>

        <section className="rpt-panel rpt-rank-panel" aria-label="Evidence sources">
          <div className="rpt-panel-head">
            <div>
              <div className="rpt-title-icon"><Link2 size={18}/></div>
              <h2>Evidence sources</h2>
              <p>Retrieved sources by publisher or domain</p>
            </div>
            <span className="rpt-mini-total">{formatNumber(sourceTotal)} sources</span>
          </div>
          {loading ? <div className="rpt-rank-loading"/> :
            sourceRows.length ? <RankingRows rows={sourceRows.map(row => ({
              ...row, share: sourceTotal ? row.value / sourceTotal * 100 : 0,
            }))} accent="mint"/> :
            <RangeEmpty title="No sources retrieved" detail="Verified claims with available evidence will populate this list."/ >
          }
          {sourceRows.length > 0 && <p className="rpt-footnote">
            <ArrowDownRight size={13}/> Shares reflect the listed publishers returned by analytics.
          </p>}
        </section>
      </div>
    </div>
  );
};

export default ReportsPage;
