"""
QuantDB Simulated Trading Service.
Handles paper trading order submission, order lifecycle queries, and trade execution history.
Performs clean input validation before forwarding to data providers.
NO REAL-MONEY TRADING IS PERFORMED.
"""

import logging
from typing import Dict, Optional, Tuple
import pandas as pd
import streamlit as st

from dashboard.providers.factory import get_provider, get_current_data_mode
from dashboard.services.portfolio_service import clear_portfolio_service_cache

logger = logging.getLogger(__name__)


def _resolve_effective_user_id(explicit_user_id: Optional[int] = None) -> Optional[int]:
    """
    Resolves the target user_id based on role and explicit arguments:
    - If explicit_user_id is passed, it is respected.
    - If user is ADMIN, returns None to allow global platform oversight.
    - If user is non-admin, strictly restricts queries to the user's own ID.
    """
    if explicit_user_id is not None:
        return explicit_user_id
    try:
        from dashboard.services.auth_service import get_current_user
        from src.auth.roles import Role
        curr = get_current_user()
        if curr:
            role = curr.get("role")
            if role == Role.ADMIN:
                return None
            return curr.get("user_id")
    except Exception:
        pass
    return None


@st.cache_data(ttl=15, show_spinner=False)
def _cached_get_orders(data_mode: str, portfolio_id: Optional[int], status: Optional[str], user_id: Optional[int]) -> pd.DataFrame:
    provider = get_provider()
    return provider.get_orders(portfolio_id=portfolio_id, status=status, user_id=user_id)


def get_orders(
    portfolio_id: Optional[int] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
) -> pd.DataFrame:
    """Retrieves orders filtered by portfolio, status, and/or user_id with RBAC enforcement."""
    effective_user_id = _resolve_effective_user_id(user_id)
    try:
        mode = get_current_data_mode()
        return _cached_get_orders(mode, portfolio_id, status, effective_user_id)
    except Exception as e:
        logger.error(f"Error fetching orders from provider (mode={get_current_data_mode()}, user_id={effective_user_id}): {e}", exc_info=True)
        try:
            return get_provider().get_orders(portfolio_id=portfolio_id, status=status, user_id=effective_user_id)
        except Exception as inner_e:
            logger.error(f"Direct provider fallback also failed for get_orders: {inner_e}", exc_info=True)
            return pd.DataFrame(columns=[
                "order_id", "portfolio_id", "security_id", "symbol",
                "timestamp", "side", "order_type", "quantity", "price", "status"
            ])


def get_open_orders(portfolio_id: Optional[int] = None, user_id: Optional[int] = None) -> pd.DataFrame:
    """Retrieves only active/pending orders."""
    return get_orders(portfolio_id=portfolio_id, status="PENDING", user_id=user_id)


@st.cache_data(ttl=15, show_spinner=False)
def _cached_get_trades(data_mode: str, portfolio_id: Optional[int], user_id: Optional[int]) -> pd.DataFrame:
    provider = get_provider()
    return provider.get_trades(portfolio_id=portfolio_id, user_id=user_id)


def get_trades(portfolio_id: Optional[int] = None, user_id: Optional[int] = None) -> pd.DataFrame:
    """Retrieves executed trade history with RBAC enforcement."""
    effective_user_id = _resolve_effective_user_id(user_id)
    try:
        mode = get_current_data_mode()
        return _cached_get_trades(mode, portfolio_id, effective_user_id)
    except Exception as e:
        logger.error(f"Error fetching trades from provider (mode={get_current_data_mode()}, user_id={effective_user_id}): {e}", exc_info=True)
        try:
            return get_provider().get_trades(portfolio_id=portfolio_id, user_id=effective_user_id)
        except Exception as inner_e:
            logger.error(f"Direct provider fallback also failed for get_trades: {inner_e}", exc_info=True)
            return pd.DataFrame(columns=[
                "trade_id", "order_id", "security_id", "symbol",
                "timestamp", "side", "quantity", "execution_price", "pnl", "transaction_cost"
            ])


def invalidate_trading_cache() -> None:
    """Invalidates affected caches after state-mutating operations like order placement."""
    try:
        _cached_get_orders.clear()
        _cached_get_trades.clear()
        clear_portfolio_service_cache()
    except Exception as e:
        logger.debug(f"Failed to invalidate trading cache: {e}")


# Alias for consistent naming across service layer
clear_trading_service_cache = invalidate_trading_cache


def submit_simulated_order(
    portfolio_id: int,
    security_id: int,
    symbol: str,
    side: str,
    order_type: str,
    quantity: int,
    price: float,
    user_id: Optional[int] = None,
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
        if user_id is None:
            try:
                from dashboard.services.auth_service import get_current_user
                curr = get_current_user()
                if curr and curr.get("user_id"):
                    user_id = curr.get("user_id")
            except Exception:
                pass

        provider = get_provider()
        order = provider.submit_order(
            portfolio_id=portfolio_id,
            security_id=security_id,
            symbol=symbol,
            side=side_clean,
            order_type=type_clean,
            quantity=qty,
            price=prc,
            user_id=user_id,
        )
        if "error" in order:
            return False, order["error"], None

        # State has changed: immediately invalidate affected caches
        invalidate_trading_cache()

        return True, f"Simulated {order_type} {side_clean} order for {qty} {symbol} placed successfully (Order #{order['order_id']}).", order
    except Exception as e:
        logger.error(f"Order submission error: {e}", exc_info=True)
        return False, f"Order submission failed: {str(e)}", None

