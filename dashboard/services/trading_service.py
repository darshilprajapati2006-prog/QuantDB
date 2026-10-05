"""
QuantDB Simulated Trading Service.
Handles paper trading order submission, order lifecycle queries, and trade execution history.
Performs clean input validation before forwarding to data providers.
NO REAL-MONEY TRADING IS PERFORMED.
"""

import logging
from typing import Dict, Optional, Tuple
import pandas as pd
from dashboard.providers.factory import get_provider

logger = logging.getLogger(__name__)


def get_orders(portfolio_id: Optional[int] = None, status: Optional[str] = None) -> pd.DataFrame:
    """Retrieves orders filtered by portfolio and/or status."""
    try:
        provider = get_provider()
        return provider.get_orders(portfolio_id=portfolio_id, status=status)
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return pd.DataFrame(columns=[
            "order_id", "portfolio_id", "security_id", "symbol",
            "timestamp", "side", "order_type", "quantity", "price", "status"
        ])


def get_open_orders(portfolio_id: Optional[int] = None) -> pd.DataFrame:
    """Retrieves only active/pending orders."""
    return get_orders(portfolio_id=portfolio_id, status="PENDING")


def get_trades(portfolio_id: Optional[int] = None) -> pd.DataFrame:
    """Retrieves executed trade history."""
    try:
        provider = get_provider()
        return provider.get_trades(portfolio_id=portfolio_id)
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        return pd.DataFrame(columns=[
            "trade_id", "order_id", "security_id", "symbol",
            "timestamp", "side", "quantity", "execution_price", "pnl", "transaction_cost"
        ])


def submit_simulated_order(
    portfolio_id: int,
    security_id: int,
    symbol: str,
    side: str,
    order_type: str,
    quantity: int,
    price: float
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Validates and places a simulated paper-trading order.
    Returns: (success: bool, message: str, order_details: Optional[Dict])
    """
    # Validation Rules
    if not portfolio_id or portfolio_id <= 0:
        return False, "Please select a valid target portfolio.", None

    if not symbol or not security_id:
        return False, "Please select a valid security instrument.", None

    side_clean = side.strip().upper()
    if side_clean not in ["BUY", "SELL"]:
        return False, "Side must be either BUY or SELL.", None

    type_clean = order_type.strip().upper()
    if type_clean not in ["MARKET", "LIMIT"]:
        return False, "Order type must be MARKET or LIMIT.", None

    try:
        qty = int(quantity)
        if qty <= 0:
            return False, "Order quantity must be a positive integer greater than zero.", None
    except (ValueError, TypeError):
        return False, "Invalid quantity specified.", None

    try:
        prc = float(price)
        if type_clean == "LIMIT" and prc <= 0:
            return False, "Limit orders require a positive price greater than zero.", None
    except (ValueError, TypeError):
        return False, "Invalid price specified.", None

    try:
        provider = get_provider()
        order = provider.submit_order(
            portfolio_id=portfolio_id,
            security_id=security_id,
            symbol=symbol,
            side=side_clean,
            order_type=type_clean,
            quantity=qty,
            price=prc
        )
        if "error" in order:
            return False, order["error"], None
        return True, f"Simulated {order_type} {side_clean} order for {qty} {symbol} placed successfully (Order #{order['order_id']}).", order
    except Exception as e:
        logger.error(f"Order submission error: {e}")
        return False, f"Order submission failed: {str(e)}", None
