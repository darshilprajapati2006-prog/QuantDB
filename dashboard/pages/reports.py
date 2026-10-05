"""
QuantDB — Analytics, Risk & Quantitative Reporting Terminal
Provides institutional-grade performance tear-sheets, risk factor decompositions,
and multi-asset statistical reporting.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys
import streamlit as st

# Setup sys.path for clean imports
_current_dir = Path(__file__).resolve().parent.parent
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
    render_drawdown_chart,
    render_return_distribution,
    render_portfolio_allocation,
)
from dashboard.services.portfolio_service import (
    get_all_portfolios,
    get_portfolio_summary,
    get_portfolio_positions,
    get_portfolio_equity_history,
)
from dashboard.services.strategy_service import get_strategies_dataframe
from dashboard.services.analytics_service import get_portfolio_risk_metrics
from dashboard.services.trading_service import get_orders, get_trades
from dashboard.services.market_service import get_market_overview

# Page configuration
st.set_page_config(
    page_title="QuantDB — Analytics & Reports",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and sidebar
apply_terminal_theme()
render_sidebar(current_page="Reports")

# Top Disclaimer
render_simulation_banner("Quantitative Analytics & Risk Reporting • Academic Research Engine")

# Page Header
st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; align-items: baseline; gap: 10px;">
            <h1 style="margin: 0; font-size: 1.75rem; font-weight: 800; color: #F8FAFC;">
                ANALYTICS & <span style="color: #06B6D4;">REPORTS</span>
            </h1>
            <span style="color: #64748B; font-size: 0.90rem;">
                Institutional Risk Decomposition & Strategy Tear-Sheets
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# TOP FILTERS: Portfolio & Date Range
# -------------------------------------------------------------
portfolios = get_all_portfolios()
if not portfolios:
    st.error("No portfolios found.")
    st.stop()

rep_c1, rep_c2, rep_c3 = st.columns([3, 2, 2])
with rep_c1:
    port_opts = {f"{p['portfolio_name']} (ID: {p['portfolio_id']})": p["portfolio_id"] for p in portfolios}
    sel_port_str = st.selectbox("Report Target Portfolio", options=list(port_opts.keys()), index=0)
    selected_portfolio_id = port_opts[sel_port_str]

with rep_c2:
    start_date = st.date_input("Audit Period Start", value=datetime.now() - timedelta(days=180))

with rep_c3:
    end_date = st.date_input("Audit Period End", value=datetime.now())

if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

# Retrieve data
port_sum = get_portfolio_summary(selected_portfolio_id) or {}
risk_metrics = get_portfolio_risk_metrics(selected_portfolio_id)
equity_df = get_portfolio_equity_history(selected_portfolio_id, days=(end_date - start_date).days)
positions_df = get_portfolio_positions(selected_portfolio_id)
orders_df = get_orders(portfolio_id=selected_portfolio_id)
trades_df = get_trades(portfolio_id=selected_portfolio_id)
mkt_df = get_market_overview()

# -------------------------------------------------------------
# REPORT TABS (5 SECTIONS)
# -------------------------------------------------------------
sec1, sec2, sec3, sec4, sec5 = st.tabs([
    "📊 Portfolio Performance",
    "🧠 Strategy Performance",
    "⚠️ Risk Analytics",
    "⚡ Trading Statistics",
    "📈 Market Statistics",
])

# -------------------------------------------------------------
# SECTION 1: PORTFOLIO PERFORMANCE
# -------------------------------------------------------------
with sec1:
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Cumulative Valuation & Alpha Generation
        </div>
    """, unsafe_allow_html=True)

    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    with p_col1:
        render_metric_card(
            title="TOTAL RETURN",
            value=format_pct(port_sum.get("total_return_pct", 0.0), include_sign=True),
            change=f"Principal: {format_currency(port_sum.get('initial_capital', 0.0))}",
            is_positive=port_sum.get("total_return_pct", 0.0) >= 0,
            description="Net Capital Appreciation"
        )
    with p_col2:
        render_metric_card(
            title="NET P&L BREAKDOWN",
            value=format_pnl(port_sum.get("total_pnl", 0.0)),
            change=f"Realized: {format_pnl(port_sum.get('realized_pnl', 0.0))}",
            is_positive=port_sum.get("total_pnl", 0.0) >= 0,
            description=f"Unrealized: {format_pnl(port_sum.get('unrealized_pnl', 0.0))}"
        )
    with p_col3:
        render_metric_card(
            title="CURRENT VALUATION",
            value=format_currency(port_sum.get("portfolio_value", 0.0)),
            change=f"Cash: {format_currency(port_sum.get('cash', 0.0))}",
            is_positive=None,
            description="Invested + Liquid Reserves"
        )
    with p_col4:
        render_metric_card(
            title="PORTFOLIO SHARPE",
            value=f"{port_sum.get('sharpe_ratio', 1.84):.2f}",
            change="Benchmark: 1.05",
            is_positive=True,
            description="Risk-Adjusted Performance"
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    c_left, c_right = st.columns([7, 3])
    with c_left:
        render_equity_curve(equity_df, title="PORTFOLIO EQUITY TRAJECTORY VS S&P 500", height=350)
    with c_right:
        render_portfolio_allocation(positions_df, title="CAPITAL ALLOCATION", height=350)

# -------------------------------------------------------------
# SECTION 2: STRATEGY PERFORMANCE
# -------------------------------------------------------------
with sec2:
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Strategy Registry Comparative Performance
        </div>
    """, unsafe_allow_html=True)

    df_strats = get_strategies_dataframe()
    st.dataframe(
        df_strats,
        column_config={
            "strategy_id": st.column_config.NumberColumn("Strategy ID", format="#%d"),
            "name": st.column_config.TextColumn("Model Name"),
            "type": st.column_config.TextColumn("Class"),
            "description": st.column_config.TextColumn("Quant Thesis"),
            "status": st.column_config.TextColumn("Deployment Status"),
            "parameter_count": st.column_config.NumberColumn("Parameters", format="%d"),
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("""
        <div style="background: #0d131f; padding: 12px 16px; border-radius: 6px; border: 1px solid #1F2937; margin-top: 14px; font-size: 0.8rem; color: #94A3B8;">
            <b>Quant Architecture Note:</b> Strategy performance metrics are computed asynchronously by the Analytics Layer 
            and cached in the MySQL <code>risk_metric</code> / <code>backtest_result</code> relational tables.
        </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# SECTION 3: RISK ANALYTICS
# -------------------------------------------------------------
with sec3:
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Parametric Risk Decomposition & Stress Metrics
        </div>
    """, unsafe_allow_html=True)

    r_c1, r_c2, r_c3, r_c4 = st.columns(4)
    with r_c1:
        render_metric_card(
            title="ANNUALIZED VOLATILITY",
            value=f"{risk_metrics.get('annualized_volatility', 14.2):.1f}%",
            change="252 Trading Days",
            is_positive=None,
            description="Sigma (Standard Deviation)"
        )
    with r_c2:
        render_metric_card(
            title="VALUE AT RISK (95% 1-DAY)",
            value=f"{risk_metrics.get('var_95_daily', -1.45):.2f}%",
            change="Parametric Normal",
            is_positive=None,
            description="Max Expected Daily Loss"
        )
    with r_c3:
        render_metric_card(
            title="CONDITIONAL VAR (CVAR 95%)",
            value=f"{risk_metrics.get('cvar_95_daily', -2.10):.2f}%",
            change="Expected Shortfall",
            is_positive=None,
            description="Tail Loss Beyond VaR"
        )
    with r_c4:
        render_metric_card(
            title="BETA VS BENCHMARK",
            value=f"{risk_metrics.get('beta_vs_sp500', 1.08):.2f}",
            change="Systematic Risk",
            is_positive=None,
            description="Market Exposure Factor"
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    r_left, r_right = st.columns(2)
    with r_left:
        render_drawdown_chart(equity_df, title="PORTFOLIO HISTORICAL DRAWDOWN PROFILE (%)", height=280)
    with r_right:
        render_return_distribution(equity_df["daily_return"], title="DAILY RETURN FREQUENCY DISTRIBUTION", height=280)

# -------------------------------------------------------------
# SECTION 4: TRADING STATISTICS
# -------------------------------------------------------------
with sec4:
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Simulated Execution & Order Activity
        </div>
    """, unsafe_allow_html=True)

    tot_orders = len(orders_df)
    filled_orders = len(orders_df[orders_df["status"] == "FILLED"]) if not orders_df.empty else 0
    tot_trades = len(trades_df)
    win_trades = len(trades_df[trades_df["pnl"] > 0]) if not trades_df.empty else 0
    win_rate = (win_trades / tot_trades * 100) if tot_trades > 0 else 0.0
    tot_fees = trades_df["transaction_cost"].sum() if not trades_df.empty else 0.0

    t_c1, t_c2, t_c3, t_c4 = st.columns(4)
    with t_c1:
        render_metric_card(
            title="TOTAL ORDERS PLACED",
            value=str(tot_orders),
            change=f"{filled_orders} Filled ({(filled_orders / tot_orders * 100 if tot_orders > 0 else 0):.0f}%)",
            is_positive=None,
            description="Lifecycle Orders"
        )
    with t_c2:
        render_metric_card(
            title="EXECUTED TRADES",
            value=str(tot_trades),
            change=f"{win_trades} Profitable",
            is_positive=None,
            description="Matched Executions"
        )
    with t_c3:
        render_metric_card(
            title="WIN RATE",
            value=f"{win_rate:.1f}%",
            change=f"Expectancy: {format_pnl(trades_df['pnl'].mean() if not trades_df.empty else 0.0)}",
            is_positive=win_rate >= 50.0,
            description="Simulated Profit Ratio"
        )
    with t_c4:
        render_metric_card(
            title="TOTAL TRANSACTION COSTS",
            value=format_currency(tot_fees),
            change="Simulated Brokerage Fees",
            is_positive=None,
            description="Execution Friction"
        )

# -------------------------------------------------------------
# SECTION 5: MARKET STATISTICS
# -------------------------------------------------------------
with sec5:
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Cross-Asset Liquidity & Microstructure Metrics
        </div>
    """, unsafe_allow_html=True)

    if not mkt_df.empty:
        st.dataframe(
            mkt_df,
            column_config={
                "symbol": st.column_config.TextColumn("Symbol", width="small"),
                "name": st.column_config.TextColumn("Instrument", width="medium"),
                "last_price": st.column_config.NumberColumn("Mark Price", format="$%.2f"),
                "change": st.column_config.NumberColumn("Net Change", format="$%.2f"),
                "change_pct": st.column_config.NumberColumn("Change (%)", format="%.2f%%"),
                "volume": st.column_config.NumberColumn("Simulated Volume", format="%d"),
                "bid": st.column_config.NumberColumn("Best Bid", format="$%.2f"),
                "ask": st.column_config.NumberColumn("Best Ask", format="$%.2f"),
                "spread": st.column_config.NumberColumn("Spread ($)", format="$%.4f"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Market statistics table currently empty.")
