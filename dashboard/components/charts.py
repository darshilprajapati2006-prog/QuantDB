"""
QuantDB Reusable Terminal Chart Components.
Built with Plotly with unified dark theme, high readability, and strict financial conventions.
Never duplicates chart styling across individual pages.
"""

from typing import Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Global Terminal Color Palette
DARK_BG = "#0B0F19"
SURFACE_BG = "#111827"
GRID_COLOR = "#1F2937"
TEXT_COLOR = "#94A3B8"
UP_GREEN = "#10B981"
DOWN_RED = "#EF4444"
CYAN_ACCENT = "#06B6D4"
BLUE_ACCENT = "#3B82F6"
BENCHMARK_COLOR = "#64748B"
FONT_FAMILY = "JetBrains Mono, monospace"


def _apply_terminal_layout(fig: go.Figure, title: Optional[str] = None, height: int = 420) -> go.Figure:
    """Applies unified dark quantitative terminal layout to a Plotly figure."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title.upper()}</b>" if title else None,
            font=dict(family=FONT_FAMILY, size=13, color="#E2E8F0"),
            x=0.01,
            y=0.98,
        ) if title else None,
        height=height,
        margin=dict(l=45, r=25, t=38 if title else 20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0d131f",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#111827",
            font_size=11,
            font_family=FONT_FAMILY,
            font_color="#F8FAFC",
            bordercolor="#374151"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        ),
        xaxis=dict(
            gridcolor=GRID_COLOR,
            showgrid=True,
            zeroline=False,
            tickfont=dict(family=FONT_FAMILY, size=10, color=TEXT_COLOR),
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            showgrid=True,
            zeroline=False,
            tickfont=dict(family=FONT_FAMILY, size=10, color=TEXT_COLOR),
            side="right",
        ),
    )
    return fig


def render_candlestick_chart(df: pd.DataFrame, symbol: str = "TICKER", height: int = 440):
    """
    Renders a 2-row subplot with Candlestick price on top and Volume bars below.
    Includes Moving Averages (SMA 20 & SMA 50) for market analysis.
    """
    if df.empty:
        st.info("No market data available to render candlestick chart.")
        return

    # Calculate rolling averages if enough data
    df = df.copy()
    if len(df) >= 20:
        df["sma20"] = df["close_price"].rolling(window=20).mean()
    else:
        df["sma20"] = np.nan
    if len(df) >= 50:
        df["sma50"] = df["close_price"].rolling(window=50).mean()
    else:
        df["sma50"] = np.nan

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df["timestamp"],
            open=df["open_price"],
            high=df["high_price"],
            low=df["low_price"],
            close=df["close_price"],
            name=f"{symbol} OHLC",
            increasing_line_color=UP_GREEN,
            decreasing_line_color=DOWN_RED,
            increasing_fillcolor=UP_GREEN,
            decreasing_fillcolor=DOWN_RED,
        ),
        row=1, col=1
    )

    # SMA Overlays
    if not df["sma20"].isna().all():
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"], y=df["sma20"],
                name="SMA 20", line=dict(color="#38BDF8", width=1.2)
            ),
            row=1, col=1
        )
    if not df["sma50"].isna().all():
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"], y=df["sma50"],
                name="SMA 50", line=dict(color="#F59E0B", width=1.2)
            ),
            row=1, col=1
        )

    # Volume Bars
    vol_colors = [UP_GREEN if c >= o else DOWN_RED for o, c in zip(df["open_price"], df["close_price"])]
    fig.add_trace(
        go.Bar(
            x=df["timestamp"],
            y=df["volume"],
            name="Volume",
            marker_color=vol_colors,
            opacity=0.6,
        ),
        row=2, col=1
    )

    fig.update_xaxes(rangeslider_visible=False)
    fig.update_yaxes(side="right", tickfont=dict(family=FONT_FAMILY, size=10, color=TEXT_COLOR))
    _apply_terminal_layout(fig, title=f"{symbol} — CANDLESTICK & VOLUME", height=height)
    st.plotly_chart(fig, use_container_width=True)


def render_volume_chart(df: pd.DataFrame, height: int = 220):
    """Renders standalone Volume distribution."""
    if df.empty:
        st.info("No volume data available.")
        return
    fig = go.Figure()
    vol_colors = [UP_GREEN if c >= o else DOWN_RED for o, c in zip(df["open_price"], df["close_price"])]
    fig.add_trace(
        go.Bar(
            x=df["timestamp"],
            y=df["volume"],
            name="Volume",
            marker_color=vol_colors,
        )
    )
    _apply_terminal_layout(fig, title="TRADING VOLUME", height=height)
    st.plotly_chart(fig, use_container_width=True)


def render_equity_curve(df: pd.DataFrame, title: str = "PORTFOLIO EQUITY CURVE", include_benchmark: bool = True, height: int = 380):
    """Renders equity curve line chart with comparative benchmark trace."""
    if df.empty or "portfolio_value" not in df.columns:
        st.info("No equity curve data available.")
        return

    fig = go.Figure()

    # Portfolio Equity Line
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["portfolio_value"],
            mode="lines",
            name="Portfolio Value",
            line=dict(color=CYAN_ACCENT, width=2.2),
            fill="tozeroy",
            fillcolor="rgba(6, 182, 212, 0.08)",
        )
    )

    # Benchmark Comparative Line
    if include_benchmark and "benchmark_value" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["benchmark_value"],
                mode="lines",
                name="S&P 500 Benchmark",
                line=dict(color=BENCHMARK_COLOR, width=1.5, dash="dash"),
            )
        )

    _apply_terminal_layout(fig, title=title, height=height)
    st.plotly_chart(fig, use_container_width=True)


def render_drawdown_chart(df: pd.DataFrame, title: str = "HISTORICAL DRAWDOWN (%)", height: int = 240):
    """Renders underwater drawdown chart filled in semi-transparent red."""
    if df.empty or "drawdown_pct" not in df.columns and "drawdown" not in df.columns:
        st.info("No drawdown data available.")
        return

    col = "drawdown_pct" if "drawdown_pct" in df.columns else "drawdown"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df[col],
            mode="lines",
            name="Drawdown %",
            line=dict(color=DOWN_RED, width=1.5),
            fill="tozeroy",
            fillcolor="rgba(239, 68, 68, 0.2)",
        )
    )
    _apply_terminal_layout(fig, title=title, height=height)
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)


def render_returns_chart(df: pd.DataFrame, title: str = "DAILY RETURNS (%)", height: int = 250):
    """Renders daily returns bar chart colored by positive/negative days."""
    if df.empty or "daily_return" not in df.columns:
        st.info("No returns data available.")
        return

    colors = [UP_GREEN if r >= 0 else DOWN_RED for r in df["daily_return"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["timestamp"],
            y=df["daily_return"],
            name="Daily Return %",
            marker_color=colors,
        )
    )
    _apply_terminal_layout(fig, title=title, height=height)
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)


def render_portfolio_allocation(positions_df: pd.DataFrame, title: str = "PORTFOLIO ALLOCATION", height: int = 340):
    """Renders a clean donut chart showing capital allocation across assets."""
    if positions_df.empty:
        st.info("No positions to allocate.")
        return

    fig = go.Figure(
        go.Pie(
            labels=positions_df["symbol"],
            values=positions_df["market_value"],
            hole=0.55,
            textinfo="label+percent",
            textfont=dict(family=FONT_FAMILY, size=11, color="#F8FAFC"),
            marker=dict(
                colors=["#06B6D4", "#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", "#EC4899", "#6366F1"],
                line=dict(color="#0B0F19", width=2)
            ),
            hoverinfo="label+value+percent",
        )
    )
    _apply_terminal_layout(fig, title=title, height=height)
    fig.update_layout(showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


def render_pnl_chart(positions_df: pd.DataFrame, title: str = "UNREALIZED P&L BY SECURITY", height: int = 320):
    """Renders horizontal bar chart of unrealized P&L per security."""
    if positions_df.empty:
        st.info("No position P&L data.")
        return

    df = positions_df.sort_values(by="unrealized_pnl", ascending=True)
    colors = [UP_GREEN if p >= 0 else DOWN_RED for p in df["unrealized_pnl"]]

    fig = go.Figure(
        go.Bar(
            y=df["symbol"],
            x=df["unrealized_pnl"],
            orientation="h",
            marker_color=colors,
            name="Unrealized P&L",
            text=[f"${x:+,.0f}" for x in df["unrealized_pnl"]],
            textposition="auto",
            textfont=dict(family=FONT_FAMILY, size=10, color="#FFFFFF"),
        )
    )
    _apply_terminal_layout(fig, title=title, height=height)
    st.plotly_chart(fig, use_container_width=True)


def render_return_distribution(returns_series: pd.Series, title: str = "RETURN DISTRIBUTION (HISTOGRAM)", height: int = 280):
    """Renders return frequency histogram with normal distribution comparison."""
    if returns_series.empty:
        st.info("No return distribution data.")
        return

    clean_series = returns_series.dropna()
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=clean_series,
            nbinsx=35,
            name="Frequency",
            marker_color=BLUE_ACCENT,
            opacity=0.75,
        )
    )
    _apply_terminal_layout(fig, title=title, height=height)
    fig.update_xaxes(ticksuffix="%", title_text="Return %")
    st.plotly_chart(fig, use_container_width=True)


def render_backtest_signals_chart(equity_df: pd.DataFrame, signals_df: pd.DataFrame, title: str = "STRATEGY EQUITY & SIGNALS", height: int = 380):
    """Renders backtest equity curve with entry/exit signal markers."""
    if equity_df.empty:
        st.info("No backtest equity curve available.")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity_df["timestamp"],
            y=equity_df["equity"],
            mode="lines",
            name="Strategy Equity",
            line=dict(color=CYAN_ACCENT, width=2.0),
        )
    )

    if not equity_df["benchmark"].isna().all():
        fig.add_trace(
            go.Scatter(
                x=equity_df["timestamp"],
                y=equity_df["benchmark"],
                mode="lines",
                name="Benchmark (Buy & Hold)",
                line=dict(color=BENCHMARK_COLOR, width=1.5, dash="dot"),
            )
        )

    _apply_terminal_layout(fig, title=title, height=height)
    st.plotly_chart(fig, use_container_width=True)
