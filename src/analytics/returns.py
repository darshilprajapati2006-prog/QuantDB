"""
Return calculations for QuantDB.

Provides:
- Simple returns
- Log returns
- Cumulative returns
- Basic return performance summary
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def simple_return(prices: pd.Series) -> pd.Series:
    """
    Calculate simple percentage returns.

    Formula:
        R_t = (P_t / P_(t-1)) - 1

    Parameters
    ----------
    prices : pd.Series
        Historical price series.

    Returns
    -------
    pd.Series
        Simple return series.
    """
    prices = _validate_prices(prices)

    return prices.pct_change()


def log_return(prices: pd.Series) -> pd.Series:
    """
    Calculate continuously compounded/log returns.

    Formula:
        r_t = ln(P_t / P_(t-1))

    Parameters
    ----------
    prices : pd.Series
        Historical price series.

    Returns
    -------
    pd.Series
        Log return series.
    """
    prices = _validate_prices(prices)

    return np.log(prices / prices.shift(1))


def cumulative_return(prices: pd.Series) -> pd.Series:
    """
    Calculate cumulative return from a historical price series.

    Formula:
        Cumulative Return = (P_t / P_0) - 1

    Parameters
    ----------
    prices : pd.Series
        Historical price series.

    Returns
    -------
    pd.Series
        Cumulative return series.
    """
    prices = _validate_prices(prices)

    first_valid_price = prices.dropna().iloc[0]

    return (prices / first_valid_price) - 1


def cumulative_return_from_returns(
    returns: pd.Series,
) -> pd.Series:
    """
    Calculate cumulative return from a return series.

    Formula:
        (1 + R_1)(1 + R_2)...(1 + R_t) - 1

    Parameters
    ----------
    returns : pd.Series
        Periodic return series.

    Returns
    -------
    pd.Series
        Cumulative return series.
    """
    if not isinstance(returns, pd.Series):
        raise TypeError("returns must be a pandas Series.")

    if returns.empty:
        return returns.copy()

    return (1 + returns.fillna(0)).cumprod() - 1


def total_return(prices: pd.Series) -> float:
    """
    Calculate total return over the complete price history.

    Returns
    -------
    float
        Total return as decimal.

    Example
    -------
    Price: 100 -> 120
    Total return: 0.20
    """
    prices = _validate_prices(prices)

    valid_prices = prices.dropna()

    if len(valid_prices) < 2:
        return 0.0

    return float((valid_prices.iloc[-1] / valid_prices.iloc[0]) - 1)


def return_summary(prices: pd.Series) -> dict:
    """
    Generate a basic return performance summary.

    Returns
    -------
    dict
        Summary containing:
        - initial_price
        - final_price
        - total_return
        - cumulative_return
        - average_return
        - number_of_observations
    """
    prices = _validate_prices(prices)

    valid_prices = prices.dropna()

    if valid_prices.empty:
        return {
            "initial_price": None,
            "final_price": None,
            "total_return": 0.0,
            "cumulative_return": pd.Series(dtype=float),
            "average_return": 0.0,
            "number_of_observations": 0,
        }

    returns = simple_return(valid_prices)

    return {
        "initial_price": float(valid_prices.iloc[0]),
        "final_price": float(valid_prices.iloc[-1]),
        "total_return": total_return(valid_prices),
        "cumulative_return": cumulative_return(valid_prices),
        "average_return": float(returns.dropna().mean())
        if returns.dropna().any()
        else 0.0,
        "number_of_observations": int(len(valid_prices)),
    }


def _validate_prices(prices: pd.Series) -> pd.Series:
    """
    Validate and normalize price input.
    """
    if not isinstance(prices, pd.Series):
        raise TypeError("prices must be a pandas Series.")

    if prices.empty:
        return prices.astype(float)

    prices = pd.to_numeric(prices, errors="coerce")

    if (prices.dropna() <= 0).any():
        raise ValueError("Prices must be positive.")

    return prices