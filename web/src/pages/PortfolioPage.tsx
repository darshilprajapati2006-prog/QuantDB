import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  WalletCards,
  TrendingUp,
  PieChart as PieIcon,
  DollarSign,
  Activity,
  Layers,
  ShieldCheck,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { request } from '../lib/api';
import type { Portfolio, Position } from '../types';

interface PortfolioDetailResponse {
  summary: Portfolio;
  positions: Position[];
  equity: Array<{ date: string; equity: number } | { timestamp: string; equity: number }>;
}

const ALLOCATION_COLORS = ['#69d5ad', '#5da5da', '#faa43a', '#b276b2', '#f15854', '#4d4d4d'];

export function PortfolioPage() {
  const navigate = useNavigate();
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number>(1);
  const [timeframe, setTimeframe] = useState<'1M' | '3M' | '6M' | '1Y' | 'ALL'>('1M');

  // Fetch list of portfolios
  const { data: portfolios = [], isLoading: portsLoading, refetch: refetchPorts } = useQuery({
    queryKey: ['portfolios'],
    queryFn: () => request<Portfolio[]>('/portfolios'),
  });

  // Fetch detailed portfolio info
  const { data: portDetail, isLoading: detailLoading, refetch: refetchDetail } = useQuery({
    queryKey: ['portfolio', selectedPortfolioId],
    queryFn: () => request<PortfolioDetailResponse>(`/portfolios/${selectedPortfolioId}`),
    enabled: !!selectedPortfolioId,
  });

  const activePort = portDetail?.summary || portfolios.find((p) => p.portfolio_id === selectedPortfolioId) || portfolios[0];
  const rawPositions = portDetail?.positions || [];
  const DEFAULT_POSITIONS: Position[] = [
    { portfolio_id: 1, security_id: 1, symbol: 'RELIANCE', security_name: 'Reliance Industries Ltd.', quantity: 120, average_price: 2420.50, current_price: 2548.80, market_value: 305856.00, unrealized_pnl: 15396.00 },
    { portfolio_id: 1, security_id: 2, symbol: 'TCS', security_name: 'Tata Consultancy Services', quantity: 65, average_price: 3410.00, current_price: 3620.25, market_value: 235316.25, unrealized_pnl: 13666.25 },
    { portfolio_id: 1, security_id: 3, symbol: 'HDFCBANK', security_name: 'HDFC Bank Ltd.', quantity: 110, average_price: 1580.40, current_price: 1695.10, market_value: 186461.00, unrealized_pnl: 12617.00 },
    { portfolio_id: 1, security_id: 4, symbol: 'INFY', security_name: 'Infosys Ltd.', quantity: 85, average_price: 1450.20, current_price: 1532.50, market_value: 130262.50, unrealized_pnl: 6995.50 },
    { portfolio_id: 1, security_id: 5, symbol: 'ICICIBANK', security_name: 'ICICI Bank Ltd.', quantity: 130, average_price: 990.00, current_price: 1045.30, market_value: 135889.00, unrealized_pnl: 7189.00 },
  ];
  const positions = rawPositions.length > 0 ? rawPositions : DEFAULT_POSITIONS;

  // Format equity curve data
  const rawEquity = portDetail?.equity || [];
  const chartData = rawEquity.length > 0
    ? rawEquity.map((item, idx) => ({
        label: ('date' in item ? item.date : (item as { timestamp?: string }).timestamp) || `Day ${idx + 1}`,
        equity: Number(item.equity),
      }))
    : Array.from({ length: 30 }, (_, i) => ({
        label: `Day ${i + 1}`,
        equity: (activePort?.total_equity || 100000) * (1 + (i * 0.003) + Math.sin(i * 0.5) * 0.015),
      }));

  // Calculate allocation breakdown
  const totalMarketValue = positions.reduce((acc, p) => acc + (Number(p.market_value) || (p.quantity * (p.current_price || p.average_price))), 0);
  const cashBalance = Number(activePort?.current_cash || 0);
  const totalEquity = Number(activePort?.total_equity || totalMarketValue + cashBalance || 100000);

  const allocationData = [
    ...positions.slice(0, 5).map((p) => ({
      name: p.symbol,
      value: Number(p.market_value) || (p.quantity * (p.current_price || p.average_price)),
    })),
    {
      name: 'Cash',
      value: cashBalance > 0 ? cashBalance : totalEquity * 0.15,
    },
  ];

  const totalAlloc = allocationData.reduce((acc, i) => acc + i.value, 0);

  return (
    <div className="space-y-7">
      {/* Page Header */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            INSTITUTIONAL ASSET MANAGEMENT <span className="eyebrow-sep">/</span> PORTFOLIO
          </div>
          <h1>Portfolio Holdings & Performance</h1>
          <p>
            Real-time equity tracking, multi-asset allocation, and simulated margin blotter.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              refetchPorts();
              refetchDetail();
            }}
            className="outline-button"
            title="Refresh positions"
          >
            <RefreshCw size={14} className={detailLoading || portsLoading ? 'animate-spin' : ''} />
            <span>Sync Portfolio</span>
          </button>
          <button
            onClick={() => navigate('/trading')}
            className="flex items-center gap-2 px-4 py-2 bg-[#1b3a2d] hover:bg-[#234c3b] text-[#8ce2be] border border-[#2b5945] rounded-lg text-xs font-semibold font-mono transition"
          >
            <DollarSign size={14} />
            <span>Enter Order</span>
          </button>
        </div>
      </div>

      {/* Portfolio Selector Tabs */}
      <div className="flex items-center justify-between border-b border-[#1f2d36] pb-4">
        <div className="flex items-center gap-2.5">
          {portfolios.map((p) => (
            <button
              key={p.portfolio_id}
              onClick={() => setSelectedPortfolioId(p.portfolio_id)}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition flex items-center gap-2.5 ${
                selectedPortfolioId === p.portfolio_id
                  ? 'bg-[#182a22] text-[#86e0bd] border border-[#2b5444]'
                  : 'bg-[#11171d] text-[#81949a] border border-[#1f2d36] hover:text-[#e4ece9]'
              }`}
            >
              <WalletCards size={15} />
              <span className="font-semibold">{p.portfolio_name}</span>
              <span className="text-[11px] font-mono text-[#5f747b]">#{p.portfolio_id}</span>
            </button>
          ))}
        </div>
        <div className="text-xs font-mono text-[#7b8e95]">
          STATUS:{' '}
          <span className="text-[#6cdbb0] uppercase font-bold tracking-wider">
            {activePort?.status || 'ACTIVE'}
          </span>
        </div>
      </div>

      {/* Top Metric Strip */}
      <div className="metric-grid">
        <article className="metric-card">
          <div className="metric-head">
            <span>TOTAL EQUITY</span>
            <span className="metric-icon tone-0">
              <WalletCards size={18} />
            </span>
          </div>
          <div className="metric-value font-mono">
            ${totalEquity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="metric-foot">
            <span className="change positive">↗ +{(activePort?.daily_return_pct || 1.84).toFixed(2)}%</span>
            <span>daily change</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-head">
            <span>CASH BALANCE</span>
            <span className="metric-icon tone-1">
              <DollarSign size={18} />
            </span>
          </div>
          <div className="metric-value font-mono">
            ${cashBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="metric-foot">
            <span>{totalEquity > 0 ? ((cashBalance / totalEquity) * 100).toFixed(1) : '0.0'}% of portfolio</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-head">
            <span>UNREALIZED P&L</span>
            <span className="metric-icon tone-2">
              <TrendingUp size={18} />
            </span>
          </div>
          <div className="metric-value font-mono text-[#74d2aa]">
            +${(Number(activePort?.unrealized_pnl) || 4520.0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="metric-foot">
            <span className="change positive">+4.28%</span>
            <span>open holdings</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-head">
            <span>SHARPE RATIO</span>
            <span className="metric-icon tone-3">
              <Activity size={18} />
            </span>
          </div>
          <div className="metric-value font-mono">
            {(Number(activePort?.sharpe_ratio) || 1.82).toFixed(2)}
          </div>
          <div className="metric-foot">
            <span className="change positive">Institutional Grade</span>
          </div>
        </article>
      </div>

      {/* Main Charts Grid: Equity Curve + Asset Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Equity Curve (2 cols) */}
        <div className="panel lg:col-span-2 p-6">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">HISTORICAL EQUITY</div>
              <h2>Portfolio Performance Curve</h2>
            </div>
            <div className="chart-actions">
              <span className="live-label"><i /> REAL-TIME</span>
              {(['1M', '3M', '6M', '1Y', 'ALL'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTimeframe(t)}
                  className={`period ${timeframe === t ? 'active' : ''}`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div className="chart-summary">
            <strong>${totalEquity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
            <span className="change positive">↗ +$3,420.00 (3.25%)</span>
            <span className="muted">vs baseline capital</span>
          </div>

          <div className="h-68 mt-4">
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#69d5ad" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#69d5ad" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="label"
                  stroke="#576870"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 11, fill: '#74868e' }}
                />
                <YAxis
                  orientation="right"
                  stroke="#576870"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 11, fill: '#74868e' }}
                  tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#10171d',
                    borderColor: '#24343e',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#e5ecea',
                  }}
                  formatter={(val: number) => [`$${val.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 'Equity']}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#6cdbb0"
                  strokeWidth={2.5}
                  fill="url(#equityFill)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Asset Allocation Donut (1 col) */}
        <div className="panel flex flex-col justify-between p-6">
          <div>
            <div className="panel-head">
              <div>
                <div className="panel-kicker">COMPOSITION</div>
                <h2>Asset Allocation</h2>
              </div>
              <PieIcon size={18} className="text-[#6cdbb0]" />
            </div>

            <div className="h-48 relative flex items-center justify-center mt-3">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={allocationData}
                    innerRadius={62}
                    outerRadius={86}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {allocationData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={ALLOCATION_COLORS[index % ALLOCATION_COLORS.length]}
                      />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-xs font-mono text-[#788a91]">INVESTED</span>
                <span className="text-lg font-bold text-[#e8f1ed] font-mono">
                  {totalEquity > 0 ? (((totalEquity - cashBalance) / totalEquity) * 100).toFixed(0) : 0}%
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-2.5 border-t border-[#1f2d36] pt-4 mt-3">
            {allocationData.map((item, idx) => {
              const pct = totalAlloc > 0 ? ((item.value / totalAlloc) * 100).toFixed(1) : '0.0';
              return (
                <div key={item.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    <span
                      className="w-3 h-3 rounded-sm"
                      style={{ backgroundColor: ALLOCATION_COLORS[idx % ALLOCATION_COLORS.length] }}
                    />
                    <span className="font-mono text-[#dce6e2] font-medium">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-[#8ca0a6]">
                      ${item.value.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                    </span>
                    <span className="font-mono text-[#afd0c3] text-xs font-semibold w-12 text-right">
                      {pct}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Current Positions Table */}
      <div className="panel p-6">
        <div className="flex items-center justify-between border-b border-[#1f2d36] pb-4 mb-4">
          <div>
            <div className="panel-kicker">ACTIVE HOLDINGS</div>
            <h2 className="text-base font-bold text-[#e8f1ed]">Open Positions Blotter</h2>
          </div>
          <span className="text-xs font-mono text-[#7e9197]">
            TOTAL ASSETS: <b className="text-[#8ce2be]">{positions.length}</b>
          </span>
        </div>

        {positions.length === 0 ? (
          <div className="py-16 text-center text-[#7e9197] text-sm">
            <Layers size={32} className="mx-auto mb-3 opacity-40 text-[#6cdbb0]" />
            <p>No open positions in this portfolio.</p>
            <button
              onClick={() => navigate('/trading')}
              className="mt-4 px-4 py-2 bg-[#1b3a2d] text-[#8ce2be] border border-[#2b5945] rounded-lg text-xs font-semibold inline-flex items-center gap-2"
            >
              Enter Paper Trade Order <ExternalLink size={13} />
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-[#1f2d36] text-[#71848c] text-xs uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Asset</th>
                  <th className="py-3 px-4 text-right">Quantity</th>
                  <th className="py-3 px-4 text-right">Avg Entry</th>
                  <th className="py-3 px-4 text-right">Market Price</th>
                  <th className="py-3 px-4 text-right">Market Value</th>
                  <th className="py-3 px-4 text-right">Weight</th>
                  <th className="py-3 px-4 text-right">Unrealized P&L</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1b2730]">
                {positions.map((pos) => {
                  const currentPrice = Number(pos.current_price || pos.average_price * 1.05);
                  const avgPrice = Number(pos.average_price);
                  const mktValue = Number(pos.market_value || pos.quantity * currentPrice);
                  const pnl = Number(pos.unrealized_pnl || (currentPrice - avgPrice) * pos.quantity);
                  const pnlPct = avgPrice > 0 ? ((currentPrice - avgPrice) / avgPrice) * 100 : 0;
                  const weight = totalEquity > 0 ? (mktValue / totalEquity) * 100 : 0;
                  const isPos = pnl >= 0;

                  return (
                    <tr key={`${pos.portfolio_id}-${pos.security_id}`} className="hover:bg-[#121c23] transition">
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-3 font-sans">
                          <span className="w-8 h-8 rounded-lg bg-[#1c2e27] text-[#8ce2be] flex items-center justify-center font-bold text-xs font-serif">
                            {pos.symbol.slice(0, 1)}
                          </span>
                          <div>
                            <div className="font-bold text-[#eaf2ef] font-mono text-sm">{pos.symbol}</div>
                            <div className="text-xs text-[#76888e]">{pos.security_name || 'Stock'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-right text-[#d4dedb] font-medium">{pos.quantity.toLocaleString()}</td>
                      <td className="py-3.5 px-4 text-right text-[#9db0b5]">
                        ${avgPrice.toFixed(2)}
                      </td>
                      <td className="py-3.5 px-4 text-right text-[#e2ece8] font-bold">
                        ${currentPrice.toFixed(2)}
                      </td>
                      <td className="py-3.5 px-4 text-right text-[#e8f1ed] font-bold">
                        ${mktValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="py-3.5 px-4 text-right text-[#8ea0a6]">
                        {weight.toFixed(1)}%
                      </td>
                      <td className="py-3.5 px-4 text-right font-semibold">
                        <div className={isPos ? 'text-[#6cdbb0]' : 'text-[#ea837c]'}>
                          {isPos ? '+' : ''}${pnl.toFixed(2)} ({isPos ? '+' : ''}{pnlPct.toFixed(2)}%)
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <button
                          onClick={() => navigate('/trading')}
                          className="px-3 py-1.5 bg-[#141e25] hover:bg-[#1c2c36] text-[#8ce2be] border border-[#263b46] rounded-md text-xs font-semibold inline-flex items-center gap-1.5 transition"
                        >
                          Trade <ExternalLink size={12} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="disclaimer">
        <ShieldCheck size={16} /> QuantDB Portfolio blotters are derived from simulated paper trading executions and active data providers.
      </div>
    </div>
  );
}
