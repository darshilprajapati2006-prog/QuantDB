# QuantDB — Project Contract

**Project Name:** QuantDB  
**Full Name:** A Database-Driven Market Data and Algorithmic Trading Research Platform  
**Version:** 1.0  
**Status:** Initial Development Contract

---

## 1. Purpose of This Document

This document is the single source of truth for the QuantDB project.

All team members must follow the database schema, architecture, interfaces, naming conventions, data formats, development workflow, and integration rules defined in this document.

Any major change to this contract must be discussed and approved by the entire team before implementation.

---

# 2. Project Overview

QuantDB is a database-driven quantitative finance research and simulated trading platform.

The system provides a centralized relational database and application layer for managing:

- Users and roles
- Exchanges
- Securities
- Historical market data
- Simulated orders
- Simulated trades
- Portfolios
- Positions
- Quantitative strategies
- Backtests
- Performance metrics
- Risk metrics
- Basic market microstructure information

The platform is intended for **research, learning, analysis, and simulated/paper trading only**.

It does not execute real-money trades.

---

# 3. Main Objectives

The project must demonstrate:

1. ER modeling
2. Relational database design
3. Primary and foreign keys
4. Integrity constraints
5. Normalization
6. SQL CRUD operations
7. Joins
8. Aggregate queries
9. Subqueries
10. Views
11. Indexing
12. Query optimization using `EXPLAIN`
13. Stored procedures
14. Stored functions
15. Triggers
16. Transactions
17. Python–MySQL integration
18. Market-data processing
19. Quantitative analysis
20. Strategy backtesting
21. Portfolio and position management
22. Risk and performance analysis
23. Market microstructure analysis
24. Interactive Streamlit dashboard

---

# 4. System Architecture

The application follows a layered architecture:

```text
                    QuantDB
                       |
                       v
                 Streamlit UI
                       |
                       v
              Python Application
                       |
          +------------+------------+
          |                         |
          v                         v
   Backend/Data Layer       Quant/Analytics Layer
          |                         |
          +------------+------------+
                       |
                       v
                    MySQL
```

The major data flow is:

```text
User
  |
  v
Streamlit Dashboard
  |
  v
Python Application
  |
  +---- Backend/Data Services
  |
  +---- Quant/Backtesting Services
  |
  v
MySQL Database
```

The frontend must not directly implement database business logic.

---

# 5. Technology Stack

## Core Technologies

- MySQL 8.x
- MySQL Workbench
- Python 3.x
- Pandas
- NumPy
- mysql-connector-python
- Streamlit
- Git
- GitHub
- VS Code

## Supporting Libraries

The following may be used where required:

- Matplotlib
- SQLAlchemy
- SciPy
- pytest

Additional dependencies should not be introduced unnecessarily and should be discussed with the team if they affect the architecture.

---

# 6. Team Responsibilities

## Member 1 — Database Architect / DBMS Lead

Primary ownership:

```text
database/
```

Responsibilities:

- ER model
- Relational schema
- Normalization
- MySQL database
- Tables
- Primary keys
- Foreign keys
- Constraints
- Master data
- Sample data
- Views
- Indexes
- Stored procedures
- Stored functions
- Triggers
- Transactions
- Query optimization
- `EXPLAIN`
- Database testing

---

## Member 2 — Backend & Market Data Engineer

Primary ownership:

```text
src/database/
src/ingestion/
src/trading/
```

Responsibilities:

- Python–MySQL connection
- Database repository layer
- SQL/application queries
- CRUD services
- Market-data ingestion
- Data cleaning
- Data validation
- Order services
- Trade services
- Portfolio services
- Position services
- Error handling
- Logging
- Application-level transaction coordination

---

## Member 3 — Quant & Backtesting Engineer

Primary ownership:

```text
src/analytics/
src/backtesting/
```

Responsibilities:

- Return calculations
- Volatility
- Sharpe ratio
- Maximum drawdown
- P&L
- Performance analysis
- Risk analysis
- Bid-ask spread
- Market depth
- Order-book imbalance
- Strategy implementation
- Backtesting engine
- Simulated execution
- Strategy comparison

---

## Member 4 — Frontend & Reporting Engineer

Primary ownership:

```text
dashboard/
```

Responsibilities:

- Streamlit application
- Navigation
- Role-based UI
- Dashboard
- Market-data page
- Trading page
- Portfolio page
- Strategy page
- Backtesting page
- Risk dashboard
- Reports
- Tables
- Charts

---

# 7. Database Schema

The following entities constitute the approved core database schema.

Table names and core column names must not be changed without team approval.

---

## 7.1 USER

```text
USER
-------------------------
user_id          PK
name
email            UNIQUE
password_hash
role
status
created_at
```

Purpose:

Stores application users and their roles.

---

## 7.2 EXCHANGE

```text
EXCHANGE
-------------------------
exchange_id      PK
exchange_name
exchange_code    UNIQUE
country
timezone
```

Purpose:

Stores exchange/master information.

---

## 7.3 SECURITY

```text
SECURITY
-------------------------
security_id      PK
exchange_id      FK
symbol
security_name
security_type
currency
status
```

Purpose:

Stores securities/instruments traded or analyzed by the platform.

Relationship:

```text
EXCHANGE 1 ---- M SECURITY
```

---

## 7.4 MARKET_DATA

```text
MARKET_DATA
-------------------------
market_data_id   PK
security_id      FK
timestamp
open_price
high_price
low_price
close_price
volume
bid_price
ask_price
```

Purpose:

Stores historical market observations.

Recommended integrity rule:

```text
UNIQUE(security_id, timestamp)
```

Relationship:

```text
SECURITY 1 ---- M MARKET_DATA
```

---

## 7.5 ORDERS

The physical MySQL table should be named `orders`.

```text
ORDERS
-------------------------
order_id         PK
user_id          FK
security_id      FK
order_type
side
quantity
order_price
order_status
order_time
```

Purpose:

Stores simulated buy/sell orders.

Allowed conceptual values:

```text
side:
BUY
SELL
```

Relationship:

```text
USER 1 ---- M ORDERS
SECURITY 1 ---- M ORDERS
```

---

## 7.6 TRADE

```text
TRADE
-------------------------
trade_id         PK
order_id         FK
security_id      FK
trade_side
quantity
execution_price
trade_time
transaction_cost
```

Purpose:

Stores simulated executions generated from orders.

Relationships:

```text
ORDERS 1 ---- M TRADE
SECURITY 1 ---- M TRADE
```

The exact execution cardinality may be constrained further during implementation depending on the simulated execution model.

---

## 7.7 PORTFOLIO

```text
PORTFOLIO
-------------------------
portfolio_id     PK
user_id          FK
portfolio_name
initial_capital
current_cash
created_at
status
```

Purpose:

Stores user portfolios used for simulated trading and analysis.

Relationship:

```text
USER 1 ---- M PORTFOLIO
```

---

## 7.8 POSITION

```text
POSITION
-------------------------
position_id      PK
portfolio_id     FK
security_id      FK
quantity
average_price
realized_pnl
unrealized_pnl
updated_at
```

Purpose:

Stores current holdings of securities inside portfolios.

Relationships:

```text
PORTFOLIO 1 ---- M POSITION
SECURITY 1 ---- M POSITION
```

Recommended integrity rule:

```text
UNIQUE(portfolio_id, security_id)
```

---

## 7.9 STRATEGY

```text
STRATEGY
-------------------------
strategy_id      PK
user_id          FK
strategy_name
description
strategy_type
parameters
status
created_at
```

Purpose:

Stores quantitative trading/research strategies.

Relationship:

```text
USER 1 ---- M STRATEGY
```

---

## 7.10 BACKTEST

```text
BACKTEST
-------------------------
backtest_id      PK
strategy_id      FK
security_id      FK
start_date
end_date
initial_capital
created_at
status
```

Purpose:

Stores backtesting configurations/runs.

Relationships:

```text
STRATEGY 1 ---- M BACKTEST
SECURITY 1 ---- M BACKTEST
```

---

## 7.11 BACKTEST_RESULT

```text
BACKTEST_RESULT
-------------------------
result_id        PK
backtest_id      FK
total_return
total_pnl
volatility
sharpe_ratio
max_drawdown
total_trades
winning_trades
losing_trades
win_rate
```

Purpose:

Stores calculated performance results for backtests.

Primary relationship:

```text
BACKTEST 1 ---- 1 BACKTEST_RESULT
```

The exact cardinality may be expanded to 1:M later if multiple result snapshots are required.

---

## 7.12 RISK_METRIC

```text
RISK_METRIC
-------------------------
metric_id        PK
portfolio_id     FK nullable
backtest_id      FK nullable
metric_date
return_value
volatility
sharpe_ratio
max_drawdown
calculated_at
```

Purpose:

Stores risk and performance metrics associated with portfolios and/or backtests.

A metric record should reference the appropriate portfolio or backtest according to the implemented design.

---

# 8. Core Relationships

The approved conceptual relationship model is:

```text
EXCHANGE
   |
   | 1:M
   v
SECURITY
   |
   | 1:M
   v
MARKET_DATA
```

Trading:

```text
USER
 |
 | 1:M
 v
ORDERS
 |
 | 1:M
 v
TRADE
 |
 v
POSITION
 |
 v
PORTFOLIO
```

Portfolio ownership:

```text
USER
 |
 | 1:M
 v
PORTFOLIO
 |
 | 1:M
 v
POSITION
 ^
 |
 | M:1
 |
SECURITY
```

Strategy/backtesting:

```text
USER
 |
 | 1:M
 v
STRATEGY
 |
 | 1:M
 v
BACKTEST
 |
 | 1:1
 v
BACKTEST_RESULT
```

Backtests also reference:

```text
SECURITY
```

Risk analysis:

```text
PORTFOLIO ─────┐
               ├──> RISK_METRIC
BACKTEST ──────┘
```

---

# 9. Database Naming Convention

Use:

- lowercase or consistent snake_case for SQL identifiers
- singular logical entity names where appropriate
- clear primary-key names
- clear foreign-key names

Examples:

```text
user_id
security_id
portfolio_id
backtest_id
```

Avoid unclear names such as:

```text
id1
data
temp
x
abc
```

The physical SQL table `orders` is used instead of `order` because `ORDER` is a SQL keyword.

---

# 10. Data Conventions

## Market Data

Market data follows:

```text
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

## Orders

Orders follow:

```text
order_id
user_id
security_id
order_type
side
quantity
order_price
order_status
order_time
```

## Backtest Results

Results follow:

```text
backtest_id
total_return
total_pnl
volatility
sharpe_ratio
max_drawdown
total_trades
winning_trades
losing_trades
win_rate
```

All modules must use these agreed field names when exchanging data.

---

# 11. Backend Interface Contract

The backend layer should expose reusable application functions/services.

Expected interfaces include:

```text
get_security_list()
get_market_data()
get_historical_prices()
get_user_orders()
create_order()
get_trades()
get_portfolio()
get_positions()
get_strategies()
get_backtest_results()
```

Interfaces should use clear parameters and return predictable data structures.

Example:

```text
get_market_data(
    security_id,
    start_date,
    end_date
)
```

The frontend must use backend services instead of directly embedding database logic.

---

# 12. Quant Interface Contract

The quantitative layer should provide reusable functions such as:

```text
calculate_returns()
calculate_volatility()
calculate_sharpe_ratio()
calculate_max_drawdown()
calculate_pnl()
calculate_microstructure_metrics()
run_backtest()
compare_strategies()
```

Example:

```text
run_backtest(
    strategy_id,
    security_id,
    start_date,
    end_date,
    initial_capital
)
```

The mathematical implementation remains inside the quant layer.

The frontend should consume the resulting metrics rather than reimplementing formulas.

---

# 13. Quantitative Metrics

The platform will support at least:

### Returns

Measure strategy/portfolio performance over time.

### Volatility

Measure variability of returns.

### Sharpe Ratio

Risk-adjusted return measure.

### Maximum Drawdown

Largest peak-to-trough decline.

### P&L

Profit and loss from simulated trading/backtesting.

### Bid-Ask Spread

Conceptually:

```text
ask_price - bid_price
```

### Market Depth

Measure available simulated/recorded liquidity at price levels where data supports it.

### Order-Book Imbalance

Measure the relative imbalance between bid and ask quantities where order-book quantity data is available.

---

# 14. Trading Flow

The simulated trading workflow is:

```text
User
  |
  v
Place Simulated Order
  |
  v
Validate Order
  |
  v
Begin Transaction
  |
  v
Create/Update Order
  |
  v
Simulate Execution
  |
  v
Create Trade
  |
  v
Update Position
  |
  v
Update Portfolio
  |
  v
Update P&L
  |
  v
Commit Transaction
```

If a critical operation fails:

```text
ROLLBACK
```

No real-money order execution is performed.

---

# 15. Backtesting Flow

The backtesting workflow is:

```text
Select Strategy
       |
       v
Select Security
       |
       v
Select Historical Period
       |
       v
Load Historical Market Data
       |
       v
Generate Strategy Signals
       |
       v
Simulate Orders/Trades
       |
       v
Calculate Portfolio Value
       |
       v
Calculate P&L
       |
       v
Calculate Performance Metrics
       |
       v
Store BACKTEST_RESULT
       |
       v
Display Results
```

---

# 16. Frontend Expectations

The Streamlit dashboard should provide appropriate pages for:

```text
Admin
Market Data
Trading
Portfolio
Strategies
Backtesting
Reports
```

The UI should provide appropriate role-based access for:

### Admin

- User management
- Exchange management
- Security/master-data management
- System reports

### Quant Researcher

- Historical market data
- Strategy management
- Backtesting
- Performance analysis
- Risk analysis
- Microstructure analysis

### Simulated Trader

- Market data
- Simulated orders
- Trades
- Positions
- Portfolio
- Simulated P&L

---

# 17. Role Definitions

## Admin

Responsible for system/master-data management.

## Quant Researcher

Responsible for quantitative research, strategies, backtesting, and analysis.

## Simulated Trader

Responsible for paper/simulated trading and portfolio monitoring.

No role is allowed to perform real-money trading through this application.

---

# 18. Development Branch Strategy

The repository uses:

```text
main
develop
database
backend
quant
frontend
```

Purpose:

### main

Stable, tested, integrated project.

No direct development.

### develop

Integration and system-testing branch.

### database

Primary development branch for Member 1.

### backend

Primary development branch for Member 2.

### quant

Primary development branch for Member 3.

### frontend

Primary development branch for Member 4.

---

# 19. Feature Branch Strategy

For larger tasks, use feature branches.

Examples:

```text
feature/database-schema
feature/market-data-loader
feature/trading-service
feature/backtesting-engine
feature/risk-analysis
feature/streamlit-dashboard
```

Recommended flow:

```text
feature branch
      |
      v
role branch
      |
      v
develop
      |
      v
main
```

---

# 20. Git Rules

Never directly develop on:

```text
main
```

Before starting work:

```bash
git switch <your-branch>
git pull origin <your-branch>
```

After completing a task:

```bash
git status
git add .
git commit -m "meaningful message"
git push origin <your-branch>
```

Use meaningful commit prefixes:

```text
feat:
fix:
db:
ui:
docs:
test:
refactor:
chore:
```

Examples:

```text
db: create security and exchange tables
feat: implement market data loader
feat: add sharpe ratio calculation
ui: add portfolio dashboard
test: add backtesting tests
docs: update relational schema
```

---

# 21. Pull Request Rules

A completed feature should not be blindly merged.

Process:

```text
Development
    |
    v
Local Testing
    |
    v
Commit
    |
    v
Push
    |
    v
Pull Request
    |
    v
Review
    |
    v
Merge
```

Before merging into `develop`, verify that the feature does not break existing modules.

Before merging `develop` into `main`, perform complete integration testing.

---

# 22. File Ownership

Primary ownership:

```text
Member 1
→ database/

Member 2
→ src/database/
→ src/ingestion/
→ src/trading/

Member 3
→ src/analytics/
→ src/backtesting/

Member 4
→ dashboard/
```

All members may read other modules.

Members should avoid modifying another member's primary module without coordination.

---

# 23. Shared Documentation

Important documentation belongs inside:

```text
docs/
```

Expected documents:

```text
problem_statement.md
objectives.md
requirements.md
er_diagram.md
relational_schema.md
normalization.md
database_implementation.md
project_report.md
project_contract.md
```

The contract document must be updated whenever an approved architectural change occurs.

---

# 24. Sample Data

Shared development/sample data belongs in:

```text
data/sample/
```

The team should use consistent sample data structures.

Market-data sample records should follow the approved market-data fields.

Quant calculations and frontend development may initially use sample/mock data so that team members can work in parallel.

---

# 25. Parallel Development Principle

Team members must not wait for the entire project to be completed before starting their work.

Parallel development is encouraged.

Example:

```text
Member 1
Actual MySQL schema
       |
       |
Member 2
Schema-compatible backend
       |
       |
Member 3
Sample-data quant engine
       |
       |
Member 4
Mock-data Streamlit UI
```

Later these modules are integrated.

---

# 26. Single Source of Truth

The following are considered authoritative:

### Database structure

```text
database/
```

### Project architecture

```text
docs/project_contract.md
```

### Shared data format

Defined in this contract.

### Application interfaces

Defined in this contract and corresponding backend/quant documentation.

No member should create duplicate schemas, duplicate market-data structures, or incompatible interfaces.

---

# 27. Change Control

If a member wants to change:

- table name
- column name
- primary key
- foreign key
- relationship
- data type
- backend interface
- quant interface
- major dependency
- application architecture

the member must first discuss the change with the team.

The process is:

```text
Proposed Change
      |
      v
Impact Analysis
      |
      v
Team Discussion
      |
      v
Approval
      |
      v
Update Contract
      |
      v
Implementation
      |
      v
Testing
```

Do not silently change shared interfaces.

---

# 28. Configuration and Security

Never commit:

```text
.env
API keys
database passwords
credentials
private secrets
```

Use:

```text
.env.example
```

as the configuration template.

Example:

```text
DB_HOST=localhost
DB_PORT=3306
DB_NAME=quantdb
DB_USER=your_username
DB_PASSWORD=your_password
```

Actual credentials must remain local.

---

# 29. Testing Requirements

Each module must have appropriate tests.

Database:

```text
tests/test_database.py
```

Quant:

```text
tests/test_analytics.py
```

Backtesting:

```text
tests/test_backtesting.py
```

Trading:

```text
tests/test_trading.py
```

Testing should cover:

- valid inputs
- invalid inputs
- edge cases
- database constraints
- transaction behavior
- mathematical correctness
- integration behavior

---

# 30. Integration Checkpoints

The project will be integrated progressively.

## Checkpoint 1

```text
MySQL
+
Schema
+
Constraints
+
Sample Data
```

## Checkpoint 2

```text
Python
+
MySQL
+
Backend Services
```

## Checkpoint 3

```text
Market Data
+
Quant Analytics
+
Backtesting
```

## Checkpoint 4

```text
Streamlit
+
Backend
+
Quant
+
Database
```

## Checkpoint 5

Full end-to-end testing.

---

# 31. Final End-to-End Application Flow

The intended complete system flow is:

```text
USER LOGIN
    |
    v
ROLE IDENTIFICATION
    |
    v
DASHBOARD
    |
    v
SELECT SECURITY
    |
    v
VIEW MARKET DATA
    |
    v
ANALYZE MARKET
    |
    v
SELECT STRATEGY
    |
    v
RUN BACKTEST
    |
    v
GENERATE SIGNALS
    |
    v
SIMULATE ORDERS
    |
    v
SIMULATE TRADES
    |
    v
UPDATE POSITIONS
    |
    v
UPDATE PORTFOLIO
    |
    v
CALCULATE P&L
    |
    v
CALCULATE RISK/PERFORMANCE
    |
    v
STORE RESULTS
    |
    v
DISPLAY REPORT
```

---

# 32. Definition of Done

A feature is considered complete only when:

```text
[ ] Implementation completed
[ ] Correct module/file used
[ ] Agreed interface followed
[ ] Tests written where applicable
[ ] Tests passed
[ ] No unnecessary breaking changes
[ ] Documentation updated if required
[ ] Commit created
[ ] Branch pushed
[ ] Pull Request reviewed
[ ] Integration verified
```

---

# 33. Golden Rules

The QuantDB team follows these rules:

1. `main` must always remain stable.
2. No direct development on `main`.
3. `develop` is the integration branch.
4. Each member owns a primary development layer.
5. Database schema is the single source of truth.
6. Shared interfaces must be agreed before implementation.
7. No silent schema changes.
8. No duplicate database schemas.
9. No credentials or secrets in Git.
10. Test before creating a Pull Request.
11. Integrate frequently instead of waiting until the end.
12. Use meaningful commits.
13. Keep the project modular.
14. Prefer simple, maintainable implementations.
15. QuantDB is a research/simulation platform, not a real-money trading system.

---

# 34. Current Development Status

Repository foundation:

```text
[✓] GitHub repository created
[✓] main branch
[✓] develop branch
[✓] database branch
[✓] backend branch
[✓] quant branch
[✓] frontend branch
[✓] Project folder structure
[✓] Basic repository files
```

Next development phases:

```text
[ ] Finalize project contract
[ ] Finalize ER model
[ ] Finalize relational schema
[ ] Finalize normalization
[ ] Implement database
[ ] Implement backend
[ ] Implement quant engine
[ ] Implement frontend
[ ] Integrate modules
[ ] Test complete system
[ ] Prepare final documentation
[ ] Prepare project demonstration
```

---

## Contract Status

**This document defines the current approved architecture and development contract for QuantDB.**

Any future architectural modification must follow the change-control process described above.