"""
QuantDB Analytics Service

Exposes Quantitative analytics (returns, risk, performance, microstructure)
through backend-friendly, frontend-independent service interfaces.
Reuses domain logic from `src.analytics`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from src.analytics import returns as ret_mod
from src.analytics import risk as risk_mod
from src.analytics import performance as perf_mod
from src.analytics import microstructure as micro_mod


def _extract_price_series(data: Any) -> pd.Series:
    """Extract a numeric price pandas Series from Series, DataFrame, or array."""
    if isinstance(data, pd.DataFrame):
        for col in ["close_price", "close", "price"]:
            if col in data.columns:
                return data[col]
        raise ValueError(
            "DataFrame must contain 'close_price', 'close', or 'price' column."
        )

    if isinstance(data, (list, np.ndarray)):
        return pd.Series(data, dtype=float)

    if isinstance(data, pd.Series):
        return data

    raise TypeError("Price data must be a pandas Series, DataFrame, or list.")


def calculate_returns(
    prices: Any,
    return_type: str = "simple",
) -> Union[pd.Series, float, Dict[str, Any]]:
    """
    Calculate returns from historical price data.

    Parameters
    ----------
    prices : pd.Series, pd.DataFrame, list
        Historical price series or market data DataFrame.
    return_type : str, default='simple'
        Type of return calculation:
        'simple', 'log', 'cumulative', 'total', or 'summary'.

    Returns
    -------
    pd.Series, float, or dict
        Calculated return series or summary dictionary.
    """
    series = _extract_price_series(prices)
    norm_type = return_type.strip().lower()

    if norm_type in {"simple", "pct", "percentage"}:
        return ret_mod.simple_return(series)

    if norm_type in {"log", "continuous"}:
        return ret_mod.log_return(series)

    if norm_type in {"cumulative", "cum"}:
        return ret_mod.cumulative_return(series)

    if norm_type in {"total"}:
        return ret_mod.total_return(series)

    if norm_type in {"summary"}:
        return ret_mod.return_summary(series)

    raise ValueError(
        f"Unknown return_type: '{return_type}'. "
        "Allowed types: 'simple', 'log', 'cumulative', 'total', 'summary'."
    )


def calculate_risk_metrics(
    returns: Any,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> Dict[str, float]:
    """
    Calculate quantitative risk metrics (volatility, Sharpe ratio, max drawdown).

    Parameters
    ----------
    returns : pd.Series, pd.DataFrame, list
        Return series or DataFrame containing return/price columns.
    risk_free_rate : float, default=0.0
        Annualized risk-free rate.
    periods_per_year : int, default=252
        Trading periods per year.

    Returns
    -------
    dict
        volatility, sharpe_ratio, max_drawdown.
    """
    if isinstance(returns, pd.DataFrame):
        if "return" in returns.columns:
            series = returns["return"]
        elif "returns" in returns.columns:
            series = returns["returns"]
        elif "close_price" in returns.columns:
            series = ret_mod.simple_return(returns["close_price"]).dropna()
        elif "close" in returns.columns:
            series = ret_mod.simple_return(returns["close"]).dropna()
        else:
            raise ValueError(
                "DataFrame must contain 'return', 'returns', or 'close_price' column."
            )
    else:
        series = returns

    vol = risk_mod.volatility(
        series,
        annualize=True,
        periods_per_year=periods_per_year,
    )
    sharpe = risk_mod.sharpe_ratio(
        series,
        risk_free_rate=risk_free_rate,
        annualize=True,
        periods_per_year=periods_per_year,
    )
    mdd = risk_mod.maximum_drawdown(series)

    return {
        "volatility": float(vol),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": float(mdd),
    }


def calculate_performance(
    trades: Any = None,
    returns: Any = None,
    equity: Any = None,
    pnl_column: str = "pnl",
) -> Dict[str, Any]:
    """
    Calculate trade and portfolio performance metrics.

    Parameters
    ----------
    trades : pd.DataFrame, list, pd.Series, optional
        Trade records containing realized P&L.
    returns : pd.Series, list, optional
        Compounded returns series.
    equity : pd.Series, list, optional
        Portfolio equity curve series.
    pnl_column : str, default='pnl'
        Name of the P&L column in trades.

    Returns
    -------
    dict
        total_return, total_pnl, winning_trades, losing_trades, win_rate,
        and optionally portfolio_performance.
    """
    if trades is None:
        trades = []

    if returns is None:
        returns = []

    summary = perf_mod.performance_summary(
        returns=returns,
        trades=trades,
        equity=equity,
        pnl_column=pnl_column,
    )

    # Ensure total_trades is cleanly exposed
    if isinstance(trades, pd.DataFrame):
        if pnl_column in trades.columns:
            total_tr = int(len(trades.dropna(subset=[pnl_column])))
        else:
            total_tr = int(len(trades))
    elif isinstance(trades, (list, tuple)):
        total_tr = int(len(trades))
    elif isinstance(trades, pd.Series):
        total_tr = int(len(trades.dropna()))
    else:
        total_tr = 0

    summary["total_trades"] = total_tr

    return summary


def calculate_microstructure(
    bid_price: float,
    ask_price: float,
    bid_size: float = 0.0,
    ask_size: float = 0.0,
) -> Dict[str, float]:
    """
    Calculate order-book and spread microstructure analytics.

    Parameters
    ----------
    bid_price : float
        Best bid price.
    ask_price : float
        Best ask price.
    bid_size : float, default=0.0
        Bid size at best bid.
    ask_size : float, default=0.0
        Ask size at best ask.

    Returns
    -------
    dict
        bid_price, ask_price, bid_ask_spread, relative_spread,
        bid_depth, ask_depth, total_depth, order_book_imbalance.
    """
    return micro_mod.microstructure_summary(
        bid_price=bid_price,
        ask_price=ask_price,
        bid_size=bid_size,
        ask_size=ask_size,
    )


def calculate_analytics_summary(
    prices: Optional[Any] = None,
    returns: Optional[Any] = None,
    trades: Optional[Any] = None,
    equity: Optional[Any] = None,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    pnl_column: str = "pnl",
) -> Dict[str, Any]:
    """
    Generate an integrated quantitative performance and risk summary.

    Parameters
    ----------
    prices : Any, optional
        Price series or DataFrame.
    returns : Any, optional
        Returns series. If omitted, computed from prices.
    trades : Any, optional
        Trade history records.
    equity : Any, optional
        Equity curve history.
    risk_free_rate : float, default=0.0
        Annualized risk-free rate.
    periods_per_year : int, default=252
        Periods per year.
    pnl_column : str, default='pnl'
        Column name for P&L in trades.

    Returns
    -------
    dict
        Combined performance and risk metrics dictionary.
    """
    if returns is None and prices is not None:
        p_series = _extract_price_series(prices)
        returns = ret_mod.simple_return(p_series).dropna()

    if returns is not None:
        risk_metrics = calculate_risk_metrics(
            returns=returns,
            risk_free_rate=risk_free_rate,
            periods_per_year=periods_per_year,
        )
    else:
        risk_metrics = {
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
        }

    perf_metrics = calculate_performance(
        trades=trades,
        returns=returns,
        equity=equity,
        pnl_column=pnl_column,
    )

    return {
        "total_return": perf_metrics.get("total_return", 0.0),
        "total_pnl": perf_metrics.get("total_pnl", 0.0),
        "volatility": risk_metrics["volatility"],
        "sharpe_ratio": risk_metrics["sharpe_ratio"],
        "max_drawdown": risk_metrics["max_drawdown"],
        "total_trades": perf_metrics.get("total_trades", 0),
        "winning_trades": perf_metrics.get("winning_trades", 0),
        "losing_trades": perf_metrics.get("losing_trades", 0),
        "win_rate": perf_metrics.get("win_rate", 0.0),
    }
