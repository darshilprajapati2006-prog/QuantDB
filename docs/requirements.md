# QuantDB — System Requirements

**Project Name:** QuantDB  
**Full Name:** A Database-Driven Market Data and Algorithmic Trading Research Platform  
**Version:** 1.0  
**Document Status:** Initial Requirements Specification

---

## 1. Purpose

This document defines the functional and non-functional requirements of the QuantDB project.

QuantDB is a database-driven quantitative finance research and simulated trading platform designed to manage financial market data, securities, users, simulated orders, trades, portfolios, positions, strategies, backtests, risk metrics, and performance analysis.

The system is intended for academic, research, and simulation purposes only. It does not execute real-money trades.

---

## 2. Scope

The system shall provide:

- Centralized financial market data management
- Exchange and security management
- User and role management
- Simulated order and trade management
- Portfolio and position tracking
- Quantitative strategy management
- Historical strategy backtesting
- Risk and performance analysis
- Basic market microstructure analysis
- Database-driven reporting and dashboards
- Python-based quantitative analysis
- MySQL-based relational database management

---

## 3. User Roles

QuantDB shall support the following roles:

### 3.1 Admin

The Admin shall be responsible for:

- Managing users
- Managing exchanges
- Managing securities
- Managing master data
- Managing system-level market data
- Monitoring system information
- Viewing administrative reports

### 3.2 Quant Researcher

The Quant Researcher shall be able to:

- View historical market data
- Analyze market data
- Create and manage quantitative strategies
- Configure strategy parameters
- Run historical backtests
- Analyze backtest results
- Calculate performance metrics
- Analyze risk metrics
- Analyze basic market microstructure data

### 3.3 Simulated Trader

The Simulated Trader shall be able to:

- View available market data
- Place simulated BUY and SELL orders
- Track simulated orders
- View simulated trades
- View portfolio information
- View positions
- Monitor simulated P&L
- Review portfolio risk and performance

---

# 4. Functional Requirements

## FR-01: User Management

The system shall:

- Create user accounts
- Store user information securely
- Assign roles to users
- Maintain user account status
- Authenticate users
- Prevent duplicate email registration
- Record user creation time
- Support role-based access to system functionality

---

## FR-02: Exchange Management

The system shall:

- Store exchange information
- Store exchange name
- Store unique exchange code
- Store country
- Store timezone
- Allow Admin users to create and manage exchanges
- Associate securities with exchanges

---

## FR-03: Security Management

The system shall:

- Store security information
- Associate each security with an exchange
- Store security symbol
- Store security name
- Store security type
- Store trading currency
- Maintain security status
- Prevent invalid exchange references

---

## FR-04: Market Data Management

The system shall:

- Store historical market data
- Associate market data with securities
- Store timestamped OHLCV information
- Store open price
- Store high price
- Store low price
- Store close price
- Store trading volume
- Store bid price
- Store ask price
- Prevent duplicate market-data records for the same security and timestamp
- Support retrieval of historical market data
- Support filtering market data by security and time period

---

## FR-05: Order Management

The system shall support simulated order management.

The system shall:

- Create simulated BUY and SELL orders
- Associate orders with users
- Associate orders with securities
- Store order type
- Store order side
- Store quantity
- Store order price
- Store order status
- Store order timestamp
- Allow users to view their own orders
- Prevent invalid quantities and prices
- Maintain order status throughout the simulated order lifecycle

No real-money order execution shall be performed.

---

## FR-06: Trade Management

The system shall:

- Record simulated trade executions
- Associate trades with orders
- Associate trades with securities
- Store trade side
- Store executed quantity
- Store execution price
- Store trade timestamp
- Store transaction cost
- Maintain referential integrity with the related order
- Support trade history retrieval

---

## FR-07: Portfolio Management

The system shall:

- Create simulated portfolios
- Associate portfolios with users
- Store portfolio name
- Store initial capital
- Store current cash
- Store portfolio status
- Record portfolio creation time
- Allow users to view their portfolios
- Support portfolio-level performance analysis

---

## FR-08: Position Management

The system shall:

- Track security positions within portfolios
- Associate positions with portfolios
- Associate positions with securities
- Store position quantity
- Store average price
- Store realized P&L
- Store unrealized P&L
- Store position update time
- Maintain consistent portfolio-position relationships

---

## FR-09: Strategy Management

The system shall:

- Allow Quant Researchers to create strategies
- Store strategy name
- Store strategy description
- Store strategy type
- Store strategy parameters
- Store strategy status
- Associate strategies with users
- Record strategy creation time
- Allow researchers to manage their strategies

---

## FR-10: Backtesting

The system shall:

- Allow historical strategy backtesting
- Associate backtests with strategies
- Associate backtests with securities
- Store backtest start date
- Store backtest end date
- Store initial capital
- Store backtest status
- Execute predefined quantitative strategies against historical market data
- Record backtest results
- Support comparison and analysis of backtest performance

Backtesting shall use historical/simulated data and shall not involve real-money execution.

---

## FR-11: Backtest Results

The system shall store:

- Total return
- Total P&L
- Volatility
- Sharpe ratio
- Maximum drawdown
- Total trades
- Winning trades
- Losing trades
- Win rate

The system shall allow users to retrieve and analyze historical backtest results.

---

## FR-12: Risk and Performance Analysis

The system shall support calculation and analysis of:

- Returns
- Volatility
- Sharpe ratio
- Maximum drawdown
- P&L
- Portfolio performance
- Backtest performance

Risk and performance metrics shall be associated with the appropriate portfolio or backtest where applicable.

---

## FR-13: Market Microstructure Analysis

The system shall support basic market microstructure analysis using available market data.

The system shall support:

- Bid price analysis
- Ask price analysis
- Bid-ask spread calculation
- Market depth analysis where data is available
- Order-book imbalance analysis where data is available

---

## FR-14: Reporting and Dashboard

The system shall provide a functional dashboard for:

- Market data visualization
- Security information
- Simulated trading
- Order history
- Trade history
- Portfolio information
- Position information
- Strategy information
- Backtest results
- Risk metrics
- Performance reports
- Market microstructure analysis

---

## FR-15: SQL Operations

The database shall support meaningful SQL operations including:

- INSERT
- SELECT
- UPDATE
- DELETE
- INNER JOIN
- LEFT JOIN
- Aggregate functions
- GROUP BY
- HAVING
- ORDER BY
- Subqueries
- Views

SQL operations shall be used to retrieve, modify, and analyze project data.

---

## FR-16: Database Integrity

The database shall enforce:

- Primary key constraints
- Foreign key constraints
- UNIQUE constraints
- NOT NULL constraints where required
- CHECK constraints where supported and applicable
- Referential integrity
- Domain/value validation

The database shall prevent invalid relationships and inconsistent records.

---

## FR-17: Database Normalization

The relational database shall be designed using normalization principles.

The schema shall target:

- First Normal Form (1NF)
- Second Normal Form (2NF)
- Third Normal Form (3NF)

BCNF shall be considered where applicable.

The final schema shall minimize:

- Data redundancy
- Update anomalies
- Insert anomalies
- Delete anomalies

---

## FR-18: Database Performance and Optimization

The system shall demonstrate database performance optimization using:

- Appropriate indexes
- Indexed primary and foreign keys where appropriate
- Composite indexes where required
- Query analysis
- EXPLAIN / execution-plan analysis
- Efficient query design

Indexes shall be created based on actual query requirements rather than indiscriminately.

---

## FR-19: Stored Procedures and Functions

The database shall include appropriate stored procedures and/or functions for recurring database operations.

Examples may include:

- Portfolio calculations
- Trade/order processing
- Performance calculations
- Frequently used data retrieval operations

Stored procedures and functions shall be designed to support the application's DBMS requirements.

---

## FR-20: Database Triggers

The system shall use appropriate database triggers where they provide meaningful database-level automation or integrity enforcement.

Possible use cases include:

- Updating related records after simulated trade execution
- Maintaining derived values
- Enforcing database-level consistency

Triggers shall not be used unnecessarily when equivalent application-level logic is more appropriate.

---

## FR-21: Transaction Management

The system shall use database transactions for operations that require atomicity.

Simulated trading operations shall maintain consistency across related records.

For example, an order execution may involve:

1. Updating order status
2. Creating a trade record
3. Updating portfolio cash
4. Updating the related position
5. Updating applicable P&L information

These operations shall succeed together or be rolled back when an error occurs.

---

## FR-22: Python Database Integration

The Python application shall:

- Connect to MySQL
- Execute parameterized SQL queries
- Retrieve database records
- Insert and update records
- Handle database errors
- Manage database transactions where required
- Provide a reusable database access layer

The application shall avoid hard-coded database credentials.

---

## FR-23: Market Data Ingestion

The system shall support ingestion of market data from structured sources such as CSV/sample historical datasets.

The ingestion process shall:

- Load market data
- Validate records
- Clean invalid data
- Check required fields
- Handle duplicate records
- Transform data into the required database format
- Insert valid records into MySQL

---

## FR-24: Data Validation

The system shall validate:

- Required fields
- Numeric values
- Price values
- Quantities
- Dates and timestamps
- Security references
- User references
- Portfolio references
- Strategy references

Invalid records shall be rejected or handled safely without corrupting existing data.

---

# 5. Non-Functional Requirements

## NFR-01: Performance

The system should provide efficient retrieval and processing of market and trading data.

Frequently accessed queries should be optimized using appropriate database techniques.

---

## NFR-02: Reliability

The system shall maintain data consistency during normal operation and simulated trading operations.

Database failures or transaction errors shall not leave related records in an inconsistent state.

---

## NFR-03: Security

The system shall:

- Avoid storing plain-text passwords
- Use password hashing for user credentials
- Avoid exposing database credentials
- Use environment variables for sensitive configuration
- Restrict functionality based on user roles

---

## NFR-04: Maintainability

The project shall use:

- Modular Python code
- Organized SQL scripts
- Clear naming conventions
- Reusable database functions
- Meaningful documentation
- Git-based version control

---

## NFR-05: Scalability

The database design should support growth in:

- Market data records
- Securities
- Users
- Orders
- Trades
- Portfolios
- Strategies
- Backtests

The schema should avoid unnecessary duplication and support efficient querying.

---

## NFR-06: Usability

The dashboard shall provide a clear and understandable interface for:

- Market data
- Simulated trading
- Portfolio monitoring
- Strategy analysis
- Backtesting
- Risk analysis
- Reports

---

## NFR-07: Testability

The system shall include tests for important components including:

- Database operations
- Data validation
- Quantitative calculations
- Backtesting
- Simulated trading operations

---

## NFR-08: Version Control

All source code, database scripts, documentation, and configuration templates shall be maintained using Git.

The project shall follow the agreed branch workflow:

- `main`
- `develop`
- `database`
- `backend`
- `quant`
- `frontend`

The `main` branch shall contain stable integrated code.

---

# 6. Database Requirements

The project shall use:

- MySQL 8.x
- MySQL Workbench

The database shall contain the following core entities:

1. USER
2. EXCHANGE
3. SECURITY
4. MARKET_DATA
5. ORDERS
6. TRADE
7. PORTFOLIO
8. POSITION
9. STRATEGY
10. BACKTEST
11. BACKTEST_RESULT
12. RISK_METRIC

The final primary keys, foreign keys, attributes, relationships, and constraints shall be defined in the approved relational schema.

---

# 7. Application Technology Requirements

The project shall use:

### Core Technologies

- Python 3.x
- MySQL 8.x
- Streamlit
- Pandas
- NumPy
- mysql-connector-python
- Git
- GitHub

### Supporting Technologies

- Matplotlib
- SQLAlchemy where appropriate
- SciPy where required
- pytest

The technology stack may be extended only when the addition is justified and does not conflict with the project contract.

---

# 8. System Architecture Requirements

The system shall follow the general architecture:

```text
                Streamlit UI
                     |
                     v
             Python Application
                     |
          +----------+----------+
          |                     |
          v                     v
     MySQL Database       Quant Analytics
          |                     |
          |                     v
          |                Backtesting
          |                     |
          +----------<----------+
