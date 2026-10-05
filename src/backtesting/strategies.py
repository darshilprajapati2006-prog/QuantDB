"""
Predefined quantitative trading strategies for QuantDB.

Strategies:
- Moving Average Crossover
- Momentum
- Mean Reversion

The module is independent of the frontend and database.
"""

from __future__ import annotations

from typing import Union

import numpy as np
import pandas as pd


SignalData = Union[pd.Series, pd.DataFrame]


def _validate_prices(prices: pd.Series) -> pd.Series:
    """Validate and normalize a price series."""
    if not isinstance(prices, pd.Series):
        prices = pd.Series(prices)

    prices = pd.to_numeric(prices, errors="coerce")

    if prices.empty:
        raise ValueError("Price series cannot be empty.")

    if prices.isna().all():
        raise ValueError("Price series contains no valid prices.")

    if (prices.dropna() <= 0).any():
        raise ValueError("Prices must be positive.")

    return prices.astype(float)


def _signal_series(values: pd.Series) -> pd.Series:
    """Convert numeric strategy values into BUY/SELL/HOLD signals."""
    return values.map(
        {
            1: "BUY",
            -1: "SELL",
            0: "HOLD",
        }
    ).fillna("HOLD")


# ============================================================
# MOVING AVERAGE STRATEGY
# ============================================================

def moving_average_strategy(
    prices: pd.Series,
    short_window: int = 5,
    long_window: int = 20,
) -> pd.Series:
    """
    Moving Average Crossover strategy.

    BUY  -> short moving average > long moving average
    SELL -> short moving average < long moving average
    HOLD -> insufficient data / equal averages

    Parameters
    ----------
    prices:
        Historical closing prices.
    short_window:
        Short moving-average window.
    long_window:
        Long moving-average window.

    Returns
    -------
    pandas.Series
        BUY / SELL / HOLD signals.
    """
    prices = _validate_prices(prices)

    if short_window <= 0 or long_window <= 0:
        raise ValueError("Moving-average windows must be positive.")

    if short_window >= long_window:
        raise ValueError("short_window must be smaller than long_window.")

    short_ma = prices.rolling(
        window=short_window,
        min_periods=short_window,
    ).mean()

    long_ma = prices.rolling(
        window=long_window,
        min_periods=long_window,
    ).mean()

    signal = pd.Series(0, index=prices.index, dtype=int)

    signal[short_ma > long_ma] = 1
    signal[short_ma < long_ma] = -1

    # No signal until both moving averages are available.
    signal[long_ma.isna()] = 0

    return _signal_series(signal)


# ============================================================
# MOMENTUM STRATEGY
# ============================================================

def momentum_strategy(
    prices: pd.Series,
    lookback: int = 5,
) -> pd.Series:
    """
    Momentum strategy.

    BUY  -> current price > price N periods ago
    SELL -> current price < price N periods ago
    HOLD -> unchanged / insufficient data

    Parameters
    ----------
    prices:
        Historical closing prices.
    lookback:
        Number of periods used to measure momentum.

    Returns
    -------
    pandas.Series
        BUY / SELL / HOLD signals.
    """
    prices = _validate_prices(prices)

    if lookback <= 0:
        raise ValueError("lookback must be positive.")

    previous_price = prices.shift(lookback)

    signal = pd.Series(0, index=prices.index, dtype=int)

    signal[prices > previous_price] = 1
    signal[prices < previous_price] = -1

    signal[previous_price.isna()] = 0

    return _signal_series(signal)


# ============================================================
# MEAN REVERSION STRATEGY
# ============================================================

def mean_reversion_strategy(
    prices: pd.Series,
    window: int = 20,
    threshold: float = 0.02,
) -> pd.Series:
    """
    Mean Reversion strategy.

    BUY  -> price is sufficiently below moving average
    SELL -> price is sufficiently above moving average
    HOLD -> price remains near moving average

    threshold represents the percentage distance from
    the moving average.

    Example:
        threshold = 0.02 -> 2%

    Returns
    -------
    pandas.Series
        BUY / SELL / HOLD signals.
    """
    prices = _validate_prices(prices)

    if window <= 0:
        raise ValueError("window must be positive.")

    if threshold < 0:
        raise ValueError("threshold cannot be negative.")

    moving_average = prices.rolling(
        window=window,
        min_periods=window,
    ).mean()

    deviation = (prices - moving_average) / moving_average

    signal = pd.Series(0, index=prices.index, dtype=int)

    # Price significantly below mean -> BUY.
    signal[deviation < -threshold] = 1

    # Price significantly above mean -> SELL.
    signal[deviation > threshold] = -1

    signal[moving_average.isna()] = 0

    return _signal_series(signal)


# ============================================================
# GENERIC STRATEGY DISPATCHER
# ============================================================

def generate_signals(
    prices: pd.Series,
    strategy: str,
    **parameters,
) -> pd.Series:
    """
    Generate trading signals using a named strategy.

    Supported strategies:
        - moving_average
        - momentum
        - mean_reversion
    """
    strategy_name = strategy.strip().lower().replace("-", "_").replace(" ", "_")

    if strategy_name in {
        "moving_average",
        "moving_average_crossover",
        "ma",
    }:
        return moving_average_strategy(prices, **parameters)

    if strategy_name in {
        "momentum",
    }:
        return momentum_strategy(prices, **parameters)

    if strategy_name in {
        "mean_reversion",
        "meanreversion",
    }:
        return mean_reversion_strategy(prices, **parameters)

    raise ValueError(
        f"Unsupported strategy: {strategy}. "
        "Use moving_average, momentum, or mean_reversion."
    )


# ============================================================
# STRATEGY RESULT
# ============================================================

def strategy_result(
    prices: pd.Series,
    strategy: str,
    **parameters,
) -> pd.DataFrame:
    """
    Return prices together with generated strategy signals.

    Useful for backtesting and analytics.
    """
    prices = _validate_prices(prices)

    signals = generate_signals(
        prices,
        strategy,
        **parameters,
    )

    return pd.DataFrame(
        {
            "price": prices,
            "signal": signals,
        }
    )