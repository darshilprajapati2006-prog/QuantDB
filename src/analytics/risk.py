"""
Risk analysis utilities for QuantDB.

Provides:
- Volatility
- Sharpe Ratio
- Maximum Drawdown

Designed to work with historical or backtest return series.
"""

from typing import Optional, Union

import numpy as np
import pandas as pd


SeriesLike = Union[pd.Series, list, np.ndarray]


def _to_series(data: SeriesLike) -> pd.Series:
    """Convert input data into a clean numeric pandas Series."""
    series = pd.Series(data, dtype="float64")
    return series.dropna()


def volatility(
    returns: SeriesLike,
    annualize: bool = True,
    periods_per_year: int = 252,
) -> float:
    """
    Calculate volatility from a return series.

    Parameters
    ----------
    returns : SeriesLike
        Periodic return series.
    annualize : bool, default=True
        Whether to annualize the volatility.
    periods_per_year : int, default=252
        Number of periods in one year.

    Returns
    -------
    float
        Volatility.
    """
    series = _to_series(returns)

    if len(series) < 2:
        return 0.0

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive.")

    vol = float(series.std(ddof=1))

    if annualize:
        vol *= np.sqrt(periods_per_year)

    return vol


def sharpe_ratio(
    returns: SeriesLike,
    risk_free_rate: float = 0.0,
    annualize: bool = True,
    periods_per_year: int = 252,
) -> float:
    """
    Calculate the Sharpe Ratio.

    Parameters
    ----------
    returns : SeriesLike
        Periodic return series.
    risk_free_rate : float, default=0.0
        Annual risk-free rate when annualize=True.
        Periodic risk-free rate when annualize=False.
    annualize : bool, default=True
        Whether to annualize the Sharpe Ratio.
    periods_per_year : int, default=252
        Number of periods in one year.

    Returns
    -------
    float
        Sharpe Ratio.
    """
    series = _to_series(returns)

    if len(series) < 2:
        return 0.0

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive.")

    if annualize:
        periodic_rf = risk_free_rate / periods_per_year
    else:
        periodic_rf = risk_free_rate

    excess_returns = series - periodic_rf
    std = float(excess_returns.std(ddof=1))

    if std == 0:
        return 0.0

    ratio = float(excess_returns.mean() / std)

    if annualize:
        ratio *= np.sqrt(periods_per_year)

    return ratio


def maximum_drawdown(returns: SeriesLike) -> float:
    """
    Calculate Maximum Drawdown from a return series.

    Returns the drawdown as a negative decimal.

    Example:
        0.10 means +10% return
        -0.20 means -20% return

    If portfolio falls 20% from its previous peak,
    maximum drawdown = -0.20.
    """
    series = _to_series(returns)

    if series.empty:
        return 0.0

    cumulative = (1.0 + series).cumprod()

    running_peak = cumulative.cummax()

    drawdown = (cumulative / running_peak) - 1.0

    return float(drawdown.min())


def risk_summary(
    returns: SeriesLike,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> dict:
    """
    Return all major risk metrics together.

    Returns
    -------
    dict
        volatility, sharpe_ratio and maximum_drawdown.
    """
    return {
        "volatility": volatility(
            returns,
            annualize=True,
            periods_per_year=periods_per_year,
        ),
        "sharpe_ratio": sharpe_ratio(
            returns,
            risk_free_rate=risk_free_rate,
            annualize=True,
            periods_per_year=periods_per_year,
        ),
        "maximum_drawdown": maximum_drawdown(returns),
    }