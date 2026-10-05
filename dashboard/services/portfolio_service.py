"""
QuantDB Portfolio Service.
Coordinates portfolio valuations, active positions, asset allocations,
and equity curve tracking across data providers.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import streamlit as st

from dashboard.providers.factory import get_provider, get_current_data_mode

logger = logging.getLogger(__name__)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_get_all_portfolios(data_mode: str) -> List[Dict]:
    provider = get_provider()
    return provider.get_portfolios()


def get_all_portfolios() -> List[Dict]:
    """Retrieves all available portfolios for the current user."""
    try:
        mode = get_current_data_mode()
        return _cached_get_all_portfolios(mode)
    except Exception as e:
        logger.error(f"Error fetching portfolios: {e}")
        try:
            return get_provider().get_portfolios()
        except Exception:
            return []


@st.cache_data(ttl=30, show_spinner=False)
def _cached_get_portfolio_summary(data_mode: str, portfolio_id: int) -> Optional[Dict]:
    provider = get_provider()
    return provider.get_portfolio(portfolio_id)


def get_portfolio_summary(portfolio_id: int) -> Optional[Dict]:
    """
    Retrieves full financial summary for a portfolio:
    Cash, invested capital, total valuation, realized P&L, unrealized P&L, Sharpe, drawdown.
    """
    try:
        mode = get_current_data_mode()
        return _cached_get_portfolio_summary(mode, portfolio_id)
    except Exception as e:
        logger.error(f"Error fetching portfolio summary for {portfolio_id}: {e}")
        try:
            return get_provider().get_portfolio(portfolio_id)
        except Exception:
            return None


@st.cache_data(ttl=30, show_spinner=False)
def _cached_get_portfolio_positions(data_mode: str, portfolio_id: int) -> pd.DataFrame:
    provider = get_provider()
    return provider.get_positions(portfolio_id)


def get_portfolio_positions(portfolio_id: int) -> pd.DataFrame:
    """
    Retrieves current position holdings for a portfolio:
    security_id, symbol, quantity, average_price, current_price, market_value, unrealized_pnl, weight.
    """
    try:
        mode = get_current_data_mode()
        return _cached_get_portfolio_positions(mode, portfolio_id)
    except Exception as e:
        logger.error(f"Error fetching positions for portfolio {portfolio_id}: {e}")
        try:
            return get_provider().get_positions(portfolio_id)
        except Exception:
            return pd.DataFrame(columns=[
                "security_id", "symbol", "quantity", "average_price", "current_price",
                "market_value", "unrealized_pnl", "weight"
            ])


@st.cache_data(ttl=60, show_spinner=False)
def _cached_get_portfolio_equity_history(data_mode: str, portfolio_id: int, days: int) -> pd.DataFrame:
    provider = get_provider()
    return provider.get_portfolio_equity_curve(portfolio_id, days)


def get_portfolio_equity_history(portfolio_id: int, days: int = 180) -> pd.DataFrame:
    """
    Retrieves daily equity curve, benchmark comparative, and drawdown history.
    """
    try:
        mode = get_current_data_mode()
        return _cached_get_portfolio_equity_history(mode, portfolio_id, days)
    except Exception as e:
        logger.error(f"Error fetching equity curve for portfolio {portfolio_id}: {e}")
        try:
            return get_provider().get_portfolio_equity_curve(portfolio_id, days)
        except Exception:
            return pd.DataFrame(columns=["timestamp", "portfolio_value", "benchmark_value", "daily_return", "drawdown_pct"])


def clear_portfolio_service_cache() -> None:
    """Explicitly invalidates all cached portfolio queries."""
    try:
        _cached_get_all_portfolios.clear()
        _cached_get_portfolio_summary.clear()
        _cached_get_portfolio_positions.clear()
        _cached_get_portfolio_equity_history.clear()
    except Exception as e:
        logger.debug(f"Failed to clear portfolio service cache: {e}")

