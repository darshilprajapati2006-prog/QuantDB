"""
QuantDB Reusable Table Components.
Renders finance-specific dataframes with proper number, currency, and timestamp formatting.
Adheres strictly to the QuantDB project data contracts.
"""

from typing import Optional
import pandas as pd
import streamlit as st


def render_dataframe(df: pd.DataFrame, **kwargs):
    """Renders DataFrame with modern width='stretch' and fallback to use_container_width=True."""
    try:
        st.dataframe(df, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kwargs)


def render_market_data_table(df: pd.DataFrame, max_rows: int = 50):
    """
    Renders formatted historical OHLCV & microstructure table:
    timestamp, symbol, open, high, low, close, volume, bid, ask, spread, mid_price, bps.
    """
    if df.empty:
        st.info("No market observations found for the specified filters.")
        return

    display_df = df.head(max_rows).copy()

    # Column configuration
    col_config = {
        "timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
        "symbol": st.column_config.TextColumn("Symbol", width="small"),
        "open_price": st.column_config.NumberColumn("Open", format="$%.2f"),
        "high_price": st.column_config.NumberColumn("High", format="$%.2f"),
        "low_price": st.column_config.NumberColumn("Low", format="$%.2f"),
        "close_price": st.column_config.NumberColumn("Close", format="$%.2f"),
        "volume": st.column_config.NumberColumn("Volume", format="%d"),
        "bid_price": st.column_config.NumberColumn("Bid", format="$%.2f"),
        "ask_price": st.column_config.NumberColumn("Ask", format="$%.2f"),
        "spread": st.column_config.NumberColumn("Spread", format="$%.4f"),
        "mid_price": st.column_config.NumberColumn("Mid Price", format="$%.4f"),
        "relative_spread_bps": st.column_config.NumberColumn("Spread (bps)", format="%.2f"),
        "order_book_imbalance": st.column_config.NumberColumn("OB Imbalance", format="%.3f"),
    }

    # Only include existing columns
    active_configs = {k: v for k, v in col_config.items() if k in display_df.columns}

    render_dataframe(
        display_df,
        column_config=active_configs,
        hide_index=True,
    )


def render_orders_table(df: pd.DataFrame, max_rows: int = 100):
    """
    Renders simulated order log:
    order_id, timestamp, symbol, side, order_type, quantity, price, status.
    """
    if df.empty:
        st.info("No orders in this view.")
        return

    display_df = df.head(max_rows).copy()

    col_config = {
        "order_id": st.column_config.NumberColumn("Order ID", format="#%d", width="small"),
        "timestamp": st.column_config.TextColumn("Time", width="medium"),
        "symbol": st.column_config.TextColumn("Symbol", width="small"),
        "side": st.column_config.TextColumn("Side", width="small"),
        "order_type": st.column_config.TextColumn("Type", width="small"),
        "quantity": st.column_config.NumberColumn("Qty", format="%d"),
        "price": st.column_config.NumberColumn("Order Price", format="$%.2f"),
        "status": st.column_config.TextColumn("Status", width="small"),
    }

    active_configs = {k: v for k, v in col_config.items() if k in display_df.columns}

    render_dataframe(
        display_df,
        column_config=active_configs,
        hide_index=True,
    )


def render_trades_table(df: pd.DataFrame, max_rows: int = 100):
    """
    Renders simulated executions / trade log:
    trade_id, timestamp, symbol, side, quantity, execution_price, pnl, transaction_cost.
    """
    if df.empty:
        st.info("No trade executions recorded.")
        return

    display_df = df.head(max_rows).copy()

    col_config = {
        "trade_id": st.column_config.NumberColumn("Trade ID", format="#%d", width="small"),
        "timestamp": st.column_config.TextColumn("Execution Time", width="medium"),
        "symbol": st.column_config.TextColumn("Symbol", width="small"),
        "side": st.column_config.TextColumn("Side", width="small"),
        "quantity": st.column_config.NumberColumn("Qty", format="%d"),
        "execution_price": st.column_config.NumberColumn("Exec Price", format="$%.2f"),
        "pnl": st.column_config.NumberColumn("Realized P&L", format="$%.2f"),
        "transaction_cost": st.column_config.NumberColumn("Fees", format="$%.2f"),
    }

    active_configs = {k: v for k, v in col_config.items() if k in display_df.columns}

    render_dataframe(
        display_df,
        column_config=active_configs,
        hide_index=True,
    )


def render_positions_table(df: pd.DataFrame):
    """
    Renders portfolio holdings table:
    symbol, quantity, average_price, current_price, market_value, unrealized_pnl, weight.
    """
    if df.empty:
        st.info("No active positions in this portfolio.")
        return

    display_df = df.copy()

    col_config = {
        "symbol": st.column_config.TextColumn("Symbol", width="small"),
        "quantity": st.column_config.NumberColumn("Position Qty", format="%d"),
        "average_price": st.column_config.NumberColumn("Avg Cost", format="$%.2f"),
        "current_price": st.column_config.NumberColumn("Mark Price", format="$%.2f"),
        "market_value": st.column_config.NumberColumn("Market Value", format="$%.2f"),
        "unrealized_pnl": st.column_config.NumberColumn("Unrealized P&L ($)", format="$%.2f"),
        "unrealized_pnl_pct": st.column_config.NumberColumn("P&L (%)", format="%.2f%%"),
        "weight": st.column_config.NumberColumn("Weight (%)", format="%.2f%%"),
    }

    active_configs = {k: v for k, v in col_config.items() if k in display_df.columns}

    render_dataframe(
        display_df,
        column_config=active_configs,
        hide_index=True,
    )


def render_backtest_results_table(df: pd.DataFrame):
    """
    Renders backtest execution summary comparison table.
    """
    if df.empty:
        st.info("No backtesting history available.")
        return

    col_config = {
        "trade_id": st.column_config.NumberColumn("Trade #", format="%d"),
        "entry_time": st.column_config.TextColumn("Entry Date"),
        "symbol": st.column_config.TextColumn("Symbol"),
        "side": st.column_config.TextColumn("Side"),
        "quantity": st.column_config.NumberColumn("Shares", format="%d"),
        "pnl": st.column_config.NumberColumn("Net P&L", format="$%.2f"),
        "return_pct": st.column_config.NumberColumn("Return", format="%.2f%%"),
        "holding_period_days": st.column_config.NumberColumn("Days Held", format="%d"),
        "result": st.column_config.TextColumn("Outcome"),
    }

    active_configs = {k: v for k, v in col_config.items() if k in df.columns}

    render_dataframe(
        df,
        column_config=active_configs,
        hide_index=True,
    )
