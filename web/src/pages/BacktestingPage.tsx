import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  BarChart3,
  Play,
  TrendingUp,
  TrendingDown,
  Calendar,
  DollarSign,
  Activity,
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  LineChart,
  Line,
} from 'recharts';
import { request } from '../lib/api';
import type { Strategy, Security, BacktestSummary } from '../types';

interface BacktestResultData {
  summary?: BacktestSummary;
  equity_curve?: Array<{ date: string; equity: number; benchmark?: number }>;
  trades?: Array<{
    date: string;
    symbol: string;
    side: 'BUY' | 'SELL';
    price: number;
    shares: number;
    pnl?: number;
  }>;
  [key: string]: unknown;
}

export function BacktestingPage() {
  // Form parameters
  const [strategyId, setStrategyId] = useState<number>(0);
  const [securityId, setSecurityId] = useState<number>(0);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [slippagePct, setSlippagePct] = useState<number>(0.05);

  // Queries
  const { data: strategies = [] } = useQuery({
    queryKey: ['strategies'],
    queryFn: () => request<Strategy[]>('/strategies'),
  });

  const { data: securities = [] } = useQuery({
    queryKey: ['securities'],
    queryFn: () => request<Security[]>('/securities'),
  });

  const { data: initialReport } = useQuery({
    queryKey: ['reports'],
    queryFn: () => request<{ backtest: BacktestSummary }>('/reports'),
  });

  // State for current results
  const [result, setResult] = useState<BacktestResultData | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const activeSec = securities.find((s) => s.security_id === securityId) || securities[0];
  const activeStrat = strategies.find((s) => s.strategy_id === strategyId) || strategies[0];
  React.useEffect(() => {
    if (!strategyId && strategies.length) setStrategyId(strategies[0].strategy_id);
    if (!securityId && securities.length) setSecurityId(securities[0].security_id);
  }, [strategyId, securityId, strategies, securities]);

  // Backtest Mutation
  const runBacktest = useMutation({
    mutationFn: async () => {
      setErrorMessage(null);
      if (!activeSec || !activeStrat || !startDate || !endDate) throw new Error('Choose a strategy, security, start date, and end date.');
      const symbol = activeSec.symbol;
      const payload = {
        strategy_id: Number(strategyId),
        security_id: Number(securityId),
        symbol,
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        initial_capital: Number(initialCapital),
        transaction_cost_pct: Number(slippagePct),
        parameters: {},
      };

      const res = await request<BacktestResultData>('/backtests', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      return res;
    },
    onSuccess: (data) => {
      setResult(data);
    },
    onError: (err: Error) => {
      setErrorMessage(err.message);
    },
  });

  const summary: BacktestSummary = result?.summary ?? initialReport?.backtest ?? {};
  const equityPoints = result?.equity_curve || [];
  const backtestTrades = result?.trades || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            HISTORICAL SIMULATION ENGINE <span className="eyebrow-sep">/</span> BACKTESTING
          </div>
          <h1>Quantitative Backtesting & Validation</h1>
          <p>
            Evaluate systematic strategies against verified tick & OHLCV history with transaction friction modeling.
          </p>
        </div>

          <span className="api-chip">
          <span className="status-dot" /> {activeStrat && activeSec ? 'ENGINE READY' : 'WAITING FOR DATA'}
        </span>
      </div>

      {/* Interactive Backtest Setup Form */}
      <div className="panel">
        <div className="flex items-center justify-between border-b border-[#1f282e] pb-3 mb-4">
          <div>
            <div className="panel-kicker">CONFIGURATION</div>
            <h2 className="text-sm font-semibold text-[#e1e9e6]">Simulation Parameters</h2>
          </div>
          <span className="text-xs font-mono text-[#74858a]">AIVEN MYSQL TICK REPLAY</span>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!activeSec || !activeStrat || !startDate || !endDate) return;
            runBacktest.mutate();
          }}
          className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3 items-end"
        >
          {/* Strategy */}
          <div>
            <label className="block text-[10px] font-mono text-[#77878d] mb-1 uppercase">Strategy</label>
            <select
              value={strategyId}
              onChange={(e) => setStrategyId(Number(e.target.value))}
              className="w-full h-8 bg-[#0c1216] border border-[#222d34] rounded text-xs text-[#dbe5e1] px-2 focus:border-[#487a66]"
            >
              {strategies.map((s) => (
                <option key={s.strategy_id} value={s.strategy_id}>
                  {s.strategy_name}
                </option>
              ))}
            </select>
          </div>

          {/* Instrument */}
          <div>
            <label className="block text-[10px] font-mono text-[#77878d] mb-1 uppercase">Instrument</label>
            <select
              value={securityId}
              onChange={(e) => setSecurityId(Number(e.target.value))}
              className="w-full h-8 bg-[#0c1216] border border-[#222d34] rounded text-xs text-[#dbe5e1] px-2 focus:border-[#487a66]"
            >
              {securities.map((s) => (
                <option key={s.security_id} value={s.security_id}>
                  {s.symbol} · {s.security_name}
                </option>
              ))}
            </select>
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-[10px] font-mono text-[#77878d] mb-1 uppercase">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full h-8 bg-[#0c1216] border border-[#222d34] rounded text-xs text-[#dbe5e1] px-2 focus:border-[#487a66]"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-[10px] font-mono text-[#77878d] mb-1 uppercase">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full h-8 bg-[#0c1216] border border-[#222d34] rounded text-xs text-[#dbe5e1] px-2 focus:border-[#487a66]"
            />
          </div>

          {/* Initial Capital */}
          <div>
            <label className="block text-[10px] font-mono text-[#77878d] mb-1 uppercase">Initial ($)</label>
            <input
              type="number"
              min="1000"
              step="5000"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              className="w-full h-8 bg-[#0c1216] border border-[#222d34] rounded text-xs text-[#dbe5e1] px-2 focus:border-[#487a66]"
            />
          </div>

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={!activeSec || !activeStrat || !startDate || !endDate || runBacktest.isPending}
              className="w-full h-8 bg-[#1b3a2d] hover:bg-[#234c3b] disabled:opacity-50 text-[#86d9b2] border border-[#2b5945] rounded text-xs font-medium transition flex items-center justify-center gap-1.5"
            >
              <Play size={11} fill="currentColor" />
              <span>{runBacktest.isPending ? 'Simulating…' : 'Run Simulation'}</span>
            </button>
          </div>
        </form>

        {errorMessage && (
          <div className="mt-3 p-2.5 bg-[#261817] border border-[#482826] rounded text-xs text-[#e58d83] flex items-center gap-2">
            <AlertCircle size={14} />
            <span>Backtest failed: {errorMessage}</span>
          </div>
        )}
      </div>

      {/* KPI Metric Strip */}
      <div className="metric-grid">
        <article className="metric-card">
          <div className="metric-head">
            <span>TOTAL RETURN</span>
            <span className="metric-icon tone-0">
              <TrendingUp size={16} />
            </span>
          </div>
          <div className="metric-value font-mono text-[#69d5ad]">
            {summary.total_return_pct == null ? '—' : `${Number(summary.total_return_pct) >= 0 ? '+' : ''}${Number(summary.total_return_pct).toFixed(2)}%`}
          </div>
          <div className="metric-foot">
            <span className="change positive">{summary.total_return_pct == null || summary.initial_capital == null ? '—' : `$${(Number(summary.initial_capital) * Number(summary.total_return_pct) / 100).toLocaleString()}`}</span>
            <span>return from starting capital</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-head">
            <span>SHARPE RATIO</span>
            <span className="metric-icon tone-1">
              <Activity size={16} />
            </span>
          </div>
          <div className="metric-value font-mono">
            {summary.sharpe_ratio == null ? '—' : Number(summary.sharpe_ratio).toFixed(2)}
          </div>
          <div className="metric-foot">
            <span className="change positive">Risk-adjusted return</span>
            <span>QuantDB metrics</span>
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
            {summary.max_drawdown_pct == null ? '—' : `${Number(summary.max_drawdown_pct).toFixed(2)}%`}
          </div>
          <div className="metric-foot">
            <span className="change negative">Peak to Trough</span>
            <span>maximum peak-to-trough decline</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-head">
            <span>WIN RATE / FACTOR</span>
            <span className="metric-icon tone-3">
              <BarChart3 size={16} />
            </span>
          </div>
          <div className="metric-value font-mono">
            {summary.win_rate_pct == null ? '—' : `${Number(summary.win_rate_pct).toFixed(1)}%`}
          </div>
          <div className="metric-foot">
            <span className="change positive">PF: {summary.profit_factor == null ? '—' : Number(summary.profit_factor).toFixed(2)}</span>
            <span>{summary.total_trades ?? '—'} Trades</span>
          </div>
        </article>
      </div>

      {/* Cumulative Return Chart vs Benchmark */}
      <div className="panel">
        <div className="panel-head">
          <div>
            <div className="panel-kicker">SIMULATED EQUITY TRAJECTORY</div>
            <h2>Strategy Cumulative Return vs Benchmark</h2>
          </div>
          <div className="chart-legend">
            <span>
              <i className="legend-line" /> Strategy Curve
            </span>
            <span>
              <i className="legend-dash" /> Buy & Hold
            </span>
          </div>
        </div>

        <div className="h-72 mt-4">
          {equityPoints.length === 0 && <div className="empty-panel-state">Run a backtest to render its portfolio curve and benchmark comparison.</div>}
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={equityPoints} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="backtestFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#69d5ad" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#69d5ad" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1e282e" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="date"
                stroke="#546369"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 10, fill: '#6e7e85' }}
              />
              <YAxis
                orientation="right"
                stroke="#546369"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 10, fill: '#6e7e85' }}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#10161b',
                  borderColor: '#222f36',
                  borderRadius: '8px',
                  fontSize: '11px',
                  color: '#e5ecea',
                }}
                formatter={(val: number) => [`$${val.toLocaleString()}`, 'Simulated Equity']}
              />
              <Area
                type="monotone"
                dataKey="equity"
                stroke="#68d1a9"
                strokeWidth={2}
                fill="url(#backtestFill)"
              />
              <Line
                type="monotone"
                dataKey="benchmark"
                stroke="#778891"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tearsheet Breakdown Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="panel">
          <div className="panel-kicker">TRADE EXECUTION STATISTICS</div>
          <h2 className="text-sm font-semibold text-[#e1e9e6] mb-3">Model Performance Matrix</h2>
          <div className="divide-y divide-[#1b252b] text-xs font-mono">
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Strategy Name</span>
              <span className="text-[#d8e2df] font-sans font-medium">{summary.strategy_name || activeStrat?.strategy_name}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Evaluated Security</span>
              <span className="text-[#d8e2df]">{summary.symbol || activeSec?.symbol}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Starting Capital</span>
              <span className="text-[#d8e2df]">{summary.initial_capital == null ? '—' : `$${Number(summary.initial_capital).toLocaleString()}`}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Ending Capital</span>
              <span className="text-[#69d5ad] font-semibold">{summary.final_capital == null ? '—' : `$${Number(summary.final_capital).toLocaleString()}`}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Slippage / Fee Model</span>
              <span className="text-[#d8e2df]">{slippagePct}% per order</span>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-kicker">RISK & RATIOS</div>
          <h2 className="text-sm font-semibold text-[#e1e9e6] mb-3">Risk-Adjusted Parameters</h2>
          <div className="divide-y divide-[#1b252b] text-xs font-mono">
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Annualized Sharpe</span>
              <span className="text-[#69d5ad]">{summary.sharpe_ratio == null ? '—' : Number(summary.sharpe_ratio).toFixed(2)}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Profit Factor</span>
              <span className="text-[#d8e2df]">{summary.profit_factor == null ? '—' : Number(summary.profit_factor).toFixed(2)}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Maximum Drawdown</span>
              <span className="text-[#ea837c]">{summary.max_drawdown_pct == null ? '—' : `${Number(summary.max_drawdown_pct).toFixed(2)}%`}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Win / Loss Ratio</span>
              <span className="text-[#d8e2df]">—</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-[#78888e]">Execution Engine</span>
              <span className="text-[#84d9b3]">QuantDB simulation service</span>
            </div>
          </div>
        </div>
      </div>

      {/* Simulated Trade Execution Blotter */}
      <div className="panel">
        <div className="panel-head">
          <div>
            <div className="panel-kicker">EXECUTION LOG</div>
            <h2>Simulated Strategy Fills & Trade Journal</h2>
          </div>
          <span className="api-chip">
            <Clock size={11} /> {backtestTrades.length} BACKTEST FILLS
          </span>
        </div>

        <div className="table-wrapper mt-3">
          <table className="data-table">
            <thead>
              <tr>
                <th>TIMESTAMP</th>
                <th>TICKER</th>
                <th>ACTION</th>
                <th className="text-right">PRICE</th>
                <th className="text-right">QTY</th>
                <th className="text-right">REALIZED P&L</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {backtestTrades.length === 0 && <tr><td colSpan={7} className="py-8 text-center text-[#7d8f96]">Run a backtest to see its simulated fills.</td></tr>}
              {backtestTrades.map((trade, i) => {
                const pnl = Number(trade.pnl ?? 0);
                return <tr key={`${trade.date}-${i}`}>
                  <td className="font-mono text-xs text-[#7d8f96]">{trade.date}</td>
                  <td className="font-semibold text-xs text-[#dbe5e2]">{trade.symbol}</td>
                  <td><span className={`badge ${trade.side === 'BUY' ? 'badge-green' : 'badge-red'}`}>{trade.side}</span></td>
                  <td className="text-right font-mono text-xs">${Number(trade.price).toFixed(2)}</td>
                  <td className="text-right font-mono text-xs">{trade.shares}</td>
                  <td className={`text-right font-mono text-xs font-semibold ${pnl >= 0 ? 'text-[#69d5ad]' : 'text-[#ea837c]'}`}>{trade.pnl == null ? '—' : `${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`}</td>
                  <td><span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#162229] text-[#7d8f96] border border-[#24353f]">SIMULATED</span></td>
                </tr>;
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="disclaimer">
        <ShieldCheck size={14} /> Backtests simulate historical behavior with past price series. Past performance does not guarantee future results.
      </div>
    </div>
  );
}
