-- File: 04_insert_master_data.sql

USE QuantDB;

-- 1. USERS

INSERT INTO users
    (name, email, password_hash, role, status, created_at)
VALUES
    ('Aarav Sharma', 'aarav@quantdb.com', 'hash_aarav_123',
     'ADMIN', 'ACTIVE', '2026-01-05 10:00:00'),

    ('Riya Patel', 'riya@quantdb.com', 'hash_riya_123',
     'QUANT_RESEARCHER', 'ACTIVE', '2026-01-08 11:30:00'),

    ('Karan Mehta', 'karan@quantdb.com', 'hash_karan_123',
     'QUANT_RESEARCHER', 'ACTIVE', '2026-01-10 09:45:00'),

    ('Neha Shah', 'neha@quantdb.com', 'hash_neha_123',
     'SIMULATED_TRADER', 'ACTIVE', '2026-01-12 14:20:00'),

    ('Arjun Verma', 'arjun@quantdb.com', 'hash_arjun_123',
     'SIMULATED_TRADER', 'ACTIVE', '2026-01-15 16:10:00'),

    ('Priya Singh', 'priya@quantdb.com', 'hash_priya_123',
     'QUANT_RESEARCHER', 'INACTIVE', '2026-02-01 12:00:00');


-- 2. EXCHANGES

INSERT INTO exchanges
    (exchange_name, exchange_code, country, timezone)
VALUES
    ('National Stock Exchange of India', 'NSE', 'India', 'Asia/Kolkata'),

    ('BSE Limited', 'BSE', 'India', 'Asia/Kolkata'),

    ('NASDAQ Stock Market', 'NASDAQ', 'United States', 'America/New_York'),

    ('New York Stock Exchange', 'NYSE', 'United States', 'America/New_York');


-- 3. SECURITIES

INSERT INTO securities
    (exchange_id, symbol, security_name, security_type, currency, status)
VALUES
    (1, 'RELIANCE', 'Reliance Industries Limited', 'EQUITY', 'INR', 'ACTIVE'),

    (1, 'TCS', 'Tata Consultancy Services Limited', 'EQUITY', 'INR', 'ACTIVE'),

    (1, 'INFY', 'Infosys Limited', 'EQUITY', 'INR', 'ACTIVE'),

    (1, 'HDFCBANK', 'HDFC Bank Limited', 'EQUITY', 'INR', 'ACTIVE'),

    (2, 'ITC', 'ITC Limited', 'EQUITY', 'INR', 'ACTIVE'),

    (2, 'SBIN', 'State Bank of India', 'EQUITY', 'INR', 'ACTIVE'),

    (3, 'AAPL', 'Apple Inc.', 'EQUITY', 'USD', 'ACTIVE'),

    (3, 'MSFT', 'Microsoft Corporation', 'EQUITY', 'USD', 'ACTIVE'),

    (3, 'NVDA', 'NVIDIA Corporation', 'EQUITY', 'USD', 'ACTIVE'),

    (4, 'JPM', 'JPMorgan Chase & Co.', 'EQUITY', 'USD', 'ACTIVE');


-- 4. PORTFOLIOS

INSERT INTO portfolios
    (user_id, portfolio_name, initial_capital, current_cash,
     created_at, status)
VALUES
    (2, 'Riya Growth Portfolio', 1000000.00, 750000.00,
     '2026-02-05 10:00:00', 'ACTIVE'),

    (3, 'Karan Quant Portfolio', 1500000.00, 1200000.00,
     '2026-02-07 11:15:00', 'ACTIVE'),

    (4, 'Neha Trading Portfolio', 500000.00, 350000.00,
     '2026-02-10 09:30:00', 'ACTIVE'),

    (5, 'Arjun Momentum Portfolio', 750000.00, 500000.00,
     '2026-02-12 13:45:00', 'ACTIVE'),

    (2, 'Riya Experimental Portfolio', 300000.00, 300000.00,
     '2026-03-01 15:00:00', 'ACTIVE');


-- 5. STRATEGIES


INSERT INTO strategies
    (user_id, strategy_name, description, strategy_type,
     parameters, status, created_at)
VALUES
    (
        2,
        'Moving Average Crossover',
        'Uses short-term and long-term moving average crossover signals.',
        'TREND_FOLLOWING',
        '{"short_window":20,"long_window":50}',
        'ACTIVE',
        '2026-02-15 10:00:00'
    ),

    (
        3,
        'Mean Reversion',
        'Identifies securities that move significantly away from their average price.',
        'MEAN_REVERSION',
        '{"lookback":20,"entry_zscore":2.0,"exit_zscore":0.5}',
        'ACTIVE',
        '2026-02-16 11:30:00'
    ),

    (
        4,
        'Momentum Strategy',
        'Selects securities showing strong recent price momentum.',
        'MOMENTUM',
        '{"lookback_days":60,"top_n":10}',
        'ACTIVE',
        '2026-02-18 09:15:00'
    ),

    (
        5,
        'RSI Reversal',
        'Uses RSI levels to identify potential reversal opportunities.',
        'TECHNICAL',
        '{"rsi_period":14,"oversold":30,"overbought":70}',
        'ACTIVE',
        '2026-02-20 14:00:00'
    ),

    (
        3,
        'Volatility Breakout',
        'Attempts to capture price movements following volatility expansion.',
        'BREAKOUT',
        '{"atr_period":14,"multiplier":2.0}',
        'ACTIVE',
        '2026-02-22 12:30:00'
    ),

    (
        2,
        'Value Strategy',
        'Selects fundamentally attractive securities using valuation metrics.',
        'VALUE',
        '{"pe_threshold":25,"pb_threshold":4}',
        'INACTIVE',
        '2026-03-01 10:45:00'
    );