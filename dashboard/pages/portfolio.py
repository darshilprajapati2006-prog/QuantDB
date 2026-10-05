"""
QuantDB — Portfolio Management & Asset Allocation Terminal
Monitors portfolio valuations, cash reserves, unrealized and realized P&L,
security position weights, and comparative historical equity performance.
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
    render_returns_chart,
    render_portfolio_allocation,
    render_pnl_chart,
)
from dashboard.components.tables import render_positions_table
from dashboard.services.portfolio_service import (
    get_all_portfolios,
    get_portfolio_summary,
    get_portfolio_positions,
    get_portfolio_equity_history,
)

# Page configuration
st.set_page_config(
    page_title="QuantDB — Portfolio Analytics",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and sidebar
apply_terminal_theme()
render_sidebar(current_page="Portfolio")

# Top Disclaimer
render_simulation_banner("Simulated Portfolio Valuation • Real-Time Mark-To-Market Accounting")

# Page Header
st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; align-items: baseline; gap: 10px;">
            <h1 style="margin: 0; font-size: 1.75rem; font-weight: 800; color: #F8FAFC;">
                PORTFOLIO <span style="color: #06B6D4;">MANAGEMENT</span>
            </h1>
            <span style="color: #64748B; font-size: 0.90rem;">
                Holdings, Capital Allocation & Performance Tracking
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# TOP SELECTORS & CONTROLS
# -------------------------------------------------------------
portfolios = get_all_portfolios()
if not portfolios:
    st.error("No portfolios available.")
    st.stop()

top_col1, top_col2, top_col3 = st.columns([3, 2, 2])

with top_col1:
    port_dict = {f"{p['portfolio_name']} (ID: {p['portfolio_id']})": p["portfolio_id"] for p in portfolios}
    sel_port_label = st.selectbox("Select Portfolio", options=list(port_dict.keys()), index=0)
    selected_portfolio_id = port_dict[sel_port_label]

with top_col2:
    start_date = st.date_input("Performance Start Date", value=datetime.now() - timedelta(days=180))

with top_col3:
    end_date = st.date_input("Performance End Date", value=datetime.now())

if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

# Load portfolio details
port_summary = get_portfolio_summary(selected_portfolio_id)
if not port_summary:
    st.error("Unable to load portfolio details.")
    st.stop()

days_diff = max(10, (end_date - start_date).days)
equity_df = get_portfolio_equity_history(selected_portfolio_id, days=days_diff)
positions_df = get_portfolio_positions(selected_portfolio_id)

# -------------------------------------------------------------
# SUMMARY METRIC CARDS (6 CARDS AS SPECIFIED)
# -------------------------------------------------------------
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    render_metric_card(
        title="INITIAL CAPITAL",
        value=format_currency(port_summary["initial_capital"]),
        change="Base Allocation",
        is_positive=None,
        description="Starting Principal"
    )

with c2:
    render_metric_card(
        title="CURRENT CASH",
        value=format_currency(port_summary["cash"]),
        change=f"{(port_summary['cash'] / port_summary['portfolio_value'] * 100):.1f}% of total",
        is_positive=None,
        description="Unallocated Buying Power"
    )

with c3:
    render_metric_card(
        title="PORTFOLIO VALUE",
        value=format_currency(port_summary["portfolio_value"]),
        change=f"{port_summary.get('total_return_pct', 0.0):+.2f}% Return",
        is_positive=port_summary.get("total_return_pct", 0.0) >= 0,
        description="Cash + Open Holdings"
    )

with c4:
    tot_pnl = port_summary["total_pnl"]
    render_metric_card(
        title="TOTAL P&L",
        value=format_pnl(tot_pnl),
        change=format_pct(port_summary.get("total_return_pct", 0.0), include_sign=True),
        is_positive=tot_pnl >= 0,
        description="Net Overall Gain/Loss"
    )

with c5:
    realized_pnl = port_summary["realized_pnl"]
    render_metric_card(
        title="REALIZED P&L",
        value=format_pnl(realized_pnl),
        change="Closed Executions",
        is_positive=realized_pnl >= 0,
        description="Booked Profit / Loss"
    )

with c6:
    unrealized_pnl = port_summary["unrealized_pnl"]
    render_metric_card(
        title="UNREALIZED P&L",
        value=format_pnl(unrealized_pnl),
        change="Open Positions",
        is_positive=unrealized_pnl >= 0,
        description="Floating Gain / Loss"
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# VISUALIZATIONS SECTION: 4 CHARTS (Equity Curve, Returns, Allocation, PnL by Security)
# -------------------------------------------------------------
row1_left, row1_right = st.columns([7, 3])

with row1_left:
    render_equity_curve(
        equity_df,
        title="PORTFOLIO EQUITY TRAJECTORY VS S&P 500",
        include_benchmark=True,
        height=360
    )

with row1_right:
    render_portfolio_allocation(positions_df, title="CAPITAL ALLOCATION BY ASSET", height=360)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

row2_left, row2_right = st.columns([6, 4])

with row2_left:
    render_returns_chart(
        equity_df,
        title="DAILY PERFORMANCE RETURN DISTRIBUTION (%)",
        height=300
    )

with row2_right:
    render_pnl_chart(positions_df, title="UNREALIZED P&L BY SECURITY", height=300)

st.markdown("<div class='quant-divider'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# ACTIVE POSITIONS TABLE
# -------------------------------------------------------------
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em;">
            Active Position Holdings
        </div>
        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace;">
            REAL-TIME MARK-TO-MARKET VALUATION
        </div>
    </div>
""", unsafe_allow_html=True)

render_positions_table(positions_df)
