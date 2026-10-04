# QuantDB — Relational Schema

**Project Name:** QuantDB  
**Full Name:** A Database-Driven Market Data and Algorithmic Trading Research Platform  
**Version:** 1.0  
**Document Status:** Finalized Initial Relational Schema

---

## 1. Purpose

This document defines the relational database schema for the QuantDB project.

The schema converts the conceptual entities and relationships of the QuantDB system into relational tables with:

- Primary keys
- Foreign keys
- Unique constraints
- Not-null constraints
- Check constraints
- Appropriate data types
- Relationship mappings
- Referential integrity rules

The schema is designed for MySQL 8.x and follows relational database design principles and normalization requirements.

The database supports market data management, simulated trading, portfolio management, quantitative strategies, backtesting, risk analysis, and performance evaluation.

---

# 2. Database Overview

The QuantDB database contains the following core relations:

1. `users`
2. `exchanges`
3. `securities`
4. `market_data`
5. `orders`
6. `trades`
7. `portfolios`
8. `positions`
9. `strategies`
10. `backtests`
11. `backtest_results`
12. `risk_metrics`

---

# 3. Relational Schema

## 3.1 USERS

### Relation

```text
USERS(
    user_id PK,
    name,
    email UNIQUE,
    password_hash,
    role,
    status,
    created_at
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| user_id | BIGINT | PK, AUTO_INCREMENT | Unique user identifier |
| name | VARCHAR(100) | NOT NULL | User's full name |
| email | VARCHAR(150) | NOT NULL, UNIQUE | User email address |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password |
| role | ENUM | NOT NULL | ADMIN, QUANT_RESEARCHER, SIMULATED_TRADER |
| status | ENUM | NOT NULL | ACTIVE, INACTIVE, SUSPENDED |
| created_at | DATETIME | NOT NULL | Account creation timestamp |

### Primary Key

```text
PK: user_id
```

### Unique Constraint

```text
UNIQUE: email
```

---

# 3.2 EXCHANGES

### Relation

```text
EXCHANGES(
    exchange_id PK,
    exchange_name,
    exchange_code UNIQUE,
    country,
    timezone
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| exchange_id | BIGINT | PK, AUTO_INCREMENT | Unique exchange identifier |
| exchange_name | VARCHAR(100) | NOT NULL | Name of exchange |
| exchange_code | VARCHAR(20) | NOT NULL, UNIQUE | Exchange code |
| country | VARCHAR(80) | NOT NULL | Country of exchange |
| timezone | VARCHAR(50) | NOT NULL | Exchange timezone |

### Primary Key

```text
PK: exchange_id
```

### Unique Constraint

```text
UNIQUE: exchange_code
```

---

# 3.3 SECURITIES

### Relation

```text
SECURITIES(
    security_id PK,
    exchange_id FK,
    symbol,
    security_name,
    security_type,
    currency,
    status,
    UNIQUE(exchange_id, symbol)
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| security_id | BIGINT | PK, AUTO_INCREMENT | Unique security identifier |
| exchange_id | BIGINT | FK, NOT NULL | Exchange on which security is listed |
| symbol | VARCHAR(30) | NOT NULL | Trading symbol |
| security_name | VARCHAR(150) | NOT NULL | Security name |
| security_type | ENUM | NOT NULL | EQUITY, ETF, INDEX, FUTURE, OPTION |
| currency | CHAR(3) | NOT NULL | Trading currency |
| status | ENUM | NOT NULL | ACTIVE, INACTIVE |
| — | — | UNIQUE | `(exchange_id, symbol)` |

### Primary Key

```text
PK: security_id
```

### Foreign Key

```text
FK: exchange_id → exchanges.exchange_id
```

### Unique Constraint

```text
UNIQUE(exchange_id, symbol)
```

This allows the same symbol to exist on different exchanges while preventing duplicate symbols within the same exchange.

---

# 3.4 MARKET_DATA

### Relation

```text
MARKET_DATA(
    market_data_id PK,
    security_id FK,
    timestamp,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    bid_price,
    ask_price,
    UNIQUE(security_id, timestamp)
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| market_data_id | BIGINT | PK, AUTO_INCREMENT | Unique market data record |
| security_id | BIGINT | FK, NOT NULL | Associated security |
| timestamp | DATETIME | NOT NULL | Market data timestamp |
| open_price | DECIMAL(18,6) | NOT NULL | Opening price |
| high_price | DECIMAL(18,6) | NOT NULL | Highest price |
| low_price | DECIMAL(18,6) | NOT NULL | Lowest price |
| close_price | DECIMAL(18,6) | NOT NULL | Closing price |
| volume | BIGINT | NOT NULL | Traded volume |
| bid_price | DECIMAL(18,6) | NULL | Best bid price |
| ask_price | DECIMAL(18,6) | NULL | Best ask price |
| — | — | UNIQUE | `(security_id, timestamp)` |

### Primary Key

```text
PK: market_data_id
```

### Foreign Key

```text
FK: security_id → securities.security_id
```

### Unique Constraint

```text
UNIQUE(security_id, timestamp)
```

This prevents duplicate market-data records for the same security and timestamp.

---

# 3.5 ORDERS

> The physical table is named `orders` instead of `order` because `ORDER` is a SQL keyword.

### Relation

```text
ORDERS(
    order_id PK,
    user_id FK,
    security_id FK,
    order_type,
    side,
    quantity,
    order_price,
    order_status,
    order_time
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| order_id | BIGINT | PK, AUTO_INCREMENT | Unique order identifier |
| user_id | BIGINT | FK, NOT NULL | User placing the simulated order |
| security_id | BIGINT | FK, NOT NULL | Security being traded |
| order_type | ENUM | NOT NULL | MARKET, LIMIT |
| side | ENUM | NOT NULL | BUY, SELL |
| quantity | DECIMAL(18,6) | NOT NULL | Requested quantity |
| order_price | DECIMAL(18,6) | NULL | Limit/order price |
| order_status | ENUM | NOT NULL | PENDING, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED |
| order_time | DATETIME | NOT NULL | Time at which order was placed |

### Primary Key

```text
PK: order_id
```

### Foreign Keys

```text
FK: user_id → users.user_id

FK: security_id → securities.security_id
```

### Business Rules

```text
quantity > 0
```

For a LIMIT order:

```text
order_price > 0
```

For a MARKET order:

```text
order_price may be NULL
```

---

# 3.6 TRADES

### Relation

```text
TRADES(
    trade_id PK,
    order_id FK,
    security_id FK,
    trade_side,
    quantity,
    execution_price,
    trade_time,
    transaction_cost
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| trade_id | BIGINT | PK, AUTO_INCREMENT | Unique trade identifier |
| order_id | BIGINT | FK, NOT NULL | Source order |
| security_id | BIGINT | FK, NOT NULL | Traded security |
| trade_side | ENUM | NOT NULL | BUY, SELL |
| quantity | DECIMAL(18,6) | NOT NULL | Executed quantity |
| execution_price | DECIMAL(18,6) | NOT NULL | Actual execution price |
| trade_time | DATETIME | NOT NULL | Execution timestamp |
| transaction_cost | DECIMAL(18,6) | NOT NULL | Transaction cost |

### Primary Key

```text
PK: trade_id
```

### Foreign Keys

```text
FK: order_id → orders.order_id

FK: security_id → securities.security_id
```

### Business Rules

```text
quantity > 0
execution_price > 0
transaction_cost >= 0
```

An order may generate multiple trades to support partial fills.

---

# 3.7 PORTFOLIOS

### Relation

```text
PORTFOLIOS(
    portfolio_id PK,
    user_id FK,
    portfolio_name,
    initial_capital,
    current_cash,
    created_at,
    status
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| portfolio_id | BIGINT | PK, AUTO_INCREMENT | Unique portfolio identifier |
| user_id | BIGINT | FK, NOT NULL | Owner of portfolio |
| portfolio_name | VARCHAR(100) | NOT NULL | Portfolio name |
| initial_capital | DECIMAL(18,6) | NOT NULL | Initial capital |
| current_cash | DECIMAL(18,6) | NOT NULL | Current available cash |
| created_at | DATETIME | NOT NULL | Portfolio creation timestamp |
| status | ENUM | NOT NULL | ACTIVE, CLOSED |

### Primary Key

```text
PK: portfolio_id
```

### Foreign Key

```text
FK: user_id → users.user_id
```

### Business Rules

```text
initial_capital >= 0
current_cash >= 0
```

---

# 3.8 POSITIONS

### Relation

```text
POSITIONS(
    position_id PK,
    portfolio_id FK,
    security_id FK,
    quantity,
    average_price,
    realized_pnl,
    unrealized_pnl,
    updated_at,
    UNIQUE(portfolio_id, security_id)
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| position_id | BIGINT | PK, AUTO_INCREMENT | Unique position identifier |
| portfolio_id | BIGINT | FK, NOT NULL | Portfolio holding the position |
| security_id | BIGINT | FK, NOT NULL | Security held |
| quantity | DECIMAL(18,6) | NOT NULL | Current quantity |
| average_price | DECIMAL(18,6) | NOT NULL | Average acquisition price |
| realized_pnl | DECIMAL(18,6) | NOT NULL | Realized profit/loss |
| unrealized_pnl | DECIMAL(18,6) | NOT NULL | Unrealized profit/loss |
| updated_at | DATETIME | NOT NULL | Last update timestamp |
| — | — | UNIQUE | `(portfolio_id, security_id)` |

### Primary Key

```text
PK: position_id
```

### Foreign Keys

```text
FK: portfolio_id → portfolios.portfolio_id

FK: security_id → securities.security_id
```

### Unique Constraint

```text
UNIQUE(portfolio_id, security_id)
```

A portfolio can have at most one current position record for a particular security.

---

# 3.9 STRATEGIES

### Relation

```text
STRATEGIES(
    strategy_id PK,
    user_id FK,
    strategy_name,
    description,
    strategy_type,
    parameters,
    status,
    created_at
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| strategy_id | BIGINT | PK, AUTO_INCREMENT | Unique strategy identifier |
| user_id | BIGINT | FK, NOT NULL | Strategy owner/creator |
| strategy_name | VARCHAR(100) | NOT NULL | Strategy name |
| description | TEXT | NULL | Strategy description |
| strategy_type | VARCHAR(50) | NOT NULL | Type of quantitative strategy |
| parameters | JSON | NULL | Strategy parameters |
| status | ENUM | NOT NULL | ACTIVE, INACTIVE, ARCHIVED |
| created_at | DATETIME | NOT NULL | Strategy creation timestamp |

### Primary Key

```text
PK: strategy_id
```

### Foreign Key

```text
FK: user_id → users.user_id
```

The `parameters` attribute stores configurable strategy parameters in JSON format.

---

# 3.10 BACKTESTS

### Relation

```text
BACKTESTS(
    backtest_id PK,
    strategy_id FK,
    security_id FK,
    start_date,
    end_date,
    initial_capital,
    created_at,
    status
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| backtest_id | BIGINT | PK, AUTO_INCREMENT | Unique backtest identifier |
| strategy_id | BIGINT | FK, NOT NULL | Strategy being tested |
| security_id | BIGINT | FK, NOT NULL | Security used for backtesting |
| start_date | DATE | NOT NULL | Backtest start date |
| end_date | DATE | NOT NULL | Backtest end date |
| initial_capital | DECIMAL(18,6) | NOT NULL | Starting capital |
| created_at | DATETIME | NOT NULL | Backtest creation timestamp |
| status | ENUM | NOT NULL | PENDING, RUNNING, COMPLETED, FAILED |

### Primary Key

```text
PK: backtest_id
```

### Foreign Keys

```text
FK: strategy_id → strategies.strategy_id

FK: security_id → securities.security_id
```

### Business Rules

```text
start_date <= end_date
initial_capital > 0
```

---

# 3.11 BACKTEST_RESULTS

### Relation

```text
BACKTEST_RESULTS(
    result_id PK,
    backtest_id FK UNIQUE,
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
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| result_id | BIGINT | PK, AUTO_INCREMENT | Unique result identifier |
| backtest_id | BIGINT | FK, NOT NULL, UNIQUE | Associated backtest |
| total_return | DECIMAL(18,8) | NOT NULL | Total strategy return |
| total_pnl | DECIMAL(18,6) | NOT NULL | Total profit/loss |
| volatility | DECIMAL(18,8) | NOT NULL | Return volatility |
| sharpe_ratio | DECIMAL(18,8) | NULL | Sharpe ratio |
| max_drawdown | DECIMAL(18,8) | NOT NULL | Maximum drawdown |
| total_trades | INT | NOT NULL | Number of trades |
| winning_trades | INT | NOT NULL | Number of profitable trades |
| losing_trades | INT | NOT NULL | Number of losing trades |
| win_rate | DECIMAL(8,4) | NOT NULL | Percentage of winning trades |

### Primary Key

```text
PK: result_id
```

### Foreign Key

```text
FK: backtest_id → backtests.backtest_id
```

### Unique Constraint

```text
UNIQUE(backtest_id)
```

This establishes a one-to-one relationship between a completed backtest and its summarized result.

---

# 3.12 RISK_METRICS

### Relation

```text
RISK_METRICS(
    metric_id PK,
    portfolio_id FK NULL,
    backtest_id FK NULL,
    metric_date,
    return_value,
    volatility,
    sharpe_ratio,
    max_drawdown,
    calculated_at
)
```

### Attributes

| Attribute | Data Type | Constraints | Description |
|---|---|---|---|
| metric_id | BIGINT | PK, AUTO_INCREMENT | Unique metric identifier |
| portfolio_id | BIGINT | FK, NULL | Portfolio associated with metric |
| backtest_id | BIGINT | FK, NULL | Backtest associated with metric |
| metric_date | DATE | NOT NULL | Date of metric calculation |
| return_value | DECIMAL(18,8) | NOT NULL | Return value |
| volatility | DECIMAL(18,8) | NOT NULL | Volatility |
| sharpe_ratio | DECIMAL(18,8) | NULL | Sharpe ratio |
| max_drawdown | DECIMAL(18,8) | NOT NULL | Maximum drawdown |
| calculated_at | DATETIME | NOT NULL | Calculation timestamp |

### Primary Key

```text
PK: metric_id
```

### Foreign Keys

```text
FK: portfolio_id → portfolios.portfolio_id

FK: backtest_id → backtests.backtest_id
```

### Business Rule

Exactly one of the following should normally identify the source of the metric:

```text
portfolio_id IS NOT NULL
OR
backtest_id IS NOT NULL
```

The database implementation should enforce this using an appropriate CHECK constraint.

---

# 4. Relationship Mapping

The major relationships between relations are:

```text
EXCHANGES
    |
    | 1 : M
    v
SECURITIES
    |
    | 1 : M
    v
MARKET_DATA
```

```text
USERS
    |
    | 1 : M
    v
ORDERS
    |
    | 1 : M
    v
TRADES
```

```text
USERS
    |
    | 1 : M
    v
PORTFOLIOS
    |
    | 1 : M
    v
POSITIONS
    |
    | M : 1
    v
SECURITIES
```

```text
USERS
    |
    | 1 : M
    v
STRATEGIES
    |
    | 1 : M
    v
BACKTESTS
    |
    | 1 : 1
    v
BACKTEST_RESULTS
```

```text
PORTFOLIOS ────────> RISK_METRICS
                       ^
                       |
BACKTESTS ────────────┘
```

---

# 5. Cardinality Summary

| Parent Relation | Child Relation | Cardinality |
|---|---|---|
| USERS | PORTFOLIOS | 1 : M |
| USERS | ORDERS | 1 : M |
| USERS | STRATEGIES | 1 : M |
| EXCHANGES | SECURITIES | 1 : M |
| SECURITIES | MARKET_DATA | 1 : M |
| SECURITIES | ORDERS | 1 : M |
| ORDERS | TRADES | 1 : M |
| SECURITIES | TRADES | 1 : M |
| PORTFOLIOS | POSITIONS | 1 : M |
| SECURITIES | POSITIONS | 1 : M |
| STRATEGIES | BACKTESTS | 1 : M |
| SECURITIES | BACKTESTS | 1 : M |
| BACKTESTS | BACKTEST_RESULTS | 1 : 1 |
| PORTFOLIOS | RISK_METRICS | 1 : M |
| BACKTESTS | RISK_METRICS | 1 : M |

---

# 6. Referential Integrity

Foreign key relationships shall maintain referential integrity.

The following references are required:

```text
securities.exchange_id
        → exchanges.exchange_id

market_data.security_id
        → securities.security_id

orders.user_id
        → users.user_id

orders.security_id
        → securities.security_id

trades.order_id
        → orders.order_id

trades.security_id
        → securities.security_id

portfolios.user_id
        → users.user_id

positions.portfolio_id
        → portfolios.portfolio_id

positions.security_id
        → securities.security_id

strategies.user_id
        → users.user_id

backtests.strategy_id
        → strategies.strategy_id

backtests.security_id
        → securities.security_id

backtest_results.backtest_id
        → backtests.backtest_id

risk_metrics.portfolio_id
        → portfolios.portfolio_id

risk_metrics.backtest_id
        → backtests.backtest_id
```

---

# 7. Integrity Constraints

The implementation should enforce the following important constraints.

### User

```text
email must be unique
role must be valid
status must be valid
```

### Security

```text
exchange_id must reference an existing exchange
(exchange_id, symbol) must be unique
```

### Market Data

```text
security_id must reference an existing security
(security_id, timestamp) must be unique
high_price >= low_price
open_price > 0
high_price > 0
low_price > 0
close_price > 0
volume >= 0
bid_price >= 0 when present
ask_price >= 0 when present
```

### Orders

```text
quantity > 0
order_price > 0 when present
side must be BUY or SELL
order_type must be MARKET or LIMIT
order_status must be valid
```

### Trades

```text
quantity > 0
execution_price > 0
transaction_cost >= 0
trade_side must be BUY or SELL
```

### Portfolios

```text
initial_capital >= 0
current_cash >= 0
```

### Positions

```text
average_price >= 0
```

### Backtests

```text
start_date <= end_date
initial_capital > 0
```

### Backtest Results

```text
total_trades >= 0
winning_trades >= 0
losing_trades >= 0
0 <= win_rate <= 100
```

### Risk Metrics

```text
At least one of portfolio_id or backtest_id must be non-null.
```

---

# 8. Normalization Target

The relational schema is designed to satisfy the requirements of normalized relational database design.

The target normalization level is:

```text
1NF → 2NF → 3NF
```

BCNF should be applied where practical and where it does not unnecessarily complicate the system.

The schema avoids unnecessary repeating groups, partial dependencies, and transitive dependencies.

Detailed normalization analysis will be documented separately in:

```text
docs/normalization.md
```

---

# 9. Naming Conventions

The following naming conventions shall be followed throughout the project:

### Tables

Use lowercase plural nouns:

```text
users
exchanges
securities
market_data
orders
trades
portfolios
positions
strategies
backtests
backtest_results
risk_metrics
```

### Primary Keys

Use:

```text
<table_singular>_id
```

Examples:

```text
user_id
security_id
portfolio_id
backtest_id
```

### Foreign Keys

Foreign keys use the same identifier as the referenced primary key.

Example:

```text
orders.user_id → users.user_id
```

### Timestamps

Use:

```text
created_at
updated_at
calculated_at
order_time
trade_time
timestamp
```

---

# 10. Database Design Principle

The database is designed around the following core flow:

```text
USER
 |
 +----> PORTFOLIO
 |          |
 |          +----> POSITION
 |
 +----> ORDERS
 |          |
 |          +----> TRADES
 |
 +----> STRATEGIES
              |
              +----> BACKTESTS
                         |
                         +----> BACKTEST_RESULTS
                         |
                         +----> RISK_METRICS

EXCHANGE
    |
    +----> SECURITY
               |
               +----> MARKET_DATA
               |
               +----> ORDERS
               |
               +----> TRADES
               |
               +----> POSITIONS
               |
               +----> BACKTESTS
```

---

# 11. Implementation Dependency Order

The MySQL tables should be created in dependency order.

Recommended order:

```text
1. users
2. exchanges
3. securities
4. market_data
5. orders
6. trades
7. portfolios
8. positions
9. strategies
10. backtests
11. backtest_results
12. risk_metrics
```

This order minimizes foreign-key dependency problems during database creation.

---

# 12. Application Architecture Mapping

The relational schema connects to the application architecture as follows:

```text
                Streamlit UI
                    |
                    v
             Python Application
                    |
          +---------+---------+
          |                   |
          v                   v
      MySQL DB          Quant Analytics
                              |
                              v
                         Backtesting
```

The database is the central source of persistent application data.

Python is responsible for:

- Database communication
- Data processing
- Quantitative calculations
- Backtesting
- Portfolio calculations
- Risk calculations
- Market microstructure calculations

Streamlit is responsible for:

- User interface
- Dashboard
- Market data display
- Simulated trading interface
- Portfolio visualization
- Strategy management
- Backtest execution interface
- Reports

---

# 13. Scope of the Schema

This schema supports:

- User management
- Exchange management
- Security management
- Historical market data
- Simulated orders
- Simulated trade execution
- Portfolio management
- Position tracking
- Strategy management
- Historical backtesting
- Quantitative performance analysis
- Risk analysis
- Market microstructure analysis
- Database reporting
- Query optimization
- Transaction management

The system is intended for academic, research, and simulation purposes.

It does **not** execute real-money financial transactions.

---

# 14. Schema Change Policy

Any change to:

- table names
- column names
- primary keys
- foreign keys
- relationships
- data types
- major constraints
- business rules

must be discussed with the complete team before implementation.

The `project_contract.md` and this relational schema should remain aligned.

If a schema change is approved:

1. Update this document first.
2. Update the ER diagram.
3. Update normalization documentation if required.
4. Update MySQL SQL scripts.
5. Update backend repository/query code.
6. Update quant/backtesting code if affected.
7. Update frontend components if affected.
8. Run integration tests.
9. Commit the change with an appropriate Git message.
10. Merge only after team review.

---

# 15. Final Schema Summary

```text
USERS
 ├── PORTFOLIOS
 │    └── POSITIONS
 │
 ├── ORDERS
 │    └── TRADES
 │
 └── STRATEGIES
      └── BACKTESTS
           └── BACKTEST_RESULTS

EXCHANGES
 └── SECURITIES
      ├── MARKET_DATA
      ├── ORDERS
      ├── TRADES
      ├── POSITIONS
      └── BACKTESTS

PORTFOLIOS
 └── RISK_METRICS

BACKTESTS
 └── RISK_METRICS
```

This relational schema is the baseline database design for the QuantDB project and should be used as the reference for database implementation, backend development, quantitative analysis, backtesting, frontend integration, testing, and project documentation.