import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Activity, ArrowUpRight, BarChart3, ChevronDown, Database, WalletCards } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { request } from '../lib/api';
import type { Health, MarketDataPoint, OverviewData, Quote } from '../types';
import type { UserProfile } from '../auth/AuthProvider';

const money = (n: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);

export default function Overview({
  data,
  quotes,
  loading,
  error,
  profile,
}: {
  data: OverviewData;
  quotes: Quote[];
  loading: boolean;
  error: boolean;
  profile: UserProfile;
}) {
  const [chartDays, setChartDays] = useState(30);
  const portfolio = data.portfolios?.[0];
  const total = Number(portfolio?.total_equity ?? portfolio?.portfolio_value ?? 0);
  const cash = Number(portfolio?.current_cash ?? 0);
  const invested = Math.max(0, total - cash);
  const returnPct = Number(portfolio?.daily_return_pct ?? 0);
  const securityId = Number(quotes[0]?.security_id ?? 0);
  const symbol = String(quotes[0]?.symbol || '');
  const { data: series = [] } = useQuery({
    queryKey: ['overview-market-series', securityId, chartDays],
    queryFn: () => request<MarketDataPoint[]>(`/market-data/${securityId}?symbol=${encodeURIComponent(symbol)}&days=${chartDays}`),
    enabled: securityId > 0 && Boolean(symbol),
  });
  const chartData = series.map((point) => ({ d: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), value: Number(point.close_price) }));
  const investedPct = total > 0 ? invested / total * 100 : 0;
  const cashPct = total > 0 ? cash / total * 100 : 0;
  const cards: Array<[string, string, string, string, boolean | null]> = [
    ['PORTFOLIO VALUE', portfolio ? money(total) : '—', portfolio ? `${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(2)}%` : '—', data.health.data_mode === 'MOCK' ? 'simulated account' : 'database portfolio', portfolio ? returnPct >= 0 : null],
    ['TOTAL P&L', portfolio ? money(Number(portfolio.total_pnl ?? 0)) : '—', 'from database', 'realized + unrealized', portfolio ? Number(portfolio.total_pnl ?? 0) >= 0 : null],
    ['INVESTED', portfolio ? money(invested) : '—', portfolio && total ? `${(invested / total * 100).toFixed(1)}%` : '—', 'of portfolio value', null],
    ['CASH BALANCE', portfolio ? money(cash) : '—', portfolio && total ? `${(cash / total * 100).toFixed(1)}%` : '—', 'available to deploy', null],
  ];

  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).toUpperCase()} <span className="eyebrow-sep">/</span> MARKET OVERVIEW
          </div>
          <h1>
            Welcome, {profile.name.split(' ')[0]} <span className="wave">✳</span>
          </h1>
          <p>
            Your quantitative research workspace is ready. Here’s your latest portfolio snapshot.
          </p>
        </div>
        <NavLink to="/health" className="outline-button">
          <span className="status-dot" /> {data.health.data_mode === 'MOCK' ? 'Simulation mode' : data.health.connected === false ? 'Database offline' : 'Database mode'} <ChevronDown size={14} />
        </NavLink>
      </div>

      {(error || loading) && (
        <div className={`api-note ${error ? 'error' : ''}`}>
          {loading
            ? 'Connecting to QuantDB API…'
                : `QuantDB API unavailable. ${
                error ? 'Confirm the API service and its database connection are running.' : ''
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
              {value}
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
              {portfolio ? [14, 21, 17, 27, 23, 31, 20, 35, 30, 38, 32, 45].map((x, j) => (
                <i key={j} style={{ height: x }} />
              )) : <small>NO PORTFOLIO DATA</small>}
            </div>
          </article>
        ))}
      </div>

      <div className="primary-grid">
        <section className="panel performance-panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">PERFORMANCE</div>
              <h2>{symbol ? `${symbol} market history` : 'Market history'}</h2>
            </div>
            <div className="chart-actions">
              <span className="live-label">
                <i /> {data.health.data_mode === 'MOCK' ? 'SIMULATED' : 'DATABASE'}
              </span>
              {[[30, '1M'], [90, '3M'], [180, '6M'], [365, '1Y']].map(([days, label]) => <button key={days} className={`period ${chartDays === days ? 'active' : ''}`} onClick={() => setChartDays(Number(days))}>{label}</button>)}
            </div>
          </div>
          <div className="chart-summary">
            <strong>{series.length ? money(Number(series[series.length - 1]?.close_price || 0)) : '—'}</strong>
            <span className="change">{symbol || 'No instrument selected'}</span>
            <span className="muted">latest close</span>
          </div>
          <div className="chart-wrap">
            {chartData.length === 0 && <div className="chart-empty">Market history appears when the QuantDB data feed is connected.</div>}
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
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
                  tickFormatter={(v) => `$${Number(v).toLocaleString()}`}
                />
                <Tooltip
                  contentStyle={{
                    background: '#121a20',
                    border: '1px solid #28343a',
                    borderRadius: 8,
                    color: '#e6eeeb',
                  }}
                  formatter={(v: number) => [money(v), 'Close']}
                />
                <Area type="monotone" dataKey="value" stroke="#0dbbd3" strokeWidth={2} fill="url(#fill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-legend">
            <span>
              <i className="legend-line" />
              {symbol ? `${symbol} close price` : 'Market close price'}
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
            <div className="donut" style={{ background: `conic-gradient(#0dbbd3 0 ${investedPct}%, #9b72e8 ${investedPct}% ${investedPct + cashPct}%, #273341 ${investedPct + cashPct}% 100%)` }}>
              <div>
                <strong>{portfolio ? money(total) : '—'}</strong>
                <small>PORTFOLIO</small>
              </div>
            </div>
          </div>
          <div className="allocation-list">
            <Alloc color="mint" name="Invested" amount={portfolio ? money(invested) : '—'} pct={portfolio && total ? `${investedPct.toFixed(1)}%` : '—'} />
            <Alloc color="purple" name="Cash" amount={portfolio ? money(cash) : '—'} pct={portfolio && total ? `${cashPct.toFixed(1)}%` : '—'} />
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
                Watchlist <span className="count">{String(quotes.length).padStart(2, '0')}</span>
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
              const change = Number(q.change_pct ?? q.change ?? 0);
              const price = Number(q.price ?? q.close_price ?? q.last_price ?? 0);
              return (
                <div className="watch-row" key={q.symbol}>
                  <div className="instrument">
                    <span className={`ticker-icon ticker-${i}`}>{q.symbol.slice(0, 1)}</span>
                    <span>
                      <b>{q.symbol}</b>
                      <small>{q.name || 'QuantDB market feed'}</small>
                    </span>
                  </div>
                  <b className="last-price">
                    {price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </b>
                  <span className={`pill-change ${change >= 0 ? 'pos' : 'neg'}`}>
                    {change >= 0 ? '+' : ''}
                    {change.toFixed(2)}%
                  </span>
                  <span className="volume">{q.volume == null ? '—' : Number(q.volume).toLocaleString()}</span>
                  <MiniLine up={change >= 0} />
                </div>
              );
            })}
            {!quotes.length && <div className="empty-panel-state">Connect the market data provider to see the instrument watchlist.</div>}
          </div>
        </section>

        <section className="panel system-panel">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">PLATFORM</div>
              <h2>System health</h2>
            </div>
            <span className="all-systems">
              <i /> {data.health.connected === false ? 'DEGRADED' : data.health.connected === true ? 'OPERATIONAL' : 'CHECKING'}
            </span>
          </div>
          <HealthRow
            title="Database"
            sub={data.health.database_status || 'Database status reported by QuantDB API'}
            status={data.health.connected === false ? 'Offline' : data.health.connected === true ? 'Connected' : 'Unknown'}
            good={data.health.connected === true}
          />
          <HealthRow title="Backend API" sub={data.health.backend_status || 'FastAPI · QuantDB'} status={error ? 'Unavailable' : 'Connected'} good={!error} />
          <HealthRow title="Quant engine" sub={data.health.quant_engine_status || 'Analytics and backtesting'} status={data.health.quant_engine_status ? 'Ready' : 'Unknown'} good={Boolean(data.health.quant_engine_status)} />
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
            <div className="empty-panel-state">Your positions and simulated executions are shown in Portfolio after a paper trade.</div>
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
              <strong>{data.risk.sharpe_ratio == null ? '—' : Number(data.risk.sharpe_ratio).toFixed(2)}</strong>
              <span>Sharpe ratio</span>
            </div>
            <span className="risk-badge">RISK</span>
          </div>
          <div className="risk-meter">
            <i style={{ width: `${Math.max(0, Math.min(100, Math.abs(Number(data.risk.max_drawdown || 0)) * 4))}%` }} />
          </div>
          <div className="risk-stats">
            <div>
              <span>Volatility</span>
              <b>{data.risk.annualized_volatility == null ? '—' : `${Number(data.risk.annualized_volatility).toFixed(1)}%`}</b>
            </div>
            <div>
              <span>Max drawdown</span>
              <b className="negative">{data.risk.max_drawdown == null ? '—' : `${Number(data.risk.max_drawdown).toFixed(1)}%`}</b>
            </div>
            <div>
              <span>Daily VaR (95%)</span>
              <b>{data.risk.var_95_daily == null ? '—' : `${Number(data.risk.var_95_daily).toFixed(2)}%`}</b>
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

