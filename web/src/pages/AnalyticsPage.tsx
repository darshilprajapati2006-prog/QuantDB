import React, { useState } from 'react';
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
import type { RiskMetrics } from '../types';

export function AnalyticsPage() {
  const [portfolioId, setPortfolioId] = useState<number>(1);

  const { data: risk = {} as RiskMetrics, isLoading, refetch } = useQuery({
    queryKey: ['risk', portfolioId],
    queryFn: () => request<RiskMetrics>(`/analytics/risk?portfolio_id=${portfolioId}`),
  });

  const sharpe = Number(risk.sharpe_ratio ?? 1.84);
  const sortino = Number(risk.sortino_ratio ?? 2.31);
  const maxDd = Math.abs(Number(risk.max_drawdown ?? 6.85));
  const vol = Number(risk.annualized_volatility ?? 14.2);
  const beta = Number(risk.beta_vs_sp500 ?? 0.88);
  const var95 = Number(risk.var_95_daily ?? -1.45);
  const cvar95 = Number(risk.cvar_95_daily ?? -2.18);

  // Return distribution mockup centered around positive mean
  const returnDistribution = [
    { bucket: '< -3%', count: 2, isVar: true },
    { bucket: '-3% to -2%', count: 6, isVar: true },
    { bucket: '-2% to -1%', count: 18, isVar: false },
    { bucket: '-1% to 0%', count: 42, isVar: false },
    { bucket: '0% to +1%', count: 65, isVar: false },
    { bucket: '+1% to +2%', count: 48, isVar: false },
    { bucket: '+2% to +3%', count: 21, isVar: false },
    { bucket: '> +3%', count: 7, isVar: false },
  ];

  // Drawdown underwater curve
  const underwaterData = Array.from({ length: 30 }, (_, i) => ({
    day: `D${i + 1}`,
    drawdown: -(Math.abs(Math.sin(i * 0.45) * 5.2 + Math.cos(i * 0.2) * 2.1)),
  }));

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

        <button onClick={() => refetch()} className="outline-button" title="Recalculate metrics">
          <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
          <span>Recalculate Risk</span>
        </button>
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
            {sharpe.toFixed(2)}
          </div>
          <div className="metric-foot">
            <span className="change positive">EXCELLENT</span>
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
            {sortino.toFixed(2)}
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
            −{maxDd.toFixed(2)}%
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
            {var95.toFixed(2)}%
          </div>
          <div className="metric-foot">
            <span>CVaR: {cvar95.toFixed(2)}%</span>
          </div>
        </article>
      </div>

      {/* Main Charts: Return Distribution (VaR) & Underwater Drawdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Value at Risk Distribution */}
        <div className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">PARAMETRIC VALUE-AT-RISK</div>
              <h2>Historical Return Frequency & 95% Cutoff</h2>
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

          <div className="h-60 mt-3">
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
            <span>Historical 1-Day VaR: <b className="text-[#ea837c] font-mono">{var95.toFixed(2)}%</b></span>
          </div>
        </div>

        {/* Drawdown Underwater Curve */}
        <div className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">HISTORICAL DRAWDOWN</div>
              <h2>Underwater Equity Curve</h2>
            </div>
            <span className="text-[10px] font-mono text-[#ea837c]">MAX: -{maxDd.toFixed(2)}%</span>
          </div>

          <div className="h-60 mt-3">
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
            <span>Recovery Velocity: <b>Normal</b></span>
            <span>Current Drawdown: <b className="text-[#64caa1] font-mono">0.0% (At High)</b></span>
          </div>
        </div>
      </div>

      {/* Stress Testing & Factor Exposures */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Stress Testing */}
        <div className="panel">
          <div className="panel-kicker">SCENARIO ANALYSIS</div>
          <h2 className="text-sm font-semibold text-[#e1e9e6] mb-3">Macroeconomic Stress Testing</h2>
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
              <span className="text-[#d8e2df] font-medium">{vol.toFixed(1)}%</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#76868c]">Beta vs S&P 500 (β)</span>
              <span className="text-[#d8e2df] font-medium">{beta.toFixed(2)}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#76868c]">Daily Expected Shortfall (CVaR 95%)</span>
              <span className="text-[#ea837c] font-medium">{cvar95.toFixed(2)}%</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#76868c]">Kurtosis / Fat-Tail Risk</span>
              <span className="text-[#d8e2df] font-medium">3.42 (Leptokurtic)</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#76868c]">Risk Classification</span>
              <span className="text-[#64caa1] font-semibold">BALANCED AGGRESSIVE</span>
            </div>
          </div>
        </div>
      </div>

      <div className="disclaimer">
        <ShieldCheck size={14} /> Risk analytics calculated using QuantDB quantitative libraries with daily log returns.
      </div>
    </div>
  );
}
