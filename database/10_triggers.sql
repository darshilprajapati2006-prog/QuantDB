USE QuantDB;

-- 10_triggers.sql
-- QuantDB Database Triggers


-- 1. Automatically update portfolio cash after a BUY trade
DELIMITER $$

CREATE TRIGGER trg_after_buy_trade
AFTER INSERT ON trades
FOR EACH ROW
BEGIN
    IF NEW.trade_side = 'BUY' THEN
        UPDATE portfolios p
        JOIN orders o
            ON p.user_id = o.user_id
        SET p.current_cash =
            p.current_cash - (NEW.quantity * NEW.execution_price)
        WHERE o.order_id = NEW.order_id;
    END IF;
END $$

DELIMITER ;


-- 2. Automatically update portfolio cash after a SELL trade
DELIMITER $$

CREATE TRIGGER trg_after_sell_trade
AFTER INSERT ON trades
FOR EACH ROW
BEGIN
    IF NEW.trade_side = 'SELL' THEN
        UPDATE portfolios p
        JOIN orders o
            ON p.user_id = o.user_id
        SET p.current_cash =
            p.current_cash + (NEW.quantity * NEW.execution_price)
        WHERE o.order_id = NEW.order_id;
    END IF;
END $$

DELIMITER ;


-- 3. Automatically update order status when a trade is inserted
DELIMITER $$

CREATE TRIGGER trg_after_trade_order_status
AFTER INSERT ON trades
FOR EACH ROW
BEGIN
    UPDATE orders
    SET order_status = 'FILLED'
    WHERE order_id = NEW.order_id;
END $$

DELIMITER ;


-- 4. Prevent negative portfolio cash
DELIMITER $$

CREATE TRIGGER trg_before_portfolio_update
BEFORE UPDATE ON portfolios
FOR EACH ROW
BEGIN
    IF NEW.current_cash < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Portfolio cash cannot be negative';
    END IF;
END $$

DELIMITER ;


-- 5. Prevent invalid market data prices
DELIMITER $$

CREATE TRIGGER trg_before_market_data_insert
BEFORE INSERT ON market_data
FOR EACH ROW
BEGIN
    IF NEW.high_price < NEW.low_price THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'High price cannot be lower than low price';
    END IF;

    IF NEW.open_price <= 0 OR NEW.close_price <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Market prices must be greater than zero';
    END IF;
END $$

DELIMITER ;