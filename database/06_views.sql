USE QuantDB;

-- ============================================
-- 06_views.sql
-- QuantDB Database Views
-- ============================================

-- 1. Security and Exchange Information
CREATE OR REPLACE VIEW vw_security_exchange AS
SELECT
    s.security_id,
    s.symbol,
    s.security_name,
    s.security_type,
    s.currency,
    s.status AS security_status,
    e.exchange_name,
    e.exchange_code,
    e.country,
    e.timezone
FROM securities s
JOIN exchanges e
    ON s.exchange_id = e.exchange_id;


-- 2. Portfolio Summary
CREATE OR REPLACE VIEW vw_portfolio_summary AS
SELECT
    p.portfolio_id,
    p.portfolio_name,
    u.user_id,
    u.name AS owner_name,
    u.email,
    p.initial_capital,
    p.current_cash,
    (p.initial_capital - p.current_cash) AS invested_amount,
    p.status,
    p.created_at
FROM portfolios p
JOIN users u
    ON p.user_id = u.user_id;


-- 3. Portfolio Positions
CREATE OR REPLACE VIEW vw_portfolio_positions AS
SELECT
    p.portfolio_id,
    p.portfolio_name,
    u.name AS owner_name,
    s.symbol,
    s.security_name,
    pos.quantity,
    pos.average_price,
    pos.realized_pnl,
    pos.unrealized_pnl,
    pos.updated_at
FROM positions pos
JOIN portfolios p
    ON pos.portfolio_id = p.portfolio_id
JOIN users u
    ON p.user_id = u.user_id
JOIN securities s
    ON pos.security_id = s.security_id;


-- 4. Order Details
CREATE OR REPLACE VIEW vw_order_details AS
SELECT
    o.order_id,
    u.name AS user_name,
    s.symbol,
    s.security_name,
    o.order_type,
    o.side,
    o.quantity,
    o.order_price,
    o.order_status,
    o.order_time
FROM orders o
JOIN users u
    ON o.user_id = u.user_id
JOIN securities s
    ON o.security_id = s.security_id;


-- 5. Trade Details
CREATE OR REPLACE VIEW vw_trade_details AS
SELECT
    t.trade_id,
    t.order_id,
    s.symbol,
    s.security_name,
    t.trade_side,
    t.quantity,
    t.execution_price,
    t.transaction_cost,
    t.trade_time
FROM trades t
JOIN securities s
    ON t.security_id = s.security_id;


-- 6. Strategy Details
CREATE OR REPLACE VIEW vw_strategy_details AS
SELECT
    st.strategy_id,
    u.name AS owner_name,
    st.strategy_name,
    st.strategy_type,
    st.description,
    st.parameters,
    st.status,
    st.created_at
FROM strategies st
JOIN users u
    ON st.user_id = u.user_id;


-- 7. Backtest Performance
CREATE OR REPLACE VIEW vw_backtest_performance AS
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
    ON b.backtest_id = br.backtest_id;


-- 8. Latest Market Data
CREATE OR REPLACE VIEW vw_latest_market_data AS
SELECT
    s.security_id,
    s.symbol,
    s.security_name,
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
WHERE m.timestamp = (
    SELECT MAX(m2.timestamp)
    FROM market_data m2
    WHERE m2.security_id = m.security_id
);


-- 9. Risk Metrics
CREATE OR REPLACE VIEW vw_risk_metrics AS
SELECT
    rm.metric_id,
    rm.metric_date,
    rm.return_value,
    rm.volatility,
    rm.sharpe_ratio,
    rm.max_drawdown,
    rm.calculated_at,
    p.portfolio_name,
    b.backtest_id
FROM risk_metrics rm
LEFT JOIN portfolios p
    ON rm.portfolio_id = p.portfolio_id
LEFT JOIN backtests b
    ON rm.backtest_id = b.backtest_id;