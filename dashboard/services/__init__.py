"""
QuantDB Services Package.
Provides clean service interfaces between Streamlit UI pages and data providers (Mock or Real).
"""

from dashboard.services import (
    analytics_service,
    auth_service,
    backtest_service,
    market_service,
    portfolio_service,
    strategy_service,
    trading_service,
)

__all__ = [
    "analytics_service",
    "auth_service",
    "backtest_service",
    "market_service",
    "portfolio_service",
    "strategy_service",
    "trading_service",
]
