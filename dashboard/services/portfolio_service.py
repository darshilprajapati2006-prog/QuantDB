"""
QuantDB Portfolio Service.
Coordinates portfolio valuations, active positions, asset allocations,
and equity curve tracking across data providers.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
from dashboard.providers.factory import get_provider

logger = logging.getLogger(__name__)


def get_all_portfolios() -> List[Dict]:
    """Retrieves all available portfolios for the current user."""
    try:
        provider = get_provider()
        return provider.get_portfolios()
    except Exception as e:
        logger.error(f"Error fetching portfolios: {e}")
        return []


def get_portfolio_summary(portfolio_id: int) -> Optional[Dict]:
    """
    Retrieves full financial summary for a portfolio:
    Cash, invested capital, total valuation, realized P&L, unrealized P&L, Sharpe, drawdown.
    """
    try:
        provider = get_provider()
        return provider.get_portfolio(portfolio_id)
    except Exception as e:
        logger.error(f"Error fetching portfolio summary for {portfolio_id}: {e}")
        return None


def get_portfolio_positions(portfolio_id: int) -> pd.DataFrame:
    """
    Retrieves current position holdings for a portfolio:
    security_id, symbol, quantity, average_price, current_price, market_value, unrealized_pnl, weight.
    """
    try:
        provider = get_provider()
        return provider.get_positions(portfolio_id)
    except Exception as e:
        logger.error(f"Error fetching positions for portfolio {portfolio_id}: {e}")
        return pd.DataFrame(columns=[
            "security_id", "symbol", "quantity", "average_price", "current_price",
            "market_value", "unrealized_pnl", "weight"
        ])


def get_portfolio_equity_history(portfolio_id: int, days: int = 180) -> pd.DataFrame:
    """
    Retrieves daily equity curve, benchmark comparative, and drawdown history.
    """
    try:
        provider = get_provider()
        return provider.get_portfolio_equity_curve(portfolio_id, days)
    except Exception as e:
        logger.error(f"Error fetching equity curve for portfolio {portfolio_id}: {e}")
        return pd.DataFrame(columns=["timestamp", "portfolio_value", "benchmark_value", "daily_return", "drawdown_pct"])
