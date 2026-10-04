USE QuantDB;

-- 11_transactions.sql
-- QuantDB Transaction Management


-- 1. Transfer cash between two portfolios
DELIMITER $$

CREATE PROCEDURE sp_transfer_portfolio_cash(
    IN p_from_portfolio BIGINT,
    IN p_to_portfolio BIGINT,
    IN p_amount DECIMAL(18,6)
)
BEGIN
    DECLARE v_from_cash DECIMAL(18,6);

    START TRANSACTION;

    SELECT current_cash
    INTO v_from_cash
    FROM portfolios
    WHERE portfolio_id = p_from_portfolio
    FOR UPDATE;

    IF v_from_cash IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Source portfolio does not exist';

    ELSEIF p_amount <= 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Transfer amount must be greater than zero';

    ELSEIF v_from_cash < p_amount THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient portfolio cash';

    ELSE
        UPDATE portfolios
        SET current_cash = current_cash - p_amount
        WHERE portfolio_id = p_from_portfolio;

        UPDATE portfolios
        SET current_cash = current_cash + p_amount
        WHERE portfolio_id = p_to_portfolio;

        COMMIT;
    END IF;
END $$

DELIMITER ;


-- 2. Create an order using a transaction
DELIMITER $$

CREATE PROCEDURE sp_create_order_transaction(
    IN p_user_id BIGINT,
    IN p_security_id BIGINT,
    IN p_order_type VARCHAR(10),
    IN p_side VARCHAR(10),
    IN p_quantity DECIMAL(18,6),
    IN p_order_price DECIMAL(18,6)
)
BEGIN
    START TRANSACTION;

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
    VALUES (
        p_user_id,
        p_security_id,
        p_order_type,
        p_side,
        p_quantity,
        p_order_price,
        'PENDING',
        NOW()
    );

    COMMIT;
END $$

DELIMITER ;


-- 3. Transaction example using SAVEPOINT
DELIMITER $$

CREATE PROCEDURE sp_update_portfolio_cash(
    IN p_portfolio_id BIGINT,
    IN p_new_cash DECIMAL(18,6)
)
BEGIN
    START TRANSACTION;

    SAVEPOINT before_cash_update;

    IF p_new_cash < 0 THEN
        ROLLBACK TO SAVEPOINT before_cash_update;

        ROLLBACK;

        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Portfolio cash cannot be negative';
    ELSE
        UPDATE portfolios
        SET current_cash = p_new_cash
        WHERE portfolio_id = p_portfolio_id;

        COMMIT;
    END IF;
END $$

DELIMITER ;