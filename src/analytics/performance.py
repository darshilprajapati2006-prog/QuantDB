"""
Performance analysis utilities for QuantDB.

Provides:
- Total Return
- Total P&L
- Winning Trades
- Losing Trades
- Win Rate
- Portfolio Performance
"""

from typing import Any, Dict, List, Union

import pandas as pd


DataLike = Union[pd.Series, List[float]]


def _to_series(data: DataLike) -> pd.Series:
    """Convert input data to a clean numeric Series."""
    return pd.Series(data, dtype="float64").dropna()


def total_return(
    returns: DataLike,
) -> float:
    """
    Calculate total compounded return.

    Example:
        [0.10, 0.05, -0.02]
        -> (1.10 * 1.05 * 0.98) - 1
    """
    series = _to_series(returns)

    if series.empty:
        return 0.0

    return float((1.0 + series).prod() - 1.0)


def total_pnl(
    trades: Any,
    pnl_column: str = "pnl",
) -> float:
    """
    Calculate total P&L from trade data.

    Supports:
    - pandas DataFrame
    - list of dictionaries
    - pandas Series

    Parameters
    ----------
    trades : Any
        Trade records containing P&L values.
    pnl_column : str
        Name of the P&L column.
    """
    if isinstance(trades, pd.DataFrame):
        if pnl_column not in trades.columns:
            raise ValueError(
                f"Missing required column: '{pnl_column}'"
            )

        pnl = pd.to_numeric(
            trades[pnl_column],
            errors="coerce",
        ).dropna()

        return float(pnl.sum())

    if isinstance(trades, pd.Series):
        pnl = pd.to_numeric(
            trades,
            errors="coerce",
        ).dropna()

        return float(pnl.sum())

    if isinstance(trades, list):
        if not trades:
            return 0.0

        values = []

        for trade in trades:
            if isinstance(trade, dict):
                if pnl_column not in trade:
                    raise ValueError(
                        f"Missing required key: '{pnl_column}'"
                    )
                values.append(trade[pnl_column])
            else:
                values.append(trade)

        pnl = pd.to_numeric(
            pd.Series(values),
            errors="coerce",
        ).dropna()

        return float(pnl.sum())

    raise TypeError(
        "trades must be a pandas Series, DataFrame, "
        "or list."
    )


def winning_trades(
    trades: Any,
    pnl_column: str = "pnl",
) -> int:
    """Return the number of profitable trades."""
    if isinstance(trades, pd.DataFrame):
        if pnl_column not in trades.columns:
            raise ValueError(
                f"Missing required column: '{pnl_column}'"
            )
        pnl = pd.to_numeric(
            trades[pnl_column],
            errors="coerce",
        ).dropna()

    elif isinstance(trades, pd.Series):
        pnl = pd.to_numeric(
            trades,
            errors="coerce",
        ).dropna()

    elif isinstance(trades, list):
        if not trades:
            return 0

        values = [
            trade[pnl_column]
            if isinstance(trade, dict)
            else trade
            for trade in trades
        ]

        pnl = pd.to_numeric(
            pd.Series(values),
            errors="coerce",
        ).dropna()

    else:
        raise TypeError(
            "trades must be a pandas Series, DataFrame, "
            "or list."
        )

    return int((pnl > 0).sum())


def losing_trades(
    trades: Any,
    pnl_column: str = "pnl",
) -> int:
    """Return the number of losing trades."""
    if isinstance(trades, pd.DataFrame):
        if pnl_column not in trades.columns:
            raise ValueError(
                f"Missing required column: '{pnl_column}'"
            )
        pnl = pd.to_numeric(
            trades[pnl_column],
            errors="coerce",
        ).dropna()

    elif isinstance(trades, pd.Series):
        pnl = pd.to_numeric(
            trades,
            errors="coerce",
        ).dropna()

    elif isinstance(trades, list):
        if not trades:
            return 0

        values = [
            trade[pnl_column]
            if isinstance(trade, dict)
            else trade
            for trade in trades
        ]

        pnl = pd.to_numeric(
            pd.Series(values),
            errors="coerce",
        ).dropna()

    else:
        raise TypeError(
            "trades must be a pandas Series, DataFrame, "
            "or list."
        )

    return int((pnl < 0).sum())


def win_rate(
    trades: Any,
    pnl_column: str = "pnl",
) -> float:
    """
    Calculate win rate as a percentage.

    Winning trades / total non-zero trades * 100
    """
    if isinstance(trades, pd.DataFrame):
        if pnl_column not in trades.columns:
            raise ValueError(
                f"Missing required column: '{pnl_column}'"
            )
        pnl = pd.to_numeric(
            trades[pnl_column],
            errors="coerce",
        ).dropna()

    elif isinstance(trades, pd.Series):
        pnl = pd.to_numeric(
            trades,
            errors="coerce",
        ).dropna()

    elif isinstance(trades, list):
        if not trades:
            return 0.0

        values = [
            trade[pnl_column]
            if isinstance(trade, dict)
            else trade
            for trade in trades
        ]

        pnl = pd.to_numeric(
            pd.Series(values),
            errors="coerce",
        ).dropna()

    else:
        raise TypeError(
            "trades must be a pandas Series, DataFrame, "
            "or list."
        )

    total_trades = len(pnl)

    if total_trades == 0:
        return 0.0

    return float((pnl > 0).sum() / total_trades * 100.0)


def portfolio_performance(
    equity: DataLike,
) -> Dict[str, float]:
    """
    Calculate basic portfolio performance.

    Parameters
    ----------
    equity : SeriesLike
        Portfolio equity values over time.

    Returns
    -------
    dict
        Initial equity
        Final equity
        Total P&L
        Total return
    """
    series = _to_series(equity)

    if series.empty:
        return {
            "initial_equity": 0.0,
            "final_equity": 0.0,
            "total_pnl": 0.0,
            "total_return": 0.0,
        }

    initial_equity = float(series.iloc[0])
    final_equity = float(series.iloc[-1])

    pnl = final_equity - initial_equity

    if initial_equity == 0:
        return_percentage = 0.0
    else:
        return_percentage = (
            pnl / initial_equity
        ) * 100.0

    return {
        "initial_equity": initial_equity,
        "final_equity": final_equity,
        "total_pnl": float(pnl),
        "total_return": float(return_percentage),
    }


def performance_summary(
    returns: DataLike,
    trades: Any,
    equity: DataLike = None,
    pnl_column: str = "pnl",
) -> Dict[str, Any]:
    """
    Return a complete performance summary.
    """
    summary = {
        "total_return": total_return(returns),
        "total_pnl": total_pnl(
            trades,
            pnl_column,
        ),
        "winning_trades": winning_trades(
            trades,
            pnl_column,
        ),
        "losing_trades": losing_trades(
            trades,
            pnl_column,
        ),
        "win_rate": win_rate(
            trades,
            pnl_column,
        ),
    }

    if equity is not None:
        summary["portfolio_performance"] = (
            portfolio_performance(equity)
        )

    return summary