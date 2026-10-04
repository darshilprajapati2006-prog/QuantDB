"""
QuantDB - Centralized SQL Queries

This module contains parameterized SQL queries used by the
repository layer.

Important:
- Do not put database connection logic here.
- Use parameterized queries (%s) to prevent SQL injection.
- Table and column names must match the QuantDB database schema.
"""


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