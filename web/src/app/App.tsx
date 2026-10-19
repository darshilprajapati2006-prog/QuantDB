import { lazy, Suspense, useState } from 'react';
import { NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { Activity, BarChart3, Bell, CandlestickChart, ChevronDown, CircleHelp, Database, FlaskConical, Gauge, LayoutDashboard, Menu, Search, Settings2, ShieldCheck, WalletCards, X } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { request } from '../lib/api';
import type { Health, OverviewData, Quote } from '../types';

// Page Imports
import { ErrorBoundary } from '../components/ErrorBoundary';
import { useAuth } from '../auth/AuthProvider';
import { AuthScreen } from '../auth/AuthScreen';
import { AccountRoleRequest } from '../auth/AccountRoleRequest';
import type { UserProfile } from '../auth/AuthProvider';
const Overview = lazy(() => import('./Overview'));

const MarketDataPage = lazy(() => import('../pages/MarketDataPage').then((m) => ({ default: m.MarketDataPage })));
const SecuritiesPage = lazy(() => import('../pages/SecuritiesPage').then((m) => ({ default: m.SecuritiesPage })));
const TradingPage = lazy(() => import('../pages/TradingPage').then((m) => ({ default: m.TradingPage })));
const PortfolioPage = lazy(() => import('../pages/PortfolioPage').then((m) => ({ default: m.PortfolioPage })));
const StrategiesPage = lazy(() => import('../pages/StrategiesPage').then((m) => ({ default: m.StrategiesPage })));
const BacktestingPage = lazy(() => import('../pages/BacktestingPage').then((m) => ({ default: m.BacktestingPage })));
const AnalyticsPage = lazy(() => import('../pages/AnalyticsPage').then((m) => ({ default: m.AnalyticsPage })));
const DatabaseExplorerPage = lazy(() => import('../pages/DatabaseExplorerPage').then((m) => ({ default: m.DatabaseExplorerPage })));
const HealthPage = lazy(() => import('../pages/HealthPage').then((m) => ({ default: m.HealthPage })));
const ReportsPage = lazy(() => import('../pages/ReportsPage').then((m) => ({ default: m.ReportsPage })));
const AdminPage = lazy(() => import('../pages/AdminPage').then((m) => ({ default: m.AdminPage })));

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
      ['User & role admin', ShieldCheck, '/admin'],
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
  '/admin': 'User & Role Management',
  '/health': 'System Health',
};

const fallback: OverviewData = { market: [], portfolios: [], health: {}, risk: {}, backtest: {} };

function initials(name?: string) {
  if (!name) return 'QD';
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'QD';
}

function pageAllowed(profile?: UserProfile | null, page?: string) {
  if (!profile || !page) return false;
  if (profile.role === 'ADMIN') return true;
  if (page === 'System Health' || page === 'Database Explorer') return profile.role === 'ADMIN';
  const allowed = profile.allowed_pages || [];
  return allowed.some((item) => item?.toLowerCase() === page.toLowerCase());
}

function LoadingScreen({ label = 'Loading your workspace…' }: { label?: string }) {
  return <div className="workspace-loading"><span className="spinner"/><b>{label}</b><small>SECURE QUANTDB WORKSPACE</small></div>;
}

function AuthSetupIssue() {
  const { error, signOutUser } = useAuth();
  const status = Number(error.match(/^API (\d+):/)?.[1] || 0);
  const sessionRejected = status === 401;
  const missingServerSetup = status === 503;
  const heading = sessionRejected ? 'Reconnect your account' : 'Account connection needed';
  const explanation = sessionRejected
    ? 'The API rejected this Firebase sign-in session. Sign in again to refresh it. If this keeps happening, the web app and API may be using different Firebase projects.'
    : missingServerSetup
      ? 'The API could not verify your Firebase account. Check that its Firebase Admin service account is configured for the same project as the web app.'
      : 'The API could not load your QuantDB profile. Check that the API and database are available, then sign in again.';
  const setupHint = sessionRejected
    ? <>Confirm <code>VITE_FIREBASE_PROJECT_ID</code> and <code>FIREBASE_PROJECT_ID</code> both equal <code>quantdb-728ef</code>.</>
    : missingServerSetup
      ? <>Configure <code>FIREBASE_SERVICE_ACCOUNT_JSON</code> or <code>FIREBASE_SERVICE_ACCOUNT_PATH</code> on the API host, plus its database settings.</>
      : <>Check API host and database settings, then try signing in again.</>;
  return <div className="auth-page"><div className="auth-card auth-issue"><span className="auth-brand-mark">Q</span><div className="auth-eyebrow">SECURE WORKSPACE</div><h1>{heading}</h1><p className="auth-subtitle">{error || 'Could not load your QuantDB profile.'}</p><div className="auth-message is-error">{explanation}</div><button className="auth-submit" onClick={() => void signOutUser()}>Return to sign in</button><p className="auth-setup-hint">{setupHint}</p></div></div>;
}

function ModuleDenied() { return <div className="module-denied"><ShieldCheck size={26}/><h2>This module is not assigned to your role</h2><p>Ask the QuantDB administrator to update your role permissions.</p></div>; }

function Guarded({ profile, page, children }: { profile: UserProfile; page: string; children: React.ReactNode }) {
  return pageAllowed(profile, page) ? <Suspense fallback={<LoadingScreen label={`Opening ${page.toLowerCase()}…`}/ >}>{children}</Suspense> : <ModuleDenied/>;
}

function App() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const auth = useAuth();
  if (auth.loading) return <LoadingScreen/>;
  if (!auth.user || auth.verificationRequired || auth.setupRequired) return <AuthScreen/>;
  if (!auth.profile) return <AuthSetupIssue/>;
  const profile = auth.profile;
  const { data = fallback, isError, isLoading } = useQuery({
    queryKey: ['overview'],
    queryFn: () => request<OverviewData>('/overview'),
  });

  const h = (data?.health || {}) as Health;
  const quotes = data?.market || [];
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

        {nav.map((group) => {
          const items = group.items.filter(([label]) => pageAllowed(profile, label === 'Paper trading' ? 'Trading' : label === 'Securities' ? 'Market Data' : label === 'Database explorer' ? 'Database Explorer' : label === 'System health' ? 'System Health' : label === 'User & role admin' ? 'Admin' : label));
          if (!items.length) return null;
          return (
          <div className="nav-group" key={group.label}>
            <div className="nav-label">{group.label}</div>
            {items.map(([label, Icon, path]) => (
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
          );
        })}

        <div className="sidebar-bottom">
          {profile?.role !== 'ADMIN' && <AccountRoleRequest />}
          <NavLink to="/health" className="mode-card block hover:border-[#3b574a] transition">
            <span className="status-dot" />
            <div>
              <b>{h?.data_mode || 'REAL'} MODE</b>
              <small>{h?.database_status || 'Database status ready'}</small>
            </div>
            <ChevronDown size={14} />
          </NavLink>
          <div className="user-row">
            <div className="avatar">{initials(profile?.name)}</div>
            <div>
              <b>{profile?.name || 'QuantDB User'}</b>
              <small>{profile?.role_display || profile?.role || 'User'}</small>
            </div>
            <button className="signout-icon" aria-label="Sign out" title="Sign out" onClick={() => void auth.signOutUser()}><ChevronDown size={15}/></button>
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
              {h?.data_mode === 'MOCK' ? 'SIMULATION' : h?.connected === false ? 'DB OFFLINE' : 'REAL DATA'} <i>·</i> QUANTDB
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
            <button className="top-avatar" aria-label="Sign out" title={`${profile?.name || 'User'} · Sign out`} onClick={() => void auth.signOutUser()}>{initials(profile?.name)}</button>
          </div>
        </header>

        <div className="content">
          <ErrorBoundary>
            <Suspense fallback={<LoadingScreen label="Opening your research workspace…" />}>
            <Routes>
              <Route path="/" element={<Overview data={data} quotes={quotes} loading={isLoading} error={isError} profile={profile}/>} />
              <Route path="/market-data" element={<Guarded profile={profile} page="Market Data"><MarketDataPage /></Guarded>} />
              <Route path="/securities" element={<Guarded profile={profile} page="Market Data"><SecuritiesPage /></Guarded>} />
              <Route path="/trading" element={<Guarded profile={profile} page="Trading"><TradingPage /></Guarded>} />
              <Route path="/portfolio" element={<Guarded profile={profile} page="Portfolio"><PortfolioPage /></Guarded>} />
              <Route path="/strategies" element={<Guarded profile={profile} page="Strategies"><StrategiesPage /></Guarded>} />
              <Route path="/backtesting" element={<Guarded profile={profile} page="Backtesting"><BacktestingPage /></Guarded>} />
              <Route path="/analytics" element={<Guarded profile={profile} page="Reports"><AnalyticsPage /></Guarded>} />
              <Route path="/reports" element={<Guarded profile={profile} page="Reports"><ReportsPage /></Guarded>} />
              <Route path="/database" element={<Guarded profile={profile} page="Database Explorer"><DatabaseExplorerPage /></Guarded>} />
              <Route path="/admin" element={<Guarded profile={profile} page="Admin"><AdminPage /></Guarded>} />
              <Route path="/health" element={<Guarded profile={profile} page="System Health"><HealthPage /></Guarded>} />
              <Route path="*" element={<Overview data={data} quotes={quotes} loading={isLoading} error={isError} profile={profile}/>} />
            </Routes>
            </Suspense>
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

export default App;
