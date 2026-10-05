"""
QuantDB - Market Data Cleaner

Cleans raw market data before validation/database insertion.

Responsibilities:
- Handle missing values
- Remove invalid prices
- Handle invalid volume
- Convert timestamps
- Remove duplicate records
- Convert data types
"""

from __future__ import annotations

import pandas as pd
import numpy as np


# ============================================================
# REQUIRED MARKET DATA COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "security_id",
    "timestamp",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume",
    "bid_price",
    "ask_price",
]


# ============================================================
# PRICE COLUMNS
# ============================================================

PRICE_COLUMNS = [
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "bid_price",
    "ask_price",
]


# ============================================================
# DATA TYPE CONVERSION
# ============================================================

def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert market data columns to appropriate data types.
    """

    df = df.copy()

    # Security ID
    if "security_id" in df.columns:
        df["security_id"] = pd.to_numeric(
            df["security_id"],
            errors="coerce"
        ).astype("Int64")

    # Timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

    # Numeric price columns
    for column in PRICE_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Volume
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(
            df["volume"],
            errors="coerce"
        )

    return df


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in market data.

    Rows with missing critical fields are removed.
    """

    df = df.copy()

    critical_columns = [
        "security_id",
        "timestamp",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
    ]

    existing_columns = [
        column
        for column in critical_columns
        if column in df.columns
    ]

    # Remove rows where critical data is missing
    df = df.dropna(subset=existing_columns)

    # Bid/ask can be missing in some datasets.
    # If missing, use close price as fallback.
    if "bid_price" in df.columns:
        df["bid_price"] = df["bid_price"].fillna(
            df["close_price"]
        )

    if "ask_price" in df.columns:
        df["ask_price"] = df["ask_price"].fillna(
            df["close_price"]
        )

    return df


# ============================================================
# REMOVE INVALID PRICES
# ============================================================

def remove_invalid_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows containing invalid price values.

    Valid price must be greater than zero.
    """

    df = df.copy()

    for column in PRICE_COLUMNS:
        if column in df.columns:
            df = df[
                df[column].notna()
                & np.isfinite(df[column])
                & (df[column] > 0)
            ]

    return df


# ============================================================
# REMOVE INVALID VOLUME
# ============================================================

def remove_invalid_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows with invalid volume.

    Volume must be non-negative and finite.
    """

    df = df.copy()

    if "volume" in df.columns:
        df = df[
            df["volume"].notna()
            & np.isfinite(df["volume"])
            & (df["volume"] >= 0)
        ]

    return df


# ============================================================
# FORMAT TIMESTAMP
# ============================================================

def format_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert timestamps into pandas datetime format
    and remove rows with invalid timestamps.
    """

    df = df.copy()

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        df = df.dropna(subset=["timestamp"])

    return df


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate market-data records.

    Duplicate definition:
    same security_id + timestamp
    """

    df = df.copy()

    duplicate_columns = [
        column
        for column in ["security_id", "timestamp"]
        if column in df.columns
    ]

    if duplicate_columns:
        df = df.drop_duplicates(
            subset=duplicate_columns,
            keep="last"
        )

    return df


# ============================================================
# SORT DATA
# ============================================================

def sort_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort market data by security and timestamp.
    """

    df = df.copy()

    sort_columns = [
        column
        for column in ["security_id", "timestamp"]
        if column in df.columns
    ]

    if sort_columns:
        df = df.sort_values(
            by=sort_columns
        ).reset_index(drop=True)

    return df


# ============================================================
# MAIN CLEANING PIPELINE
# ============================================================

def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Complete market-data cleaning pipeline.

    Steps:
    1. Check columns
    2. Convert data types
    3. Handle missing values
    4. Remove invalid prices
    5. Remove invalid volume
    6. Format timestamps
    7. Remove duplicates
    8. Sort data
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    # Check required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    cleaned = df.copy()

    # Cleaning pipeline
    cleaned = convert_data_types(cleaned)
    cleaned = handle_missing_values(cleaned)
    cleaned = remove_invalid_prices(cleaned)
    cleaned = remove_invalid_volume(cleaned)
    cleaned = format_timestamps(cleaned)
    cleaned = remove_duplicates(cleaned)
    cleaned = sort_market_data(cleaned)

    return cleaned


# ============================================================
# TEST / DEMO
# ============================================================

if __name__ == "__main__":

    # Sample dirty market data
    data = {
        "security_id": [1, 1, 1, 1, 1, 1],
        "timestamp": [
            "2026-01-01 09:15:00",
            "2026-01-01 09:16:00",
            "2026-01-01 09:17:00",
            "2026-01-01 09:17:00",  # duplicate
            "invalid timestamp",
            "2026-01-01 09:19:00",
        ],
        "open_price": [
            100.00,
            100.20,
            100.10,
            100.10,
            100.40,
            -50.00,  # invalid
        ],
        "high_price": [
            100.50,
            100.60,
            100.50,
            100.50,
            100.80,
            100.70,
        ],
        "low_price": [
            99.80,
            100.00,
            100.00,
            100.00,
            100.30,
            100.20,
        ],
        "close_price": [
            100.20,
            100.10,
            100.40,
            100.40,
            100.35,
            100.60,
        ],
        "volume": [
            10000,
            12500,
            11000,
            11000,
            15000,
            -100,  # invalid
        ],
        "bid_price": [
            100.15,
            100.05,
            100.35,
            100.35,
            100.30,
            100.55,
        ],
        "ask_price": [
            100.25,
            100.15,
            100.45,
            100.45,
            100.40,
            100.65,
        ],
    }

    raw_data = pd.DataFrame(data)

    print("=" * 60)
    print("RAW DATA")
    print("=" * 60)

    print(raw_data)
    print(f"\nRaw rows: {len(raw_data)}")

    cleaned_data = clean_market_data(raw_data)

    print("\n" + "=" * 60)
    print("CLEANED DATA")
    print("=" * 60)

    print(cleaned_data)

    print(f"\nCleaned rows: {len(cleaned_data)}")
    print("\nCleaning completed successfully!")