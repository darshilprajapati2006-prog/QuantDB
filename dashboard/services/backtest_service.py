"""
QuantDB Backtesting Service.
Mediates backtest execution requests, validation of simulation parameters,
and formatting of quantitative performance metrics for the UI.
All quantitative backtesting computations are delegated to the Quant Engine or Mock Provider.
"""

from datetime import datetime
import json
import logging
from typing import Dict, Optional, Tuple
import streamlit as st

from dashboard.providers.factory import get_provider, get_current_data_mode
from dashboard.mock.backtests import get_latest_backtest_summary

logger = logging.getLogger(__name__)


@st.cache_data(ttl=180, show_spinner=False)
def _cached_run_backtest(
    data_mode: str,
    strategy_id: int,
    security_id: int,
    symbol: str,
    start_str: str,
    end_str: str,
    initial_capital: float,
    transaction_cost_pct: float,
    params_json: str
) -> Dict:
    provider = get_provider()
    start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S") if start_str else datetime.min
    end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S") if end_str else datetime.max
    params = json.loads(params_json) if params_json else {}
    return provider.run_backtest(
        strategy_id=strategy_id,
        security_id=security_id,
        symbol=symbol,
        start_date=start_dt,
        end_date=end_dt,
        initial_capital=initial_capital,
        transaction_cost_pct=transaction_cost_pct,
        parameters=params
    )


def execute_backtest(
    strategy_id: int,
    security_id: int,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 100000.0,
    transaction_cost_pct: float = 0.05,
    parameters: Optional[Dict] = None
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Validates input and requests a strategy backtest run from the active provider.
    Returns: (success: bool, message: str, backtest_payload: Optional[Dict])
    """
    # Validation
    if not strategy_id:
        return False, "Please select a quantitative strategy.", None

    if not security_id or not symbol:
        return False, "Please select a security instrument for backtesting.", None

    if start_date >= end_date:
        return False, "Backtest start date must be strictly before end date.", None

    if initial_capital <= 0:
        return False, "Initial capital must be greater than zero.", None

    if transaction_cost_pct < 0 or transaction_cost_pct > 5.0:
        return False, "Transaction cost must be between 0.0% and 5.0%.", None

    try:
        mode = get_current_data_mode()
        start_str = start_date.strftime("%Y-%m-%d %H:%M:%S") if start_date else ""
        end_str = end_date.strftime("%Y-%m-%d %H:%M:%S") if end_date else ""
        params_json = json.dumps(parameters or {}, sort_keys=True)
        result = _cached_run_backtest(
            mode,
            strategy_id,
            security_id,
            symbol,
            start_str,
            end_str,
            initial_capital,
            transaction_cost_pct,
            params_json
        )

        if not result or "error" in result:
            err = result.get("error", "Backtesting engine returned an empty response.") if result else "No response."
            return False, f"Backtest failed: {err}", None

        return True, "Backtest execution completed successfully.", result

    except Exception as e:
        logger.error(f"Backtesting execution error: {e}")
        # Fallback to direct execution if caching encountered an issue
        try:
            provider = get_provider()
            res = provider.run_backtest(
                strategy_id=strategy_id,
                security_id=security_id,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                transaction_cost_pct=transaction_cost_pct,
                parameters=parameters or {}
            )
            if res and "error" not in res:
                return True, "Backtest execution completed successfully.", res
        except Exception:
            pass
        return False, f"Backtesting service encountered an unexpected error: {str(e)}", None


def get_latest_summary() -> Dict:
    """Returns the default summary snapshot for the overview dashboard."""
    try:
        return get_latest_backtest_summary()
    except Exception as e:
        logger.error(f"Error fetching latest backtest summary: {e}")
        return {}


def clear_backtest_service_cache() -> None:
    """Explicitly invalidates all cached backtest simulations."""
    try:
        _cached_run_backtest.clear()
    except Exception as e:
        logger.debug(f"Failed to clear backtest service cache: {e}")

