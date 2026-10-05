"""
QuantDB — Quantitative Finance Research & Simulation Platform
Main Application Overview Dashboard.
"""

from datetime import datetime
from pathlib import Path
import sys
import streamlit as st

# Setup sys.path to guarantee clean imports
_current_dir = Path(__file__).resolve().parent
_root_dir = _current_dir.parent
for _p in [str(_root_dir), str(_current_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dashboard.components.theme import apply_terminal_theme
from dashboard.components.sidebar import render_sidebar
from dashboard.components.status import render_simulation_banner
from dashboard.components.metrics import render_metric_card, format_currency, format_pnl, format_pct
from dashboard.components.charts import (
    render_equity_curve,
    render_returns_chart,
    render_portfolio_allocation,
)
from dashboard.components.tables import render_orders_table, render_trades_table
from dashboard.services.portfolio_service import (
    get_all_portfolios,
    get_portfolio_summary,
    get_portfolio_equity_history,
    get_portfolio_positions,
)
from dashboard.services.market_service import get_market_overview
from dashboard.services.trading_service import get_orders, get_trades
from dashboard.services.backtest_service import get_latest_summary
from dashboard.services.strategy_service import get_strategies
from dashboard.services.analytics_service import get_portfolio_risk_metrics, get_system_health

# Page configuration
st.set_page_config(
    page_title="QuantDB — Terminal Overview",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and sidebar
apply_terminal_theme()
render_sidebar(current_page="Overview")

# Top Disclaimer / Banner
render_simulation_banner("Simulated Trading & Market Research Terminal • Academic Research Purpose")

# Page Header
st.markdown("""
    <div style="margin-bottom: 20px;">
        <div style="display: flex; align-items: baseline; gap: 12px;">
            <h1 style="margin: 0; font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em; color: #F8FAFC;">
                QUANT<span style="color: #06B6D4;">DB</span>
            </h1>
            <span style="color: #64748B; font-size: 0.95rem; font-weight: 500;">
                Quantitative Finance Research & Simulation Platform
            </span>
        </div>
        <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
            DATABASE-DRIVEN MARKET DATA & ALGORITHMIC TRADING ENGINE
        </div>
    </div>
""", unsafe_allow_html=True)

# Select active portfolio
portfolios = get_all_portfolios()
active_port_id = 1
if portfolios:
    port_map = {f"{p['portfolio_name']} (ID: {p['portfolio_id']})": p["portfolio_id"] for p in portfolios}
    selected_name = st.selectbox(
        "Active Simulation Portfolio",
        options=list(port_map.keys()),
        index=0,
        label_visibility="collapsed"
    )
    active_port_id = port_map[selected_name]

# Fetch Portfolio Summary
port_summary = get_portfolio_summary(active_port_id) or {
    "portfolio_value": 1000000.0,
    "total_pnl": 0.0,
    "daily_return_pct": 0.0,
    "sharpe_ratio": 1.5,
    "max_drawdown": -5.0,
    "initial_capital": 1000000.0,
    "cash": 300000.0,
}

active_strats = get_strategies()
risk_metrics = get_portfolio_risk_metrics(active_port_id)

# -------------------------------------------------------------
# 1. SUMMARY METRIC CARDS
# -------------------------------------------------------------
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    render_metric_card(
        title="PORTFOLIO VALUE",
        value=format_currency(port_summary["portfolio_value"]),
        change=f"{port_summary.get('total_return_pct', 0.0):+.2f}% all-time",
        is_positive=port_summary.get("total_return_pct", 0.0) >= 0,
        description="Cash + Open Holdings"
    )

with col2:
    tot_pnl = port_summary.get("total_pnl", 0.0)
    render_metric_card(
        title="TOTAL P&L",
        value=format_pnl(tot_pnl),
        change=f"Realized: {format_pnl(port_summary.get('realized_pnl', 0.0))}",
        is_positive=tot_pnl >= 0,
        description="Realized + Unrealized"
    )

with col3:
    daily_ret = port_summary.get("daily_return_pct", 0.0)
    render_metric_card(
        title="DAILY RETURN",
        value=format_pct(daily_ret, precision=2, include_sign=True),
        change="Simulated 24H",
        is_positive=daily_ret >= 0,
        description="Mark-to-market drift"
    )

with col4:
    sharpe = risk_metrics.get("sharpe_ratio", 1.84)
    render_metric_card(
        title="SHARPE RATIO",
        value=f"{sharpe:.2f}",
        change=f"Sortino: {risk_metrics.get('sortino_ratio', 2.15):.2f}",
        is_positive=sharpe >= 1.0,
        description="Annualized (Rf=4.0%)"
    )

with col5:
    max_dd = risk_metrics.get("max_drawdown", -6.8)
    render_metric_card(
        title="MAX DRAWDOWN",
        value=f"{max_dd:.1f}%",
        change=f"VaR (95%): {risk_metrics.get('var_95_daily', -1.45):.2f}%",
        is_positive=False if max_dd < -10 else None,
        description="Peak-to-trough decline"
    )

with col6:
    render_metric_card(
        title="ACTIVE STRATEGIES",
        value=str(len(active_strats)),
        change="1 Running Backtest",
        is_positive=None,
        description="Algorithmic Library"
    )

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. CHARTS SECTION: Equity Curve + Daily Returns & Allocation
# -------------------------------------------------------------
equity_df = get_portfolio_equity_history(active_port_id, days=180)
positions_df = get_portfolio_positions(active_port_id)

chart_col1, chart_col2 = st.columns([7, 3])

with chart_col1:
    tab_eq, tab_ret = st.tabs(["📈 Portfolio Equity Curve", "📊 Daily Returns Distribution"])
    with tab_eq:
        render_equity_curve(
            equity_df,
            title="180-DAY PORTFOLIO EQUITY CURVE VS S&P 500 BENCHMARK",
            include_benchmark=True,
            height=370
        )
    with tab_ret:
        render_returns_chart(
            equity_df,
            title="DAILY RETURN FLUCTUATIONS (%)",
            height=370
        )

with chart_col2:
    st.markdown("""
        <div style="font-size: 0.78rem; text-transform: uppercase; color: #94A3B8; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Asset Allocation
        </div>
    """, unsafe_allow_html=True)
    render_portfolio_allocation(positions_df, title="CAPITAL ALLOCATION", height=370)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. MARKET OVERVIEW TICKER WATCHLIST
# -------------------------------------------------------------
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em;">
            Market Securities Overview
        </div>
        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace;">
            LIVE SIMULATED QUOTES
        </div>
    </div>
""", unsafe_allow_html=True)

mkt_summary = get_market_overview()
if not mkt_summary.empty:
    mkt_cols = st.columns(len(mkt_summary))
    for i, (_, row) in enumerate(mkt_summary.iterrows()):
        with mkt_cols[i]:
            is_up = row["change"] >= 0
            change_str = f"{row['change']:+.2f} ({row['change_pct']:+.2f}%)"
            render_metric_card(
                title=f"{row['symbol']}",
                value=f"${row['last_price']:.2f}",
                change=change_str,
                is_positive=is_up,
                description=f"Vol: {row['volume']:,}",
                badge=f"Spread ${row['spread']:.2f}"
            )

st.markdown("<div class='quant-divider'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. RECENT ACTIVITY & LATEST BACKTEST
# -------------------------------------------------------------
act_col1, act_col2 = st.columns([6, 4])

with act_col1:
    tab_ord, tab_trd = st.tabs(["⚡ Recent Simulated Orders", "💰 Recent Executions"])
    with tab_ord:
        orders_df = get_orders(portfolio_id=active_port_id)
        render_orders_table(orders_df.head(5))
    with tab_trd:
        trades_df = get_trades(portfolio_id=active_port_id)
        render_trades_table(trades_df.head(5))

with act_col2:
    st.markdown("""
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Latest Backtest Snapshot
        </div>
    """, unsafe_allow_html=True)

    bt_summary = get_latest_summary()
    if bt_summary:
        st.markdown(f"""
            <div class="quant-card" style="margin-bottom: 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC;">Dual Moving Average (SMA)</span>
                    <span class="status-pill status-pill-cyan">AAPL • 1Y</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; margin-top: 10px;">
                    <div><span style="color: #64748B;">Total Return:</span> <span style="color: #10B981; font-weight: 700;">+{bt_summary.get('total_return', 0.0)}%</span></div>
                    <div><span style="color: #64748B;">Net P&L:</span> <span style="color: #10B981; font-weight: 700;">+${bt_summary.get('total_pnl', 0.0):,.0f}</span></div>
                    <div><span style="color: #64748B;">Sharpe Ratio:</span> <span style="color: #38BDF8; font-weight: 700;">{bt_summary.get('sharpe_ratio', 1.84)}</span></div>
                    <div><span style="color: #64748B;">Max Drawdown:</span> <span style="color: #EF4444; font-weight: 700;">{bt_summary.get('max_drawdown', -8.2)}%</span></div>
                    <div><span style="color: #64748B;">Win Rate:</span> <span style="color: #F8FAFC;">{bt_summary.get('win_rate', 58.0)}%</span></div>
                    <div><span style="color: #64748B;">Total Trades:</span> <span style="color: #F8FAFC;">{bt_summary.get('total_trades', 35)}</span></div>
                </div>
                <div style="margin-top: 12px; text-align: right;">
                    <span style="font-size: 0.72rem; color: #94A3B8;">Navigate to <b>Backtesting</b> in the sidebar for full parameter optimization.</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
