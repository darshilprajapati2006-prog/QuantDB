"""
QuantDB — Market Data Research Terminal
Provides high-resolution OHLCV candlestick time-series, volume profiling,
historical quote archives, and market microstructure analysis.
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
from dashboard.components.metrics import render_metric_card, format_currency, format_pct
from dashboard.components.charts import render_candlestick_chart, render_volume_chart
from dashboard.components.tables import render_market_data_table
from dashboard.services.market_service import (
    get_available_securities,
    get_available_exchanges,
    get_historical_market_data,
)

# Page configuration
st.set_page_config(
    page_title="QuantDB — Market Data Research",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and sidebar
apply_terminal_theme()
render_sidebar(current_page="Market Data")

# Top Disclaimer
render_simulation_banner("Simulated Market Feeds • Historical & Microstructure Analytics")

# Page Header
st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; align-items: baseline; gap: 10px;">
            <h1 style="margin: 0; font-size: 1.75rem; font-weight: 800; color: #F8FAFC;">
                MARKET DATA <span style="color: #06B6D4;">RESEARCH</span>
            </h1>
            <span style="color: #64748B; font-size: 0.90rem;">
                Time-Series OHLCV & Microstructure Analysis
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# TOP CONTROLS & FILTERS
# -------------------------------------------------------------
securities = get_available_securities()
exchanges = get_available_exchanges()

if not securities:
    st.error("Unable to load market data: No securities found in provider.")
    st.stop()

filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([2.5, 2, 2, 2, 1.5])

with filter_col1:
    sec_options = [f"{s['symbol']} — {s['security_name']}" for s in securities]
    sec_selection = st.selectbox("Security Instrument", options=sec_options, index=0)
    selected_symbol = sec_selection.split(" — ")[0]
    selected_sec = next((s for s in securities if s["symbol"] == selected_symbol), securities[0])

with filter_col2:
    exch_options = ["ALL EXCHANGES"] + [e["exchange_code"] for e in exchanges]
    selected_exch = st.selectbox("Exchange", options=exch_options, index=0)

with filter_col3:
    default_start = datetime.now() - timedelta(days=90)
    start_date = st.date_input("Start Date", value=default_start)

with filter_col4:
    end_date = st.date_input("End Date", value=datetime.now())

with filter_col5:
    interval = st.selectbox("Interval", options=["1D", "1H", "15m"], index=0)

# Validation check
if start_date > end_date:
    st.error("Invalid Date Range: Start Date cannot be after End Date.")
    st.stop()

# -------------------------------------------------------------
# DATA RETRIEVAL (VIA SERVICE LAYER ONLY)
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
    st.warning(f"No market data available for {selected_symbol} in the selected period.")
    st.stop()

# Compute summary stats from latest rows
latest_row = df_market.iloc[-1]
prev_row = df_market.iloc[-2] if len(df_market) >= 2 else latest_row
price_change = latest_row["close_price"] - prev_row["close_price"]
price_change_pct = (price_change / prev_row["close_price"]) * 100 if prev_row["close_price"] > 0 else 0.0

# -------------------------------------------------------------
# SUMMARY METRIC CARDS
# -------------------------------------------------------------
m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)

with m_col1:
    render_metric_card(
        title="LAST CLOSE",
        value=format_currency(latest_row["close_price"]),
        change=f"{price_change:+.2f} ({price_change_pct:+.2f}%)",
        is_positive=price_change >= 0,
        description=f"Close as of {latest_row['timestamp'][:10]}"
    )

with m_col2:
    render_metric_card(
        title="DAILY CHANGE",
        value=f"{price_change:+.2f}",
        change=format_pct(price_change_pct, include_sign=True),
        is_positive=price_change >= 0,
        description="Net Price Movement"
    )

with m_col3:
    render_metric_card(
        title="PERIOD VOLUME",
        value=f"{int(latest_row['volume']):,}",
        change="Simulated Vol",
        is_positive=None,
        description=f"Interval: {interval}"
    )

with m_col4:
    render_metric_card(
        title="BEST BID",
        value=format_currency(latest_row["bid_price"]),
        change="Order Depth Top",
        is_positive=None,
        description="Highest buyer quote"
    )

with m_col5:
    render_metric_card(
        title="BEST ASK",
        value=format_currency(latest_row["ask_price"]),
        change="Order Depth Top",
        is_positive=None,
        description="Lowest seller quote"
    )

with m_col6:
    spread_val = latest_row["spread"]
    render_metric_card(
        title="BID-ASK SPREAD",
        value=f"${spread_val:.2f}",
        change=f"{latest_row['relative_spread_bps']:.1f} bps",
        is_positive=None,
        description="Liquidity Friction"
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# MAIN CANDLESTICK + VOLUME CHART
# -------------------------------------------------------------
render_candlestick_chart(df_market, symbol=selected_symbol, height=450)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# MARKET MICROSTRUCTURE SECTION
# -------------------------------------------------------------
st.markdown("""
    <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 10px;">
        Market Microstructure & Order Book Analytics
    </div>
""", unsafe_allow_html=True)

micro_col1, micro_col2, micro_col3, micro_col4 = st.columns(4)

with micro_col1:
    render_metric_card(
        title="SPREAD (ABSOLUTE)",
        value=f"${latest_row['spread']:.4f}",
        change="Ask - Bid",
        is_positive=None,
        description="Touch Spread"
    )

with micro_col2:
    render_metric_card(
        title="MID-MARKET PRICE",
        value=format_currency(latest_row["mid_price"], precision=4),
        change="(Bid + Ask) / 2",
        is_positive=None,
        description="Theoretical fair value"
    )

with micro_col3:
    render_metric_card(
        title="RELATIVE SPREAD",
        value=f"{latest_row['relative_spread_bps']:.2f} bps",
        change="Spread / Mid × 10,000",
        is_positive=latest_row["relative_spread_bps"] < 10.0,
        description="Tighter indicates higher liquidity"
    )

with micro_col4:
    imbalance = latest_row["order_book_imbalance"]
    bias = "BUY BIAS" if imbalance > 0.1 else ("SELL BIAS" if imbalance < -0.1 else "NEUTRAL")
    render_metric_card(
        title="ORDER BOOK IMBALANCE",
        value=f"{imbalance:+.3f}",
        change=bias,
        is_positive=imbalance > 0,
        description="[-1.0 Sell-heavy to +1.0 Buy-heavy]"
    )

st.markdown("<div class='quant-divider'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# HISTORICAL MARKET DATA ARCHIVE TABLE
# -------------------------------------------------------------
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em;">
            Historical Market Data Records
        </div>
        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace;">
            SHOWING LATEST OBSERVATIONS
        </div>
    </div>
""", unsafe_allow_html=True)

render_market_data_table(df_market.sort_values(by="timestamp", ascending=False))
