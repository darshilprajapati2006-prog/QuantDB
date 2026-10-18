import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  BarChart2,
  Calendar,
  Layers,
  Search,
  RefreshCw,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  ShieldCheck,
} from 'lucide-react';
import { request } from '../lib/api';
import type { Security, MarketDataPoint } from '../types';

export function MarketDataPage() {
  const [selectedSecId, setSelectedSecId] = useState<number>(1);
  const [timeframe, setTimeframe] = useState<string>('ALL');

  // Fetch securities
  const { data: securities = [], isLoading: secLoading } = useQuery({
    queryKey: ['securities'],
    queryFn: () => request<Security[]>('/securities'),
  });

  // Selected security
  const activeSec = securities.find((s) => s.security_id === selectedSecId) || securities[0];

  // Fetch market data for active security
  const {
    data: marketData = [],
    isLoading: mktLoading,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['market-data', activeSec?.security_id, activeSec?.symbol],
    queryFn: () =>
      request<MarketDataPoint[]>(
        `/market-data/${activeSec?.security_id || 1}?symbol=${activeSec?.symbol || 'RELIANCE'}&days=365`
      ),
    enabled: !!activeSec,
  });

  const latest = marketData.length > 0 ? marketData[marketData.length - 1] : null;
  const previous = marketData.length > 1 ? marketData[marketData.length - 2] : latest;

  const priceChange = latest && previous ? latest.close_price - previous.close_price : 0;
  const priceChangePct =
    latest && previous && previous.close_price > 0
      ? (priceChange / previous.close_price) * 100
      : 0;
  const isUp = priceChange >= 0;

  // Chart data formatting
  const chartData = marketData.map((d) => ({
    date: d.timestamp ? d.timestamp.slice(0, 10) : '',
    close: Number(d.close_price),
    open: Number(d.open_price),
    high: Number(d.high_price),
    low: Number(d.low_price),
    volume: Number(d.volume),
  }));

  return (
    <div className="space-y-7">
      {/* Page Header */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            QUANTDB RESEARCH <span className="eyebrow-sep">/</span> MARKET DATA
          </div>
          <h1 className="flex items-center gap-3">
            <span>Market Data Terminal</span>
            {activeSec && (
              <span className="text-xs px-2.5 py-1 rounded-md bg-[#162A25] text-[#76D2AE] border border-[#2A4E43] font-mono">
                {activeSec.symbol}
              </span>
            )}
          </h1>
          <p>
            High-resolution OHLCV price series, spread dynamics & quote archives from Aiven MySQL.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono bg-[#11171C] hover:bg-[#162026] text-[#A6B5B3] border border-[#202B31] rounded-md transition"
          >
            <RefreshCw size={13} className={isFetching ? 'animate-spin text-[#06B6D4]' : ''} />
            <span>Sync Live</span>
          </button>
        </div>
      </div>

      {/* Instrument Selector & Quick Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Instrument Dropdown */}
        <div className="bg-[#11171C] border border-[#202B31] rounded-lg p-3">
          <label className="text-[10px] font-mono uppercase text-[#718087] block mb-1.5">
            Active Instrument
          </label>
          {secLoading ? (
            <div className="text-xs text-[#718087] animate-pulse">Loading securities...</div>
          ) : (
            <select
              value={activeSec?.security_id || 1}
              onChange={(e) => setSelectedSecId(Number(e.target.value))}
              className="w-full bg-[#0B1015] border border-[#2A353A] rounded-md px-2.5 py-1.5 text-xs text-[#E5ECEA] font-medium focus:outline-none focus:border-[#06B6D4]"
            >
              {securities.map((sec) => (
                <option key={sec.security_id} value={sec.security_id}>
                  {sec.symbol} — {sec.security_name} ({sec.currency})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Current Price Card */}
        <div className="bg-[#11171C] border border-[#202B31] rounded-lg p-3">
          <span className="text-[10px] font-mono uppercase text-[#718087] block">Last Close Price</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-xl font-bold font-mono text-[#F0F5F2]">
              {latest ? `$${Number(latest.close_price).toFixed(2)}` : '$—'}
            </span>
            <span
              className={`text-xs font-mono font-semibold flex items-center ${
                isUp ? 'text-[#10B981]' : 'text-[#EF4444]'
              }`}
            >
              {isUp ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
              {priceChangePct >= 0 ? '+' : ''}
              {priceChangePct.toFixed(2)}%
            </span>
          </div>
          <span className="text-[10px] text-[#6B7B81] mt-0.5 block">
            {latest?.timestamp ? `As of ${latest.timestamp.slice(0, 16)}` : 'Real-time observation'}
          </span>
        </div>

        {/* 24h High / Low */}
        <div className="bg-[#11171C] border border-[#202B31] rounded-lg p-3">
          <span className="text-[10px] font-mono uppercase text-[#718087] block">Session Range</span>
          <div className="flex items-center justify-between text-xs font-mono mt-1 text-[#E5ECEA]">
            <span>Low: ${latest ? Number(latest.low_price).toFixed(2) : '—'}</span>
            <span className="text-[#6B7B81]">|</span>
            <span>High: ${latest ? Number(latest.high_price).toFixed(2) : '—'}</span>
          </div>
          <div className="w-full bg-[#1A242B] rounded-full h-1.5 mt-2 overflow-hidden">
            <div className="bg-gradient-to-r from-[#06B6D4] to-[#10B981] h-1.5 rounded-full w-2/3"></div>
          </div>
        </div>

        {/* Volume & Microstructure */}
        <div className="bg-[#11171C] border border-[#202B31] rounded-lg p-3">
          <span className="text-[10px] font-mono uppercase text-[#718087] block">Trading Volume</span>
          <div className="text-xl font-bold font-mono text-[#06B6D4] mt-1">
            {latest?.volume ? Number(latest.volume).toLocaleString() : '—'}
          </div>
          <span className="text-[10px] text-[#6B7B81] block mt-0.5">
            Spread: ${latest?.spread ? Number(latest.spread).toFixed(4) : '0.05'} (
            {latest?.relative_spread_bps ? `${Number(latest.relative_spread_bps).toFixed(1)} bps` : '2.1 bps'}
            )
          </span>
        </div>
      </div>

      {/* Main Interactive Chart Section */}
      <div className="bg-[#11171C] border border-[#202B31] rounded-lg p-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1C252B]">
          <div className="flex items-center gap-3">
            <BarChart2 size={16} className="text-[#06B6D4]" />
            <h2 className="text-sm font-semibold text-[#F0F5F2] uppercase tracking-wide">
              {activeSec?.symbol} — Historical Price Evolution
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-[#1A2522] text-[#76D2AE] font-mono">
              ● 1D INTERVAL
            </span>
          </div>

          <div className="flex items-center gap-1 bg-[#0B1015] p-1 rounded-md border border-[#1E293B]">
            {['1W', '1M', '3M', '6M', '1Y', 'ALL'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2.5 py-1 text-[10px] font-mono rounded transition ${
                  timeframe === tf
                    ? 'bg-[#1E293B] text-[#06B6D4] font-bold shadow-sm'
                    : 'text-[#718087] hover:text-[#E5ECEA]'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Price Chart */}
        <div className="h-64 sm:h-80 w-full mt-4">
          {mktLoading ? (
            <div className="h-full flex items-center justify-center text-xs text-[#718087] font-mono">
              Fetching time-series bars from Aiven MySQL...
            </div>
          ) : chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-[#718087] font-mono">
              No historical bars available for {activeSec?.symbol}.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1E293B" vertical={false} strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#64748B', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                />
                <YAxis
                  orientation="right"
                  domain={['auto', 'auto']}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#64748B', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                  tickFormatter={(val) => `$${val}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    border: '1px solid #1E293B',
                    borderRadius: '6px',
                    fontSize: '11px',
                    fontFamily: 'JetBrains Mono',
                    color: '#F8FAFC',
                  }}
                  formatter={(val: number) => [`$${val.toFixed(2)}`, 'Close Price']}
                  labelFormatter={(lbl) => `Date: ${lbl}`}
                />
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke="#06B6D4"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#priceGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Volume Subplot */}
        {chartData.length > 0 && (
          <div className="h-20 w-full mt-2 pt-2 border-t border-[#1C252B]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 0, right: 10, left: -15, bottom: 0 }}>
                <XAxis dataKey="date" hide />
                <YAxis orientation="right" hide domain={[0, 'auto']} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    border: '1px solid #1E293B',
                    borderRadius: '6px',
                    fontSize: '10px',
                    fontFamily: 'JetBrains Mono',
                  }}
                  formatter={(val: number) => [val.toLocaleString(), 'Volume']}
                />
                <Bar dataKey="volume" fill="#3B82F6" opacity={0.6} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Historical Data Table */}
      <div className="bg-[#11171C] border border-[#202B31] rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Layers size={15} className="text-[#06B6D4]" />
            <h3 className="text-xs font-semibold text-[#F0F5F2] uppercase font-mono tracking-wider">
              OHLCV Quote Records ({marketData.length} Observations)
            </h3>
          </div>
          <span className="text-[10px] text-[#6B7B81] font-mono">
            Table: <code className="text-[#38BDF8]">market_data</code>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-[#1F2937] text-[10px] text-[#718087] uppercase tracking-wider">
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3 text-right">Open</th>
                <th className="py-2.5 px-3 text-right">High</th>
                <th className="py-2.5 px-3 text-right">Low</th>
                <th className="py-2.5 px-3 text-right">Close</th>
                <th className="py-2.5 px-3 text-right">Volume</th>
                <th className="py-2.5 px-3 text-right">Bid / Ask</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#182126] text-[#DCE5E1]">
              {marketData.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-4 text-center text-[#718087]">
                    No rows to display.
                  </td>
                </tr>
              ) : (
                marketData.slice(-15).reverse().map((row, idx) => {
                  const isRowUp = row.close_price >= row.open_price;
                  return (
                    <tr key={idx} className="hover:bg-[#162026] transition">
                      <td className="py-2.5 px-3 text-[#A6B5B3]">
                        {row.timestamp ? row.timestamp.replace('T', ' ').slice(0, 16) : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right">${Number(row.open_price).toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-right text-[#10B981]">
                        ${Number(row.high_price).toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-[#EF4444]">
                        ${Number(row.low_price).toFixed(2)}
                      </td>
                      <td
                        className={`py-2.5 px-3 text-right font-bold ${
                          isRowUp ? 'text-[#10B981]' : 'text-[#EF4444]'
                        }`}
                      >
                        ${Number(row.close_price).toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-[#A6B5B3]">
                        {Number(row.volume).toLocaleString()}
                      </td>
                      <td className="py-2.5 px-3 text-right text-[#718087]">
                        ${Number(row.bid_price || row.close_price * 0.999).toFixed(2)} / $
                        {Number(row.ask_price || row.close_price * 1.001).toFixed(2)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
export default MarketDataPage;
