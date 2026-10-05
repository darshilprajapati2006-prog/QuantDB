"""
QuantDB Market Data Service.
Acts as the intermediary between the UI pages and the active data provider.
Contains no direct database queries or raw SQL.
"""

from datetime import datetime
import logging
from typing import Dict, List, Optional
import pandas as pd
import streamlit as st

from dashboard.providers.factory import get_provider, get_current_data_mode

logger = logging.getLogger(__name__)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_get_securities(data_mode: str) -> List[Dict]:
    provider = get_provider()
    return provider.get_securities()


def get_available_securities() -> List[Dict]:
    """Retrieves all active securities available for analysis and trading."""
    try:
        mode = get_current_data_mode()
        return _cached_get_securities(mode)
    except Exception as e:
        logger.error(f"Error fetching securities: {e}")
        try:
            return get_provider().get_securities()
        except Exception:
            return []


@st.cache_data(ttl=300, show_spinner=False)
def _cached_get_exchanges(data_mode: str) -> List[Dict]:
    provider = get_provider()
    return provider.get_exchanges()


def get_available_exchanges() -> List[Dict]:
    """Retrieves the list of exchanges configured in the system."""
    try:
        mode = get_current_data_mode()
        return _cached_get_exchanges(mode)
    except Exception as e:
        logger.error(f"Error fetching exchanges: {e}")
        try:
            return get_provider().get_exchanges()
        except Exception:
            return []


@st.cache_data(ttl=120, show_spinner=False)
def _cached_get_historical_market_data(
    data_mode: str,
    security_id: int,
    symbol: str,
    start_str: str,
    end_str: str,
    interval: str
) -> pd.DataFrame:
    provider = get_provider()
    start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S") if start_str else datetime.min
    end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S") if end_str else datetime.max
    return provider.get_market_data(security_id, symbol, start_dt, end_dt, interval)


def get_historical_market_data(
    security_id: int,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    interval: str = "1D"
) -> pd.DataFrame:
    """
    Retrieves historical OHLCV, bid/ask quotes, and microstructure metrics for a security.
    Returns a validated DataFrame conforming strictly to the data contract.
    """
    if start_date > end_date:
        logger.warning("Start date cannot be after end date.")
        return pd.DataFrame()

    try:
        mode = get_current_data_mode()
        start_str = start_date.strftime("%Y-%m-%d %H:%M:%S") if start_date else ""
        end_str = end_date.strftime("%Y-%m-%d %H:%M:%S") if end_date else ""
        df = _cached_get_historical_market_data(
            mode, security_id, symbol, start_str, end_str, interval
        )
        if df is None or df.empty:
            return pd.DataFrame(columns=[
                "timestamp", "security_id", "symbol", "open_price", "high_price",
                "low_price", "close_price", "volume", "bid_price", "ask_price",
                "spread", "mid_price", "relative_spread_bps", "order_book_imbalance"
            ])
        return df
    except Exception as e:
        logger.error(f"Error fetching historical market data for {symbol}: {e}")
        try:
            return get_provider().get_market_data(security_id, symbol, start_date, end_date, interval)
        except Exception:
            return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def _cached_get_market_overview(data_mode: str) -> pd.DataFrame:
    provider = get_provider()
    return provider.get_market_overview()


def get_market_overview() -> pd.DataFrame:
    """Returns a high-level summary of active tickers for the Overview page."""
    try:
        mode = get_current_data_mode()
        return _cached_get_market_overview(mode)
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        try:
            return get_provider().get_market_overview()
        except Exception:
            return pd.DataFrame()


def get_latest_quote(symbol: str) -> Optional[Dict]:
    """Retrieves the latest available price and bid/ask quote for a symbol."""
    try:
        overview_df = get_market_overview()
        if not overview_df.empty:
            match = overview_df[overview_df["symbol"] == symbol]
            if not match.empty:
                return match.iloc[0].to_dict()
    except Exception as e:
        logger.error(f"Error fetching latest quote for {symbol}: {e}")
    return None


def clear_market_service_cache() -> None:
    """Explicitly invalidates all cached market service queries."""
    try:
        _cached_get_securities.clear()
        _cached_get_exchanges.clear()
        _cached_get_historical_market_data.clear()
        _cached_get_market_overview.clear()
    except Exception as e:
        logger.debug(f"Failed to clear market service cache: {e}")

