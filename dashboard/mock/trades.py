"""
QuantDB Mock Trades Storage and Management.
Tracks simulated executed trades and realized P&L.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd


_SIMULATED_TRADES: List[Dict] = [
    {
        "trade_id": 5001,
        "order_id": 1001,
        "security_id": 1,
        "symbol": "AAPL",
        "timestamp": (datetime.now() - timedelta(hours=2, minutes=13)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "BUY",
        "quantity": 250,
        "execution_price": 222.50,
        "pnl": 500.0,
        "transaction_cost": 2.50,
    },
    {
        "trade_id": 5002,
        "order_id": 1002,
        "security_id": 3,
        "symbol": "NVDA",
        "timestamp": (datetime.now() - timedelta(hours=5, minutes=29)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "BUY",
        "quantity": 500,
        "execution_price": 126.80,
        "pnl": 975.0,
        "transaction_cost": 4.20,
    },
    {
        "trade_id": 5003,
        "order_id": 998,
        "security_id": 5,
        "symbol": "AMZN",
        "timestamp": (datetime.now() - timedelta(days=1, hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "SELL",
        "quantity": 300,
        "execution_price": 188.20,
        "pnl": 2430.0,
        "transaction_cost": 3.00,
    },
    {
        "trade_id": 5004,
        "order_id": 1005,
        "security_id": 7,
        "symbol": "SPY",
        "timestamp": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "BUY",
        "quantity": 200,
        "execution_price": 558.00,
        "pnl": 420.0,
        "transaction_cost": 2.00,
    },
    {
        "trade_id": 5005,
        "order_id": 991,
        "security_id": 6,
        "symbol": "TSLA",
        "timestamp": (datetime.now() - timedelta(days=3, hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "side": "SELL",
        "quantity": 100,
        "execution_price": 238.50,
        "pnl": -350.0,
        "transaction_cost": 1.80,
    }
]


def get_trades(portfolio_id: Optional[int] = None) -> pd.DataFrame:
    """Returns trades as a DataFrame matching data contract."""
    trades = _SIMULATED_TRADES
    if not trades:
        return pd.DataFrame(columns=[
            "trade_id", "order_id", "security_id", "symbol",
            "timestamp", "side", "quantity", "execution_price", "pnl", "transaction_cost"
        ])
    return pd.DataFrame(trades).sort_values(by="timestamp", ascending=False)


def record_simulated_trade(
    order_id: int,
    security_id: int,
    symbol: str,
    side: str,
    quantity: int,
    execution_price: float,
    pnl: float = 0.0,
    transaction_cost: float = 2.0
) -> Dict:
    """Records a new simulated executed trade."""
    new_id = max([t["trade_id"] for t in _SIMULATED_TRADES], default=5000) + 1
    trade = {
        "trade_id": new_id,
        "order_id": order_id,
        "security_id": security_id,
        "symbol": symbol,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "side": side.upper(),
        "quantity": quantity,
        "execution_price": execution_price,
        "pnl": pnl,
        "transaction_cost": transaction_cost,
    }
    _SIMULATED_TRADES.insert(0, trade)
    return trade
