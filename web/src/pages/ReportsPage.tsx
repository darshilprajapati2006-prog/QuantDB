import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ShieldCheck,
  Printer,
  Download,
  Share2,
  FileText,
  TrendingUp,
  Activity,
  Layers,
  CheckCircle2,
  Calendar,
} from 'lucide-react';
import { request } from '../lib/api';
import type { RiskMetrics, BacktestSummary } from '../types';

interface ReportsData {
  risk: RiskMetrics;
  backtest: BacktestSummary;
}

export function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: () => request<ReportsData>('/reports'),
  });

  const risk = data?.risk || ({} as RiskMetrics);
  const backtest = data?.backtest || ({} as BacktestSummary);

  const sortino = (risk as RiskMetrics & { sortino_ratio?: number }).sortino_ratio;
  const maxDd = risk.max_drawdown;
  const vol = risk.annualized_volatility;
  const beta = risk.beta_vs_sp500;
  const var95 = risk.var_95_daily;

  const handlePrint = () => {
    window.print();
  };

  const monthlyData: Array<{ year: number; jan: string; feb: string; mar: string; apr: string; may: string; jun: string; jul: string; aug: string; sep: string; oct: string; nov: string; dec: string; ytd: string }> = [];

  return (
    <div className="space-y-6">
      {/* Page Heading */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            ACADEMIC RESEARCH & TEARSHEETS <span className="eyebrow-sep">/</span> REPORTS
          </div>
          <h1>Quantitative Performance Tearsheet</h1>
          <p>
            Standardized institutional tearsheet detailing factor exposures, risk ratios, and simulated returns.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={handlePrint} className="outline-button">
            <Printer size={13} />
            <span>Print Tearsheet</span>
          </button>
        </div>
      </div>

      {/* Tearsheet Container (Formatted cleanly for screen & print) */}
      <div className="panel bg-[#0d1419] border-[#22333c] p-6 space-y-6">
        {/* Tearsheet Title & Meta */}
        <div className="border-b border-[#1f2d36] pb-4 flex flex-col md:flex-row md:items-center justify-between gap-2">
          <div>
            <div className="text-[10px] font-mono text-[#74d2aa] uppercase tracking-wider">
              QUANTDB RESEARCH INITIATIVE · FACTOR STRATEGY REPORT
            </div>
            <h2 className="text-xl font-bold text-[#e8f1ed] mt-1 font-sans">
              {backtest.strategy_name || 'Portfolio risk and performance summary'}
            </h2>
            <div className="text-xs text-[#708288] mt-1">
              QuantDB account metrics · Paper trading simulation
            </div>
          </div>

          <div className="text-right text-xs font-mono">
            <div className="text-[#84959b]">DATE GENERATED</div>
            <div className="text-[#d8e3df] font-bold">{new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }).toUpperCase()}</div>
          </div>
        </div>

        {/* Executive Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-[#10171d] border border-[#1f2b33] rounded-lg p-3">
            <span className="text-[10px] font-mono text-[#6c7d84] block uppercase">Annualized Return</span>
            <span className="text-lg font-bold text-[#72d2ab] font-mono mt-1 block">
              {backtest.total_return_pct == null ? '—' : `${Number(backtest.total_return_pct) >= 0 ? '+' : ''}${Number(backtest.total_return_pct).toFixed(2)}%`}
            </span>
            <span className="text-[10px] text-[#78888e] font-mono">Latest backtest return</span>
          </div>

          <div className="bg-[#10171d] border border-[#1f2b33] rounded-lg p-3">
            <span className="text-[10px] font-mono text-[#6c7d84] block uppercase">Sharpe Ratio</span>
            <span className="text-lg font-bold text-[#e5ecea] font-mono mt-1 block">
              {risk.sharpe_ratio == null ? '—' : Number(risk.sharpe_ratio).toFixed(2)}
            </span>
            <span className="text-[10px] text-[#78888e] font-mono">from selected portfolio</span>
          </div>

          <div className="bg-[#10171d] border border-[#1f2b33] rounded-lg p-3">
            <span className="text-[10px] font-mono text-[#6c7d84] block uppercase">Maximum Drawdown</span>
            <span className="text-lg font-bold text-[#ea837c] font-mono mt-1 block">
              {maxDd == null ? '—' : `${Number(maxDd).toFixed(2)}%`}
            </span>
            <span className="text-[10px] text-[#78888e] font-mono">maximum peak-to-trough decline</span>
          </div>

          <div className="bg-[#10171d] border border-[#1f2b33] rounded-lg p-3">
            <span className="text-[10px] font-mono text-[#6c7d84] block uppercase">Win Rate / PF</span>
            <span className="text-lg font-bold text-[#e5ecea] font-mono mt-1 block">
              {backtest.win_rate_pct == null ? '—' : `${Number(backtest.win_rate_pct).toFixed(1)}%`}
            </span>
            <span className="text-[10px] text-[#78888e] font-mono">Profit Factor: {backtest.profit_factor == null ? '—' : Number(backtest.profit_factor).toFixed(2)}</span>
          </div>
        </div>

        {/* Monthly Returns Matrix */}
        <div>
          <div className="text-xs font-mono text-[#76878d] uppercase mb-2.5 flex items-center gap-1.5">
            <Calendar size={13} />
            <span>Monthly Return Distribution Matrix (%)</span>
          </div>
          <div className="overflow-x-auto border border-[#1e2b33] rounded-lg">
            <table className="w-full text-center text-xs font-mono">
              <thead className="bg-[#11181e] text-[#697980] border-b border-[#1e2b33]">
                <tr>
                  <th className="py-2 px-3 text-left">Year</th>
                  <th className="py-2 px-2">Jan</th>
                  <th className="py-2 px-2">Feb</th>
                  <th className="py-2 px-2">Mar</th>
                  <th className="py-2 px-2">Apr</th>
                  <th className="py-2 px-2">May</th>
                  <th className="py-2 px-2">Jun</th>
                  <th className="py-2 px-2">Jul</th>
                  <th className="py-2 px-2">Aug</th>
                  <th className="py-2 px-2">Sep</th>
                  <th className="py-2 px-2">Oct</th>
                  <th className="py-2 px-2">Nov</th>
                  <th className="py-2 px-2">Dec</th>
                  <th className="py-2 px-3 font-bold text-[#e5ecea]">YTD</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e2b33] bg-[#0c1216]">
                {monthlyData.length === 0 && <tr><td colSpan={14} className="py-8 text-center text-[#778991]">Monthly portfolio return observations are not available yet.</td></tr>}
                {monthlyData.map((row) => (
                  <tr key={row.year} className="hover:bg-[#10171d]">
                    <td className="py-2.5 px-3 text-left font-bold text-[#e5ecea]">{row.year}</td>
                    <td className={`py-2 px-2 ${row.jan.startsWith('+') ? 'text-[#72d2ab]' : 'text-[#ea837c]'}`}>{row.jan}</td>
                    <td className={`py-2 px-2 ${row.feb.startsWith('+') ? 'text-[#72d2ab]' : 'text-[#ea837c]'}`}>{row.feb}</td>
                    <td className={`py-2 px-2 ${row.mar.startsWith('+') ? 'text-[#72d2ab]' : 'text-[#ea837c]'}`}>{row.mar}</td>
                    <td className={`py-2 px-2 ${row.apr.startsWith('+') ? 'text-[#72d2ab]' : 'text-[#ea837c]'}`}>{row.apr}</td>
                    <td className="py-2 px-2 text-[#5a6b71]">{row.may}</td>
                    <td className="py-2 px-2 text-[#5a6b71]">{row.jun}</td>
                    <td className="py-2 px-2 text-[#5a6b71]">{row.jul}</td>
                    <td className="py-2 px-2 text-[#5a6b71]">{row.aug}</td>
                    <td className="py-2 px-2 text-[#5a6b71]">{row.sep}</td>
                    <td className="py-2 px-2 text-[#5a6b71]">{row.oct}</td>
                    <td className="py-2 px-2 text-[#5a6b71]">{row.nov}</td>
                    <td className="py-2 px-2 text-[#5a6b71]">{row.dec}</td>
                    <td className="py-2.5 px-3 font-bold text-[#72d2ab]">{row.ytd}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Statistical Performance Breakdown Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-[#1f2b33] rounded-lg p-4 bg-[#10171d]">
            <h3 className="text-xs font-semibold text-[#e5ecea] uppercase tracking-wider mb-3">
              Risk & Volatility Indicators
            </h3>
            <div className="divide-y divide-[#182329] text-xs font-mono">
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">Annualized Volatility</span>
                <span className="text-[#d8e2df] font-medium">{vol == null ? '—' : `${Number(vol).toFixed(1)}%`}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">Downside Deviation</span>
                <span className="text-[#d8e2df] font-medium">—</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">Sortino Ratio</span>
                <span className="text-[#72d2ab] font-medium">{sortino == null ? '—' : Number(sortino).toFixed(2)}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">Value at Risk (95% 1-day)</span>
                <span className="text-[#ea837c] font-medium">{var95 == null ? '—' : `${Number(var95).toFixed(2)}%`}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">Calmar Ratio</span>
                <span className="text-[#d8e2df] font-medium">—</span>
              </div>
            </div>
          </div>

          <div className="border border-[#1f2b33] rounded-lg p-4 bg-[#10171d]">
            <h3 className="text-xs font-semibold text-[#e5ecea] uppercase tracking-wider mb-3">
              Market Factor Exposure
            </h3>
            <div className="divide-y divide-[#182329] text-xs font-mono">
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">Beta vs Benchmark</span>
                <span className="text-[#d8e2df] font-medium">{beta == null ? '—' : Number(beta).toFixed(2)}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">R-Squared</span>
                <span className="text-[#d8e2df] font-medium">—</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">Information Ratio</span>
                <span className="text-[#72d2ab] font-medium">—</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">Tracking Error</span>
                <span className="text-[#d8e2df] font-medium">—</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#728389]">Correlation</span>
                <span className="text-[#d8e2df] font-medium">—</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="disclaimer">
        <ShieldCheck size={14} /> Tearsheets generated automatically by QuantDB Research Service for academic and paper trading review.
      </div>
    </div>
  );
}
