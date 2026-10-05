"""
QuantDB - Market Data Loader

Responsibilities:
- Load market data from CSV files
- Accept Pandas DataFrames
- Load sample datasets
- Provide a consistent DataFrame output

This module does NOT clean or validate data.
Cleaning -> cleaner.py
Validation -> validator.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd


# Supported input type
DataSource = Union[str, Path, pd.DataFrame]


class MarketDataLoader:
    """
    Loader for QuantDB market data.

    Supports:
    1. CSV files
    2. Pandas DataFrames
    3. Sample datasets
    """

    def __init__(self) -> None:
        self.last_loaded_data: pd.DataFrame | None = None

    # ---------------------------------------------------------
    # LOAD CSV
    # ---------------------------------------------------------

    def load_csv(
        self,
        file_path: str | Path,
        **read_csv_kwargs,
    ) -> pd.DataFrame:
        """
        Load market data from a CSV file.

        Parameters
        ----------
        file_path:
            Path to the CSV file.

        Returns
        -------
        pd.DataFrame
            Loaded market data.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Provided path is not a file: {path}"
            )

        if path.suffix.lower() != ".csv":
            raise ValueError(
                f"Expected a CSV file, got: {path.suffix}"
            )

        try:
            data = pd.read_csv(path, **read_csv_kwargs)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to read CSV file: {path}"
            ) from exc

        self.last_loaded_data = data.copy()

        return data

    # ---------------------------------------------------------
    # LOAD DATAFRAME
    # ---------------------------------------------------------

    def load_dataframe(
        self,
        data: pd.DataFrame,
        copy: bool = True,
    ) -> pd.DataFrame:
        """
        Load market data from an existing Pandas DataFrame.

        Parameters
        ----------
        data:
            Input Pandas DataFrame.

        copy:
            Whether to return a copy of the DataFrame.

        Returns
        -------
        pd.DataFrame
            Loaded market data.
        """

        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                "Expected a pandas DataFrame."
            )

        loaded_data = data.copy() if copy else data

        self.last_loaded_data = loaded_data

        return loaded_data

    # ---------------------------------------------------------
    # LOAD SAMPLE DATA
    # ---------------------------------------------------------

    def load_sample_data(
        self,
        file_path: str | Path | None = None,
    ) -> pd.DataFrame:
        """
        Load a sample market dataset.

        If file_path is provided, the sample data is loaded
        from that CSV file.

        If no file_path is provided, a small built-in sample
        dataset is returned for testing/development.
        """

        if file_path is not None:
            return self.load_csv(file_path)

        sample_data = pd.DataFrame(
            {
                "security_id": [1, 1, 1, 1, 1],
                "timestamp": pd.to_datetime(
                    [
                        "2026-01-01 09:15:00",
                        "2026-01-01 09:16:00",
                        "2026-01-01 09:17:00",
                        "2026-01-01 09:18:00",
                        "2026-01-01 09:19:00",
                    ]
                ),
                "open_price": [
                    100.00,
                    100.20,
                    100.10,
                    100.40,
                    100.35,
                ],
                "high_price": [
                    100.50,
                    100.60,
                    100.50,
                    100.80,
                    100.70,
                ],
                "low_price": [
                    99.80,
                    100.00,
                    99.90,
                    100.20,
                    100.10,
                ],
                "close_price": [
                    100.20,
                    100.10,
                    100.40,
                    100.35,
                    100.60,
                ],
                "volume": [
                    10000,
                    12500,
                    11000,
                    15000,
                    13200,
                ],
                "bid_price": [
                    100.15,
                    100.05,
                    100.35,
                    100.30,
                    100.55,
                ],
                "ask_price": [
                    100.25,
                    100.15,
                    100.45,
                    100.40,
                    100.65,
                ],
            }
        )

        self.last_loaded_data = sample_data.copy()

        return sample_data

    # ---------------------------------------------------------
    # GENERIC LOAD METHOD
    # ---------------------------------------------------------

    def load(
        self,
        source: DataSource,
    ) -> pd.DataFrame:
        """
        Automatically load data based on the source type.

        Supported:
        - CSV path
        - Pandas DataFrame
        """

        if isinstance(source, pd.DataFrame):
            return self.load_dataframe(source)

        if isinstance(source, (str, Path)):
            return self.load_csv(source)

        raise TypeError(
            "Unsupported data source. "
            "Provide a CSV path or Pandas DataFrame."
        )

    # ---------------------------------------------------------
    # BASIC INFORMATION
    # ---------------------------------------------------------

    def get_info(
        self,
        data: pd.DataFrame | None = None,
    ) -> dict:
        """
        Return basic information about loaded market data.
        """

        if data is None:
            data = self.last_loaded_data

        if data is None:
            raise ValueError(
                "No market data has been loaded yet."
            )

        return {
            "rows": len(data),
            "columns": list(data.columns),
            "column_count": len(data.columns),
            "memory_usage_bytes": int(
                data.memory_usage(deep=True).sum()
            ),
        }


# -------------------------------------------------------------
# DEFAULT LOADER INSTANCE
# -------------------------------------------------------------

loader = MarketDataLoader()


# -------------------------------------------------------------
# SIMPLE FUNCTION INTERFACES
# -------------------------------------------------------------

def load_csv(
    file_path: str | Path,
    **read_csv_kwargs,
) -> pd.DataFrame:
    """
    Convenience function for loading CSV market data.
    """

    return loader.load_csv(
        file_path,
        **read_csv_kwargs,
    )


def load_dataframe(
    data: pd.DataFrame,
    copy: bool = True,
) -> pd.DataFrame:
    """
    Convenience function for loading a DataFrame.
    """

    return loader.load_dataframe(
        data,
        copy=copy,
    )


def load_sample_data(
    file_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Convenience function for loading sample market data.
    """

    return loader.load_sample_data(file_path)


# -------------------------------------------------------------
# LOCAL TEST
# -------------------------------------------------------------

if __name__ == "__main__":

    print("QuantDB Market Data Loader Test")
    print("-" * 40)

    data = load_sample_data()

    print(f"Rows: {len(data)}")
    print(f"Columns: {list(data.columns)}")
    print()
    print(data)