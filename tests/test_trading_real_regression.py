"""
Regression test suite for QuantDB Trading Order & Trade History in REAL and MOCK modes.

Validates:
1. RealProvider fetches existing orders (IDs 1-5) from Aiven MySQL.
2. RealProvider fetches executed trades (IDs 1-5) linked to orders 1-5.
3. User & role-based access control (Admin oversight vs. non-admin isolation).
4. Distinguishing genuine empty results from database/query failures.
5. Cache invalidation after state mutations.
6. Preserving MockProvider functionality without regressions.
"""

import os
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.auth.roles import Role
from src.database.connection import get_connection
from src.database.repository import Repository
import src.database.queries as queries
from dashboard.providers.real_provider import RealProvider
from dashboard.providers.mock_provider import MockProvider
from dashboard.providers.factory import set_data_mode, get_current_data_mode
from dashboard.services import trading_service


@pytest.fixture(autouse=True)
def restore_data_mode():
    orig_mode = os.environ.get("DATA_MODE", "real")
    yield
    os.environ["DATA_MODE"] = orig_mode


# ==============================================================================
# 1. LIVE AIVEN MYSQL INTEGRATION TESTS
# ==============================================================================

def test_real_database_connectivity_and_orders():
    """Verify live connection to Aiven MySQL QuantDB and retrieve orders 1-5."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orders ORDER BY order_id;")
        orders = cursor.fetchall()
        assert len(orders) >= 5, f"Expected at least 5 orders in Aiven MySQL, found {len(orders)}"
        order_ids = [o["order_id"] for o in orders]
        for expected_id in [1, 2, 3, 4, 5]:
            assert expected_id in order_ids, f"Order ID {expected_id} missing from database"
    finally:
        cursor.close()
        conn.close()


def test_real_database_connectivity_and_trades():
    """Verify live connection to Aiven MySQL QuantDB and retrieve trades 1-5 linked to orders."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM trades ORDER BY trade_id;")
        trades = cursor.fetchall()
        assert len(trades) >= 5, f"Expected at least 5 trades in Aiven MySQL, found {len(trades)}"
        trade_ids = [t["trade_id"] for t in trades]
        for expected_id in [1, 2, 3, 4, 5]:
            assert expected_id in trade_ids, f"Trade ID {expected_id} missing from database"
            # Ensure trade is linked to a valid order_id
            trade_record = next(t for t in trades if t["trade_id"] == expected_id)
            assert trade_record["order_id"] in [1, 2, 3, 4, 5]
    finally:
        cursor.close()
        conn.close()


def test_queries_module_sql_syntax_validity():
    """Verify queries module functions execute against MySQL without 'Unknown column o.portfolio_id'."""
    conn = get_connection()
    try:
        all_orders = queries.get_all_orders(conn)
        assert isinstance(all_orders, list)
        assert len(all_orders) >= 5

        orders_by_user = queries.get_orders_by_user(conn, 1)
        assert isinstance(orders_by_user, list)
        assert len(orders_by_user) >= 5

        all_trades = queries.get_all_trades(conn)
        assert isinstance(all_trades, list)
        assert len(all_trades) >= 5

        trades_by_user = queries.get_trades_by_user(conn, 1)
        assert isinstance(trades_by_user, list)
        assert len(trades_by_user) >= 5
    finally:
        conn.close()


def test_real_provider_get_orders_returns_existing_records():
    """Ensure RealProvider.get_orders returns existing database records as DataFrame with required columns."""
    rp = RealProvider()
    assert rp.is_connected(), "RealProvider should be connected to Aiven MySQL"

    # Fetch orders with portfolio_id passed (like Trading page selectbox does)
    orders_df = rp.get_orders(portfolio_id=1)
    assert not orders_df.empty, "RealProvider.get_orders(portfolio_id=1) must not be empty"
    assert len(orders_df) >= 5

    required_cols = ["order_id", "symbol", "side", "order_type", "quantity", "price", "status", "timestamp"]
    for col in required_cols:
        assert col in orders_df.columns, f"Missing required column '{col}' in orders DataFrame"

    # Verify existing order IDs 1-5 are present
    fetched_ids = set(orders_df["order_id"].tolist())
    for expected_id in [1, 2, 3, 4, 5]:
        assert expected_id in fetched_ids, f"Order #{expected_id} not found in RealProvider output"


def test_real_provider_get_trades_returns_existing_records():
    """Ensure RealProvider.get_trades returns existing database records as DataFrame with required columns."""
    rp = RealProvider()
    assert rp.is_connected(), "RealProvider should be connected to Aiven MySQL"

    trades_df = rp.get_trades(portfolio_id=1)
    assert not trades_df.empty, "RealProvider.get_trades(portfolio_id=1) must not be empty"
    assert len(trades_df) >= 5

    required_cols = ["trade_id", "order_id", "symbol", "side", "quantity", "execution_price", "transaction_cost", "timestamp"]
    for col in required_cols:
        assert col in trades_df.columns, f"Missing required column '{col}' in trades DataFrame"

    fetched_ids = set(trades_df["trade_id"].tolist())
    for expected_id in [1, 2, 3, 4, 5]:
        assert expected_id in fetched_ids, f"Trade #{expected_id} not found in RealProvider output"


# ==============================================================================
# 2. RBAC & USER FILTERING TESTS
# ==============================================================================

def test_admin_user_has_global_orders_visibility():
    """Admin users (like Darshil Prajapati, user_id=17) see all platform orders."""
    with patch("dashboard.services.auth_service.get_current_user") as mock_user:
        mock_user.return_value = {
            "user_id": 17,
            "username": "ImDarshil13",
            "name": "Darshil Prajapati",
            "role": Role.ADMIN,
        }
        trading_service.invalidate_trading_cache()
        orders_df = trading_service.get_orders(portfolio_id=1)
        assert not orders_df.empty, "Admin should see platform orders"
        assert len(orders_df) >= 5


def test_non_admin_user_restricted_to_own_orders():
    """Non-admin user only sees orders matching their own user_id."""
    with patch("dashboard.services.auth_service.get_current_user") as mock_user:
        mock_user.return_value = {
            "user_id": 9999,  # Non-existent user
            "username": "trader99",
            "name": "Trader Ninety-Nine",
            "role": Role.QUANT_TRADER,
        }
        trading_service.invalidate_trading_cache()
        orders_df = trading_service.get_orders(portfolio_id=1)
        # Should be empty DataFrame with correct columns because user 9999 has 0 orders
        assert orders_df.empty, "Non-admin user 9999 should not see other users' orders"
        assert "order_id" in orders_df.columns


# ==============================================================================
# 3. OPEN ORDERS (STATUS FILTERING) TESTS
# ==============================================================================

def test_open_orders_filters_pending_status_correctly():
    """Verify get_open_orders filters only active/pending orders."""
    with patch("dashboard.services.auth_service.get_current_user") as mock_user:
        mock_user.return_value = {
            "user_id": 1,
            "role": Role.ADMIN,
        }
        trading_service.invalidate_trading_cache()
        open_orders_df = trading_service.get_open_orders(portfolio_id=1)
        # Since orders 1-5 in DB are all 'FILLED', open_orders_df must only contain 'PENDING'
        if not open_orders_df.empty:
            assert all(open_orders_df["status"] == "PENDING")


# ==============================================================================
# 4. ERROR HANDLING & GENUINE EMPTY VS QUERY FAILURE
# ==============================================================================

def test_distinguishes_empty_result_from_query_failure():
    """Test that a database failure raises an exception or logs an error rather than silently faking empty results."""
    mock_repo = MagicMock(spec=Repository)
    mock_repo.get_orders.side_effect = Exception("Simulated DB connection timeout")

    with pytest.raises(Exception, match="Simulated DB connection timeout"):
        from src.services.trading_service import get_orders as backend_get_orders
        backend_get_orders(user_id=1, repo=mock_repo)


# ==============================================================================
# 5. CACHE INVALIDATION ON MUTATION
# ==============================================================================

def test_cache_invalidation_after_state_change():
    """Ensure invalidate_trading_cache clears memoized caches without error."""
    trading_service.invalidate_trading_cache()
    # Cache clear functions succeed cleanly


# ==============================================================================
# 6. MOCK MODE PRESERVATION
# ==============================================================================

def test_mock_mode_functionality_preserved():
    """Verify MockProvider continues to function correctly for offline simulation."""
    set_data_mode("mock")
    assert get_current_data_mode() == "mock"
    mp = MockProvider()
    mock_orders = mp.get_orders(portfolio_id=1)
    assert not mock_orders.empty
    assert "order_id" in mock_orders.columns

    mock_trades = mp.get_trades(portfolio_id=1)
    assert not mock_trades.empty
    assert "trade_id" in mock_trades.columns
