# QuantDB

> **Database-Driven Market Data Management, Paper Trading, Quantitative Research & Strategy Backtesting Platform**

An academic, institutional-grade DBMS + Quantitative Finance platform implementing an end-to-end data pipeline from a normalized MySQL database to algorithmic trading strategies, risk factor models, and an interactive Streamlit research terminal.

---

## 1. Problem Statement

Financial market data systems require strict ACID consistency for order-book executions and portfolio valuations alongside high-throughput chronological data access for quantitative time-series models. Academic research often struggles with fractured architectures where database schemas, transaction semantics, and algorithmic backtesting models are disconnected.

**QuantDB** solves this by establishing a disciplined, unified architecture connecting a 3NF normalized relational database in MySQL with a high-performance quantitative analytics engine, simulated paper trading execution framework, and a research dashboard.

---

## 2. Objectives

- **Database Engineering**: Design and implement 12 normalized relational entities with declarative constraints, foreign keys, stored procedures, stored functions, database triggers, and transaction isolation.
- **Data Ingestion & Cleaning**: Ingest and validate historical OHLCV data, enforce chronological ordering, and guarantee bid-ask and price invariant integrity.
- **Quantitative Analytics**: Compute returns (simple, log, cumulative), risk metrics (annualized volatility, Sharpe ratio, Sortino ratio, maximum drawdown, Value at Risk), and microstructure statistics (bid-ask spread, relative spread in bps, order-book imbalance).
- **Strategy Backtesting**: Model event-driven quantitative trading strategies (Moving Average Crossover, Momentum, Mean Reversion) over historical data with transaction friction and performance tear-sheets.
- **Paper Trading Simulation**: Simulate realistic order matching and trade settlement with zero real-money exposure.
- **Provider Architecture**: Support dual data modes (`REAL` backed by MySQL and `MOCK` for offline development/cloud demonstration) through clean abstraction boundaries.

---

## 3. Platform Architecture

```text
Streamlit Research Terminal (dashboard/app.py & pages/)
      ↓
Frontend Service Layer (dashboard/services/*.py)
      ↓
Provider Factory (dashboard/providers/factory.py)
      ↓
Mock Provider (Autonomous Simulation)  OR  Real Provider (Backend Bridge)
      ↓
Backend Service Layer (src/services/*.py)
      ↓
Repository Layer (src/database/repository.py & queries.py)
      ↓
MySQL QuantDB (12 Normalized Entities, Views, Stored Procedures, Triggers)
      ↓
Quant Analytics & Backtesting Engine (src/analytics/*, src/backtesting/*)
```

---

## 4. Features & Module Scope

| Feature / Page | Description | Primary Engine / Service |
| :--- | :--- | :--- |
| **Platform Overview** | Real-time market pulse, active portfolio snapshot, system topological metrics. | `dashboard.services.market_service`, `portfolio_service` |
| **Market Data** | Candlestick charting, volume analysis, bid/ask depth, microstructure metrics. | `src.services.market_service` & `src.analytics.microstructure` |
| **Simulated Trading** | Market/Limit paper order tickets, trade history, execution logging. | `src.services.trading_service` & `src.trading.orders` |
| **Portfolio Analysis** | Holdings valuation, cash tracking, P&L attribution, deterministic equity curves. | `src.services.portfolio_service` & `src.trading.portfolio` |
| **Strategy Catalog** | Predefined algorithmic strategy specifications, parameter validation schemas. | `src.backtesting.strategies` |
| **Backtesting Engine** | Event-driven historical simulation, equity curves, drawdown series, trade records. | `src.services.backtest_service` & `src.backtesting.engine` |
| **Risk & Reports** | Institutional performance tear-sheets, Sharpe, Volatility, VaR / CVaR. | `src.services.analytics_service` & `src.analytics.risk` |
| **Admin Console** | Platform topology, database health diagnostics, RBAC, DB-backed user management. | `src.database.repository` (Users, Exchanges, Securities) |

---

## 5. Database Architecture & SQL Implementation

The platform is backed by a 3NF normalized MySQL database with 12 core relational entities:

1. **`users`**: Platform user accounts, unique usernames, PBKDF2-HMAC-SHA256 password credentials, RBAC roles (`ADMIN`, `QUANT_RESEARCHER`, `QUANT_TRADER`, `USER`), and account status.
2. **`exchanges`**: Global stock exchange master records (`NSE`, `BSE`, `NASDAQ`, `NYSE`), countries, and timezone definitions.
3. **`securities`**: Financial instruments master catalog with foreign keys to exchanges, security types (`EQUITY`, `ETF`), and currencies.
4. **`market_data`**: Historical market data records (OHLCV, bid, ask, volume) with timestamp indexing and foreign key referencing securities.
5. **`orders`**: Order lifecycle records (BUY/SELL, MARKET/LIMIT, order status: `PENDING`, `FILLED`, `CANCELLED`, `REJECTED`).
6. **`trades`**: Executed transaction trade records linked to parent orders with quantities, execution prices, and transaction costs.
7. **`portfolios`**: User portfolio accounts tracking initial capital, current cash, creation dates, and status.
8. **`positions`**: Open holdings tracking security quantities, average prices, realized P&L, and unrealized P&L.
9. **`strategies`**: Quantitative strategy registry catalog with strategy types and descriptions.
10. **`backtests`**: Executed backtest run logs recording strategy, security, date ranges, and initial capital.
11. **`backtest_results`**: Quantitative results produced by backtests (total return, Sharpe, drawdown, win rate, trade counts).
12. **`risk_metrics`**: Precomputed portfolio risk factor observations (volatility, beta, VaR, Sharpe).

### SQL Scripts & Execution Order

All database scripts are located under `database/` and must be executed in exact numerical sequence:

```text
01_create_database.sql    → Creates the QuantDB database instance.
02_create_tables.sql      → Generates all 12 normalized tables with column definitions.
03_constraints.sql        → Enforces Primary Keys, Foreign Keys, Unique Keys, and Check Constraints.
04_insert_master_data.sql → Seeds foundational users, exchanges, securities, portfolios, strategies.
05_insert_market_data.sql → Seeds verified historical OHLCV & quote datasets (RELIANCE, AAPL, etc.).
06_views.sql              → Creates analytical database views (e.g. vw_portfolio_summary, vw_latest_quotes).
07_indexes.sql            → Composite B-Tree indexes on timestamps, tickers, and foreign keys.
08_procedures.sql         → Stored procedures (sp_create_order, sp_execute_trade, sp_record_backtest).
09_functions.sql          → Stored functions (fn_win_rate, fn_position_value, fn_backtest_profit_pct).
10_triggers.sql           → Database triggers for automated cash updates, trade matching, and price validation.
11_transactions.sql       → ACID transaction procedures with row locking (FOR UPDATE) and SAVEPOINT rollbacks.
12_authentication.sql     → Authentication, PBKDF2 credentials, and Role-Based Access Control (RBAC) migration.
```

---

## 6. Technology Stack

- **Relational Database**: MySQL 8.x
- **Core Language**: Python 3.10+
- **Data Manipulation**: Pandas 2.x, NumPy 1.26+
- **Frontend / UI**: Streamlit 1.35+
- **Interactive Visualizations**: Plotly 5.18+
- **Database Connector**: `mysql-connector-python` 9.x
- **Configuration & Secrets**: `python-dotenv` 1.x / Streamlit Secrets
- **Testing & Quality Assurance**: `pytest` 9.x, `hypothesis`

---

## 7. Setup & Installation

### 1. Clone Repository

```bash
git clone https://github.com/darshilprajapati2006-prog/QuantDB.git
cd QuantDB
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Initialization (For Real Mode)

Log in to your local MySQL server and execute the scripts in sequence:

```bash
mysql -u root -p < database/01_create_database.sql
mysql -u root -p < database/02_create_tables.sql
mysql -u root -p < database/03_constraints.sql
mysql -u root -p < database/04_insert_master_data.sql
mysql -u root -p < database/05_insert_market_data.sql
mysql -u root -p < database/06_views.sql
mysql -u root -p < database/07_indexes.sql
mysql -u root -p < database/08_procedures.sql
mysql -u root -p < database/09_functions.sql
mysql -u root -p < database/10_triggers.sql
mysql -u root -p < database/11_transactions.sql
```

### 4. Configure Environment Variables

Copy the provided template and specify your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
DB_HOST=localhost
DB_PORT=3306
DB_NAME=QuantDB
DB_USER=root
DB_PASSWORD=your_password
DATA_MODE=real
```

---

## 8. Running the Application

Launch the research dashboard using Streamlit:

```bash
python3 -m streamlit run dashboard/app.py
```

Open your browser at `http://localhost:8501`.

---

## 9. Operating Modes: Real vs. Mock

- **MOCK MODE (`DATA_MODE=mock`)**:
  - Operates completely autonomously in-memory using mathematically calibrated geometric Brownian motion price series and execution models.
  - Used for cloud demo deployments (e.g. Streamlit Community Cloud) and environments without a local MySQL instance.
  - Transparently identified across all UI cards as `MOCK` / `Simulated`.
- **REAL MODE (`DATA_MODE=real`)**:
  - Connects directly to MySQL QuantDB via `src.database.connection` and repository queries.
  - Executes quant calculations through `src.services.*` and `src.analytics.*`.
  - Performs health checks and displays real error states if the database is unreachable, with zero silent fallback to synthetic data.

---

## 10. Automated Testing

Run the full verification test suites:

### Backend & Quant Test Suite (147 tests)

```bash
python3 -m pytest tests/ -v
```

### Frontend Services & Contract Test Suite (10 tests)

```bash
python3 dashboard/test_suite.py
```

All 157 automated tests pass with 100% success.

---

## 11. Cloud Deployment

The live demonstration of the platform is hosted on Streamlit Cloud:
👉 **[https://quantdb.streamlit.app/](https://quantdb.streamlit.app/)**

> **Note on Cloud Deployment**: The public cloud demo runs in `MOCK` mode by default because local MySQL instances are not exposed to the public internet. If deployed against a managed cloud MySQL database, `DATA_MODE=real` and database credentials can be provided securely via Streamlit Cloud Secrets.

---

## 12. Academic Scope & Disclaimer

This software was engineered strictly for **academic demonstration, quantitative finance research, algorithmic backtesting, and database systems study**. 

**No Real-Money Trading**: QuantDB contains zero integration with commercial brokerages, financial exchange order routers, or monetary settlement systems. All trading orders, positions, and backtests are simulated.
