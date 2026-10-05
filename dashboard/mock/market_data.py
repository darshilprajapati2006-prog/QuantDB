"""
QuantDB Mock Market Data Generator.
Produces realistic OHLCV price series, bid/ask quotes, and microstructure metrics
strictly adhering to the QuantDB project contract.
"""

from datetime import datetime, timedelta
import math
import random
from typing import Dict, List, Optional
import pandas as pd


# Master list of supported securities and exchanges
EXCHANGES = [
    {"exchange_id": 1, "exchange_code": "NASDAQ", "exchange_name": "Nasdaq Stock Market", "country": "United States", "timezone": "America/New_York"},
    {"exchange_id": 2, "exchange_code": "NYSE", "exchange_name": "New York Stock Exchange", "country": "United States", "timezone": "America/New_York"},
    {"exchange_id": 3, "exchange_code": "CBOE", "exchange_name": "Chicago Board Options Exchange", "country": "United States", "timezone": "America/Chicago"},
]

SECURITIES = [
    {"security_id": 1, "symbol": "AAPL", "security_name": "Apple Inc.", "exchange_id": 1, "security_type": "EQUITY", "currency": "USD", "base_price": 224.50, "volatility": 0.016},
    {"security_id": 2, "symbol": "MSFT", "security_name": "Microsoft Corporation", "exchange_id": 1, "security_type": "EQUITY", "currency": "USD", "base_price": 428.10, "volatility": 0.014},
    {"security_id": 3, "symbol": "NVDA", "security_name": "NVIDIA Corporation", "exchange_id": 1, "security_type": "EQUITY", "currency": "USD", "base_price": 128.75, "volatility": 0.028},
    {"security_id": 4, "symbol": "GOOGL", "security_name": "Alphabet Inc.", "exchange_id": 1, "security_type": "EQUITY", "currency": "USD", "base_price": 179.20, "volatility": 0.018},
    {"security_id": 5, "symbol": "AMZN", "security_name": "Amazon.com Inc.", "exchange_id": 1, "security_type": "EQUITY", "currency": "USD", "base_price": 186.40, "volatility": 0.019},
    {"security_id": 6, "symbol": "TSLA", "security_name": "Tesla Inc.", "exchange_id": 1, "security_type": "EQUITY", "currency": "USD", "base_price": 242.80, "volatility": 0.035},
    {"security_id": 7, "symbol": "SPY", "security_name": "SPDR S&P 500 ETF Trust", "exchange_id": 2, "security_type": "ETF", "currency": "USD", "base_price": 560.10, "volatility": 0.009},
    {"security_id": 8, "symbol": "QQQ", "security_name": "Invesco QQQ Trust", "exchange_id": 1, "security_type": "ETF", "currency": "USD", "base_price": 482.30, "volatility": 0.013},
]


def get_securities_list() -> List[Dict]:
    """Returns the list of all available securities."""
    return list(SECURITIES)


def get_exchanges_list() -> List[Dict]:
    """Returns the list of all available exchanges."""
    return list(EXCHANGES)


def generate_ohlcv_data(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    interval: str = "1D"
) -> pd.DataFrame:
    """
    Generates realistic geometric Brownian motion OHLCV time-series data with bid/ask spread.
    Data contract follows:
        timestamp, security_id, symbol, open_price, high_price, low_price, close_price,
        volume, bid_price, ask_price, spread, mid_price, relative_spread_bps, order_book_imbalance
    """
    sec = next((s for s in SECURITIES if s["symbol"] == symbol), SECURITIES[0])
    sec_id = sec["security_id"]
    base_price = sec["base_price"]
    daily_vol = sec["volatility"]

    # Determine timestamps
    if interval == "1H":
        delta = timedelta(hours=1)
        freq_periods = int((end_date - start_date).total_seconds() / 3600)
    elif interval == "15m":
        delta = timedelta(minutes=15)
        freq_periods = int((end_date - start_date).total_seconds() / 900)
    else:  # "1D" default
        delta = timedelta(days=1)
        freq_periods = (end_date - start_date).days

    freq_periods = max(10, min(freq_periods, 500))  # Bound between 10 and 500 rows

    # Deterministic pseudo-random seed based on symbol to ensure smooth chart consistency across renders
    seed_val = sum(ord(c) for c in symbol) + 42
    rng = random.Random(seed_val)

    rows = []
    current_price = base_price * (0.85 + rng.random() * 0.15)  # Start somewhat lower to show trend
    drift = 0.0003  # slight positive market drift

    curr_time = start_date
    for _ in range(freq_periods):
        # Skip weekends if daily
        if interval == "1D" and curr_time.weekday() >= 5:
            curr_time += delta
            continue

        # Geometric Brownian Motion step
        shock = rng.gauss(0, 1)
        ret = drift + daily_vol * shock
        open_p = current_price
        close_p = open_p * math.exp(ret)

        # Realistic intra-period range
        high_extra = abs(rng.gauss(0, daily_vol * 0.6))
        low_extra = abs(rng.gauss(0, daily_vol * 0.6))
        high_p = max(open_p, close_p) * (1 + high_extra)
        low_p = min(open_p, close_p) * (1 - low_extra)

        # Volume correlated with price volatility and magnitude
        vol_base = int(1_500_000 * (1.0 + abs(ret) * 15) * (0.7 + rng.random() * 0.6))
        if symbol in ["SPY", "QQQ"]:
            vol_base *= 4

        # Bid/Ask quotes (tighter for high liquidity, wider for volatile)
        spread_bps = max(1.0, (daily_vol * 1000) * (0.3 + rng.random() * 0.4))  # bps: 3 to 15 bps
        half_spread = (close_p * (spread_bps / 10000.0)) / 2.0
        bid_p = round(close_p - half_spread, 2)
        ask_p = round(close_p + half_spread, 2)
        spread_val = round(ask_p - bid_p, 4)
        mid_p = round((bid_p + ask_p) / 2.0, 4)
        rel_spread_bps = round((spread_val / mid_p) * 10000.0, 2) if mid_p > 0 else 0.0

        # Microstructure: Order book imbalance (-1 to +1)
        ob_imbalance = round((rng.random() * 2.0) - 1.0, 3)

        rows.append({
            "timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S") if interval != "1D" else curr_time.strftime("%Y-%m-%d"),
            "security_id": sec_id,
            "symbol": symbol,
            "open_price": round(open_p, 2),
            "high_price": round(high_p, 2),
            "low_price": round(low_p, 2),
            "close_price": round(close_p, 2),
            "volume": vol_base,
            "bid_price": bid_p,
            "ask_price": ask_p,
            "spread": spread_val,
            "mid_price": mid_p,
            "relative_spread_bps": rel_spread_bps,
            "order_book_imbalance": ob_imbalance,
        })

        current_price = close_p
        curr_time += delta

    df = pd.DataFrame(rows)
    return df


def get_market_overview_summary() -> pd.DataFrame:
    """Returns a fast summary of all major securities for the overview screen."""
    summary_rows = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)

    for sec in SECURITIES:
        df = generate_ohlcv_data(sec["symbol"], start_date, end_date, interval="1D")
        if len(df) >= 2:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            change = latest["close_price"] - prev["close_price"]
            change_pct = (change / prev["close_price"]) * 100
        elif len(df) == 1:
            latest = df.iloc[-1]
            change = 0.0
            change_pct = 0.0
        else:
            continue

        summary_rows.append({
            "symbol": sec["symbol"],
            "name": sec["security_name"],
            "last_price": latest["close_price"],
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": latest["volume"],
            "bid": latest["bid_price"],
            "ask": latest["ask_price"],
            "spread": latest["spread"],
        })

    return pd.DataFrame(summary_rows)
