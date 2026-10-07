"""
QuantDB — Simulated Paper Trading Execution Terminal
Supports order ticket entry, limit/market order validation, simulation matching,
and trade history inspection.
NO REAL-MONEY TRADING IS PERFORMED.
"""

from datetime import datetime
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
from dashboard.components.metrics import render_metric_card, format_currency, format_pnl
from dashboard.components.tables import render_orders_table, render_trades_table
from dashboard.services.portfolio_service import get_all_portfolios, get_portfolio_summary
from dashboard.services.market_service import get_available_securities, get_latest_quote
from dashboard.services.trading_service import (
    get_orders,
    get_open_orders,
    get_trades,
    submit_simulated_order,
)

from dashboard.services.auth_service import require_auth

# Page configuration
st.set_page_config(
    page_title="QuantDB — Simulated Trading",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and authentication guard
apply_terminal_theme()
require_auth("Trading")
render_sidebar(current_page="Trading")

# Mandatory Simulation Banner
render_simulation_banner("Simulated Trading Engine • Virtual Execution Only • No Real Capital Risk")

# Page Header
st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; align-items: baseline; gap: 10px;">
            <h1 style="margin: 0; font-size: 1.75rem; font-weight: 800; color: #F8FAFC;">
                SIMULATED <span style="color: #06B6D4;">TRADING</span>
            </h1>
            <span style="color: #64748B; font-size: 0.90rem;">
                Paper Trading Terminal & Simulated Execution Router
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Portfolios & Securities Lookup
portfolios = get_all_portfolios()
securities = get_available_securities()

if not portfolios or not securities:
    st.error("Trading terminal unavailable: Portfolios or securities failed to load.")
    st.stop()

# -------------------------------------------------------------
# TWO-COLUMN TRADING INTERFACE: Order Ticket on Left, Active Market & Books on Right
# -------------------------------------------------------------
ticket_col, viewer_col = st.columns([4, 6])

with ticket_col:
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Simulated Order Ticket
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='quant-card' style='padding: 20px;'>", unsafe_allow_html=True)

        # 1. Target Portfolio
        port_dict = {f"{p['portfolio_name']} (ID: {p['portfolio_id']})": p["portfolio_id"] for p in portfolios}
        sel_port_label = st.selectbox("Target Portfolio", options=list(port_dict.keys()), index=0)
        selected_portfolio_id = port_dict[sel_port_label]
        port_info = get_portfolio_summary(selected_portfolio_id)

        # Show available buying power
        avail_cash = port_info.get("cash", 0.0) if port_info else 0.0
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; margin: -6px 0 12px 0;">
                <span style="color: #64748B;">Buying Power / Cash:</span>
                <span style="color: #34D399; font-weight: 700;">{format_currency(avail_cash)}</span>
            </div>
        """, unsafe_allow_html=True)

        # 2. Target Security
        sec_dict = {f"{s['symbol']} ({s['security_name']})": s for s in securities}
        sel_sec_label = st.selectbox("Security Instrument", options=list(sec_dict.keys()), index=0)
        selected_sec = sec_dict[sel_sec_label]
        curr_quote = get_latest_quote(selected_sec["symbol"]) or {"last_price": selected_sec.get("base_price", 150.0), "spread": 0.05}
        mark_price = curr_quote.get("last_price", 150.0)

        # 3. Side & Order Type
        side_c, type_c = st.columns(2)
        with side_c:
            side = st.radio("Order Side", options=["BUY", "SELL"], horizontal=True, index=0)
        with type_c:
            order_type = st.radio("Order Type", options=["MARKET", "LIMIT"], horizontal=True, index=0)

        # 4. Quantity and Price Inputs
        qty_c, prc_c = st.columns(2)
        with qty_c:
            quantity = st.number_input("Quantity (Shares)", min_value=1, max_value=1000000, value=100, step=10)
        with prc_c:
            if order_type == "LIMIT":
                limit_price = st.number_input("Limit Price ($)", min_value=0.01, value=float(round(mark_price, 2)), step=0.1)
            else:
                st.text_input("Estimated Exec Price ($)", value=f"~${mark_price:.2f} (MKT)", disabled=True)
                limit_price = float(round(mark_price, 2))

        # Estimated Total
        est_total = quantity * limit_price
        est_fee = round(est_total * 0.0001, 2)
        st.markdown(f"""
            <div style="background: #0d131f; padding: 10px 14px; border-radius: 4px; border: 1px solid #1F2937; margin: 12px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: #94A3B8;">Est. Notional Value:</span>
                    <span style="color: #F8FAFC; font-weight: 700;">{format_currency(est_total)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94A3B8;">Est. Exchange Fee:</span>
                    <span style="color: #F8FAFC;">{format_currency(est_fee)}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Order Submission Button
        btn_label = f"SUBMIT SIMULATED {side} ORDER"
        btn_type = "primary" if side == "BUY" else "secondary"
        if st.button(btn_label, use_container_width=True, type=btn_type):
            success, msg, ord_obj = submit_simulated_order(
                portfolio_id=selected_portfolio_id,
                security_id=selected_sec["security_id"],
                symbol=selected_sec["symbol"],
                side=side,
                order_type=order_type,
                quantity=int(quantity),
                price=float(limit_price),
            )
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

        st.markdown("</div>", unsafe_allow_html=True)

with viewer_col:
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Execution & Market Depth Snapshot
        </div>
    """, unsafe_allow_html=True)

    # 3 Summary metrics for selected security
    v_c1, v_c2, v_c3 = st.columns(3)
    with v_c1:
        render_metric_card(
            title=f"{selected_sec['symbol']} LAST",
            value=f"${mark_price:.2f}",
            change=f"{curr_quote.get('change_pct', 0.0):+.2f}%",
            is_positive=curr_quote.get("change_pct", 0.0) >= 0,
            description="Mark Price"
        )
    with v_c2:
        render_metric_card(
            title="SPREAD",
            value=f"${curr_quote.get('spread', 0.04):.2f}",
            change="Simulated Liquidity",
            is_positive=None,
            description="Inside Market"
        )
    with v_c3:
        render_metric_card(
            title="EXCHANGE ROUTE",
            value=selected_sec.get("currency", "USD"),
            change=f"Sec ID: {selected_sec['security_id']}",
            is_positive=None,
            description=selected_sec.get("security_type", "EQUITY")
        )

    # Simulated Level-2 Order Book Depth Visualizer
    st.markdown("""
        <div style="background: #0d131f; padding: 12px; border-radius: 6px; border: 1px solid #1F2937; margin-top: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace; font-weight: 700; border-bottom: 1px solid #1F2937; padding-bottom: 4px;">
                <span>BID SIZE</span>
                <span>BID PRICE</span>
                <span style="color: #F8FAFC;">SPREAD</span>
                <span>ASK PRICE</span>
                <span>ASK SIZE</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; padding: 5px 0;">
                <span style="color: #34D399;">1,400</span>
                <span style="color: #34D399; font-weight: 700;">${:.2f}</span>
                <span style="color: #94A3B8;">${:.2f}</span>
                <span style="color: #F87171; font-weight: 700;">${:.2f}</span>
                <span style="color: #F87171;">950</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; padding: 5px 0;">
                <span style="color: #34D399;">2,100</span>
                <span style="color: #34D399; font-weight: 700;">${:.2f}</span>
                <span style="color: #64748B;">L2</span>
                <span style="color: #F87171; font-weight: 700;">${:.2f}</span>
                <span style="color: #F87171;">1,800</span>
            </div>
        </div>
    """.format(
        mark_price - 0.02,
        0.04,
        mark_price + 0.02,
        mark_price - 0.05,
        mark_price + 0.05
    ), unsafe_allow_html=True)

st.markdown("<div class='quant-divider'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# ORDERS & TRADES TABLES
# -------------------------------------------------------------
t_tab1, t_tab2, t_tab3 = st.tabs([
    "⚡ Open Orders (Pending)",
    "📜 Full Order History",
    "💰 Executed Trades & Fills"
])

with t_tab1:
    open_orders_df = get_open_orders(portfolio_id=selected_portfolio_id)
    render_orders_table(open_orders_df)

with t_tab2:
    all_orders_df = get_orders(portfolio_id=selected_portfolio_id)
    render_orders_table(all_orders_df)

with t_tab3:
    trades_df = get_trades(portfolio_id=selected_portfolio_id)
    render_trades_table(trades_df)
