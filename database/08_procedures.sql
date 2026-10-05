USE QuantDB;

-- 08_procedures.sql
-- QuantDB Stored Procedures


-- 1. Get all portfolios of a user
DELIMITER $$

CREATE PROCEDURE sp_get_user_portfolios(IN p_user_id BIGINT)
BEGIN
    SELECT
        p.portfolio_id,
        p.portfolio_name,
        p.initial_capital,
        p.current_cash,
        p.status,
        p.created_at
    FROM portfolios p
    WHERE p.user_id = p_user_id
    ORDER BY p.created_at DESC;
END $$

DELIMITER ;


-- 2. Get market data for a security
DELIMITER $$

CREATE PROCEDURE sp_get_market_data(
    IN p_security_id BIGINT,
    IN p_start_date DATETIME,
    IN p_end_date DATETIME
)
BEGIN
    SELECT
        m.market_data_id,
        s.symbol,
        m.timestamp,
        m.open_price,
        m.high_price,
        m.low_price,
        m.close_price,
        m.volume,
        m.bid_price,
        m.ask_price
    FROM market_data m
    JOIN securities s
        ON m.security_id = s.security_id
    WHERE m.security_id = p_security_id
      AND m.timestamp BETWEEN p_start_date AND p_end_date
    ORDER BY m.timestamp;
END $$

DELIMITER ;


-- 3. Get orders of a user
DELIMITER $$

CREATE PROCEDURE sp_get_user_orders(IN p_user_id BIGINT)
BEGIN
    SELECT
        o.order_id,
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
    WHERE o.user_id = p_user_id
    ORDER BY o.order_time DESC;
END $$

DELIMITER ;


-- 4. Get trades for a security
DELIMITER $$

CREATE PROCEDURE sp_get_security_trades(IN p_security_id BIGINT)
BEGIN
    SELECT
        t.trade_id,
        t.order_id,
        s.symbol,
        t.trade_side,
        t.quantity,
        t.execution_price,
        t.transaction_cost,
        t.trade_time
    FROM trades t
    JOIN securities s
        ON t.security_id = s.security_id
    WHERE t.security_id = p_security_id
    ORDER BY t.trade_time DESC;
END $$

DELIMITER ;


-- 5. Get strategies created by a user
DELIMITER $$

CREATE PROCEDURE sp_get_user_strategies(IN p_user_id BIGINT)
BEGIN
    SELECT
        strategy_id,
        strategy_name,
        strategy_type,
        description,
        parameters,
        status,
        created_at
    FROM strategies
    WHERE user_id = p_user_id
    ORDER BY created_at DESC;
END $$

DELIMITER ;


-- 6. Get backtest performance
DELIMITER $$

CREATE PROCEDURE sp_get_backtest_performance(IN p_backtest_id BIGINT)
BEGIN
    SELECT
        b.backtest_id,
        st.strategy_name,
        s.symbol,
        b.start_date,
        b.end_date,
        b.initial_capital,
        b.status,
        br.total_return,
        br.total_pnl,
        br.volatility,
        br.sharpe_ratio,
        br.max_drawdown,
        br.total_trades,
        br.winning_trades,
        br.losing_trades,
        br.win_rate
    FROM backtests b
    JOIN strategies st
        ON b.strategy_id = st.strategy_id
    JOIN securities s
        ON b.security_id = s.security_id
    LEFT JOIN backtest_results br
        ON b.backtest_id = br.backtest_id
    WHERE b.backtest_id = p_backtest_id;
END $$

DELIMITER ;