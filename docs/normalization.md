# QuantDB — Database Normalization

**Project Name:** QuantDB  
**Full Name:** A Database-Driven Market Data and Algorithmic Trading Research Platform  
**Version:** 1.0  
**Document Status:** Initial Normalization Specification

---

## 1. Purpose

This document describes the normalization of the QuantDB relational database.

The main purpose of normalization is to organize data efficiently, reduce data redundancy, prevent update anomalies, and maintain data integrity.

The QuantDB database is designed to follow standard relational database normalization principles, primarily up to **Third Normal Form (3NF)**, with **BCNF** applied where appropriate.

---

## 2. Normalization Goals

The database normalization process aims to:

1. Reduce duplicate data.
2. Eliminate unnecessary data repetition.
3. Prevent insertion anomalies.
4. Prevent update anomalies.
5. Prevent deletion anomalies.
6. Maintain referential integrity.
7. Improve consistency of financial market data.
8. Create well-structured relational tables.
9. Ensure that non-key attributes depend on the appropriate key.
10. Support efficient SQL queries and future database optimization.

---

## 3. Functional Dependencies

The major functional dependencies in QuantDB are as follows.

### USER

```text
user_id → name, email, password_hash, role, status, created_at
```

`user_id` uniquely identifies each user.

---

### EXCHANGE

```text
exchange_id → exchange_name, exchange_code, country, timezone
```

`exchange_id` uniquely identifies an exchange.

Additionally:

```text
exchange_code → exchange_name, country, timezone
```

because `exchange_code` is unique.

---

### SECURITY

```text
security_id → exchange_id, symbol, security_name,
               security_type, currency, status
```

`security_id` uniquely identifies a security.

---

### MARKET_DATA

```text
market_data_id → security_id, timestamp,
                  open_price, high_price, low_price,
                  close_price, volume, bid_price, ask_price
```

The combination:

```text
(security_id, timestamp)
```

is also unique for a market-data record.

---

### ORDERS

```text
order_id → user_id, security_id, order_type,
            side, quantity, order_price,
            order_status, order_time
```

`order_id` uniquely identifies an order.

---

### TRADE

```text
trade_id → order_id, security_id, trade_side,
            quantity, execution_price,
            trade_time, transaction_cost
```

`trade_id` uniquely identifies a trade.

---

### PORTFOLIO

```text
portfolio_id → user_id, portfolio_name,
                initial_capital, current_cash,
                created_at, status
```

`portfolio_id` uniquely identifies a portfolio.

---

### POSITION

```text
position_id → portfolio_id, security_id,
               quantity, average_price,
               realized_pnl, unrealized_pnl,
               updated_at
```

The combination:

```text
(portfolio_id, security_id)
```

is also unique.

---

### STRATEGY

```text
strategy_id → user_id, strategy_name,
               description, strategy_type,
               parameters, status, created_at
```

`strategy_id` uniquely identifies a trading strategy.

---

### BACKTEST

```text
backtest_id → strategy_id, security_id,
               start_date, end_date,
               initial_capital, created_at, status
```

`backtest_id` uniquely identifies a backtest execution.

---

### BACKTEST_RESULT

```text
result_id → backtest_id, total_return,
             total_pnl, volatility,
             sharpe_ratio, max_drawdown,
             total_trades, winning_trades,
             losing_trades, win_rate
```

`result_id` uniquely identifies a backtest result.

---

### RISK_METRIC

```text
metric_id → portfolio_id, backtest_id,
             metric_date, return_value,
             volatility, sharpe_ratio,
             max_drawdown, calculated_at
```

`metric_id` uniquely identifies a risk-metric record.

---

# 4. First Normal Form (1NF)

A relation is in **First Normal Form (1NF)** when:

- Each column contains atomic values.
- There are no repeating groups.
- Each row is uniquely identifiable.
- Each attribute contains a single value for a particular record.

QuantDB tables follow 1NF by storing atomic values in individual columns.

### Example

The `SECURITY` table stores:

```text
security_id
exchange_id
symbol
security_name
security_type
currency
status
```

Each attribute contains a single atomic value.

Similarly, `MARKET_DATA` stores individual price and volume values:

```text
open_price
high_price
low_price
close_price
volume
bid_price
ask_price
```

Instead of storing multiple prices or securities inside a single field, each value is stored separately.

Therefore:

```text
SECURITY ∈ 1NF
MARKET_DATA ∈ 1NF
ORDERS ∈ 1NF
TRADE ∈ 1NF
PORTFOLIO ∈ 1NF
POSITION ∈ 1NF
STRATEGY ∈ 1NF
BACKTEST ∈ 1NF
```

and similarly for the remaining relations.

---

# 5. Second Normal Form (2NF)

A relation is in **Second Normal Form (2NF)** when:

1. It is already in 1NF.
2. Every non-key attribute is fully dependent on the entire candidate key.
3. There are no partial dependencies.

Most QuantDB tables use a single-column primary key such as:

```text
user_id
exchange_id
security_id
order_id
trade_id
portfolio_id
strategy_id
backtest_id
result_id
metric_id
```

Since these tables have single-attribute primary keys, partial dependency cannot occur.

---

## 5.1 Composite Uniqueness in MARKET_DATA

The `MARKET_DATA` table contains:

```text
market_data_id
security_id
timestamp
open_price
high_price
low_price
close_price
volume
bid_price
ask_price
```

A business-level uniqueness constraint can be defined as:

```text
UNIQUE(security_id, timestamp)
```

This ensures that a security does not have multiple market-data records for the same timestamp.

The price-related attributes depend on the complete market-data record identified by:

```text
(security_id, timestamp)
```

Therefore, no partial dependency exists.

---

## 5.2 Composite Uniqueness in POSITION

The `POSITION` table contains:

```text
position_id
portfolio_id
security_id
quantity
average_price
realized_pnl
unrealized_pnl
updated_at
```

A portfolio should normally have one position record for a particular security.

Therefore:

```text
UNIQUE(portfolio_id, security_id)
```

is applied.

The position attributes depend on the complete portfolio-security combination.

Thus, the relation satisfies 2NF.

---

# 6. Third Normal Form (3NF)

A relation is in **Third Normal Form (3NF)** when:

1. It is already in 2NF.
2. No non-key attribute depends on another non-key attribute.
3. There are no transitive dependencies.

QuantDB separates independent entities into their own relations to avoid transitive dependencies.

---

## 6.1 USER and PORTFOLIO

Instead of storing user information repeatedly inside every portfolio record, QuantDB stores users separately.

### USER

```text
USER(
    user_id PK,
    name,
    email,
    password_hash,
    role,
    status,
    created_at
)
```

### PORTFOLIO

```text
PORTFOLIO(
    portfolio_id PK,
    user_id FK,
    portfolio_name,
    initial_capital,
    current_cash,
    created_at,
    status
)
```

The portfolio stores only `user_id` as the reference to the user.

Therefore, user information is not duplicated across portfolio records.

---

## 6.2 EXCHANGE and SECURITY

Exchange information is separated from security information.

### EXCHANGE

```text
EXCHANGE(
    exchange_id PK,
    exchange_name,
    exchange_code UNIQUE,
    country,
    timezone
)
```

### SECURITY

```text
SECURITY(
    security_id PK,
    exchange_id FK,
    symbol,
    security_name,
    security_type,
    currency,
    status
)
```

The security table stores `exchange_id` rather than repeating:

```text
exchange_name
country
timezone
```

for every security.

This eliminates transitive and redundant data.

---

## 6.3 SECURITY and MARKET_DATA

Market data references the security using:

```text
security_id
```

The market-data table does not repeatedly store:

```text
symbol
security_name
exchange_name
```

Instead:

```text
MARKET_DATA → SECURITY → EXCHANGE
```

This avoids unnecessary duplication.

---

## 6.4 USER and ORDERS

Order records reference users using:

```text
user_id
```

The order table does not repeat:

```text
name
email
role
```

for every order.

Therefore, user-related information remains centralized in the `USER` table.

---

## 6.5 STRATEGY and BACKTEST

Strategies are stored separately from backtest executions.

### STRATEGY

```text
STRATEGY(
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

### BACKTEST

```text
BACKTEST(
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

A strategy can therefore be reused for multiple backtests without duplicating strategy information.

---

# 7. BCNF Consideration

**Boyce-Codd Normal Form (BCNF)** is a stronger version of 3NF.

A relation is in BCNF when every determinant is a candidate key.

QuantDB is designed so that major relations satisfy BCNF where practical.

Examples include:

```text
USER
EXCHANGE
SECURITY
ORDERS
TRADE
PORTFOLIO
STRATEGY
BACKTEST
BACKTEST_RESULT
```

Unique constraints such as:

```text
USER.email
EXCHANGE.exchange_code
```

also represent candidate-key-like business identifiers.

The database design avoids storing attributes that introduce unnecessary functional dependencies between non-key attributes.

---

# 8. Example of an Unnormalized Design

Consider an initial hypothetical trading table:

```text
TRADING_RECORD(
    order_id,
    user_name,
    user_email,
    exchange_name,
    symbol,
    security_name,
    order_type,
    quantity,
    order_price,
    trade_price,
    portfolio_name
)
```

This design creates significant redundancy.

For example, the same user information may be repeated for every order.

Similarly, exchange and security information may be repeated for every transaction.

---

# 9. Problems with the Unnormalized Design

### 9.1 Update Anomaly

If a user's email changes, multiple rows may need to be updated.

If one row is not updated, inconsistent data can occur.

---

### 9.2 Insertion Anomaly

A new security may not be insertable unless an order also exists.

This incorrectly couples independent entities.

---

### 9.3 Deletion Anomaly

Deleting the last order of a security could unintentionally remove the only stored information about that security.

---

### 9.4 Data Redundancy

The same exchange, user, and security information may appear repeatedly.

This increases storage requirements and the possibility of inconsistent data.

---

# 10. Normalized QuantDB Design

The normalized design separates independent entities:

```text
USER
  |
  +---- ORDER
  |
  +---- PORTFOLIO
  |
  +---- STRATEGY

EXCHANGE
  |
  +---- SECURITY
          |
          +---- MARKET_DATA
          |
          +---- ORDER
          |
          +---- TRADE
          |
          +---- POSITION

STRATEGY
  |
  +---- BACKTEST
          |
          +---- BACKTEST_RESULT

PORTFOLIO
  |
  +---- POSITION
  |
  +---- RISK_METRIC
```

This decomposition reduces redundancy while maintaining relationships through primary and foreign keys.

---

# 11. Normalization Summary

| Relation | 1NF | 2NF | 3NF | Main Reason |
|---|---|---|---|---|
| USER | Yes | Yes | Yes | User attributes depend on user_id |
| EXCHANGE | Yes | Yes | Yes | Exchange attributes depend on exchange_id |
| SECURITY | Yes | Yes | Yes | Security attributes depend on security_id |
| MARKET_DATA | Yes | Yes | Yes | Market values depend on security and timestamp |
| ORDERS | Yes | Yes | Yes | Order attributes depend on order_id |
| TRADE | Yes | Yes | Yes | Trade attributes depend on trade_id |
| PORTFOLIO | Yes | Yes | Yes | Portfolio attributes depend on portfolio_id |
| POSITION | Yes | Yes | Yes | Position attributes depend on portfolio/security |
| STRATEGY | Yes | Yes | Yes | Strategy attributes depend on strategy_id |
| BACKTEST | Yes | Yes | Yes | Backtest attributes depend on backtest_id |
| BACKTEST_RESULT | Yes | Yes | Yes | Result attributes depend on result_id |
| RISK_METRIC | Yes | Yes | Yes | Metric attributes depend on metric_id |

---

# 12. Integrity After Normalization

Normalization is supported by database integrity constraints.

### Primary Keys

Each entity has a unique primary key.

Examples:

```text
user_id
security_id
order_id
trade_id
portfolio_id
strategy_id
backtest_id
```

### Foreign Keys

Relationships are maintained through foreign keys.

Examples:

```text
SECURITY.exchange_id → EXCHANGE.exchange_id

MARKET_DATA.security_id → SECURITY.security_id

ORDERS.user_id → USER.user_id

ORDERS.security_id → SECURITY.security_id

TRADE.order_id → ORDERS.order_id

PORTFOLIO.user_id → USER.user_id

POSITION.portfolio_id → PORTFOLIO.portfolio_id

POSITION.security_id → SECURITY.security_id

STRATEGY.user_id → USER.user_id

BACKTEST.strategy_id → STRATEGY.strategy_id

BACKTEST.security_id → SECURITY.security_id

BACKTEST_RESULT.backtest_id → BACKTEST.backtest_id
```

---

# 13. Conclusion

The QuantDB relational database is designed using normalization principles to achieve a structured, consistent, and maintainable database architecture.

The design:

- follows 1NF by maintaining atomic attributes;
- follows 2NF by eliminating partial dependencies;
- follows 3NF by eliminating unnecessary transitive dependencies;
- applies BCNF principles where appropriate;
- reduces redundancy;
- prevents common insertion, update, and deletion anomalies;
- maintains referential integrity through primary and foreign keys;
- provides a strong foundation for SQL operations, transactions, analytics, and future database optimization.

The normalized design will be used as the basis for the MySQL database implementation of QuantDB.