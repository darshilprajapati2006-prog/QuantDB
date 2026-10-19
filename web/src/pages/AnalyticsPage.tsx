import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Gauge,
  ShieldCheck,
  TrendingDown,
  AlertTriangle,
  Activity,
  Layers,
  ArrowDownRight,
  Info,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import { request } from '../lib/api';
import type { Portfolio, RiskMetrics } from '../types';

export function AnalyticsPage() {
  const [portfolioId, setPortfolioId] = useState<number>(0);
  const { data: portfolios = [] } = useQuery({ queryKey: ['portfolios'], queryFn: () => request<Portfolio[]>('/portfolios') });
  useEffect(() => {
    if (portfolios.length && !portfolios.some((item) => item.portfolio_id === portfolioId)) setPortfolioId(portfolios[0].portfolio_id);
  }, [portfolios, portfolioId]);
  const { data: risk = {} as RiskMetrics, isLoading, refetch } = useQuery({
    queryKey: ['risk', portfolioId],
    queryFn: () => request<RiskMetrics>(`/analytics/risk?portfolio_id=${portfolioId}`),
    enabled: portfolioId > 0,
  });
  const sortino = (risk as RiskMetrics & { sortino_ratio?: number }).sortino_ratio;
  const maxDd = risk.max_drawdown;
  const vol = risk.annualized_volatility;
  const beta = risk.beta_vs_sp500;
  const var95 = risk.var_95_daily;
  const cvar95 = risk.cvar_95_daily;
  const returnDistribution: Array<{ bucket: string; count: number; isVar: boolean }> = [];
  const underwaterData: Array<{ day: string; drawdown: number }> = [];

  const stressTests = [
    { scenario: '2008 Global Financial Crisis', impact: -21.4, severity: 'HIGH' },
    { scenario: '2020 Covid Liquidity Shock', impact: -14.8, severity: 'HIGH' },
    { scenario: 'Federal Reserve +100bps Rate Hike', impact: -3.8, severity: 'MODERATE' },
    { scenario: 'Tech Sector Valuation Compression', impact: -7.2, severity: 'MODERATE' },
    { scenario: 'Crude Oil & Energy Spike (+30%)', impact: -1.9, severity: 'LOW' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            QUANTITATIVE RISK MANAGEMENT <span className="eyebrow-sep">/</span> RISK ANALYTICS
          </div>
          <h1>Portfolio Risk & Statistical Analytics</h1>
          <p>
            Value-at-Risk (VaR), Conditional VaR, drawdown duration, and scenario stress testing.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select aria-label="Portfolio for risk metrics" value={portfolioId} onChange={(event) => setPortfolioId(Number(event.target.value))} className="outline-button">
            {portfolios.length === 0 && <option value={0}>No portfolio</option>}
            {portfolios.map((portfolio) => <option key={portfolio.portfolio_id} value={portfolio.portfolio_id}>{portfolio.portfolio_name}</option>)}
          </select>
          <button onClick={() => refetch()} disabled={!portfolioId} className="outline-button" title="Recalculate metrics">
            <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
            <span>Recalculate Risk</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Strip */}
      <div className="metric-grid">
        <article className="metric-card">
          <div className="metric-head">
            <span>SHARPE RATIO</span>
            <span className="metric-icon tone-0">
              <Activity size={16} />
            </span>
          </div>
          <div className="metric-value font-mono text-[#69d5ad]">
            {risk.sharpe_ratio == null ? '—' : Number(risk.sharpe_ratio).toFixed(2)}
          </div>
          <div className="metric-foot">
            <span className="change">{risk.sharpe_ratio == null ? 'Awaiting data' : Number(risk.sharpe_ratio) >= 1 ? 'Positive' : 'Below 1.0'}</span>
            <span>Excess return / risk</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-head">
            <span>SORTINO RATIO</span>
            <span className="metric-icon tone-1">
              <ShieldCheck size={16} />
            </span>
          </div>
          <div className="metric-value font-mono">
            {sortino == null ? '—' : Number(sortino).toFixed(2)}
          </div>
          <div className="metric-foot">
            <span className="change positive">Downside risk only</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-head">
            <span>MAX DRAWDOWN</span>
            <span className="metric-icon tone-2">
              <TrendingDown size={16} />
            </span>
          </div>
          <div className="metric-value font-mono text-[#ea837c]">
            {maxDd == null ? '—' : `${Number(maxDd).toFixed(2)}%`}
          </div>
          <div className="metric-foot">
            <span className="change negative">Peak-to-Trough</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-head">
            <span>DAILY VaR (95%)</span>
            <span className="metric-icon tone-3">
              <AlertTriangle size={16} />
            </span>
          </div>
          <div className="metric-value font-mono text-[#e6b88a]">
            {var95 == null ? '—' : `${Number(var95).toFixed(2)}%`}
          </div>
          <div className="metric-foot">
            <span>CVaR: {cvar95 == null ? '—' : `${Number(cvar95).toFixed(2)}%`}</span>
          </div>
        </article>
      </div>

      {/* Main Charts: Return Distribution (VaR) & Underwater Drawdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Value at Risk Distribution */}
        <div className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">HISTORICAL RISK DATA</div>
              <h2>Return Frequency & 95% Cutoff</h2>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-mono">
              <span className="flex items-center gap-1 text-[#ea837c]">
                <span className="w-2 h-2 rounded-sm bg-[#e48a82]" /> Tail Loss (VaR)
              </span>
              <span className="flex items-center gap-1 text-[#64caa1]">
                <span className="w-2 h-2 rounded-sm bg-[#5da5da]" /> Normal Dist.
              </span>
            </div>
          </div>

          <div className="h-60 mt-3 relative">
            {returnDistribution.length === 0 && <div className="chart-empty">Historical return series are not available for this account yet.</div>}
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={returnDistribution} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#1c262c" vertical={false} />
                <XAxis dataKey="bucket" stroke="#56666d" tick={{ fontSize: 9, fill: '#6c7c83' }} axisLine={false} tickLine={false} />
                <YAxis stroke="#56666d" tick={{ fontSize: 9, fill: '#6c7c83' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#10161b',
                    borderColor: '#222f36',
                    borderRadius: '8px',
                    fontSize: '11px',
                    color: '#e5ecea',
                  }}
                  formatter={(val: number) => [`${val} Trading Days`, 'Frequency']}
                />
                <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                  {returnDistribution.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={entry.isVar ? '#e48a82' : '#457b9d'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[11px] text-[#78888e] flex items-center justify-between border-t border-[#1e272d] pt-2.5 mt-2">
            <span>Confidence Interval: <b>95.0%</b></span>
            <span>Historical 1-Day VaR: <b className="text-[#ea837c] font-mono">{var95 == null ? '—' : `${Number(var95).toFixed(2)}%`}</b></span>
          </div>
        </div>

        {/* Drawdown Underwater Curve */}
        <div className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">HISTORICAL DRAWDOWN</div>
              <h2>Underwater Equity Curve</h2>
            </div>
            <span className="text-[10px] font-mono text-[#ea837c]">MAX: {maxDd == null ? '—' : `${Number(maxDd).toFixed(2)}%`}</span>
          </div>

          <div className="h-60 mt-3 relative">
            {underwaterData.length === 0 && <div className="chart-empty">Drawdown history will appear after QuantDB has valuation observations.</div>}
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={underwaterData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="drawdownFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ea837c" stopOpacity={0.0} />
                    <stop offset="100%" stopColor="#ea837c" stopOpacity={0.35} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1c262c" vertical={false} />
                <XAxis dataKey="day" stroke="#56666d" tick={{ fontSize: 9, fill: '#6c7c83' }} axisLine={false} tickLine={false} />
                <YAxis
                  stroke="#56666d"
                  tick={{ fontSize: 9, fill: '#6c7c83' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[-10, 0]}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#10161b',
                    borderColor: '#222f36',
                    borderRadius: '8px',
                    fontSize: '11px',
                    color: '#e5ecea',
                  }}
                  formatter={(val: number) => [`${val.toFixed(2)}%`, 'Drawdown']}
                />
                <Area type="monotone" dataKey="drawdown" stroke="#e48a82" strokeWidth={1.5} fill="url(#drawdownFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[11px] text-[#78888e] flex items-center justify-between border-t border-[#1e272d] pt-2.5 mt-2">
            <span>Recovery Velocity: <b>—</b></span>
            <span>Current Drawdown: <b className="text-[#64caa1] font-mono">—</b></span>
          </div>
        </div>
      </div>

      {/* Stress Testing & Factor Exposures */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Stress Testing */}
        <div className="panel">
          <div className="panel-kicker">ILLUSTRATIVE SCENARIO ASSUMPTIONS</div>
          <h2 className="text-sm font-semibold text-[#e1e9e6] mb-3">Example Market Shock Scenarios</h2>
          <div className="divide-y divide-[#1e272d] text-xs font-mono">
            {stressTests.map((st) => (
              <div key={st.scenario} className="py-2.5 flex items-center justify-between">
                <div>
                  <div className="text-[#d8e2df] font-sans font-medium">{st.scenario}</div>
                  <div className="text-[10px] text-[#6a7b81]">{st.severity} SEVERITY STRESS</div>
                </div>
                <span className="text-[#ea837c] font-semibold text-sm">
                  {st.impact.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Statistical Factors */}
        <div className="panel">
          <div className="panel-kicker">STATISTICAL MEASURES</div>
          <h2 className="text-sm font-semibold text-[#e1e9e6] mb-3">Risk Factor Attributes</h2>
          <div className="divide-y divide-[#1e272d] text-xs font-mono">
            <div className="py-2.5 flex justify-between">
              <span className="text-[#76868c]">Annualized Volatility (σ)</span>
              <span className="text-[#d8e2df] font-medium">{vol == null ? '—' : `${Number(vol).toFixed(1)}%`}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#76868c]">Beta vs S&P 500 (β)</span>
              <span className="text-[#d8e2df] font-medium">{beta == null ? '—' : Number(beta).toFixed(2)}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#76868c]">Daily Expected Shortfall (CVaR 95%)</span>
              <span className="text-[#ea837c] font-medium">{cvar95 == null ? '—' : `${Number(cvar95).toFixed(2)}%`}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#76868c]">Kurtosis / Fat-Tail Risk</span>
              <span className="text-[#d8e2df] font-medium">Not calculated</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#76868c]">Risk Classification</span>
              <span className="text-[#64caa1] font-semibold">Awaiting data</span>
            </div>
          </div>
        </div>
      </div>

      <div className="disclaimer">
        <ShieldCheck size={14} /> Portfolio risk metrics come from the selected account. Example market shock scenarios are illustrative and are not portfolio forecasts.
      </div>
    </div>
  );
}
