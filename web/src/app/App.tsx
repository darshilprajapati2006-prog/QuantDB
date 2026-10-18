import { useState } from 'react';
import { NavLink, Route, Routes, useLocation } from 'react-router-dom';
import {
  Activity,
  ArrowUpRight,
  BarChart3,
  Bell,
  CandlestickChart,
  ChevronDown,
  CircleHelp,
  Database,
  FlaskConical,
  Gauge,
  LayoutDashboard,
  Menu,
  Search,
  Settings2,
  ShieldCheck,
  WalletCards,
  X,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { request } from '../lib/api';
import type { Health, OverviewData, Quote } from '../types';

// Page Imports
import { MarketDataPage } from '../pages/MarketDataPage';
import { SecuritiesPage } from '../pages/SecuritiesPage';
import { TradingPage } from '../pages/TradingPage';
import { PortfolioPage } from '../pages/PortfolioPage';
import { StrategiesPage } from '../pages/StrategiesPage';
import { BacktestingPage } from '../pages/BacktestingPage';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { DatabaseExplorerPage } from '../pages/DatabaseExplorerPage';
import { HealthPage } from '../pages/HealthPage';
import { ReportsPage } from '../pages/ReportsPage';
import { ErrorBoundary } from '../components/ErrorBoundary';

const nav = [
  {
    label: 'WORKSPACE',
    items: [
      ['Overview', LayoutDashboard, '/'],
      ['Market data', CandlestickChart, '/market-data'],
      ['Securities', Search, '/securities'],
      ['Paper trading', Activity, '/trading'],
      ['Portfolio', WalletCards, '/portfolio'],
    ],
  },
  {
    label: 'RESEARCH',
    items: [
      ['Strategies', FlaskConical, '/strategies'],
      ['Backtesting', BarChart3, '/backtesting'],
      ['Risk analytics', Gauge, '/analytics'],
      ['Reports', ShieldCheck, '/reports'],
    ],
  },
  {
    label: 'PLATFORM',
    items: [
      ['Database explorer', Database, '/database'],
      ['System health', Settings2, '/health'],
    ],
  },
] as const;

const pathTitles: Record<string, string> = {
  '/': 'Overview',
  '/market-data': 'Market Data',
  '/securities': 'Securities Catalog',
  '/trading': 'Paper Trading',
  '/portfolio': 'Portfolio Holdings',
  '/strategies': 'Strategy Catalog',
  '/backtesting': 'Backtesting Engine',
  '/analytics': 'Risk Analytics',
  '/reports': 'Research Reports',
  '/database': 'Database Explorer',
  '/health': 'System Health',
};

const fallback: OverviewData = { market: [], portfolios: [], health: {}, risk: {}, backtest: {} };
const fallbackQuotes: Quote[] = [
  { symbol: 'NIFTY 50', price: 24192.35, change_pct: 0.82 },
  { symbol: 'S&P 500', price: 5842.47, change_pct: 0.43 },
  { symbol: 'NASDAQ', price: 18472.91, change_pct: -0.28 },
  { symbol: 'GOLD', price: 2748.2, change_pct: 0.16 },
];
const history = Array.from({ length: 32 }, (_, i) => ({
  d: `${String(i + 1).padStart(2, '0')}`,
  value: 100 + i * 1.75 + Math.sin(i * 0.6) * 8 + Math.cos(i * 0.21) * 4,
}));
const money = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);

function App() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const { data = fallback, isError, isLoading } = useQuery({
    queryKey: ['overview'],
    queryFn: () => request<OverviewData>('/overview'),
  });

  const h = data.health as Health;
  const quotes = data.market?.length ? data.market : fallbackQuotes;
  const currentTitle = pathTitles[location.pathname] || 'Research Workspace';

  return (
    <div className="shell">
      <aside className={`sidebar ${open ? 'show' : ''}`}>
        <div className="brand">
          <span className="brand-mark">
            <Activity size={20} />
          </span>
          <span>
            quant<span className="brand-light">db</span>
            <small>RESEARCH TERMINAL</small>
          </span>
          <button className="icon-button close-menu" onClick={() => setOpen(false)}>
            <X size={18} />
          </button>
        </div>

        <div className="workspace-select">
          <span className="workspace-icon">QD</span>
          <span>
            <b>QuantDB Research</b>
            <small>Personal workspace</small>
          </span>
          <ChevronDown size={15} />
        </div>

        {nav.map((group) => (
          <div className="nav-group" key={group.label}>
            <div className="nav-label">{group.label}</div>
            {group.items.map(([label, Icon, path]) => (
              <NavLink
                end={path === '/'}
                to={path}
                key={label}
                onClick={() => setOpen(false)}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <Icon size={17} />
                <span>{label}</span>
                {label === 'Paper trading' && <span className="nav-dot" />}
              </NavLink>
            ))}
          </div>
        ))}

        <div className="sidebar-bottom">
          <NavLink to="/health" className="mode-card block hover:border-[#3b574a] transition">
            <span className="status-dot" />
            <div>
              <b>{h.data_mode || 'REAL'} MODE</b>
              <small>Aiven Cloud MySQL 8.0</small>
            </div>
            <ChevronDown size={14} />
          </NavLink>
          <div className="user-row">
            <div className="avatar">DP</div>
            <div>
              <b>Darshil Prajapati</b>
              <small>Administrator</small>
            </div>
            <ChevronDown size={15} />
          </div>
        </div>
      </aside>

      {open && <button className="scrim" aria-label="Close menu" onClick={() => setOpen(false)} />}

      <main className="main">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setOpen(true)}>
            <Menu size={19} />
          </button>
          <div className="crumb">
            <span>Workspace</span>
            <span className="slash">/</span>
            <b>{currentTitle}</b>
          </div>
          <div className="top-actions">
            <div className="market-status">
              <span className="status-dot" />
              LIVE DATA <i>·</i> AIVEN CLOUD
            </div>
            <button className="search-box">
              <Search size={15} />
              <span>Search instruments...</span>
              <kbd>⌘ K</kbd>
            </button>
            <button className="icon-button notify">
              <Bell size={18} />
              <i />
            </button>
            <div className="top-avatar">DP</div>
          </div>
        </header>

        <div className="content">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Overview data={data} quotes={quotes} loading={isLoading} error={isError} />} />
              <Route path="/market-data" element={<MarketDataPage />} />
              <Route path="/securities" element={<SecuritiesPage />} />
              <Route path="/trading" element={<TradingPage />} />
              <Route path="/portfolio" element={<PortfolioPage />} />
              <Route path="/strategies" element={<StrategiesPage />} />
              <Route path="/backtesting" element={<BacktestingPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/database" element={<DatabaseExplorerPage />} />
              <Route path="/health" element={<HealthPage />} />
              <Route path="*" element={<Overview data={data} quotes={quotes} loading={isLoading} error={isError} />} />
            </Routes>
          </ErrorBoundary>

          <footer>
            <span>
              QuantDB <b>v1.0.0</b> · Institutional research & algorithmic trading terminal
            </span>
            <span>
              <CircleHelp size={13} /> Documentation <span className="footer-sep">·</span> Paper trading only
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function Overview({
  data,
  quotes,
  loading,
  error,
}: {
  data: OverviewData;
  quotes: Quote[];
  loading: boolean;
  error: boolean;
}) {
  const cards: Array<[string, string, string, string, boolean | null]> = [
    ['TOTAL EQUITY', '$128,430.80', '+2.84%', 'vs. last month', true],
    ['TODAY’S P&L', '+$2,184.50', '+1.72%', 'vs. previous close', true],
    ['INVESTED', '$94,210.00', '73.4%', 'of total equity', null],
    ['CASH BALANCE', '$34,220.80', '26.6%', 'available to deploy', null],
  ];

  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            MONDAY, OCTOBER 18, 2026 <span className="eyebrow-sep">/</span> MARKET OVERVIEW
          </div>
          <h1>
            Good morning, Darshil <span className="wave">✳</span>
          </h1>
          <p>
            Your portfolio is up <strong>2.84%</strong> this month. Here’s your research snapshot.
          </p>
        </div>
        <NavLink to="/health" className="outline-button">
          <span className="status-dot" /> Live Aiven DB <ChevronDown size={14} />
        </NavLink>
      </div>

      {(error || loading) && (
        <div className={`api-note ${error ? 'error' : ''}`}>
          {loading
            ? 'Connecting to QuantDB API…'
            : `API unavailable. Showing sample research data. ${
                error ? 'Start the API with uvicorn api.main:app --reload' : ''
              }`}
        </div>
      )}

      <div className="metric-grid">
        {cards.map(([label, value, delta, sub, positive], i) => (
          <article className="metric-card" key={label}>
            <div className="metric-head">
              <span>{label}</span>
              <span className={`metric-icon tone-${i}`}>
                <MetricIcon index={i} />
              </span>
            </div>
            <div className="metric-value">
              {data.portfolios.length && i === 0
                ? money(Number(data.portfolios[0]?.total_equity || 128430.8))
                : value}
            </div>
            <div className="metric-foot">
              <span
                className={`change ${
                  positive === false ? 'negative' : positive === true ? 'positive' : ''
                }`}
              >
                {positive === false ? '' : '↗ '}
                {delta}
              </span>
              <span>{sub}</span>
            </div>
            <div className={`spark spark-${i}`}>
              {[14, 21, 17, 27, 23, 31, 20, 35, 30, 38, 32, 45].map((x, j) => (
                <i key={j} style={{ height: x }} />
              ))}
            </div>
          </article>
        ))}
      </div>

      <div className="primary-grid">
        <section className="panel performance-panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">PERFORMANCE</div>
              <h2>Portfolio performance</h2>
            </div>
            <div className="chart-actions">
              <span className="live-label">
                <i /> LIVE
              </span>
              <button className="period active">1M</button>
              <button className="period">3M</button>
              <button className="period">6M</button>
              <button className="period">1Y</button>
              <button className="period">ALL</button>
            </div>
          </div>
          <div className="chart-summary">
            <strong>$128,430.80</strong>
            <span className="change positive">↗ $3,560.20 (2.84%)</span>
            <span className="muted">past month</span>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#69d5ad" stopOpacity={0.19} />
                    <stop offset="95%" stopColor="#69d5ad" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#202a31" vertical={false} />
                <XAxis
                  dataKey="d"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#687781', fontSize: 10 }}
                  interval={5}
                />
                <YAxis
                  orientation="right"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#687781', fontSize: 10 }}
                  domain={['dataMin - 10', 'dataMax + 10']}
                  tickFormatter={(v) => `$${v}k`}
                />
                <Tooltip
                  contentStyle={{
                    background: '#121a20',
                    border: '1px solid #28343a',
                    borderRadius: 8,
                    color: '#e6eeeb',
                  }}
                  formatter={(v: number) => [`$${(v * 1000).toLocaleString()}`, 'Equity']}
                />
                <Area type="monotone" dataKey="value" stroke="#68d1a9" strokeWidth={2} fill="url(#fill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-legend">
            <span>
              <i className="legend-line" />
              Portfolio equity
            </span>
            <span>
              <i className="legend-dash" />
              Benchmark · S&P 500
            </span>
          </div>
        </section>

        <section className="panel allocation-panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">ALLOCATION</div>
              <h2>Asset allocation</h2>
            </div>
            <button className="more">···</button>
          </div>
          <div className="donut-area">
            <div className="donut">
              <div>
                <strong>$128.4k</strong>
                <small>TOTAL VALUE</small>
              </div>
            </div>
          </div>
          <div className="allocation-list">
            <Alloc color="mint" name="Equities" amount="$86,238" pct="67.1%" />
            <Alloc color="blue" name="ETFs" amount="$24,402" pct="19.0%" />
            <Alloc color="purple" name="Cash" amount="$17,790" pct="13.9%" />
          </div>
          <NavLink to="/portfolio" className="text-link">
            View portfolio <span>→</span>
          </NavLink>
        </section>
      </div>

      <div className="secondary-grid">
        <section className="panel market-panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">MARKET PULSE</div>
              <h2>
                Watchlist <span className="count">04</span>
              </h2>
            </div>
            <NavLink to="/market-data" className="text-link">
              All markets <span>→</span>
            </NavLink>
          </div>
          <div className="watch-table">
            <div className="table-head">
              <span>INSTRUMENT</span>
              <span>LAST PRICE</span>
              <span>CHANGE</span>
              <span>VOLUME</span>
              <span />
            </div>
            {quotes.slice(0, 4).map((q, i) => {
              const change = Number(q.change_pct ?? q.change ?? [0.82, -0.31, 1.24, 0.46][i]);
              const price = Number(q.price ?? q.close_price ?? [24192.35, 5842.47, 18472.91, 2748.2][i]);
              return (
                <div className="watch-row" key={q.symbol}>
                  <div className="instrument">
                    <span className={`ticker-icon ticker-${i}`}>{q.symbol.slice(0, 1)}</span>
                    <span>
                      <b>{q.symbol}</b>
                      <small>{['NIFTY 50 · NSE', 'S&P 500 · INDEX', 'NASDAQ · INDEX', 'GOLD · COMMODITY'][i]}</small>
                    </span>
                  </div>
                  <b className="last-price">
                    {price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </b>
                  <span className={`pill-change ${change >= 0 ? 'pos' : 'neg'}`}>
                    {change >= 0 ? '+' : ''}
                    {change.toFixed(2)}%
                  </span>
                  <span className="volume">{Number(q.volume ?? [24.8, 3.42, 5.16, 1.2][i]).toFixed(1)}M</span>
                  <MiniLine up={change >= 0} />
                </div>
              );
            })}
          </div>
        </section>

        <section className="panel system-panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">PLATFORM</div>
              <h2>System health</h2>
            </div>
            <span className="all-systems">
              <i /> OPERATIONAL
            </span>
          </div>
          <HealthRow
            title="Database"
            sub={data.health.database_status || 'Aiven MySQL · QuantDB'}
            status={data.health.connected === false ? 'Degraded' : 'Connected'}
            good={data.health.connected !== false}
          />
          <HealthRow title="Backend API" sub="FastAPI · v1.0.0" status="Healthy" good />
          <HealthRow title="Quant engine" sub="Analytics · Backtesting" status="Ready" good />
          <div className="system-foot">
            <span>Last checked just now</span>
            <NavLink to="/health">
              View diagnostics <span>→</span>
            </NavLink>
          </div>
        </section>
      </div>

      <div className="bottom-grid">
        <section className="panel positions-panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">YOUR PORTFOLIO</div>
              <h2>Top positions</h2>
            </div>
            <NavLink className="text-link" to="/portfolio">
              View all <span>→</span>
            </NavLink>
          </div>
          <div className="positions-table">
            <div className="table-head">
              <span>ASSET</span>
              <span>SHARES</span>
              <span>AVG. PRICE</span>
              <span>MARKET VALUE</span>
              <span>UNREALIZED P&L</span>
            </div>
            {[
              ['NVDA', 'NVIDIA Corporation', '42', '$118.24', '$6,947.40', '+39.8%', 'n'],
              ['AAPL', 'Apple Inc.', '28', '$201.50', '$6,235.60', '+10.5%', 'a'],
              ['MSFT', 'Microsoft Corp.', '15', '$412.80', '$6,180.15', '+0.1%', 'm'],
              ['AMZN', 'Amazon.com Inc.', '31', '$187.90', '$5,823.80', '−0.2%', 'am'],
            ].map((r) => (
              <div className="position-row" key={r[0]}>
                <div className="instrument">
                  <span className={`ticker-icon ticker-${r[6]}`}>{r[0][0]}</span>
                  <span>
                    <b>{r[0]}</b>
                    <small>{r[1]}</small>
                  </span>
                </div>
                <span>{r[2]}</span>
                <span>{r[3]}</span>
                <b>{r[4]}</b>
                <span className={`pnl ${r[5][0] === '+' ? 'positive' : 'negative'}`}>{r[5]}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="panel risk-panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">RISK OVERVIEW</div>
              <h2>Portfolio risk</h2>
            </div>
            <NavLink className="text-link" to="/analytics">
              Details <span>→</span>
            </NavLink>
          </div>
          <div className="risk-main">
            <div>
              <strong>{Number(data.risk.sharpe_ratio || 1.84).toFixed(2)}</strong>
              <span>Sharpe ratio</span>
            </div>
            <span className="risk-badge">GOOD</span>
          </div>
          <div className="risk-meter">
            <i />
          </div>
          <div className="risk-stats">
            <div>
              <span>Volatility</span>
              <b>{Number(data.risk.annualized_volatility || 14.2).toFixed(1)}%</b>
            </div>
            <div>
              <span>Max drawdown</span>
              <b className="negative">−{Math.abs(Number(data.risk.max_drawdown || 6.8)).toFixed(1)}%</b>
            </div>
            <div>
              <span>Daily VaR (95%)</span>
              <b>{Number(data.risk.var_95_daily || -1.45).toFixed(2)}%</b>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

function MetricIcon({ index }: { index: number }) {
  return [
    <WalletCards size={16} key={0} />,
    <ArrowUpRight size={16} key={1} />,
    <BarChart3 size={16} key={2} />,
    <Database size={16} key={3} />,
  ][index];
}

function Alloc({
  color,
  name,
  amount,
  pct,
}: {
  color: string;
  name: string;
  amount: string;
  pct: string;
}) {
  return (
    <div className="allocation-row">
      <i className={color} />
      <span>{name}</span>
      <b>{amount}</b>
      <small>{pct}</small>
    </div>
  );
}

function HealthRow({
  title,
  sub,
  status,
  good,
}: {
  title: string;
  sub: string;
  status: string;
  good: boolean;
}) {
  return (
    <div className="health-row">
      <span className={`health-icon ${good ? 'healthy' : ''}`}>
        <Activity size={15} />
      </span>
      <span className="health-copy">
        <b>{title}</b>
        <small>{sub}</small>
      </span>
      <span className={`health-status ${good ? 'good' : 'bad'}`}>
        <i />
        {status}
      </span>
    </div>
  );
}

function MiniLine({ up }: { up: boolean }) {
  return (
    <svg className="mini-line" viewBox="0 0 66 24" preserveAspectRatio="none">
      <polyline
        fill="none"
        stroke={up ? '#64caa1' : '#eb7c78'}
        strokeWidth="1.7"
        points={
          up
            ? '0,18 9,13 17,16 25,9 34,14 43,6 51,10 59,2 66,5'
            : '0,4 9,8 17,6 25,14 34,10 43,16 51,12 59,21 66,18'
        }
      />
    </svg>
  );
}

export default App;
