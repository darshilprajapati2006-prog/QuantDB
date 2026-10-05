"""
QuantDB Market Data Service.
Acts as the intermediary between the UI pages and the active data provider.
Contains no direct database queries or raw SQL.
"""

from datetime import datetime
import logging
from typing import Dict, List, Optional
import pandas as pd
from dashboard.providers.factory import get_provider

logger = logging.getLogger(__name__)


def get_available_securities() -> List[Dict]:
    """Retrieves all active securities available for analysis and trading."""
    try:
        provider = get_provider()
        return provider.get_securities()
    except Exception as e:
        logger.error(f"Error fetching securities: {e}")
        return []


def get_available_exchanges() -> List[Dict]:
    """Retrieves the list of exchanges configured in the system."""
    try:
        provider = get_provider()
        return provider.get_exchanges()
    except Exception as e:
        logger.error(f"Error fetching exchanges: {e}")
        return []


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
        provider = get_provider()
        df = provider.get_market_data(security_id, symbol, start_date, end_date, interval)
        if df is None or df.empty:
            return pd.DataFrame(columns=[
                "timestamp", "security_id", "symbol", "open_price", "high_price",
                "low_price", "close_price", "volume", "bid_price", "ask_price",
                "spread", "mid_price", "relative_spread_bps", "order_book_imbalance"
            ])
        return df
    except Exception as e:
        logger.error(f"Error fetching historical market data for {symbol}: {e}")
        return pd.DataFrame()


def get_market_overview() -> pd.DataFrame:
    """Returns a high-level summary of active tickers for the Overview page."""
    try:
        provider = get_provider()
        return provider.get_market_overview()
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
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
