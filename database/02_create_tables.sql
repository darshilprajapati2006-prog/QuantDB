
USE QuantDB;

-- 1. USERS

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT AUTO_INCREMENT,
    username VARCHAR(50) NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM(
        'USER',
        'QUANT_TRADER',
        'QUANT_RESEARCHER',
        'ADMIN',
        'SIMULATED_TRADER'
    ) NOT NULL,
    status ENUM(
        'ACTIVE',
        'INACTIVE',
        'SUSPENDED'
    ) NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,

    PRIMARY KEY (user_id),
    UNIQUE (email),
    UNIQUE (username)
);


-- 2. EXCHANGES

CREATE TABLE IF NOT EXISTS exchanges (
    exchange_id BIGINT AUTO_INCREMENT,
    exchange_name VARCHAR(100) NOT NULL,
    exchange_code VARCHAR(20) NOT NULL,
    country VARCHAR(80) NOT NULL,
    timezone VARCHAR(50) NOT NULL,

    PRIMARY KEY (exchange_id),
    UNIQUE (exchange_code)
);


-- 3. SECURITIES

CREATE TABLE IF NOT EXISTS securities (
    security_id BIGINT AUTO_INCREMENT,
    exchange_id BIGINT NOT NULL,
    symbol VARCHAR(30) NOT NULL,
    security_name VARCHAR(150) NOT NULL,
    security_type ENUM(
        'EQUITY',
        'ETF',
        'INDEX',
        'FUTURE',
        'OPTION'
    ) NOT NULL,
    currency CHAR(3) NOT NULL,
    status ENUM(
        'ACTIVE',
        'INACTIVE'
    ) NOT NULL,

    PRIMARY KEY (security_id),
    UNIQUE (exchange_id, symbol)
);


-- 4. MARKET_DATA

CREATE TABLE IF NOT EXISTS market_data (
    market_data_id BIGINT AUTO_INCREMENT,
    security_id BIGINT NOT NULL,
    timestamp DATETIME NOT NULL,
    open_price DECIMAL(18,6) NOT NULL,
    high_price DECIMAL(18,6) NOT NULL,
    low_price DECIMAL(18,6) NOT NULL,
    close_price DECIMAL(18,6) NOT NULL,
    volume BIGINT NOT NULL,
    bid_price DECIMAL(18,6) NULL,
    ask_price DECIMAL(18,6) NULL,

    PRIMARY KEY (market_data_id),
    UNIQUE (security_id, timestamp)
);


-- 5. ORDERS

CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    security_id BIGINT NOT NULL,
    order_type ENUM(
        'MARKET',
        'LIMIT'
    ) NOT NULL,
    side ENUM(
        'BUY',
        'SELL'
    ) NOT NULL,
    quantity DECIMAL(18,6) NOT NULL,
    order_price DECIMAL(18,6) NULL,
    order_status ENUM(
        'PENDING',
        'PARTIALLY_FILLED',
        'FILLED',
        'CANCELLED',
        'REJECTED'
    ) NOT NULL,
    order_time DATETIME NOT NULL,

    PRIMARY KEY (order_id)
);


-- 6. TRADES

CREATE TABLE IF NOT EXISTS trades (
    trade_id BIGINT AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    security_id BIGINT NOT NULL,
    trade_side ENUM(
        'BUY',
        'SELL'
    ) NOT NULL,
    quantity DECIMAL(18,6) NOT NULL,
    execution_price DECIMAL(18,6) NOT NULL,
    trade_time DATETIME NOT NULL,
    transaction_cost DECIMAL(18,6) NOT NULL,

    PRIMARY KEY (trade_id)
);


-- 7. PORTFOLIOS

CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    portfolio_name VARCHAR(100) NOT NULL,
    initial_capital DECIMAL(18,6) NOT NULL,
    current_cash DECIMAL(18,6) NOT NULL,
    created_at DATETIME NOT NULL,
    status ENUM(
        'ACTIVE',
        'CLOSED'
    ) NOT NULL,

    PRIMARY KEY (portfolio_id)
);


-- 8. POSITIONS

CREATE TABLE IF NOT EXISTS positions (
    position_id BIGINT AUTO_INCREMENT,
    portfolio_id BIGINT NOT NULL,
    security_id BIGINT NOT NULL,
    quantity DECIMAL(18,6) NOT NULL,
    average_price DECIMAL(18,6) NOT NULL,
    realized_pnl DECIMAL(18,6) NOT NULL,
    unrealized_pnl DECIMAL(18,6) NOT NULL,
    updated_at DATETIME NOT NULL,

    PRIMARY KEY (position_id),
    UNIQUE (portfolio_id, security_id)
);


-- 9. STRATEGIES

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    parameters JSON NULL,
    status ENUM(
        'ACTIVE',
        'INACTIVE',
        'ARCHIVED'
    ) NOT NULL,
    created_at DATETIME NOT NULL,

    PRIMARY KEY (strategy_id)
);


-- 10. BACKTESTS

CREATE TABLE IF NOT EXISTS backtests (
    backtest_id BIGINT AUTO_INCREMENT,
    strategy_id BIGINT NOT NULL,
    security_id BIGINT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(18,6) NOT NULL,
    created_at DATETIME NOT NULL,
    status ENUM(
        'PENDING',
        'RUNNING',
        'COMPLETED',
        'FAILED'
    ) NOT NULL,

    PRIMARY KEY (backtest_id)
);


-- 11. BACKTEST_RESULTS

CREATE TABLE IF NOT EXISTS backtest_results (
    result_id BIGINT AUTO_INCREMENT,
    backtest_id BIGINT NOT NULL,
    total_return DECIMAL(18,8) NOT NULL,
    total_pnl DECIMAL(18,6) NOT NULL,
    volatility DECIMAL(18,8) NOT NULL,
    sharpe_ratio DECIMAL(18,8) NULL,
    max_drawdown DECIMAL(18,8) NOT NULL,
    total_trades INT NOT NULL,
    winning_trades INT NOT NULL,
    losing_trades INT NOT NULL,
    win_rate DECIMAL(8,4) NOT NULL,

    PRIMARY KEY (result_id),
    UNIQUE (backtest_id)
);


-- 12. RISK_METRICS

CREATE TABLE IF NOT EXISTS risk_metrics (
    metric_id BIGINT AUTO_INCREMENT,
    portfolio_id BIGINT NULL,
    backtest_id BIGINT NULL,
    metric_date DATE NOT NULL,
    return_value DECIMAL(18,8) NOT NULL,
    volatility DECIMAL(18,8) NOT NULL,
    sharpe_ratio DECIMAL(18,8) NULL,
    max_drawdown DECIMAL(18,8) NOT NULL,
    calculated_at DATETIME NOT NULL,

    PRIMARY KEY (metric_id)
);


-- 13. EMAIL_OTPS (AUTHENTICATION & VERIFICATION)

CREATE TABLE IF NOT EXISTS email_otps (
    otp_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    otp_hash VARCHAR(255) NOT NULL,
    purpose VARCHAR(30) NOT NULL DEFAULT 'REGISTRATION',
    expires_at DATETIME NOT NULL,
    attempt_count INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    verified_at DATETIME NULL,

    PRIMARY KEY (otp_id),
    CONSTRAINT fk_email_otps_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_email_otps_user_purpose (user_id, purpose, is_used),
    INDEX idx_email_otps_expires (expires_at)
);