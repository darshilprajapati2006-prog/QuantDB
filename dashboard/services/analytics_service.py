"""
QuantDB Analytics & System Status Service.
Supplies risk metrics (Sharpe, Drawdown, VaR, Volatility), system health indicators,
and analytical reports for the dashboard.
"""

import logging
from typing import Dict, Optional
from dashboard.providers.factory import get_provider

logger = logging.getLogger(__name__)


def get_system_health() -> Dict:
    """
    Returns system status metrics:
    DATA_MODE, Backend status, Database status, Quant Engine status, Version.
    """
    try:
        provider = get_provider()
        return provider.get_system_status()
    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        return {
            "data_mode": "UNKNOWN",
            "backend_status": "Unavailable",
            "database_status": "Unavailable",
            "quant_engine_status": "Unavailable",
            "version": "1.0.0",
            "connected": False,
        }


def get_portfolio_risk_metrics(portfolio_id: int = 1) -> Dict:
    """Retrieves computed risk statistics (Sharpe, Sortino, VaR, CVaR, Beta, Max Drawdown)."""
    try:
        provider = get_provider()
        return provider.get_risk_metrics(portfolio_id)
    except Exception as e:
        logger.error(f"Error fetching risk metrics: {e}")
        return {
            "portfolio_id": portfolio_id,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "annualized_volatility": 0.0,
            "beta_vs_sp500": 1.0,
            "var_95_daily": 0.0,
            "cvar_95_daily": 0.0,
        }


def get_platform_users() -> list:
    """Retrieves all registered platform users from the active provider."""
    try:
        provider = get_provider()
        return provider.get_users()
    except Exception as e:
        logger.error(f"Error fetching platform users: {e}")
        return []

