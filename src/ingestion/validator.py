"""
QuantDB - Market Data Validator

Validates cleaned market data before insertion into MySQL.

Validation rules:
- Required columns must exist
- Prices must be positive
- Volume must be non-negative
- Timestamps must be valid
- OHLC relationships must be valid
- Bid/ask prices must be consistent
"""

from __future__ import annotations

import pandas as pd
import numpy as np


# ============================================================
# REQUIRED COLUMNS
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
]


# ============================================================
# VALIDATION RESULT
# ============================================================

class ValidationResult:
    """
    Stores validation status and validation errors.
    """

    def __init__(self):
        self.is_valid = True
        self.errors: list[str] = []

    def add_error(self, message: str) -> None:
        self.is_valid = False
        self.errors.append(message)

    def __repr__(self) -> str:
        return (
            f"ValidationResult("
            f"is_valid={self.is_valid}, "
            f"errors={self.errors})"
        )


# ============================================================
# REQUIRED COLUMN VALIDATION
# ============================================================

def validate_required_columns(
    df: pd.DataFrame,
    result: ValidationResult,
) -> None:
    """
    Check whether all required columns are present.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        result.add_error(
            f"Missing required columns: {missing_columns}"
        )


# ============================================================
# PRICE VALIDATION
# ============================================================

def validate_positive_prices(
    df: pd.DataFrame,
    result: ValidationResult,
) -> None:
    """
    Check that OHLC prices are positive and finite.
    """

    for column in PRICE_COLUMNS:

        if column not in df.columns:
            continue

        invalid_mask = (
            df[column].isna()
            | ~np.isfinite(df[column])
            | (df[column] <= 0)
        )

        invalid_count = int(invalid_mask.sum())

        if invalid_count > 0:
            result.add_error(
                f"{column} contains "
                f"{invalid_count} invalid price value(s)."
            )


# ============================================================
# VOLUME VALIDATION
# ============================================================

def validate_volume(
    df: pd.DataFrame,
    result: ValidationResult,
) -> None:
    """
    Volume must be non-negative and finite.
    """

    if "volume" not in df.columns:
        return

    invalid_mask = (
        df["volume"].isna()
        | ~np.isfinite(df["volume"])
        | (df["volume"] < 0)
    )

    invalid_count = int(invalid_mask.sum())

    if invalid_count > 0:
        result.add_error(
            f"Volume contains "
            f"{invalid_count} invalid value(s)."
        )


# ============================================================
# TIMESTAMP VALIDATION
# ============================================================

def validate_timestamps(
    df: pd.DataFrame,
    result: ValidationResult,
) -> None:
    """
    Check that timestamps are valid datetime values.
    """

    if "timestamp" not in df.columns:
        return

    timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    invalid_count = int(timestamps.isna().sum())

    if invalid_count > 0:
        result.add_error(
            f"Timestamp contains "
            f"{invalid_count} invalid value(s)."
        )


# ============================================================
# OHLC VALIDATION
# ============================================================

def validate_ohlc_relationships(
    df: pd.DataFrame,
    result: ValidationResult,
) -> None:
    """
    Validate OHLC relationships.

    Rules:

    High >= Open
    High >= Close
    High >= Low

    Low <= Open
    Low <= Close
    Low <= High
    """

    required = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
    ]

    if not all(column in df.columns for column in required):
        return

    invalid_mask = (
        (df["high_price"] < df["open_price"])
        | (df["high_price"] < df["close_price"])
        | (df["high_price"] < df["low_price"])
        | (df["low_price"] > df["open_price"])
        | (df["low_price"] > df["close_price"])
        | (df["low_price"] > df["high_price"])
    )

    invalid_count = int(invalid_mask.sum())

    if invalid_count > 0:
        result.add_error(
            f"OHLC relationships are invalid "
            f"for {invalid_count} row(s)."
        )


# ============================================================
# BID / ASK VALIDATION
# ============================================================

def validate_bid_ask(
    df: pd.DataFrame,
    result: ValidationResult,
) -> None:
    """
    Validate bid/ask consistency.

    Rules:
    - Bid must be positive
    - Ask must be positive
    - Ask >= Bid
    """

    if "bid_price" not in df.columns:
        return

    if "ask_price" not in df.columns:
        return

    invalid_mask = (
        df["bid_price"].isna()
        | df["ask_price"].isna()
        | ~np.isfinite(df["bid_price"])
        | ~np.isfinite(df["ask_price"])
        | (df["bid_price"] <= 0)
        | (df["ask_price"] <= 0)
        | (df["ask_price"] < df["bid_price"])
    )

    invalid_count = int(invalid_mask.sum())

    if invalid_count > 0:
        result.add_error(
            f"Bid/ask consistency failed "
            f"for {invalid_count} row(s)."
        )


# ============================================================
# SECURITY ID VALIDATION
# ============================================================

def validate_security_id(
    df: pd.DataFrame,
    result: ValidationResult,
) -> None:
    """
    Validate security IDs.
    """

    if "security_id" not in df.columns:
        return

    invalid_mask = (
        df["security_id"].isna()
        | (pd.to_numeric(
            df["security_id"],
            errors="coerce"
        ) <= 0)
    )

    invalid_count = int(invalid_mask.sum())

    if invalid_count > 0:
        result.add_error(
            f"security_id contains "
            f"{invalid_count} invalid value(s)."
        )


# ============================================================
# COMPLETE VALIDATION
# ============================================================

def validate_market_data(
    df: pd.DataFrame,
) -> ValidationResult:
    """
    Run all market-data validation checks.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Input must be a pandas DataFrame."
        )

    result = ValidationResult()

    if df.empty:
        result.add_error(
            "DataFrame is empty."
        )
        return result

    # 1. Required columns
    validate_required_columns(df, result)

    # Stop further validation if required columns are missing
    if not all(
        column in df.columns
        for column in REQUIRED_COLUMNS
    ):
        return result

    # 2. Security ID
    validate_security_id(df, result)

    # 3. Positive prices
    validate_positive_prices(df, result)

    # 4. Non-negative volume
    validate_volume(df, result)

    # 5. Valid timestamps
    validate_timestamps(df, result)

    # 6. OHLC relationships
    validate_ohlc_relationships(df, result)

    # 7. Bid/ask consistency
    validate_bid_ask(df, result)

    return result


# ============================================================
# SIMPLE BOOLEAN VALIDATION
# ============================================================

def is_valid_market_data(
    df: pd.DataFrame,
) -> bool:
    """
    Return True if market data passes all validations.
    """

    result = validate_market_data(df)

    return result.is_valid


# ============================================================
# TEST / DEMO
# ============================================================

if __name__ == "__main__":

    # Valid sample data
    data = {
        "security_id": [1, 1, 1],

        "timestamp": [
            "2026-01-01 09:15:00",
            "2026-01-01 09:16:00",
            "2026-01-01 09:17:00",
        ],

        "open_price": [
            100.00,
            100.20,
            100.10,
        ],

        "high_price": [
            100.50,
            100.60,
            100.50,
        ],

        "low_price": [
            99.80,
            100.00,
            100.00,
        ],

        "close_price": [
            100.20,
            100.10,
            100.40,
        ],

        "volume": [
            10000,
            12500,
            11000,
        ],

        "bid_price": [
            100.15,
            100.05,
            100.35,
        ],

        "ask_price": [
            100.25,
            100.15,
            100.45,
        ],
    }

    test_data = pd.DataFrame(data)

    print("=" * 60)
    print("QuantDB MARKET DATA VALIDATION")
    print("=" * 60)

    validation = validate_market_data(test_data)

    print("\nValidation Status:")

    if validation.is_valid:
        print("VALID")
        print("Market data is ready for MySQL insertion.")

    else:
        print("INVALID")

        print("\nValidation Errors:")

        for error in validation.errors:
            print(f"- {error}")

    print("\n" + "=" * 60)

    # Boolean check
    print(
        f"is_valid_market_data(): "
        f"{is_valid_market_data(test_data)}"
    )