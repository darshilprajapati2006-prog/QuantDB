"""
QuantDB — Market Data Research & Live Trading Terminal
Provides high-resolution OHLCV candlestick time-series, live order routing,
Level-2 order book depth, streaming tape, and market microstructure analysis.
"""

from datetime import datetime, timedelta
from pathlib import Path
import random
import sys
# pyrefly: ignore[missing-import]
import streamlit as st
import pandas as pd
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    # Streamlit's native fragment timer below keeps the simulation live without
    # requiring this optional component to be installed in the active runtime.
    st_autorefresh = None

# Setup sys.path for clean imports
_current_dir = Path(__file__).resolve().parent.parent
_root_dir = _current_dir.parent
for _p in [str(_root_dir), str(_current_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dashboard.components.theme import apply_terminal_theme
from dashboard.components.sidebar import render_sidebar
from dashboard.components.status import render_simulation_banner
from dashboard.components.metrics import render_metric_card, format_currency, format_pct
from dashboard.components.charts import render_candlestick_chart
from dashboard.components.tables import render_market_data_table, render_orders_table
from dashboard.services.market_service import (
    get_available_securities,
    get_available_exchanges,
    get_historical_market_data,
    clear_market_service_cache,
)
from dashboard.services.portfolio_service import (
    get_all_portfolios,
    get_portfolio_summary,
    clear_portfolio_service_cache,
)
from dashboard.services.trading_service import (
    submit_simulated_order,
    get_orders,
    clear_trading_service_cache,
)
from dashboard.providers.factory import get_current_data_mode
from dashboard.services.auth_service import require_auth


_SIMULATION_TIMEFRAMES = {
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "1H": timedelta(hours=1),
    "1D": timedelta(days=1),
}


def _seed_simulation_bars(symbol: str, price: float, timeframe: str, count: int = 120) -> list[dict]:
    duration = _SIMULATION_TIMEFRAMES[timeframe]
    rng = random.Random(f"{symbol}:{timeframe}:quantdb-simulation")
    now = datetime.now()
    bucket_now = now.replace(second=0, microsecond=0)
    if timeframe == "5m":
        bucket_now = bucket_now.replace(minute=(bucket_now.minute // 5) * 5)
    elif timeframe == "15m":
        bucket_now = bucket_now.replace(minute=(bucket_now.minute // 15) * 15)
    elif timeframe == "1H":
        bucket_now = bucket_now.replace(minute=0)
    elif timeframe == "1D":
        bucket_now = bucket_now.replace(hour=0, minute=0)
    interval_volatility = 0.0015 if timeframe in {"1m", "5m"} else 0.003
    closes = [price * (1.0 + rng.uniform(-0.025, -0.005))]
    for _ in range(count - 1):
        closes.append(max(0.01, closes[-1] * (1.0 + rng.gauss(0, interval_volatility))))
    bars = []
    start = bucket_now - duration * count
    for index, close in enumerate(closes):
        open_price = closes[index - 1] if index else close * (1.0 + rng.gauss(0, interval_volatility / 3))
        high_price = max(open_price, close) * (1.0 + abs(rng.gauss(0, interval_volatility / 2)))
        low_price = min(open_price, close) * (1.0 - abs(rng.gauss(0, interval_volatility / 2)))
        bars.append({
            "timestamp": start + duration * index,
            "open_price": round(open_price, 2),
            "high_price": round(high_price, 2),
            "low_price": round(low_price, 2),
            "close_price": round(close, 2),
            "volume": rng.randint(800, 24000),
        })
    bars[-1]["close_price"] = round(price, 2)
    bars[-1]["high_price"] = max(bars[-1]["high_price"], round(price, 2))
    bars[-1]["low_price"] = min(bars[-1]["low_price"], round(price, 2))
    return bars


def _advance_simulation(feed: dict, symbol: str, timeframe: str) -> None:
    now = datetime.now()
    previous_price = float(feed["price"])
    drift = random.gauss(0.00002, 0.00055)
    next_price = max(0.01, round(previous_price * (1.0 + drift), 2))
    volume = random.randint(25, 950)
    feed["price"] = next_price
    feed["spread"] = max(0.01, round(next_price * random.uniform(0.00015, 0.00045), 2))
    feed["volume"] = int(feed.get("volume", 0)) + volume
    feed["ticks_count"] = int(feed.get("ticks_count", 0)) + 1
    feed["imbalance"] = max(-1.0, min(1.0, float(feed.get("imbalance", 0.0)) + random.uniform(-0.08, 0.08)))
    feed["last_tick_at"] = now
    side = "BUY" if next_price >= previous_price else "SELL"
    feed.setdefault("recent_trades", []).insert(0, {
        "time": now.strftime("%H:%M:%S"), "side": side, "price": next_price, "shares": volume,
    })
    feed["recent_trades"] = feed["recent_trades"][:40]
    bar_sets = feed.setdefault("bars_by_interval", {})
    bars = bar_sets.get(timeframe)
    if bars is None:
        bars = _seed_simulation_bars(symbol, previous_price, timeframe)
    bucket = now.replace(second=0, microsecond=0)
    if timeframe == "5m":
        bucket = bucket.replace(minute=(bucket.minute // 5) * 5)
    elif timeframe == "15m":
        bucket = bucket.replace(minute=(bucket.minute // 15) * 15)
    elif timeframe == "1H":
        bucket = bucket.replace(minute=0)
    elif timeframe == "1D":
        bucket = bucket.replace(hour=0, minute=0)
    if bars and bars[-1]["timestamp"] == bucket:
        bar = bars[-1]
        bar["high_price"] = max(bar["high_price"], next_price)
        bar["low_price"] = min(bar["low_price"], next_price)
        bar["close_price"] = next_price
        bar["volume"] += volume
    else:
        bars.append({
            "timestamp": bucket,
            "open_price": previous_price,
            "high_price": max(previous_price, next_price),
            "low_price": min(previous_price, next_price),
            "close_price": next_price,
            "volume": volume,
        })
    bar_sets[timeframe] = bars[-400:]

# Page configuration
st.set_page_config(
    page_title="QuantDB — Market Data & Live Trading",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and authentication guard
apply_terminal_theme()
require_auth("Market Data")
render_sidebar(current_page="Market Data")

# Top Disclaimer Banner
render_simulation_banner("Paper-Only Live Simulation • Simulated Quotes, Candles, Order Book & Order Routing")

# -------------------------------------------------------------
# TOP CONTROLS & SECURITY FILTERS
# -------------------------------------------------------------
securities = get_available_securities()
exchanges = get_available_exchanges()

if not securities:
    st.error("Unable to load market data: No securities found in provider.")
    st.stop()

filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([2.5, 2, 2, 2, 1.5])

with filter_col2:
    exch_options = ["ALL EXCHANGES"] + [e["exchange_code"] for e in exchanges]
    selected_exch = st.selectbox("Exchange", options=exch_options, index=0, key="md_exchange_filter")

exchange_by_id = {str(exchange.get("exchange_id")): exchange.get("exchange_code") for exchange in exchanges}
exchange_securities = securities if selected_exch == "ALL EXCHANGES" else [
    security for security in securities
    if security.get("exchange_code") == selected_exch
    or exchange_by_id.get(str(security.get("exchange_id"))) == selected_exch
]
if not exchange_securities:
    st.warning(f"No securities are configured for {selected_exch}.")
    st.stop()

with filter_col1:
    sec_options = [f"{security['symbol']} — {security['security_name']}" for security in exchange_securities]
    if st.session_state.get("md_security_instrument") not in sec_options:
        st.session_state["md_security_instrument"] = sec_options[0]
    sec_selection = st.selectbox("Security Instrument", options=sec_options, key="md_security_instrument")
    selected_symbol = sec_selection.split(" — ")[0]
    selected_sec = next((security for security in exchange_securities if security["symbol"] == selected_symbol), exchange_securities[0])

with filter_col3:
    default_start = datetime.now().date() - timedelta(days=90)
    start_date = st.date_input("Start Date", value=default_start)

with filter_col4:
    end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=1))

with filter_col5:
    interval = st.selectbox("History interval", options=["1D", "1H", "15m"], index=0)

# Validation check
if start_date > end_date:
    st.error("Invalid Date Range: Start Date cannot be after End Date.")
    st.stop()

# -------------------------------------------------------------
# DATA RETRIEVAL (VIA SERVICE LAYER)
# -------------------------------------------------------------
with st.spinner(f"Loading market data for {selected_symbol}..."):
    df_market = get_historical_market_data(
        security_id=selected_sec["security_id"],
        symbol=selected_symbol,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time()),
        interval=interval
    )

if df_market.empty:
    st.info(f"No archived bars found for {selected_symbol} in this date range. The live simulation remains available.")
    baseline_price = float(selected_sec.get("base_price") or 100.0)
    latest_row = {
        "timestamp": datetime.now(),
        "close_price": baseline_price,
        "volume": 0,
        "spread": max(0.01, baseline_price * 0.0003),
        "order_book_imbalance": 0.0,
    }
    prev_row = latest_row
else:
    df_market = df_market.sort_values("timestamp").reset_index(drop=True)
    latest_row = df_market.iloc[-1]
    prev_row = df_market.iloc[-2] if len(df_market) >= 2 else latest_row

# -------------------------------------------------------------
# LIVE TICK SIMULATION ENGINE IN SESSION STATE
# -------------------------------------------------------------
tick_key = f"live_feed_{selected_symbol}"
if tick_key not in st.session_state:
    base_price = float(latest_row["close_price"])
    base_spread = max(0.04, float(latest_row.get("spread", 0.10)))
    st.session_state[tick_key] = {
        "price": base_price,
        "spread": base_spread,
        "volume": 0,
        "ticks_count": 0,
        "recent_trades": [],
        "bars_by_interval": {},
        "last_tick_at": None,
        "imbalance": random.uniform(-0.3, 0.3),
    }

live_feed = st.session_state[tick_key]
if "market_sim_running" not in st.session_state:
    st.session_state["market_sim_running"] = True
if st.session_state["market_sim_running"]:
    if hasattr(st, "fragment"):
        @st.fragment(run_every=2)
        def _refresh_live_market_data():
            # The page's chart, metrics, and order book are rendered outside this
            # fragment, so request a normal app rerun when the timer fires.
            st.rerun()

        _refresh_live_market_data()
    elif st_autorefresh is not None:
        st_autorefresh(interval=2000, key=f"market-simulation-refresh-{selected_symbol}")
    last_tick_at = live_feed.get("last_tick_at")
    if last_tick_at is None or (datetime.now() - last_tick_at).total_seconds() >= 1.8:
        _advance_simulation(live_feed, selected_symbol, st.session_state.get("market_chart_timeframe", "1m"))
elif live_feed.get("last_tick_at") is None:
    _advance_simulation(live_feed, selected_symbol, st.session_state.get("market_chart_timeframe", "1m"))
cur_price = live_feed["price"]
cur_spread = live_feed["spread"]
cur_bid = round(cur_price - (cur_spread / 2.0), 2)
cur_ask = round(cur_price + (cur_spread / 2.0), 2)
live_change = cur_price - prev_row["close_price"]
live_change_pct = (live_change / prev_row["close_price"]) * 100 if prev_row["close_price"] > 0 else 0.0
rel_spread_bps = (cur_spread / cur_price) * 10000.0 if cur_price > 0 else 4.0

# -------------------------------------------------------------
# PAGE HEADER WITH LIVE TRADING STREAM STATUS & QUICK CONTROLS
# -------------------------------------------------------------
hdr_col1, hdr_col2, hdr_col3 = st.columns([6, 2.2, 1.8])
with hdr_col1:
    st.markdown(f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; align-items: baseline; gap: 12px;">
                <h1 style="margin: 0; font-size: 1.70rem; font-weight: 800; color: #F8FAFC;">
                    MARKET DATA <span style="color: #06B6D4;">& LIVE TRADING</span>
                </h1>
                <span class="status-pill status-pill-green" style="font-size: 0.72rem;">
                    ● SIMULATION {'RUNNING' if st.session_state.get('market_sim_running', True) else 'PAUSED'}
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

with hdr_col2:
    simulation_label = "⏸ Pause" if st.session_state["market_sim_running"] else "▶ Resume"
    if st.button(simulation_label, key="btn_toggle_simulation", use_container_width=True, type="secondary"):
        st.session_state["market_sim_running"] = not st.session_state["market_sim_running"]
        st.rerun()

with hdr_col3:
    if st.button("⚡ Step tick", key="btn_next_tick", use_container_width=True):
        _advance_simulation(live_feed, selected_symbol, st.session_state.get("market_chart_timeframe", "1m"))
        st.rerun()

# -------------------------------------------------------------
# SUMMARY METRICS
# -------------------------------------------------------------
ts_label = live_feed["last_tick_at"].strftime("%H:%M:%S") if live_feed.get("last_tick_at") else datetime.now().strftime("%H:%M:%S")
vol_num = int(live_feed["volume"])
vol_str = f"{vol_num / 1e6:.1f}M" if vol_num >= 1e6 else f"{vol_num:,}"
metric_items = [
    ("LIVE SIM PRICE", format_currency(cur_price), f"{live_change:+.2f} ({live_change_pct:+.2f}%)", live_change >= 0, f"Tick {live_feed['ticks_count']} · {ts_label}"),
    ("NET CHANGE", f"{live_change:+.2f}", format_pct(live_change_pct, include_sign=True), live_change >= 0, "From prior reference close"),
    ("SIMULATED VOLUME", vol_str, "Paper feed", None, f"History: {interval}"),
    ("BEST BID", format_currency(cur_bid), "Level 1", None, "Highest simulated buyer quote"),
    ("BEST ASK", format_currency(cur_ask), "Level 1", None, "Lowest simulated seller quote"),
    ("BID–ASK SPREAD", f"${cur_spread:.2f}", f"{rel_spread_bps:.1f} bps", None, "Simulated liquidity friction"),
]
for metric_offset in range(0, len(metric_items), 3):
    metric_columns = st.columns(3, gap="medium")
    for metric_column, metric in zip(metric_columns, metric_items[metric_offset:metric_offset + 3]):
        with metric_column:
            render_metric_card(title=metric[0], value=metric[1], change=metric[2], is_positive=metric[3], description=metric[4])

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# MAIN WORKSPACE: CANDLESTICK CHART & DIRECT LIVE TRADING DESK
# -------------------------------------------------------------
chart_col, trade_col = st.columns([6.8, 3.2])

with chart_col:
    chart_header, chart_controls = st.columns([7, 2])
    with chart_header:
        st.markdown(f"**{selected_symbol} · SIMULATED LIVE CANDLES**  ·  {live_feed['ticks_count']:,} ticks")
        st.caption("Paper-only generated price action. Database history is available in the archive tab.")
    with chart_controls:
        chart_timeframe = st.selectbox("Chart timeframe", options=list(_SIMULATION_TIMEFRAMES), index=0, key="market_chart_timeframe", label_visibility="collapsed")
    df_display = pd.DataFrame(live_feed.get("bars_by_interval", {}).get(chart_timeframe, []))
    if df_display.empty:
        seeded_bars = _seed_simulation_bars(selected_symbol, cur_price, chart_timeframe)
        now = datetime.now()
        current_bucket = now.replace(second=0, microsecond=0)
        if chart_timeframe == "5m":
            current_bucket = current_bucket.replace(minute=(current_bucket.minute // 5) * 5)
        elif chart_timeframe == "15m":
            current_bucket = current_bucket.replace(minute=(current_bucket.minute // 15) * 15)
        elif chart_timeframe == "1H":
            current_bucket = current_bucket.replace(minute=0)
        elif chart_timeframe == "1D":
            current_bucket = current_bucket.replace(hour=0, minute=0)
        seeded_bars.append({"timestamp": current_bucket, "open_price": cur_price, "high_price": cur_price, "low_price": cur_price, "close_price": cur_price, "volume": 0})
        live_feed.setdefault("bars_by_interval", {})[chart_timeframe] = seeded_bars[-400:]
        df_display = pd.DataFrame(live_feed.get("bars_by_interval", {}).get(chart_timeframe, []))
    render_candlestick_chart(df_display, symbol=selected_symbol, height=430)

    # Market Microstructure metrics
    st.markdown("""
        <div style="font-size: 0.80rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin: 12px 0 8px 0;">
            Market Microstructure & Order Book Analytics
        </div>
    """, unsafe_allow_html=True)

    micro_c1, micro_c2, micro_c3, micro_c4 = st.columns(4)
    with micro_c1:
        render_metric_card(
            title="SPREAD (ABSOLUTE)",
            value=f"${cur_spread:.4f}",
            change="Ask - Bid",
            is_positive=None,
            description="Touch Spread"
        )
    with micro_c2:
        mid_prc = round((cur_bid + cur_ask) / 2.0, 4)
        render_metric_card(
            title="MID-MARKET PRICE",
            value=format_currency(mid_prc, precision=4),
            change="(Bid + Ask) / 2",
            is_positive=None,
            description="Theoretical fair value"
        )
    with micro_c3:
        render_metric_card(
            title="RELATIVE SPREAD",
            value=f"{rel_spread_bps:.2f} bps",
            change="Spread / Mid × 10,000",
            is_positive=rel_spread_bps < 10.0,
            description="Tighter = higher liquidity"
        )
    with micro_c4:
        imbalance = float(live_feed.get("imbalance", 0.0))
        bias = "BUY BIAS" if imbalance > 0.1 else ("SELL BIAS" if imbalance < -0.1 else "NEUTRAL")
        render_metric_card(
            title="ORDER BOOK IMBALANCE",
            value=f"{imbalance:+.3f}",
            change=bias,
            is_positive=imbalance > 0,
            description="Order book pressure"
        )

with trade_col:
    # ---------------------------------------------------------
    # DIRECT LIVE TRADING EXECUTION DOCK
    # ---------------------------------------------------------
    mode_str = get_current_data_mode()
    mode_badge_color = "status-pill-green" if mode_str == "REAL" else "status-pill-cyan"
    mode_label = "AIVEN MYSQL REAL" if mode_str == "REAL" else "MOCK ENGINE"

    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-size: 0.82rem; text-transform: uppercase; color: #F8FAFC; font-weight: 700; letter-spacing: 0.08em;">
                ⚡ Live Trading Desk
            </div>
            <span class="status-pill {mode_badge_color}" style="font-size: 0.62rem;">
                {mode_label}
            </span>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='quant-card' style='padding: 14px;'>", unsafe_allow_html=True)

        # 1. Target Portfolio
        portfolios = get_all_portfolios()
        if portfolios:
            port_map = {f"{p['portfolio_name']} (ID: {p['portfolio_id']})": p["portfolio_id"] for p in portfolios}
            sel_port_label = st.selectbox("Portfolio Account", options=list(port_map.keys()), index=0, key="md_port_select")
            active_pid = port_map[sel_port_label]
            port_info = get_portfolio_summary(active_pid)
            cash_avail = port_info.get("cash", 0.0) if port_info else 0.0
            st.markdown(f"""
                <div style="display: flex; justify-content: space-between; font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; margin: -4px 0 10px 0;">
                    <span style="color: #64748B;">Buying Power:</span>
                    <span style="color: #34D399; font-weight: 700;">{format_currency(cash_avail)}</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            active_pid = 1

        # 2. Side & Order Type
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            trade_side = st.radio("Side", options=["BUY", "SELL"], horizontal=True, index=0, key="md_trade_side")
        with t_col2:
            trade_type = st.radio("Type", options=["MARKET", "LIMIT"], horizontal=True, index=0, key="md_order_type")

        # 3. Quantity & Quick Presets
        qty_col, prc_col = st.columns(2)
        with qty_col:
            trade_qty = st.number_input("Shares", min_value=1, max_value=500000, value=100, step=10, key="md_trade_qty")
        with prc_col:
            default_exec_prc = cur_ask if trade_side == "BUY" else cur_bid
            if trade_type == "LIMIT":
                trade_price = st.number_input("Limit Price ($)", min_value=0.01, value=float(round(default_exec_prc, 2)), step=0.1, key="md_trade_price")
            else:
                st.text_input("Estimated Price", value=f"${default_exec_prc:.2f} (MKT)", disabled=True)
                trade_price = float(round(default_exec_prc, 2))

        # Quick size buttons
        st.markdown("<div style='font-size: 0.68rem; color: #94A3B8; margin-bottom: 4px;'>Quick Quantity:</div>", unsafe_allow_html=True)
        q_b1, q_b2 = st.columns(2)
        with q_b1:
            if st.button("+10", key="btn_q10", use_container_width=True):
                st.session_state["md_trade_qty"] = 10
                st.rerun()
        with q_b2:
            if st.button("+50", key="btn_q50", use_container_width=True):
                st.session_state["md_trade_qty"] = 50
                st.rerun()
        q_b3, q_b4 = st.columns(2)
        with q_b3:
            if st.button("+100", key="btn_q100", use_container_width=True):
                st.session_state["md_trade_qty"] = 100
                st.rerun()
        with q_b4:
            if st.button("+500", key="btn_q500", use_container_width=True):
                st.session_state["md_trade_qty"] = 500
                st.rerun()

        # Trade calculation breakdown
        notional = trade_qty * trade_price
        fee = round(notional * 0.0001, 2)
        st.markdown(f"""
            <div style="background: rgba(13, 19, 31, 0.9); padding: 8px 12px; border-radius: 4px; border: 1px solid #1E293B; margin: 10px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.74rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                    <span style="color: #94A3B8;">Est. Notional:</span>
                    <span style="color: #F8FAFC; font-weight: 700;">{format_currency(notional)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94A3B8;">Est. Fee (1 bps):</span>
                    <span style="color: #94A3B8;">{format_currency(fee)}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Submit Action Button
        btn_label = f"⚡ SUBMIT LIVE {trade_side} ORDER"
        btn_type = "primary" if trade_side == "BUY" else "secondary"
        if st.button(btn_label, use_container_width=True, type=btn_type, key="btn_submit_live_order"):
            success, msg, ord_obj = submit_simulated_order(
                portfolio_id=active_pid,
                security_id=selected_sec["security_id"],
                symbol=selected_symbol,
                side=trade_side,
                order_type=trade_type,
                quantity=int(trade_qty),
                price=float(trade_price),
            )
            if success:
                st.success(f"✅ {msg}")
                # Record in live tape
                live_feed["recent_trades"].insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "side": trade_side,
                    "price": trade_price,
                    "shares": int(trade_qty),
                })
                clear_trading_service_cache()
                clear_portfolio_service_cache()
                st.rerun()
            else:
                st.error(f"❌ Execution Rejected: {msg}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # LIVE LEVEL-2 ORDER BOOK DEPTH LADDER
    # ---------------------------------------------------------
    st.markdown("""
        <div style="font-size: 0.80rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin: 12px 0 8px 0;">
            Level-2 Order Depth Ladder
        </div>
    """, unsafe_allow_html=True)

    bids_depth = [(round(cur_bid - 0.05 * level, 2), random.randint(800, 9200)) for level in range(5)]
    asks_depth = [(round(cur_ask + 0.05 * level, 2), random.randint(800, 9200)) for level in range(5)]

    ladder_html = """
    <div style="background: rgba(13, 19, 31, 0.95); padding: 10px; border-radius: 6px; border: 1px solid #1E293B; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;">
        <div style="display: flex; justify-content: space-between; color: #64748B; font-weight: 700; border-bottom: 1px solid #1E293B; padding-bottom: 4px; margin-bottom: 6px;">
            <span>BID SIZE</span>
            <span>BID ($)</span>
            <span>ASK ($)</span>
            <span>ASK SIZE</span>
        </div>
    """
    for (b_p, b_s), (a_p, a_s) in zip(bids_depth, asks_depth):
        ladder_html += f"""
        <div style="display: flex; justify-content: space-between; padding: 2px 0;">
            <span style="color: #10B981; font-weight: 600;">{b_s:,}</span>
            <span style="color: #34D399;">${b_p:.2f}</span>
            <span style="color: #F43F5E;">${a_p:.2f}</span>
            <span style="color: #FB7185; font-weight: 600;">{a_s:,}</span>
        </div>
        """
    ladder_html += f"""
        <div style="margin-top: 6px; border-top: 1px solid #1E293B; padding-top: 4px; display: flex; justify-content: space-between; color: #94A3B8; font-size: 0.68rem;">
            <span>TOUCH SPREAD:</span>
            <span style="color: #06B6D4; font-weight: 700;">${cur_spread:.2f} ({rel_spread_bps:.1f} bps)</span>
        </div>
    </div>
    """
    st.markdown(ladder_html, unsafe_allow_html=True)

st.markdown("<div class='quant-divider'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# INTERACTIVE TABS: LIVE TAPE, ACTIVE ORDERS & HISTORICAL RECORDS
# -------------------------------------------------------------
tab_tape, tab_my_orders, tab_history = st.tabs([
    "⚡ Streaming Trade Tape",
    f"📋 {selected_symbol} Orders & Executions",
    "📜 Historical Market Data Archive"
])

with tab_tape:
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em;">
                Live Tape • Recent Executions for {selected_symbol}
            </div>
            <span style="font-size: 0.70rem; color: #10B981; font-family: 'JetBrains Mono', monospace;">
                STREAMING DIRECT TICKS
            </span>
        </div>
    """, unsafe_allow_html=True)

    recent_trades = live_feed.get("recent_trades", [])
    if recent_trades:
        tape_df = pd.DataFrame(recent_trades)
        st.dataframe(
            tape_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "time": st.column_config.TextColumn("Execution Time"),
                "side": st.column_config.TextColumn("Side"),
                "price": st.column_config.NumberColumn("Price ($)", format="$%.2f"),
                "shares": st.column_config.NumberColumn("Shares Filled", format="%d"),
            }
        )
    else:
        st.info("No live trade ticks recorded yet in this session.")

with tab_my_orders:
    all_orders = get_orders()
    sym_orders = all_orders[all_orders["symbol"] == selected_symbol] if not all_orders.empty and "symbol" in all_orders.columns else pd.DataFrame()
    if not sym_orders.empty:
        render_orders_table(sym_orders)
    else:
        st.info(f"No recent order executions recorded for {selected_symbol} in current view.")

with tab_history:
    render_market_data_table(df_market.sort_values(by="timestamp", ascending=False))

