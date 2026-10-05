"""
QuantDB Mock Strategies Library.
Defines available quantitative strategy metadata, parameter specifications, and descriptions.
The frontend displays and configures these parameters without executing quantitative logic locally.
"""

from typing import Dict, List, Optional
import pandas as pd


STRATEGIES_CATALOG = [
    {
        "strategy_id": 1,
        "name": "Dual Moving Average Crossover",
        "type": "Trend Following",
        "description": "Generates buy signals when a fast simple moving average crosses above a slow moving average, and sell signals on cross below.",
        "status": "ACTIVE",
        "parameters": [
            {"name": "short_window", "type": "int", "default": 20, "min": 5, "max": 100, "description": "Fast SMA lookback periods"},
            {"name": "long_window", "type": "int", "default": 50, "min": 20, "max": 300, "description": "Slow SMA lookback periods"},
            {"name": "stop_loss_pct", "type": "float", "default": 3.5, "min": 0.5, "max": 15.0, "description": "Trailing stop loss percentage"},
        ]
    },
    {
        "strategy_id": 2,
        "name": "RSI / Price Momentum",
        "type": "Momentum",
        "description": "Exploits intermediate-term price velocity and overbought/oversold relative strength thresholds.",
        "status": "ACTIVE",
        "parameters": [
            {"name": "lookback_period", "type": "int", "default": 14, "min": 5, "max": 60, "description": "RSI calculation window"},
            {"name": "oversold_threshold", "type": "float", "default": 30.0, "min": 10.0, "max": 45.0, "description": "Entry trigger level"},
            {"name": "overbought_threshold", "type": "float", "default": 70.0, "min": 55.0, "max": 90.0, "description": "Exit trigger level"},
        ]
    },
    {
        "strategy_id": 3,
        "name": "Bollinger Bands Mean Reversion",
        "type": "Mean Reversion",
        "description": "Identifies statistically stretched prices against rolling moving averages and expects reversion to the mean.",
        "status": "ACTIVE",
        "parameters": [
            {"name": "lookback_period", "type": "int", "default": 20, "min": 10, "max": 90, "description": "Moving average window"},
            {"name": "z_score_threshold", "type": "float", "default": 2.0, "min": 1.0, "max": 3.5, "description": "Standard deviation band width"},
            {"name": "exit_at_mean", "type": "bool", "default": True, "description": "Exit position when price reaches mean band"},
        ]
    },
    {
        "strategy_id": 4,
        "name": "MACD Trend Confirmation",
        "type": "Trend Following",
        "description": "Utilizes exponential moving average convergence/divergence with signal line smoothing for momentum confirmation.",
        "status": "RESEARCH",
        "parameters": [
            {"name": "fast_ema", "type": "int", "default": 12, "min": 5, "max": 30, "description": "Fast EMA span"},
            {"name": "slow_ema", "type": "int", "default": 26, "min": 15, "max": 60, "description": "Slow EMA span"},
            {"name": "signal_span", "type": "int", "default": 9, "min": 3, "max": 20, "description": "Signal line EMA span"},
        ]
    },
    {
        "strategy_id": 5,
        "name": "Statistical Arbitrage Pairs",
        "type": "Arbitrage",
        "description": "Cointegration-based pairs trading model capturing temporary spread dislocations between correlated assets.",
        "status": "RESEARCH",
        "parameters": [
            {"name": "lookback_window", "type": "int", "default": 60, "min": 20, "max": 250, "description": "Cointegration lookback window"},
            {"name": "entry_z_score", "type": "float", "default": 2.2, "min": 1.0, "max": 4.0, "description": "Spread entry z-score"},
            {"name": "exit_z_score", "type": "float", "default": 0.5, "min": 0.0, "max": 1.5, "description": "Spread exit z-score"},
        ]
    }
]


def get_strategies_catalog() -> List[Dict]:
    """Returns the full strategy catalog with metadata and parameters."""
    return list(STRATEGIES_CATALOG)


def get_strategy_by_id(strategy_id: int) -> Optional[Dict]:
    """Returns strategy metadata by ID."""
    return next((s for s in STRATEGIES_CATALOG if s["strategy_id"] == strategy_id), STRATEGIES_CATALOG[0])


def get_strategies_df() -> pd.DataFrame:
    """Returns a high-level summary DataFrame of strategies."""
    rows = []
    for s in STRATEGIES_CATALOG:
        rows.append({
            "strategy_id": s["strategy_id"],
            "name": s["name"],
            "type": s["type"],
            "description": s["description"],
            "status": s["status"],
            "param_count": len(s["parameters"]),
        })
    return pd.DataFrame(rows)
