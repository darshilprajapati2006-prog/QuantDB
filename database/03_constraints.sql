
USE QuantDB;


-- FOREIGN KEY CONSTRAINTS

-- SECURITIES -> EXCHANGES
ALTER TABLE securities
ADD CONSTRAINT fk_securities_exchange
FOREIGN KEY (exchange_id)
REFERENCES exchanges(exchange_id);


-- MARKET_DATA -> SECURITIES
ALTER TABLE market_data
ADD CONSTRAINT fk_market_data_security
FOREIGN KEY (security_id)
REFERENCES securities(security_id);


-- ORDERS -> USERS
ALTER TABLE orders
ADD CONSTRAINT fk_orders_user
FOREIGN KEY (user_id)
REFERENCES users(user_id);


-- ORDERS -> SECURITIES
ALTER TABLE orders
ADD CONSTRAINT fk_orders_security
FOREIGN KEY (security_id)
REFERENCES securities(security_id);


-- TRADES -> ORDERS
ALTER TABLE trades
ADD CONSTRAINT fk_trades_order
FOREIGN KEY (order_id)
REFERENCES orders(order_id);


-- TRADES -> SECURITIES
ALTER TABLE trades
ADD CONSTRAINT fk_trades_security
FOREIGN KEY (security_id)
REFERENCES securities(security_id);


-- PORTFOLIOS -> USERS
ALTER TABLE portfolios
ADD CONSTRAINT fk_portfolios_user
FOREIGN KEY (user_id)
REFERENCES users(user_id);


-- POSITIONS -> PORTFOLIOS
ALTER TABLE positions
ADD CONSTRAINT fk_positions_portfolio
FOREIGN KEY (portfolio_id)
REFERENCES portfolios(portfolio_id);


-- POSITIONS -> SECURITIES
ALTER TABLE positions
ADD CONSTRAINT fk_positions_security
FOREIGN KEY (security_id)
REFERENCES securities(security_id);


-- STRATEGIES -> USERS
ALTER TABLE strategies
ADD CONSTRAINT fk_strategies_user
FOREIGN KEY (user_id)
REFERENCES users(user_id);


-- BACKTESTS -> STRATEGIES
ALTER TABLE backtests
ADD CONSTRAINT fk_backtests_strategy
FOREIGN KEY (strategy_id)
REFERENCES strategies(strategy_id);


-- BACKTESTS -> SECURITIES
ALTER TABLE backtests
ADD CONSTRAINT fk_backtests_security
FOREIGN KEY (security_id)
REFERENCES securities(security_id);


-- BACKTEST_RESULTS -> BACKTESTS
ALTER TABLE backtest_results
ADD CONSTRAINT fk_backtest_results_backtest
FOREIGN KEY (backtest_id)
REFERENCES backtests(backtest_id);


-- RISK_METRICS -> PORTFOLIOS
ALTER TABLE risk_metrics
ADD CONSTRAINT fk_risk_metrics_portfolio
FOREIGN KEY (portfolio_id)
REFERENCES portfolios(portfolio_id);


-- RISK_METRICS -> BACKTESTS
ALTER TABLE risk_metrics
ADD CONSTRAINT fk_risk_metrics_backtest
FOREIGN KEY (backtest_id)
REFERENCES backtests(backtest_id);


-- CHECK CONSTRAINTS

-- MARKET DATA
ALTER TABLE market_data
ADD CONSTRAINT chk_market_data_open_price
CHECK (open_price > 0);

ALTER TABLE market_data
ADD CONSTRAINT chk_market_data_high_price
CHECK (high_price > 0);

ALTER TABLE market_data
ADD CONSTRAINT chk_market_data_low_price
CHECK (low_price > 0);

ALTER TABLE market_data
ADD CONSTRAINT chk_market_data_close_price
CHECK (close_price > 0);

ALTER TABLE market_data
ADD CONSTRAINT chk_market_data_high_low
CHECK (high_price >= low_price);

ALTER TABLE market_data
ADD CONSTRAINT chk_market_data_volume
CHECK (volume >= 0);

ALTER TABLE market_data
ADD CONSTRAINT chk_market_data_bid_price
CHECK (bid_price IS NULL OR bid_price >= 0);

ALTER TABLE market_data
ADD CONSTRAINT chk_market_data_ask_price
CHECK (ask_price IS NULL OR ask_price >= 0);


-- ORDERS
ALTER TABLE orders
ADD CONSTRAINT chk_orders_quantity
CHECK (quantity > 0);

ALTER TABLE orders
ADD CONSTRAINT chk_orders_price
CHECK (
    order_price IS NULL
    OR order_price > 0
);

ALTER TABLE orders
ADD CONSTRAINT chk_orders_limit_price
CHECK (
    order_type = 'MARKET'
    OR (order_type = 'LIMIT' AND order_price > 0)
);


-- TRADES
ALTER TABLE trades
ADD CONSTRAINT chk_trades_quantity
CHECK (quantity > 0);

ALTER TABLE trades
ADD CONSTRAINT chk_trades_execution_price
CHECK (execution_price > 0);

ALTER TABLE trades
ADD CONSTRAINT chk_trades_transaction_cost
CHECK (transaction_cost >= 0);


-- PORTFOLIOS
ALTER TABLE portfolios
ADD CONSTRAINT chk_portfolios_initial_capital
CHECK (initial_capital >= 0);

ALTER TABLE portfolios
ADD CONSTRAINT chk_portfolios_current_cash
CHECK (current_cash >= 0);


-- POSITIONS
ALTER TABLE positions
ADD CONSTRAINT chk_positions_average_price
CHECK (average_price >= 0);


-- BACKTESTS
ALTER TABLE backtests
ADD CONSTRAINT chk_backtests_dates
CHECK (start_date <= end_date);

ALTER TABLE backtests
ADD CONSTRAINT chk_backtests_initial_capital
CHECK (initial_capital > 0);


-- BACKTEST RESULTS
ALTER TABLE backtest_results
ADD CONSTRAINT chk_backtest_results_total_trades
CHECK (total_trades >= 0);

ALTER TABLE backtest_results
ADD CONSTRAINT chk_backtest_results_winning_trades
CHECK (winning_trades >= 0);

ALTER TABLE backtest_results
ADD CONSTRAINT chk_backtest_results_losing_trades
CHECK (losing_trades >= 0);

ALTER TABLE backtest_results
ADD CONSTRAINT chk_backtest_results_win_rate
CHECK (win_rate >= 0 AND win_rate <= 100);


-- RISK METRICS
ALTER TABLE risk_metrics
ADD CONSTRAINT chk_risk_metrics_source
CHECK (
    (portfolio_id IS NOT NULL AND backtest_id IS NULL)
    OR
    (portfolio_id IS NULL AND backtest_id IS NOT NULL)
);