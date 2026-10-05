"""
QuantDB Mock Orders Storage and Management.
Supports querying open orders, order history, and submitting simulated orders.
"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional
import pandas as pd


# Initial simulated orders
_SIMULATED_ORDERS: List[Dict] = [
    {
        "order_id": 1001,
        "portfolio_id": 1,
        "security_id": 1,
        "symbol": "AAPL",
        "timestamp": (datetime.now() - timedelta(hours=2, minutes=14)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": 250,
        "price": 222.50,
        "status": "FILLED",
    },
    {
        "order_id": 1002,
        "portfolio_id": 1,
        "security_id": 3,
        "symbol": "NVDA",
        "timestamp": (datetime.now() - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 500,
        "price": 126.80,
        "status": "FILLED",
    },
    {
        "order_id": 1003,
        "portfolio_id": 1,
        "security_id": 2,
        "symbol": "MSFT",
        "timestamp": (datetime.now() - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": 100,
        "price": 425.00,
        "status": "PENDING",
    },
    {
        "order_id": 1004,
        "portfolio_id": 2,
        "security_id": 6,
        "symbol": "TSLA",
        "timestamp": (datetime.now() - timedelta(days=1, hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "SELL",
        "order_type": "LIMIT",
        "quantity": 150,
        "price": 245.00,
        "status": "CANCELLED",
    },
    {
        "order_id": 1005,
        "portfolio_id": 1,
        "security_id": 7,
        "symbol": "SPY",
        "timestamp": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": 200,
        "price": 558.00,
        "status": "FILLED",
    },
]


def get_orders(portfolio_id: Optional[int] = None, status_filter: Optional[str] = None) -> pd.DataFrame:
    """Returns orders as a DataFrame matching data contract."""
    orders = _SIMULATED_ORDERS
    if portfolio_id is not None:
        orders = [o for o in orders if o["portfolio_id"] == portfolio_id]
    if status_filter is not None:
        orders = [o for o in orders if o["status"].upper() == status_filter.upper()]

    if not orders:
        return pd.DataFrame(columns=[
            "order_id", "portfolio_id", "security_id", "symbol",
            "timestamp", "side", "order_type", "quantity", "price", "status"
        ])
    return pd.DataFrame(orders).sort_values(by="timestamp", ascending=False)


def submit_simulated_order(
    portfolio_id: int,
    security_id: int,
    symbol: str,
    side: str,
    order_type: str,
    quantity: int,
    price: float
) -> Dict:
    """Submits a new simulated order with automated matching and execution for Market orders."""
    new_id = max([o["order_id"] for o in _SIMULATED_ORDERS], default=1000) + 1
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Determine status: Market orders fill immediately; Limit orders fill if price is aggressive, otherwise pending
    status = "FILLED" if order_type.upper() == "MARKET" else "PENDING"

    order = {
        "order_id": new_id,
        "portfolio_id": portfolio_id,
        "security_id": security_id,
        "symbol": symbol,
        "timestamp": now_str,
        "side": side.upper(),
        "order_type": order_type.upper(),
        "quantity": quantity,
        "price": price,
        "status": status,
    }
    _SIMULATED_ORDERS.insert(0, order)
    return order
