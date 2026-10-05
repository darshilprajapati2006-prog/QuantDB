"""
QuantDB Trading Service

Provides the backend interface for simulated (paper) trading only.
Connects with `src.trading.orders`, `src.trading.trades`, and the repository layer.
Strictly paper-trading/simulation: no live broker connections or real money.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.trading.orders import (
    Order,
    create_order as domain_create_order,
    cancel_order as domain_cancel_order,
    fill_order as domain_fill_order,
    get_order_summary as domain_get_order_summary,
)
from src.trading.trades import (
    Trade,
    execute_order as domain_execute_order,
    get_trade_summary as domain_get_trade_summary,
    DEFAULT_TRANSACTION_COST_RATE,
)

# In-memory store for simulation testing when repository/DB is not active
_simulated_orders: List[Order] = []
_simulated_trades: List[Trade] = []


def create_order(
    user_id: int,
    security_id: int,
    side: str,
    order_type: str,
    quantity: float,
    order_price: Optional[float] = None,
    repo: Optional[Any] = None,
) -> Order:
    """
    Create a new simulated trading order.

    Parameters
    ----------
    user_id : int
        User identifier.
    security_id : int
        Security identifier.
    side : str
        'BUY' or 'SELL'.
    order_type : str
        'MARKET' or 'LIMIT'.
    quantity : float
        Positive trade quantity.
    order_price : float, optional
        Required for LIMIT orders.
    repo : Repository, optional
        Database repository instance.

    Returns
    -------
    Order
        Created simulated Order object.
    """
    order = domain_create_order(
        user_id=user_id,
        security_id=security_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        order_price=order_price,
    )

    if repo is not None:
        try:
            order_id = repo.create_order(
                user_id=order.user_id,
                security_id=order.security_id,
                order_type=order.order_type,
                side=order.side,
                quantity=order.quantity,
                order_price=order.order_price,
                order_status=order.order_status,
                order_time=order.order_time.strftime("%Y-%m-%d %H:%M:%S")
                if order.order_time
                else None,
            )
            order.order_id = order_id
        except Exception:
            # When running without DB connection, keep in-memory
            pass

    if order.order_id is None:
        order.order_id = len(_simulated_orders) + 1

    _simulated_orders.append(order)
    return order


def execute_order(
    order: Order,
    execution_price: float,
    transaction_cost_rate: float = DEFAULT_TRANSACTION_COST_RATE,
    repo: Optional[Any] = None,
) -> Trade:
    """
    Execute and fill a simulated order, generating a Trade record.

    Parameters
    ----------
    order : Order
        Open or pending Order.
    execution_price : float
        Simulated execution price.
    transaction_cost_rate : float, default=0.001
        Commission/fee rate fraction.
    repo : Repository, optional
        Database repository instance.

    Returns
    -------
    Trade
        Executed simulated Trade object.
    """
    if order.order_status != "FILLED":
        domain_fill_order(order, execution_price=execution_price)

    trade = domain_execute_order(
        order=order,
        execution_price=execution_price,
        cost_rate=transaction_cost_rate,
    )

    if repo is not None:
        try:
            trade_id = repo.create_trade(
                order_id=trade.order_id,
                security_id=trade.security_id,
                trade_side=trade.trade_side,
                quantity=trade.quantity,
                execution_price=trade.execution_price,
                trade_time=trade.trade_time.strftime("%Y-%m-%d %H:%M:%S")
                if trade.trade_time
                else None,
                transaction_cost=trade.transaction_cost,
            )
            trade.trade_id = trade_id
            if order.order_id is not None:
                repo.update_order_status(order.order_id, "FILLED")
        except Exception:
            pass

    if trade.trade_id is None:
        trade.trade_id = len(_simulated_trades) + 1

    _simulated_trades.append(trade)
    return trade


def cancel_order(
    order: Order,
    repo: Optional[Any] = None,
) -> Order:
    """
    Cancel a simulated order.
    """
    cancelled = domain_cancel_order(order)
    if repo is not None and cancelled.order_id is not None:
        try:
            repo.update_order_status(cancelled.order_id, "CANCELLED")
        except Exception:
            pass
    return cancelled


def get_orders(
    user_id: Optional[int] = None,
    security_id: Optional[int] = None,
    repo: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve orders from database repository or simulated memory store.
    """
    if repo is not None:
        try:
            db_orders = repo.get_orders(user_id=user_id)
            if db_orders:
                if security_id is not None:
                    db_orders = [o for o in db_orders if o.get("security_id") == security_id]
                return db_orders
        except Exception:
            pass

    # Fallback to simulated in-memory orders
    results = []
    for o in _simulated_orders:
        if user_id is not None and o.user_id != user_id:
            continue
        if security_id is not None and o.security_id != security_id:
            continue
        results.append(domain_get_order_summary(o))
    return results


def get_trades(
    security_id: Optional[int] = None,
    order_id: Optional[int] = None,
    repo: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve trades from database repository or simulated memory store.
    """
    if repo is not None:
        try:
            db_trades = repo.get_trades(security_id=security_id)
            if db_trades:
                if order_id is not None:
                    db_trades = [t for t in db_trades if t.get("order_id") == order_id]
                return db_trades
        except Exception:
            pass

    results = []
    for t in _simulated_trades:
        if security_id is not None and t.security_id != security_id:
            continue
        if order_id is not None and t.order_id != order_id:
            continue
        results.append(domain_get_trade_summary(t))
    return results


def get_order_summary(order: Order) -> Dict[str, Any]:
    """Return summary dictionary of an order."""
    return domain_get_order_summary(order)


def get_trade_summary(trade: Trade) -> Dict[str, Any]:
    """Return summary dictionary of a trade."""
    return domain_get_trade_summary(trade)
