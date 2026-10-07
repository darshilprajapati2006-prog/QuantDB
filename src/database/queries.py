"""
QuantDB - Centralized SQL Queries

This module contains parameterized SQL queries used by the
repository layer.

Important:
- Do not put database connection logic here.
- Use parameterized queries (%s) to prevent SQL injection.
- Table and column names must match the QuantDB database schema.
"""

from typing import Any, Dict, List, Optional
from .connection import DatabaseConnectionError


# ============================================================
# USERS
# ============================================================

GET_USER_BY_ID = """
SELECT
    user_id,
    name,
    email,
    password_hash,
    role,
    status,
    created_at
FROM users
WHERE user_id = %s;
"""

GET_USER_BY_EMAIL = """
SELECT
    user_id,
    name,
    email,
    password_hash,
    role,
    status,
    created_at
FROM users
WHERE email = %s;
"""

GET_USER_BY_USERNAME = """
SELECT
    user_id,
    name,
    email,
    password_hash,
    role,
    status,
    created_at
FROM users
WHERE email = %s;
"""

GET_USER_BY_IDENTIFIER = """
SELECT
    user_id,
    name,
    email,
    password_hash,
    role,
    status,
    created_at
FROM users
WHERE email = %s OR email LIKE CONCAT(%s, '@%%')
ORDER BY (email = %s) DESC
LIMIT 1;
"""

GET_ALL_USERS = """
SELECT
    user_id,
    name,
    email,
    role,
    status,
    created_at
FROM users
ORDER BY user_id;
"""

UPDATE_USER_ROLE = """
UPDATE users
SET role = %s
WHERE user_id = %s;
"""

UPDATE_USER_STATUS = """
UPDATE users
SET status = %s
WHERE user_id = %s;
"""

UPDATE_USER_PASSWORD_HASH = """
UPDATE users
SET password_hash = %s
WHERE user_id = %s;
"""

UPDATE_USER_VERIFIED = """
UPDATE users
SET is_verified = %s
WHERE user_id = %s;
"""

UPDATE_UNVERIFIED_USER = """
UPDATE users
SET name = %s,
    password_hash = %s,
    created_at = %s
WHERE user_id = %s;
"""

CREATE_USER = """
INSERT INTO users (
    name,
    email,
    password_hash,
    role,
    status,
    created_at
) VALUES (%s, %s, %s, %s, %s, %s);
"""

# ============================================================
# EMAIL OTP & VERIFICATION
# ============================================================

INSERT_EMAIL_OTP = """
INSERT INTO email_otps (
    user_id,
    otp_hash,
    purpose,
    expires_at,
    attempt_count,
    max_attempts,
    is_used,
    created_at
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
"""

GET_LATEST_OTP_FOR_USER = """
SELECT
    otp_id,
    user_id,
    otp_hash,
    purpose,
    expires_at,
    attempt_count,
    max_attempts,
    is_used,
    created_at,
    verified_at
FROM email_otps
WHERE user_id = %s AND purpose = %s AND is_used = FALSE
ORDER BY created_at DESC
LIMIT 1;
"""

INCREMENT_OTP_ATTEMPTS = """
UPDATE email_otps
SET attempt_count = attempt_count + 1
WHERE otp_id = %s;
"""

MARK_OTP_VERIFIED = """
UPDATE email_otps
SET is_used = TRUE,
    verified_at = %s
WHERE otp_id = %s;
"""

INVALIDATE_USER_OTPS = """
UPDATE email_otps
SET is_used = TRUE
WHERE user_id = %s AND purpose = %s;
"""


# ============================================================
# EXCHANGES
# ============================================================

GET_EXCHANGE_BY_ID = """
SELECT
    exchange_id,
    exchange_name,
    exchange_code,
    country,
    timezone
FROM exchanges
WHERE exchange_id = %s;
"""

GET_ALL_EXCHANGES = """
SELECT
    exchange_id,
    exchange_name,
    exchange_code,
    country,
    timezone
FROM exchanges
ORDER BY exchange_name;
"""


# ============================================================
# SECURITIES
# ============================================================

GET_SECURITY_BY_ID = """
SELECT
    security_id,
    exchange_id,
    symbol,
    security_name,
    security_type,
    currency,
    status
FROM securities
WHERE security_id = %s;
"""

GET_SECURITY_BY_SYMBOL = """
SELECT
    security_id,
    exchange_id,
    symbol,
    security_name,
    security_type,
    currency,
    status
FROM securities
WHERE symbol = %s;
"""

GET_ALL_SECURITIES = """
SELECT
    s.security_id,
    s.exchange_id,
    e.exchange_code,
    s.symbol,
    s.security_name,
    s.security_type,
    s.currency,
    s.status
FROM securities s
JOIN exchanges e
    ON s.exchange_id = e.exchange_id
ORDER BY s.symbol;
"""

GET_ACTIVE_SECURITIES = """
SELECT
    security_id,
    exchange_id,
    symbol,
    security_name,
    security_type,
    currency,
    status
FROM securities
WHERE status = 'ACTIVE'
ORDER BY symbol;
"""


# ============================================================
# MARKET DATA
# ============================================================

GET_MARKET_DATA_BY_SECURITY = """
SELECT
    market_data_id,
    security_id,
    timestamp,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    bid_price,
    ask_price
FROM market_data
WHERE security_id = %s
ORDER BY timestamp;
"""

GET_MARKET_DATA_BY_SECURITY_DATE_RANGE = """
SELECT
    market_data_id,
    security_id,
    timestamp,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    bid_price,
    ask_price
FROM market_data
WHERE security_id = %s
  AND timestamp BETWEEN %s AND %s
ORDER BY timestamp;
"""

GET_LATEST_MARKET_DATA = """
SELECT
    market_data_id,
    security_id,
    timestamp,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    bid_price,
    ask_price
FROM market_data
WHERE security_id = %s
ORDER BY timestamp DESC
LIMIT 1;
"""

GET_MARKET_DATA_LIMIT = """
SELECT
    market_data_id,
    security_id,
    timestamp,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    bid_price,
    ask_price
FROM market_data
WHERE security_id = %s
ORDER BY timestamp DESC
LIMIT %s;
"""


# ============================================================
# ORDERS
# ============================================================

GET_ORDER_BY_ID = """
SELECT
    order_id,
    user_id,
    security_id,
    order_type,
    side,
    quantity,
    order_price,
    order_status,
    order_time
FROM orders
WHERE order_id = %s;
"""

GET_ORDERS_BY_USER = """
SELECT
    o.order_id,
    o.user_id,
    o.security_id,
    s.symbol,
    o.order_type,
    o.side,
    o.quantity,
    o.order_price,
    o.order_status,
    o.order_time
FROM orders o
JOIN securities s
    ON o.security_id = s.security_id
WHERE o.user_id = %s
ORDER BY o.order_time DESC;
"""

GET_ORDERS_BY_SECURITY = """
SELECT
    o.order_id,
    o.user_id,
    o.security_id,
    s.symbol,
    o.order_type,
    o.side,
    o.quantity,
    o.order_price,
    o.order_status,
    o.order_time
FROM orders o
JOIN securities s
    ON o.security_id = s.security_id
WHERE o.security_id = %s
ORDER BY o.order_time DESC;
"""

GET_ALL_ORDERS = """
SELECT
    o.order_id,
    o.user_id,
    o.security_id,
    s.symbol,
    o.order_type,
    o.side,
    o.quantity,
    o.order_price,
    o.order_status,
    o.order_time
FROM orders o
JOIN securities s
    ON o.security_id = s.security_id
ORDER BY o.order_time DESC;
"""

CREATE_ORDER = """
INSERT INTO orders (
    user_id,
    security_id,
    order_type,
    side,
    quantity,
    order_price,
    order_status,
    order_time
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
"""

UPDATE_ORDER_STATUS = """
UPDATE orders
SET order_status = %s
WHERE order_id = %s;
"""


# ============================================================
# TRADES
# ============================================================

GET_TRADE_BY_ID = """
SELECT
    trade_id,
    order_id,
    security_id,
    trade_side,
    quantity,
    execution_price,
    trade_time,
    transaction_cost
FROM trades
WHERE trade_id = %s;
"""

GET_TRADES_BY_ORDER = """
SELECT
    trade_id,
    order_id,
    security_id,
    trade_side,
    quantity,
    execution_price,
    trade_time,
    transaction_cost
FROM trades
WHERE order_id = %s
ORDER BY trade_time;
"""

GET_TRADES_BY_SECURITY = """
SELECT
    t.trade_id,
    t.order_id,
    t.security_id,
    s.symbol,
    t.trade_side,
    t.quantity,
    t.execution_price,
    t.trade_time,
    t.transaction_cost
FROM trades t
JOIN securities s
    ON t.security_id = s.security_id
WHERE t.security_id = %s
ORDER BY t.trade_time DESC;
"""

GET_ALL_TRADES = """
SELECT
    t.trade_id,
    t.order_id,
    t.security_id,
    s.symbol,
    t.trade_side,
    t.quantity,
    t.execution_price,
    t.trade_time,
    t.transaction_cost
FROM trades t
JOIN securities s
    ON t.security_id = s.security_id
ORDER BY t.trade_time DESC;
"""

CREATE_TRADE = """
INSERT INTO trades (
    order_id,
    security_id,
    trade_side,
    quantity,
    execution_price,
    trade_time,
    transaction_cost
)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""


# ============================================================
# PORTFOLIOS
# ============================================================

GET_PORTFOLIO_BY_ID = """
SELECT
    portfolio_id,
    user_id,
    portfolio_name,
    initial_capital,
    current_cash,
    created_at,
    status
FROM portfolios
WHERE portfolio_id = %s;
"""

GET_PORTFOLIOS_BY_USER = """
SELECT
    portfolio_id,
    user_id,
    portfolio_name,
    initial_capital,
    current_cash,
    created_at,
    status
FROM portfolios
WHERE user_id = %s
ORDER BY portfolio_id;
"""

GET_ALL_PORTFOLIOS = """
SELECT
    p.portfolio_id,
    p.user_id,
    u.name AS user_name,
    p.portfolio_name,
    p.initial_capital,
    p.current_cash,
    p.created_at,
    p.status
FROM portfolios p
JOIN users u
    ON p.user_id = u.user_id
ORDER BY p.portfolio_id;
"""

CREATE_PORTFOLIO = """
INSERT INTO portfolios (
    user_id,
    portfolio_name,
    initial_capital,
    current_cash,
    created_at,
    status
)
VALUES (%s, %s, %s, %s, %s, %s);
"""

UPDATE_PORTFOLIO_CASH = """
UPDATE portfolios
SET current_cash = %s
WHERE portfolio_id = %s;
"""


# ============================================================
# POSITIONS
# ============================================================

GET_POSITION_BY_ID = """
SELECT
    position_id,
    portfolio_id,
    security_id,
    quantity,
    average_price,
    realized_pnl,
    unrealized_pnl,
    updated_at
FROM positions
WHERE position_id = %s;
"""

GET_POSITIONS_BY_PORTFOLIO = """
SELECT
    p.position_id,
    p.portfolio_id,
    p.security_id,
    s.symbol,
    p.quantity,
    p.average_price,
    p.realized_pnl,
    p.unrealized_pnl,
    p.updated_at
FROM positions p
JOIN securities s
    ON p.security_id = s.security_id
WHERE p.portfolio_id = %s
ORDER BY s.symbol;
"""

GET_POSITION_BY_PORTFOLIO_SECURITY = """
SELECT
    position_id,
    portfolio_id,
    security_id,
    quantity,
    average_price,
    realized_pnl,
    unrealized_pnl,
    updated_at
FROM positions
WHERE portfolio_id = %s
  AND security_id = %s;
"""

CREATE_POSITION = """
INSERT INTO positions (
    portfolio_id,
    security_id,
    quantity,
    average_price,
    realized_pnl,
    unrealized_pnl,
    updated_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

UPDATE_POSITION = """
UPDATE positions
SET
    quantity = %s,
    average_price = %s,
    realized_pnl = %s,
    unrealized_pnl = %s,
    updated_at = %s
WHERE position_id = %s;
"""


# ============================================================
# STRATEGIES
# ============================================================

GET_STRATEGY_BY_ID = """
SELECT
    strategy_id,
    user_id,
    strategy_name,
    description,
    strategy_type,
    parameters,
    status,
    created_at
FROM strategies
WHERE strategy_id = %s;
"""

GET_STRATEGIES_BY_USER = """
SELECT
    strategy_id,
    user_id,
    strategy_name,
    description,
    strategy_type,
    parameters,
    status,
    created_at
FROM strategies
WHERE user_id = %s
ORDER BY created_at DESC;
"""

GET_ACTIVE_STRATEGIES = """
SELECT
    strategy_id,
    user_id,
    strategy_name,
    description,
    strategy_type,
    parameters,
    status,
    created_at
FROM strategies
WHERE status = 'ACTIVE'
ORDER BY strategy_name;
"""

CREATE_STRATEGY = """
INSERT INTO strategies (
    user_id,
    strategy_name,
    description,
    strategy_type,
    parameters,
    status,
    created_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

UPDATE_STRATEGY_STATUS = """
UPDATE strategies
SET status = %s
WHERE strategy_id = %s;
"""


# ============================================================
# BACKTESTS
# ============================================================

GET_BACKTEST_BY_ID = """
SELECT
    backtest_id,
    strategy_id,
    security_id,
    start_date,
    end_date,
    initial_capital,
    created_at,
    status
FROM backtests
WHERE backtest_id = %s;
"""

GET_BACKTESTS_BY_STRATEGY = """
SELECT
    b.backtest_id,
    b.strategy_id,
    s.strategy_name,
    b.security_id,
    sec.symbol,
    b.start_date,
    b.end_date,
    b.initial_capital,
    b.created_at,
    b.status
FROM backtests b
JOIN strategies s
    ON b.strategy_id = s.strategy_id
JOIN securities sec
    ON b.security_id = sec.security_id
WHERE b.strategy_id = %s
ORDER BY b.created_at DESC;
"""

GET_ALL_BACKTESTS = """
SELECT
    b.backtest_id,
    b.strategy_id,
    s.strategy_name,
    b.security_id,
    sec.symbol,
    b.start_date,
    b.end_date,
    b.initial_capital,
    b.created_at,
    b.status
FROM backtests b
JOIN strategies s
    ON b.strategy_id = s.strategy_id
JOIN securities sec
    ON b.security_id = sec.security_id
ORDER BY b.created_at DESC;
"""

CREATE_BACKTEST = """
INSERT INTO backtests (
    strategy_id,
    security_id,
    start_date,
    end_date,
    initial_capital,
    created_at,
    status
)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

UPDATE_BACKTEST_STATUS = """
UPDATE backtests
SET status = %s
WHERE backtest_id = %s;
"""


# ============================================================
# BACKTEST RESULTS
# ============================================================

GET_BACKTEST_RESULT_BY_ID = """
SELECT
    result_id,
    backtest_id,
    total_return,
    total_pnl,
    volatility,
    sharpe_ratio,
    max_drawdown,
    total_trades,
    winning_trades,
    losing_trades,
    win_rate
FROM backtest_results
WHERE result_id = %s;
"""

GET_BACKTEST_RESULT = """
SELECT
    result_id,
    backtest_id,
    total_return,
    total_pnl,
    volatility,
    sharpe_ratio,
    max_drawdown,
    total_trades,
    winning_trades,
    losing_trades,
    win_rate
FROM backtest_results
WHERE backtest_id = %s;
"""

CREATE_BACKTEST_RESULT = """
INSERT INTO backtest_results (
    backtest_id,
    total_return,
    total_pnl,
    volatility,
    sharpe_ratio,
    max_drawdown,
    total_trades,
    winning_trades,
    losing_trades,
    win_rate
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""


# ============================================================
# RISK METRICS
# ============================================================

GET_RISK_METRIC_BY_ID = """
SELECT
    metric_id,
    portfolio_id,
    backtest_id,
    metric_date,
    return_value,
    volatility,
    sharpe_ratio,
    max_drawdown,
    calculated_at
FROM risk_metrics
WHERE metric_id = %s;
"""

GET_RISK_METRICS_BY_PORTFOLIO = """
SELECT
    metric_id,
    portfolio_id,
    backtest_id,
    metric_date,
    return_value,
    volatility,
    sharpe_ratio,
    max_drawdown,
    calculated_at
FROM risk_metrics
WHERE portfolio_id = %s
ORDER BY metric_date DESC;
"""

GET_RISK_METRICS_BY_BACKTEST = """
SELECT
    metric_id,
    portfolio_id,
    backtest_id,
    metric_date,
    return_value,
    volatility,
    sharpe_ratio,
    max_drawdown,
    calculated_at
FROM risk_metrics
WHERE backtest_id = %s
ORDER BY metric_date DESC;
"""

CREATE_RISK_METRIC = """
INSERT INTO risk_metrics (
    portfolio_id,
    backtest_id,
    metric_date,
    return_value,
    volatility,
    sharpe_ratio,
    max_drawdown,
    calculated_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
"""


# ============================================================
# DASHBOARD / ANALYTICS QUERIES
# ============================================================

GET_PORTFOLIO_SUMMARY = """
SELECT
    p.portfolio_id,
    p.portfolio_name,
    p.initial_capital,
    p.current_cash,
    COALESCE(SUM(pos.realized_pnl), 0) AS realized_pnl,
    COALESCE(SUM(pos.unrealized_pnl), 0) AS unrealized_pnl
FROM portfolios p
LEFT JOIN positions pos
    ON p.portfolio_id = pos.portfolio_id
WHERE p.portfolio_id = %s
GROUP BY
    p.portfolio_id,
    p.portfolio_name,
    p.initial_capital,
    p.current_cash;
"""

GET_TRADE_STATISTICS = """
SELECT
    COUNT(*) AS total_trades,
    SUM(CASE WHEN trade_side = 'BUY' THEN 1 ELSE 0 END) AS buy_trades,
    SUM(CASE WHEN trade_side = 'SELL' THEN 1 ELSE 0 END) AS sell_trades,
    COALESCE(SUM(transaction_cost), 0) AS total_transaction_cost
FROM trades;
"""

GET_ORDER_STATISTICS = """
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_status = 'PENDING' THEN 1 ELSE 0 END) AS pending_orders,
    SUM(CASE WHEN order_status = 'FILLED' THEN 1 ELSE 0 END) AS filled_orders,
    SUM(CASE WHEN order_status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_orders,
    SUM(CASE WHEN order_status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected_orders
FROM orders;
"""


# ============================================================
# QUERY EXECUTION HELPERS (USED BY REPOSITORY LAYER)
# ============================================================

def _check_conn(conn):
    if conn is None:
        raise DatabaseConnectionError("Database connection is None.")

def _close_cursor(cursor):
    if cursor is not None and hasattr(cursor, "close"):
        try:
            _close_cursor(cursor)
        except Exception:
            pass

def _normalize_user_dict(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Normalizes a user database row into a standardized dictionary contract.
    Ensures 'username' and 'is_verified' keys are always present even when
    the underlying Aiven schema does not have those physical columns.
    """
    if not row:
        return None
    res = dict(row)
    if "username" not in res or not res["username"]:
        email_val = res.get("email") or ""
        res["username"] = email_val.split("@")[0] if email_val else (res.get("name") or f"user_{res.get('user_id')}")
    if "is_verified" not in res:
        res["is_verified"] = True
    return res


def get_user_by_id(conn, user_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_USER_BY_ID, (user_id,))
        return _normalize_user_dict(cursor.fetchone())
    finally:
        _close_cursor(cursor)


def get_user_by_email(conn, email: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_USER_BY_EMAIL, (email,))
        return _normalize_user_dict(cursor.fetchone())
    finally:
        _close_cursor(cursor)


def get_user_by_username(conn, username: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        # Schema contract: email is the primary credential in users table.
        # Fall back to identifier match if username entered without domain.
        cursor.execute(GET_USER_BY_IDENTIFIER, (username, username, username))
        return _normalize_user_dict(cursor.fetchone())
    finally:
        _close_cursor(cursor)


def get_user_by_identifier(conn, identifier: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_USER_BY_IDENTIFIER, (identifier, identifier, identifier))
        return _normalize_user_dict(cursor.fetchone())
    finally:
        _close_cursor(cursor)


def get_all_users(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_ALL_USERS)
        rows = cursor.fetchall() or []
        return [_normalize_user_dict(r) for r in rows if r]
    finally:
        _close_cursor(cursor)


def update_user_role(conn, user_id: int, role: str) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute(UPDATE_USER_ROLE, (role, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        _close_cursor(cursor)


def update_user_status(conn, user_id: int, status: str) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute(UPDATE_USER_STATUS, (status, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        _close_cursor(cursor)


def update_user_password(conn, user_id: int, password_hash: str) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute(UPDATE_USER_PASSWORD_HASH, (password_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        _close_cursor(cursor)


def update_user_verified(conn, user_id: int, is_verified: bool = True) -> bool:
    cursor = conn.cursor()
    try:
        try:
            cursor.execute(UPDATE_USER_VERIFIED, (is_verified, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as col_err:
            # If is_verified column does not exist on target database, gracefully succeed
            if "Unknown column 'is_verified'" in str(col_err) or "1054" in str(col_err):
                return True
            raise
    finally:
        _close_cursor(cursor)


def update_unverified_user(
    conn, user_id: int, name: str, *args, username: Optional[str] = None, password_hash: str = "", **kwargs
) -> bool:
    cursor = conn.cursor()
    try:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        resolved_hash = password_hash
        if not resolved_hash and len(args) >= 1:
            # Legacy positional args: (conn, user_id, name, username, password_hash)
            resolved_hash = args[-1]
        elif "password_hash" in kwargs:
            resolved_hash = kwargs["password_hash"]

        cursor.execute(
            UPDATE_UNVERIFIED_USER, (name, resolved_hash, now, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        _close_cursor(cursor)


def create_user(
    conn,
    name: str = "",
    email: str = "",
    password_hash: str = "",
    role: str = "USER",
    status: str = "ACTIVE",
    created_at: Optional[str] = None,
    *args,
    **kwargs,
) -> int:
    cursor = conn.cursor()
    try:
        from datetime import datetime
        now = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        resolved_name = name
        resolved_email = email
        resolved_hash = password_hash
        resolved_role = role
        resolved_status = status

        # Handle legacy positional calls: (conn, username, name, email, password_hash, role, status)
        if "@" not in email and len(args) >= 1 and "@" in str(args[0]):
            resolved_name = email
            resolved_email = args[0]
            resolved_hash = args[1] if len(args) > 1 else password_hash
            resolved_role = args[2] if len(args) > 2 else role
            resolved_status = args[3] if len(args) > 3 else status
        elif "email" in kwargs:
            resolved_email = kwargs["email"]
            resolved_name = kwargs.get("name", resolved_name)
            resolved_hash = kwargs.get("password_hash", resolved_hash)
            resolved_role = kwargs.get("role", resolved_role)
            resolved_status = kwargs.get("status", resolved_status)

        cursor.execute(
            CREATE_USER,
            (resolved_name, resolved_email, resolved_hash, resolved_role, resolved_status, now),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        _close_cursor(cursor)


def insert_email_otp(
    conn,
    user_id: int,
    otp_hash: str,
    purpose: str = "REGISTRATION",
    expires_at: Optional[str] = None,
    max_attempts: int = 5,
) -> int:
    cursor = conn.cursor()
    try:
        from datetime import datetime, timedelta
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        exp_str = expires_at or (now_dt + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            INSERT_EMAIL_OTP,
            (user_id, otp_hash, purpose, exp_str, 0, max_attempts, False, now_str),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        _close_cursor(cursor)


def get_latest_otp_for_user(
    conn, user_id: int, purpose: str = "REGISTRATION"
) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_LATEST_OTP_FOR_USER, (user_id, purpose))
        return cursor.fetchone()
    finally:
        _close_cursor(cursor)


def increment_otp_attempts(conn, otp_id: int) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute(INCREMENT_OTP_ATTEMPTS, (otp_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        _close_cursor(cursor)


def mark_otp_verified(conn, otp_id: int) -> bool:
    cursor = conn.cursor()
    try:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(MARK_OTP_VERIFIED, (now, otp_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        _close_cursor(cursor)


def invalidate_user_otps(conn, user_id: int, purpose: str = "REGISTRATION") -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute(INVALIDATE_USER_OTPS, (user_id, purpose))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        _close_cursor(cursor)


def get_security_by_id(conn, security_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_SECURITY_BY_ID, (security_id,))
        return cursor.fetchone()
    finally:
        _close_cursor(cursor)


def get_all_securities(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_ALL_SECURITIES)
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_market_data(
    conn,
    security_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        if start_time is not None and end_time is not None:
            cursor.execute(
                GET_MARKET_DATA_BY_SECURITY_DATE_RANGE,
                (security_id, start_time, end_time),
            )
        else:
            cursor.execute(GET_MARKET_DATA_BY_SECURITY, (security_id,))
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_order_by_id(conn, order_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_ORDER_BY_ID, (order_id,))
        return cursor.fetchone()
    finally:
        _close_cursor(cursor)


def get_orders_by_user(conn, user_id: int) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_ORDERS_BY_USER, (user_id,))
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_all_orders(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_ALL_ORDERS)
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def insert_order(
    conn,
    user_id: int,
    security_id: int,
    order_type: str,
    side: str,
    quantity: float,
    order_price: Optional[float],
    order_status: str,
    order_time: str,
) -> int:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            CREATE_ORDER,
            (
                user_id,
                security_id,
                order_type,
                side,
                quantity,
                order_price,
                order_status,
                order_time,
            ),
        )
        return cursor.lastrowid
    finally:
        _close_cursor(cursor)


def update_order_status(conn, order_id: int, order_status: str) -> int:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(UPDATE_ORDER_STATUS, (order_status, order_id))
        return cursor.rowcount
    finally:
        _close_cursor(cursor)


def get_trade_by_id(conn, trade_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_TRADE_BY_ID, (trade_id,))
        return cursor.fetchone()
    finally:
        _close_cursor(cursor)


def get_trades_by_security(conn, security_id: int) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_TRADES_BY_SECURITY, (security_id,))
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_all_trades(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_ALL_TRADES)
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def insert_trade(
    conn,
    order_id: int,
    security_id: int,
    trade_side: str,
    quantity: float,
    execution_price: float,
    trade_time: str,
    transaction_cost: float,
) -> int:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            CREATE_TRADE,
            (
                order_id,
                security_id,
                trade_side,
                quantity,
                execution_price,
                trade_time,
                transaction_cost,
            ),
        )
        return cursor.lastrowid
    finally:
        _close_cursor(cursor)


def get_portfolio_by_id(conn, portfolio_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_PORTFOLIO_BY_ID, (portfolio_id,))
        return cursor.fetchone()
    finally:
        _close_cursor(cursor)


def get_portfolios_by_user(conn, user_id: int) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_PORTFOLIOS_BY_USER, (user_id,))
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_all_portfolios(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_ALL_PORTFOLIOS)
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_position(
    conn,
    portfolio_id: int,
    security_id: int,
) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            GET_POSITION_BY_PORTFOLIO_SECURITY,
            (portfolio_id, security_id),
        )
        return cursor.fetchone()
    finally:
        _close_cursor(cursor)


def get_positions_by_portfolio(
    conn,
    portfolio_id: int,
) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_POSITIONS_BY_PORTFOLIO, (portfolio_id,))
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_strategy_by_id(conn, strategy_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_STRATEGY_BY_ID, (strategy_id,))
        return cursor.fetchone()
    finally:
        _close_cursor(cursor)


def get_strategies_by_user(conn, user_id: int) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_STRATEGIES_BY_USER, (user_id,))
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_all_strategies(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_ACTIVE_STRATEGIES)
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def insert_strategy(
    conn,
    user_id: int,
    strategy_name: str,
    description: Optional[str],
    strategy_type: str,
    parameters: Optional[str],
    status: str,
    created_at: str,
) -> int:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            CREATE_STRATEGY,
            (
                user_id,
                strategy_name,
                description,
                strategy_type,
                parameters,
                status,
                created_at,
            ),
        )
        return cursor.lastrowid
    finally:
        _close_cursor(cursor)


def get_backtest_by_id(conn, backtest_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_BACKTEST_BY_ID, (backtest_id,))
        return cursor.fetchone()
    finally:
        _close_cursor(cursor)


def get_backtests_by_strategy(
    conn,
    strategy_id: int,
) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_BACKTESTS_BY_STRATEGY, (strategy_id,))
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_all_backtests(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_ALL_BACKTESTS)
        return cursor.fetchall()
    finally:
        _close_cursor(cursor)


def get_backtest_result(conn, backtest_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(GET_BACKTEST_RESULT, (backtest_id,))
        return cursor.fetchone()
    finally:
        _close_cursor(cursor)


def get_risk_metrics(
    conn,
    portfolio_id: Optional[int] = None,
    backtest_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        if portfolio_id is not None:
            cursor.execute(GET_RISK_METRICS_BY_PORTFOLIO, (portfolio_id,))
            return cursor.fetchall()
        elif backtest_id is not None:
            cursor.execute(GET_RISK_METRICS_BY_BACKTEST, (backtest_id,))
            return cursor.fetchall()
        return []
    finally:
        _close_cursor(cursor)