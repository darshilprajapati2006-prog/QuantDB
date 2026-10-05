"""
QuantDB Market Data Service

Provides clean, normalized, and validated market data access to the
Quant analytics/backtesting layers and frontend dashboard.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union

import numpy as np
import pandas as pd

from src.database.repository import repository as default_repository

REQUIRED_MARKET_COLUMNS = ["timestamp", "close_price"]


def validate_market_data(df: pd.DataFrame) -> bool:
    """
    Validate market data DataFrame structure and integrity.

    Verifies:
    - df is a non-empty pandas DataFrame
    - required columns exist ('timestamp', 'close_price')
    - timestamps are valid and strictly chronological
    - prices are numeric and positive
    - OHLC relationship integrity where OHLC columns are present

    Returns:
        True if valid.

    Raises:
        ValueError or TypeError if validation fails.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Market data must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Market data DataFrame cannot be empty.")

    for col in REQUIRED_MARKET_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Market data missing required column: '{col}'")

    # Timestamp validity and ordering
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        converted = pd.to_datetime(df["timestamp"], errors="coerce")
        if converted.isna().any():
            raise ValueError("Market data contains invalid or unparseable timestamps.")
        timestamps = converted
    else:
        timestamps = df["timestamp"]

    if timestamps.isna().any():
        raise ValueError("Market data contains null timestamps.")

    if not timestamps.is_monotonic_increasing:
        raise ValueError("Market data timestamps must be sorted chronologically.")

    # Price validation
    close_numeric = pd.to_numeric(df["close_price"], errors="coerce")
    if close_numeric.isna().any():
        raise ValueError("close_price column contains non-numeric or NaN values.")

    if (close_numeric <= 0).any():
        raise ValueError("close_price values must be strictly positive.")

    # OHLC consistency check if OHLC columns are present
    ohlc_present = all(
        col in df.columns for col in ["open_price", "high_price", "low_price", "close_price"]
    )
    if ohlc_present:
        o = pd.to_numeric(df["open_price"], errors="coerce")
        h = pd.to_numeric(df["high_price"], errors="coerce")
        l = pd.to_numeric(df["low_price"], errors="coerce")
        c = close_numeric

        if (o <= 0).any() or (h <= 0).any() or (l <= 0).any():
            raise ValueError("All OHLC prices must be strictly positive.")

        max_oc = np.maximum(o, c)
        min_oc = np.minimum(o, c)

        if (h < max_oc - 1e-9).any():
            raise ValueError("high_price cannot be lower than open_price or close_price.")

        if (l > min_oc + 1e-9).any():
            raise ValueError("low_price cannot be higher than open_price or close_price.")

    return True


def get_market_data(
    security_id: int,
    start_date: Optional[Union[str, datetime, pd.Timestamp]] = None,
    end_date: Optional[Union[str, datetime, pd.Timestamp]] = None,
    repo: Optional[Any] = None,
) -> pd.DataFrame:
    """
    Retrieve clean historical market data for a given security.

    Parameters
    ----------
    security_id : int
        Unique security identifier (positive integer).
    start_date : str, datetime, or pd.Timestamp, optional
        Filter start date/time (inclusive).
    end_date : str, datetime, or pd.Timestamp, optional
        Filter end date/time (inclusive).
    repo : Repository, optional
        Database repository instance. Defaults to singleton repository.

    Returns
    -------
    pandas.DataFrame
        Clean, validated, chronologically sorted DataFrame.
    """
    if not isinstance(security_id, int) or security_id <= 0:
        raise ValueError("security_id must be a positive integer.")

    start_dt: Optional[pd.Timestamp] = None
    end_dt: Optional[pd.Timestamp] = None

    if start_date is not None:
        try:
            start_dt = pd.to_datetime(start_date)
        except Exception as e:
            raise ValueError(f"Invalid start_date format: {start_date}") from e

    if end_date is not None:
        try:
            end_dt = pd.to_datetime(end_date)
        except Exception as e:
            raise ValueError(f"Invalid end_date format: {end_date}") from e

    if start_dt is not None and end_dt is not None and start_dt > end_dt:
        raise ValueError(
            f"start_date ({start_dt}) cannot be greater than end_date ({end_dt})."
        )

    # Use supplied repository or default
    active_repo = repo if repo is not None else default_repository

    str_start = start_dt.strftime("%Y-%m-%d %H:%M:%S") if start_dt is not None else None
    str_end = end_dt.strftime("%Y-%m-%d %H:%M:%S") if end_dt is not None else None

    raw_records = active_repo.get_market_data(
        security_id=security_id,
        start_time=str_start,
        end_time=str_end,
    )

    if not raw_records:
        raise ValueError(f"No market data found for security_id: {security_id}")

    df = pd.DataFrame(raw_records)
    if df.empty:
        raise ValueError(f"No market data found for security_id: {security_id}")

    # Column mapping if alias used (e.g. close -> close_price)
    if "close" in df.columns and "close_price" not in df.columns:
        df["close_price"] = df["close"]

    if "timestamp" not in df.columns:
        if "date" in df.columns:
            df["timestamp"] = df["date"]
        else:
            raise ValueError("Market data missing required 'timestamp' column.")

    # Normalize timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    if df.empty:
        raise ValueError("No valid timestamps found in market data.")

    # Sort chronologically and drop duplicate timestamps
    df = df.sort_values("timestamp")
    df = df.drop_duplicates(subset=["timestamp"], keep="last")

    # Date range filtering
    if start_dt is not None:
        df = df[df["timestamp"] >= start_dt]
    if end_dt is not None:
        df = df[df["timestamp"] <= end_dt]

    if df.empty:
        raise ValueError(
            f"No market data found for security_id {security_id} within the specified date range."
        )

    # Cast numeric columns
    numeric_columns = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "bid_price",
        "ask_price",
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Validate final DataFrame
    validate_market_data(df)

    return df.reset_index(drop=True)
