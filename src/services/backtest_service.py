"""
QuantDB Backtest Service

Provides a clean backend interface for orchestrating quantitative backtests.
Bridges between database market data, strategy signal generation, and the
Quant backtest engine (`src.backtesting.engine`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Union

import pandas as pd

from src.backtesting.engine import BacktestEngine
from src.services.market_service import get_market_data

SUPPORTED_STRATEGIES = {
    "moving_average",
    "moving_average_crossover",
    "ma",
    "momentum",
    "mean_reversion",
    "meanreversion",
}


def _validate_backtest_parameters(
    strategy: str,
    security: Any,
    initial_capital: float,
    start_date: Optional[Any],
    end_date: Optional[Any],
    transaction_cost: float,
    strategy_parameters: Optional[Dict[str, Any]],
) -> None:
    """Validate strategy, security, capital, date range, and cost parameters."""
    if not strategy or not isinstance(strategy, str):
        raise ValueError("A valid strategy name string must be provided.")

    norm_strategy = strategy.strip().lower().replace("-", "_").replace(" ", "_")
    if norm_strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(
            f"Unsupported strategy '{strategy}'. "
            f"Allowed strategies: 'moving_average', 'momentum', 'mean_reversion'."
        )

    if security is None or (isinstance(security, str) and not security.strip()):
        raise ValueError("A valid security identifier or symbol must be provided.")

    if initial_capital is None or initial_capital <= 0:
        raise ValueError(f"initial_capital must be positive, got: {initial_capital}")

    if transaction_cost < 0:
        raise ValueError(
            f"transaction_cost cannot be negative, got: {transaction_cost}"
        )

    if start_date is not None and end_date is not None:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        if start_dt > end_dt:
            raise ValueError(
                f"start_date ({start_dt}) cannot be greater than end_date ({end_dt})."
            )


def _check_minimum_data_requirements(
    data: pd.DataFrame,
    strategy: str,
    params: Dict[str, Any],
) -> None:
    """Verify that the dataset contains sufficient rows for strategy calculation."""
    num_rows = len(data)
    norm_strat = strategy.strip().lower().replace("-", "_").replace(" ", "_")

    if norm_strat in {"moving_average", "moving_average_crossover", "ma"}:
        long_win = int(params.get("long_window", 20))
        short_win = int(params.get("short_window", 5))
        if short_win >= long_win:
            raise ValueError(
                f"short_window ({short_win}) must be smaller than long_window ({long_win})."
            )
        if num_rows < long_win:
            raise ValueError(
                f"Insufficient historical data ({num_rows} rows) for moving average long_window ({long_win})."
            )

    elif norm_strat == "momentum":
        lookback = int(params.get("lookback", 5))
        if num_rows <= lookback:
            raise ValueError(
                f"Insufficient historical data ({num_rows} rows) for momentum lookback ({lookback})."
            )

    elif norm_strat in {"mean_reversion", "meanreversion"}:
        window = int(params.get("window", 20))
        if num_rows < window:
            raise ValueError(
                f"Insufficient historical data ({num_rows} rows) for mean reversion window ({window})."
            )


def run_backtest(
    strategy: str,
    security: Any,
    historical_data: Optional[pd.DataFrame] = None,
    start_date: Optional[Union[str, datetime, pd.Timestamp]] = None,
    end_date: Optional[Union[str, datetime, pd.Timestamp]] = None,
    initial_capital: float = 100000.0,
    transaction_cost: float = 0.0,
    strategy_parameters: Optional[Dict[str, Any]] = None,
    repo: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Run a complete historical backtest through the Quant engine.

    Parameters
    ----------
    strategy : str
        Strategy name ('moving_average', 'momentum', 'mean_reversion').
    security : Any
        Security ID (int) or symbol name.
    historical_data : pd.DataFrame, optional
        Pre-loaded historical price DataFrame. If None, fetched via market_service.
    start_date : str, datetime, optional
        Backtest evaluation start date.
    end_date : str, datetime, optional
        Backtest evaluation end date.
    initial_capital : float, default=100000.0
        Starting simulated capital balance.
    transaction_cost : float, default=0.0
        Transaction cost fraction (e.g. 0.001 = 0.1%).
    strategy_parameters : dict, optional
        Parameters specific to the selected strategy (e.g. windows, threshold).
    repo : Repository, optional
        Database repository instance used if market data needs to be retrieved.

    Returns
    -------
    dict
        Structured backtest result dictionary.
    """
    params = strategy_parameters or {}

    # 1. Parameter validation
    _validate_backtest_parameters(
        strategy=strategy,
        security=security,
        initial_capital=initial_capital,
        start_date=start_date,
        end_date=end_date,
        transaction_cost=transaction_cost,
        strategy_parameters=params,
    )

    # 2. Market data acquisition & preparation
    if historical_data is None:
        if isinstance(security, int):
            sec_id = security
        elif isinstance(security, str) and security.isdigit():
            sec_id = int(security)
        else:
            raise ValueError(
                f"Cannot fetch market data automatically for non-integer security '{security}'. "
                "Please provide historical_data or a numeric security_id."
            )

        data = get_market_data(
            security_id=sec_id,
            start_date=start_date,
            end_date=end_date,
            repo=repo,
        )
    else:
        if not isinstance(historical_data, pd.DataFrame):
            raise TypeError("historical_data must be a pandas DataFrame.")
        if historical_data.empty:
            raise ValueError("historical_data cannot be empty.")
        data = historical_data.copy()

    if "close_price" not in data.columns and "close" not in data.columns:
        raise ValueError("Historical data must contain 'close_price' or 'close' column.")

    # 3. Check data requirements for strategy
    _check_minimum_data_requirements(data, strategy, params)

    # 4. Invoke existing Quant backtesting engine
    engine = BacktestEngine(
        strategy=strategy,
        security=security,
        historical_data=data,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        transaction_cost=transaction_cost,
        strategy_parameters=params,
    )

    result = engine.run()

    # 5. Return standardized, backend- and frontend-friendly contract
    trades_df = result.get("trades", pd.DataFrame())
    equity_df = result.get("equity_curve", pd.DataFrame())

    return {
        "strategy": result.get("strategy", strategy),
        "security": result.get("security", security),
        "start_date": result.get("start_date", start_date),
        "end_date": result.get("end_date", end_date),
        "initial_capital": float(result.get("initial_capital", initial_capital)),
        "final_equity": float(result.get("final_equity", initial_capital)),
        "total_return": float(result.get("total_return", 0.0)),
        "total_pnl": float(result.get("total_pnl", 0.0)),
        "volatility": float(result.get("volatility", 0.0)),
        "sharpe_ratio": float(result.get("sharpe_ratio", 0.0)),
        "max_drawdown": float(result.get("max_drawdown", 0.0)),
        "total_trades": int(result.get("total_trades", 0)),
        "winning_trades": int(result.get("winning_trades", 0)),
        "losing_trades": int(result.get("losing_trades", 0)),
        "win_rate": float(result.get("win_rate", 0.0)),
        "trades": trades_df,
        "equity_curve": equity_df,
    }
