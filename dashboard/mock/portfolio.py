"""
QuantDB Mock Portfolio Data Generator.
Produces realistic portfolios, active positions, and historical equity curves.
Follows the exact data contracts defined in the project specification.
"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional
import pandas as pd


# Default simulated portfolios
DEFAULT_PORTFOLIOS = [
    {
        "portfolio_id": 1,
        "user_id": 1,
        "portfolio_name": "Quant Alpha Core",
        "initial_capital": 1000000.0,
        "cash": 342150.0,
        "created_at": "2024-01-01 09:30:00",
        "status": "ACTIVE",
    },
    {
        "portfolio_id": 2,
        "user_id": 1,
        "portfolio_name": "Tech Momentum Strategy",
        "initial_capital": 500000.0,
        "cash": 112400.0,
        "created_at": "2024-03-15 09:30:00",
        "status": "ACTIVE",
    },
    {
        "portfolio_id": 3,
        "user_id": 2,
        "portfolio_name": "Statistical Arbitrage Sandbox",
        "initial_capital": 250000.0,
        "cash": 248900.0,
        "created_at": "2024-06-01 09:30:00",
        "status": "ACTIVE",
    }
]

# Holdings per portfolio
PORTFOLIO_HOLDINGS = {
    1: [
        {"security_id": 1, "symbol": "AAPL", "quantity": 1200, "average_price": 210.50, "current_price": 224.50},
        {"security_id": 2, "symbol": "MSFT", "quantity": 650, "average_price": 412.00, "current_price": 428.10},
        {"security_id": 3, "symbol": "NVDA", "quantity": 1800, "average_price": 115.20, "current_price": 128.75},
        {"security_id": 7, "symbol": "SPY", "quantity": 400, "average_price": 542.80, "current_price": 560.10},
    ],
    2: [
        {"security_id": 3, "symbol": "NVDA", "quantity": 2100, "average_price": 119.40, "current_price": 128.75},
        {"security_id": 5, "symbol": "AMZN", "quantity": 700, "average_price": 178.50, "current_price": 186.40},
        {"security_id": 6, "symbol": "TSLA", "quantity": 350, "average_price": 235.00, "current_price": 242.80},
    ],
    3: [
        {"security_id": 1, "symbol": "AAPL", "quantity": 50, "average_price": 223.00, "current_price": 224.50},
    ]
}


def get_portfolios_list() -> List[Dict]:
    """Returns all available user portfolios."""
    return list(DEFAULT_PORTFOLIOS)


def get_portfolio_by_id(portfolio_id: int) -> Optional[Dict]:
    """Computes comprehensive portfolio summary including valuations and P&L."""
    base = next((p for p in DEFAULT_PORTFOLIOS if p["portfolio_id"] == portfolio_id), DEFAULT_PORTFOLIOS[0])
    positions_df = get_portfolio_positions(portfolio_id)

    market_val_positions = float(positions_df["market_value"].sum()) if not positions_df.empty else 0.0
    unrealized_pnl = float(positions_df["unrealized_pnl"].sum()) if not positions_df.empty else 0.0
    
    # Realized P&L simulated from closed trades
    realized_map = {1: 42350.0, 2: 18450.0, 3: 1200.0}
    realized_pnl = realized_map.get(portfolio_id, 0.0)

    total_pnl = realized_pnl + unrealized_pnl
    portfolio_value = base["cash"] + market_val_positions
    return_pct = round(((portfolio_value - base["initial_capital"]) / base["initial_capital"]) * 100, 2)
    daily_return_pct = round((unrealized_pnl / portfolio_value) * 0.45, 2)  # Believable daily return fraction

    return {
        "portfolio_id": portfolio_id,
        "portfolio_name": base["portfolio_name"],
        "initial_capital": base["initial_capital"],
        "cash": base["cash"],
        "invested_capital": round(market_val_positions, 2),
        "portfolio_value": round(portfolio_value, 2),
        "realized_pnl": round(realized_pnl, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "total_pnl": round(total_pnl, 2),
        "total_return_pct": return_pct,
        "daily_return_pct": daily_return_pct,
        "sharpe_ratio": 1.84 if portfolio_id == 1 else (1.62 if portfolio_id == 2 else 0.95),
        "max_drawdown": -6.8 if portfolio_id == 1 else (-11.4 if portfolio_id == 2 else -3.2),
        "volatility": 14.2 if portfolio_id == 1 else (19.8 if portfolio_id == 2 else 9.5),
    }


def get_portfolio_positions(portfolio_id: int) -> pd.DataFrame:
    """Returns positions table matching the data contract."""
    holdings = PORTFOLIO_HOLDINGS.get(portfolio_id, PORTFOLIO_HOLDINGS[1])
    rows = []
    total_val = 0.0

    for h in holdings:
        mkt_val = h["quantity"] * h["current_price"]
        total_val += mkt_val

    for h in holdings:
        mkt_val = h["quantity"] * h["current_price"]
        cost_basis = h["quantity"] * h["average_price"]
        unrealized = mkt_val - cost_basis
        unrealized_pct = (unrealized / cost_basis) * 100 if cost_basis > 0 else 0.0
        weight = (mkt_val / total_val) * 100 if total_val > 0 else 0.0

        rows.append({
            "security_id": h["security_id"],
            "symbol": h["symbol"],
            "quantity": h["quantity"],
            "average_price": round(h["average_price"], 2),
            "current_price": round(h["current_price"], 2),
            "market_value": round(mkt_val, 2),
            "cost_basis": round(cost_basis, 2),
            "unrealized_pnl": round(unrealized, 2),
            "unrealized_pnl_pct": round(unrealized_pct, 2),
            "weight": round(weight, 2),
        })

    return pd.DataFrame(rows)


def get_historical_equity_curve(portfolio_id: int, days: int = 180) -> pd.DataFrame:
    """Generates realistic daily historical equity curve and returns for the portfolio."""
    rng = random.Random(portfolio_id * 100 + 7)
    base = next((p for p in DEFAULT_PORTFOLIOS if p["portfolio_id"] == portfolio_id), DEFAULT_PORTFOLIOS[0])
    initial_cap = base["initial_capital"]

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    dates = []
    equity_vals = []
    benchmark_vals = []
    daily_rets = []

    curr_eq = initial_cap
    curr_bench = initial_cap
    prev_eq = initial_cap

    curr_date = start_date
    while curr_date <= end_date:
        if curr_date.weekday() < 5:  # Weekdays only
            dates.append(curr_date.strftime("%Y-%m-%d"))
            shock = rng.gauss(0.0004, 0.008)  # Positive alpha drift
            bench_shock = rng.gauss(0.0003, 0.007)

            curr_eq *= (1.0 + shock)
            curr_bench *= (1.0 + bench_shock)

            d_ret = (curr_eq - prev_eq) / prev_eq
            prev_eq = curr_eq

            equity_vals.append(round(curr_eq, 2))
            benchmark_vals.append(round(curr_bench, 2))
            daily_rets.append(round(d_ret * 100, 3))

        curr_date += timedelta(days=1)

    df = pd.DataFrame({
        "timestamp": dates,
        "portfolio_value": equity_vals,
        "benchmark_value": benchmark_vals,
        "daily_return": daily_rets,
    })

    # Add drawdown calculation
    df["peak"] = df["portfolio_value"].cummax()
    df["drawdown_pct"] = ((df["portfolio_value"] - df["peak"]) / df["peak"]) * 100
    df["drawdown_pct"] = df["drawdown_pct"].round(2)

    return df
