USE QuantDB;

-- 09_functions.sql
-- QuantDB Stored Functions

-- 1. Calculate invested amount of a portfolio
DELIMITER $$

CREATE FUNCTION fn_portfolio_invested_amount(
    p_portfolio_id BIGINT
)
RETURNS DECIMAL(18,6)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_invested_amount DECIMAL(18,6);

    SELECT (initial_capital - current_cash)
    INTO v_invested_amount
    FROM portfolios
    WHERE portfolio_id = p_portfolio_id;

    RETURN COALESCE(v_invested_amount, 0);
END $$

DELIMITER ;


-- 2. Calculate position value
DELIMITER $$

CREATE FUNCTION fn_position_value(
    p_position_id BIGINT
)
RETURNS DECIMAL(18,6)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_position_value DECIMAL(18,6);

    SELECT (quantity * average_price)
    INTO v_position_value
    FROM positions
    WHERE position_id = p_position_id;

    RETURN COALESCE(v_position_value, 0);
END $$

DELIMITER ;


-- 3. Calculate win rate
DELIMITER $$

CREATE FUNCTION fn_win_rate(
    p_winning_trades INT,
    p_total_trades INT
)
RETURNS DECIMAL(8,4)
DETERMINISTIC
BEGIN
    IF p_total_trades <= 0 THEN
        RETURN 0;
    END IF;

    RETURN (p_winning_trades / p_total_trades) * 100;
END $$

DELIMITER ;


-- 4. Calculate backtest profit percentage
DELIMITER $$

CREATE FUNCTION fn_backtest_profit_percentage(
    p_backtest_id BIGINT
)
RETURNS DECIMAL(18,8)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_profit_percentage DECIMAL(18,8);

    SELECT
        (br.total_pnl / b.initial_capital) * 100
    INTO v_profit_percentage
    FROM backtests b
    JOIN backtest_results br
        ON b.backtest_id = br.backtest_id
    WHERE b.backtest_id = p_backtest_id;

    RETURN COALESCE(v_profit_percentage, 0);
END $$

DELIMITER ;


-- 5. Calculate total quantity held in a portfolio
DELIMITER $$

CREATE FUNCTION fn_portfolio_total_quantity(
    p_portfolio_id BIGINT
)
RETURNS DECIMAL(18,6)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_total_quantity DECIMAL(18,6);

    SELECT SUM(quantity)
    INTO v_total_quantity
    FROM positions
    WHERE portfolio_id = p_portfolio_id;

    RETURN COALESCE(v_total_quantity, 0);
END $$

DELIMITER ;