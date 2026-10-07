"""
QuantDB — Quantitative Strategy Backtesting Terminal
Executes algorithmic simulations, calculates risk-adjusted performance metrics,
renders underwater drawdowns, and delivers granular trade-by-trade analytics.
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
    render_returns_chart,
    render_backtest_signals_chart,
    render_return_distribution,
)
from dashboard.components.tables import render_backtest_results_table
from dashboard.services.strategy_service import get_strategies, get_strategy_by_id
from dashboard.services.market_service import get_available_securities
from dashboard.services.backtest_service import execute_backtest

from dashboard.services.auth_service import require_auth

# Page configuration
st.set_page_config(
    page_title="QuantDB — Strategy Backtesting",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and authentication guard
apply_terminal_theme()
require_auth("Backtesting")
render_sidebar(current_page="Backtesting")

# Top Disclaimer
render_simulation_banner("Quantitative Backtesting Simulation Engine • Historical Replay")

# Page Header
st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; align-items: baseline; gap: 10px;">
            <h1 style="margin: 0; font-size: 1.75rem; font-weight: 800; color: #F8FAFC;">
                STRATEGY <span style="color: #06B6D4;">BACKTESTING</span>
            </h1>
            <span style="color: #64748B; font-size: 0.90rem;">
                Quantitative Replay Engine & Alpha Verification
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

strategies = get_strategies()
securities = get_available_securities()

if not strategies or not securities:
    st.error("Backtesting engine unavailable: Missing strategies or securities.")
    st.stop()

# -------------------------------------------------------------
# TOP CONFIGURATION PANEL
# -------------------------------------------------------------
with st.container():
    st.markdown("<div class='quant-card' style='padding: 18px;'>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 12px;">
            Backtest Simulation Parameters
        </div>
    """, unsafe_allow_html=True)

    # Pre-select strategy if passed from strategies page
    default_strat_id = st.session_state.get("backtest_strategy_id", strategies[0]["strategy_id"])
    strat_ids = [s["strategy_id"] for s in strategies]
    strat_idx = strat_ids.index(default_strat_id) if default_strat_id in strat_ids else 0

    p_col1, p_col2, p_col3, p_col4, p_col5, p_col6 = st.columns([2.5, 2, 1.8, 1.8, 1.8, 1.8])

    with p_col1:
        strat_opts = {f"#{s['strategy_id']} {s['name']}": s["strategy_id"] for s in strategies}
        sel_strat_label = st.selectbox("Algorithmic Strategy", options=list(strat_opts.keys()), index=strat_idx)
        selected_strategy_id = strat_opts[sel_strat_label]
        strat_spec = get_strategy_by_id(selected_strategy_id) or strategies[0]

    with p_col2:
        sec_opts = {f"{s['symbol']} — {s['security_name']}": s for s in securities}
        sel_sec_label = st.selectbox("Underlying Asset", options=list(sec_opts.keys()), index=0)
        selected_sec = sec_opts[sel_sec_label]

    with p_col3:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=365))

    with p_col4:
        end_date = st.date_input("End Date", value=datetime.now())

    with p_col5:
        initial_capital = st.number_input("Initial Capital ($)", min_value=1000.0, value=100000.0, step=10000.0)

    with p_col6:
        transaction_cost = st.number_input("Cost / Fee (%)", min_value=0.0, max_value=3.0, value=0.05, step=0.01)

    # Strategy Parameters Accordion
    params_dict = {}
    with st.expander("🛠️ Strategy Parameter Fine-Tuning", expanded=False):
        p_items = strat_spec.get("parameters", [])
        if p_items:
            p_cols = st.columns(len(p_items))
            for i, p in enumerate(p_items):
                with p_cols[i]:
                    p_name = p["name"]
                    p_def = p.get("default", 20)
                    p_type = p.get("type", "int")
                    if p_type == "int":
                        val = st.number_input(f"{p_name}", value=int(p_def), step=1, key=f"bt_param_{p_name}")
                    elif p_type == "float":
                        val = st.number_input(f"{p_name}", value=float(p_def), step=0.1, key=f"bt_param_{p_name}")
                    else:
                        val = st.checkbox(f"{p_name}", value=bool(p_def), key=f"bt_param_{p_name}")
                    params_dict[p_name] = val
        else:
            st.write("This strategy operates with standard calibrated parameters.")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Run Backtest Button
    if st.button("🚀 RUN QUANTITATIVE BACKTEST", use_container_width=True, type="primary"):
        with st.spinner("Processing event-driven historical simulation & calculating risk metrics..."):
            success, msg, bt_payload = execute_backtest(
                strategy_id=selected_strategy_id,
                security_id=selected_sec["security_id"],
                symbol=selected_sec["symbol"],
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.max.time()),
                initial_capital=float(initial_capital),
                transaction_cost_pct=float(transaction_cost),
                parameters=params_dict,
            )
            if success and bt_payload:
                st.session_state["active_backtest"] = bt_payload
                st.toast("Backtest execution completed!", icon="✅")
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)

bt_data = st.session_state.get("active_backtest")
if not bt_data:
    st.markdown("""
        <div class="quant-card" style="text-align: center; padding: 36px 20px; margin-top: 16px;">
            <div style="font-size: 2rem; margin-bottom: 8px;">⚡</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">
                Ready for Quantitative Backtest Execution
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; max-width: 600px; margin: 0 auto 16px auto;">
                Select your target security instrument, backtest date window, and model parameters above,
                then click <b style="color: #06B6D4;">RUN QUANTITATIVE BACKTEST</b> to simulate order matching and evaluate risk-adjusted metrics.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

summary = bt_data["summary"]
df_equity = bt_data["equity_curve"]
df_trades = bt_data["trades"]
df_signals = bt_data["signals"]

# -------------------------------------------------------------
# 1. PERFORMANCE SUMMARY METRICS
# -------------------------------------------------------------
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
st.markdown("""
    <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
        Quantitative Performance Metrics
    </div>
""", unsafe_allow_html=True)

r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns(5)
with r1_c1:
    tot_ret = summary["total_return"]
    render_metric_card(
        title="TOTAL RETURN",
        value=format_pct(tot_ret, precision=2, include_sign=True),
        change=f"Final: {format_currency(summary['final_capital'])}",
        is_positive=tot_ret >= 0,
        description="Net Cumulative Alpha"
    )
with r1_c2:
    tot_pnl = summary["total_pnl"]
    render_metric_card(
        title="TOTAL P&L",
        value=format_pnl(tot_pnl),
        change=f"Principal: {format_currency(summary['initial_capital'])}",
        is_positive=tot_pnl >= 0,
        description="Absolute Dollar Profit"
    )
with r1_c3:
    render_metric_card(
        title="CAGR",
        value=format_pct(summary.get("cagr", 0.0), include_sign=True),
        change="Annual Compound",
        is_positive=summary.get("cagr", 0.0) >= 0,
        description="Compound Annual Growth Rate"
    )
with r1_c4:
    sharpe = summary["sharpe_ratio"]
    render_metric_card(
        title="SHARPE RATIO",
        value=f"{sharpe:.2f}",
        change=f"Profit Factor: {summary.get('profit_factor', 1.78):.2f}",
        is_positive=sharpe >= 1.0,
        description="Risk-adjusted Return (Rf=4%)"
    )
with r1_c5:
    max_dd = summary["max_drawdown"]
    render_metric_card(
        title="MAX DRAWDOWN",
        value=f"{max_dd:.2f}%",
        change=f"Vol: {summary.get('volatility', 16.0):.1f}%",
        is_positive=False if max_dd < -15 else None,
        description="Maximum Peak-to-Trough Decline"
    )

st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns(5)
with r2_c1:
    render_metric_card(
        title="TOTAL TRADES",
        value=str(summary["total_trades"]),
        change=f"Avg P&L: {format_pnl(summary.get('avg_trade_pnl', 0.0))}",
        is_positive=None,
        description="Executed Round-Trips"
    )
with r2_c2:
    render_metric_card(
        title="WIN RATE",
        value=f"{summary['win_rate']:.1f}%",
        change=f"{summary['winning_trades']}W / {summary['losing_trades']}L",
        is_positive=summary["win_rate"] >= 50.0,
        description="Winning Trade Ratio"
    )
with r2_c3:
    render_metric_card(
        title="AVERAGE TRADE P&L",
        value=format_pnl(summary.get("avg_trade_pnl", 0.0)),
        change="Per Trade Expectancy",
        is_positive=summary.get("avg_trade_pnl", 0.0) >= 0,
        description="Mathematical Edge"
    )
with r2_c4:
    render_metric_card(
        title="BEST TRADE",
        value=format_pnl(summary.get("best_trade", 0.0)),
        change="Max Single Gain",
        is_positive=True,
        description="Outlier Winner"
    )
with r2_c5:
    render_metric_card(
        title="WORST TRADE",
        value=format_pnl(summary.get("worst_trade", 0.0)),
        change="Max Single Loss",
        is_positive=False,
        description="Controlled Risk Event"
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. CHARTS (Equity Curve, Drawdown, Daily Returns, Signals, Distribution)
# -------------------------------------------------------------
tab_c1, tab_c2, tab_c3, tab_c4, tab_c5 = st.tabs([
    "📈 Equity Curve",
    "📉 Underwater Drawdown",
    "📊 Daily Returns",
    "🎯 Entry / Exit Signals",
    "🔔 Return Distribution"
])

with tab_c1:
    render_backtest_signals_chart(
        df_equity,
        df_signals,
        title=f"STRATEGY EQUITY TRAJECTORY VS S&P 500 BENCHMARK ({summary['symbol']})"
    )

with tab_c2:
    render_drawdown_chart(
        df_equity,
        title="UNDERWATER DRAWDOWN PROFILE (%)"
    )

with tab_c3:
    render_returns_chart(
        df_equity,
        title="DAILY ALGORITHMIC RETURN SERIES (%)"
    )

with tab_c4:
    render_backtest_signals_chart(
        df_equity,
        df_signals,
        title="EXECUTION SIGNALS & PRICE TRAJECTORY"
    )

with tab_c5:
    render_return_distribution(
        df_equity["daily_return"],
        title="RETURN FREQUENCY DISTRIBUTION"
    )

st.markdown("<div class='quant-divider'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. TRADE ANALYSIS & LOG
# -------------------------------------------------------------
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em;">
            Trade-By-Trade Simulation Log
        </div>
        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace;">
            AUDIT TRAIL & EXECUTION OUTCOMES
        </div>
    </div>
""", unsafe_allow_html=True)

trade_filter = st.radio(
    "Filter Trades",
    options=["ALL TRADES", "WINNING TRADES ONLY", "LOSING TRADES ONLY"],
    horizontal=True,
    index=0
)

filtered_trades = df_trades.copy()
if trade_filter == "WINNING TRADES ONLY":
    filtered_trades = filtered_trades[filtered_trades["pnl"] > 0]
elif trade_filter == "LOSING TRADES ONLY":
    filtered_trades = filtered_trades[filtered_trades["pnl"] <= 0]

render_backtest_results_table(filtered_trades)
