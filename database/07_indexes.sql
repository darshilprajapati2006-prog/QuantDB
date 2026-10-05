USE QuantDB;

-- 07_indexes.sql
-- QuantDB Database Indexes

-- Users
CREATE INDEX idx_users_role
ON users(role);

CREATE INDEX idx_users_status
ON users(status);


-- Securities
CREATE INDEX idx_securities_symbol
ON securities(symbol);

CREATE INDEX idx_securities_type
ON securities(security_type);


-- Market Data
CREATE INDEX idx_market_data_security_time
ON market_data(security_id, timestamp);

CREATE INDEX idx_market_data_timestamp
ON market_data(timestamp);


-- Orders
CREATE INDEX idx_orders_user
ON orders(user_id);

CREATE INDEX idx_orders_security
ON orders(security_id);

CREATE INDEX idx_orders_status
ON orders(order_status);

CREATE INDEX idx_orders_time
ON orders(order_time);


-- Trades
CREATE INDEX idx_trades_order
ON trades(order_id);

CREATE INDEX idx_trades_security
ON trades(security_id);

CREATE INDEX idx_trades_time
ON trades(trade_time);


-- Portfolios
CREATE INDEX idx_portfolios_user
ON portfolios(user_id);

CREATE INDEX idx_portfolios_status
ON portfolios(status);


-- Positions
CREATE INDEX idx_positions_security
ON positions(security_id);


-- Strategies
CREATE INDEX idx_strategies_user
ON strategies(user_id);

CREATE INDEX idx_strategies_type
ON strategies(strategy_type);

CREATE INDEX idx_strategies_status
ON strategies(status);


-- Backtests
CREATE INDEX idx_backtests_strategy
ON backtests(strategy_id);

CREATE INDEX idx_backtests_security
ON backtests(security_id);

CREATE INDEX idx_backtests_status
ON backtests(status);

CREATE INDEX idx_backtests_dates
ON backtests(start_date, end_date);


-- Backtest Results
CREATE INDEX idx_backtest_results_backtest
ON backtest_results(backtest_id);


-- Risk Metrics
CREATE INDEX idx_risk_metrics_portfolio_date
ON risk_metrics(portfolio_id, metric_date);

CREATE INDEX idx_risk_metrics_backtest_date
ON risk_metrics(backtest_id, metric_date);