# QuantDB — Frontend & Research Dashboard

A terminal-grade Quantitative Finance, Market Data, Simulated Trading, and Backtesting dashboard built for the **QuantDB** DBMS + Quantitative Finance research platform.

Inspired by institutional quantitative research terminals, QuantDB delivers high data density, dark-first visual ergonomics, and clear separation of concerns.

---

## Architecture Overview

```text
                    QUANTDB
                       |
                       v
               Streamlit Dashboard
          (Overview, Market Data, Trading,
           Portfolio, Strategies, Backtesting,
           Reports, Admin)
                       |
                       v
                Frontend Services
          (market_service, trading_service,
           portfolio_service, strategy_service,
           backtest_service, analytics_service)
                       |
                       v
                Provider Factory
             (DATA_MODE = mock | real)
                       |
          +------------+------------+
          |                         |
          v                         v
    Mock Provider             Real Provider
(Autonomous Simulation)  (Finalized Backend Bridge)
                                    |
                       +------------+------------+
                       |                         |
                       v                         v
                Backend Services          Quant Services
                 (src/services)           (src/analytics,
                 (src/database)            src/backtesting)
                       |                         |
                       v                         v
                     MySQL                Analytics Engine
                    QuantDB                      |
                                                 v
                                           Backtesting
                                                 |
                                                 v
                                           Risk Metrics
```

---

## Directory Structure

```text
dashboard/
├── .streamlit/
│   └── config.toml          # Custom dark terminal theme configuration
├── app.py                   # Platform Overview Dashboard entrypoint
├── test_suite.py            # Automated test suite for services & contracts
│
├── pages/
│   ├── market_data.py       # OHLCV candlesticks, volume, and microstructure
│   ├── trading.py           # Paper trading execution & order ticket
│   ├── portfolio.py         # Portfolio valuation, asset allocation & positions
│   ├── strategies.py        # Quant strategy catalog & parameter schemas
│   ├── backtesting.py       # Event-driven backtest simulation & trade logs
│   ├── reports.py           # Institutional risk tear-sheets & factor analytics
│   └── admin.py             # Governance, RBAC, master catalogs & topology
│
├── components/
│   ├── theme.py             # Bloomberg terminal-inspired CSS & design tokens
│   ├── charts.py            # Reusable Plotly dark-themed financial charts
│   ├── tables.py            # Financial number & timestamp formatted tables
│   ├── metrics.py           # Terminal metric cards with positive/negative states
│   ├── sidebar.py           # Persistent navigation, mode switch, & live status
│   └── status.py            # Paper trading disclaimers & status pill badges
│
├── services/
│   ├── market_service.py    # Historical quotes & ticker lookup
│   ├── trading_service.py   # Paper order validation & execution routing
│   ├── portfolio_service.py # Valuations, positions & equity curves
│   ├── strategy_service.py  # Algorithmic strategy metadata & schema
│   ├── backtest_service.py  # Backtest execution & metrics retrieval
│   └── analytics_service.py # System health, Sharpe, VaR & risk metrics
│
├── providers/
│   ├── factory.py           # Provider instantiation & DATA_MODE toggle
│   ├── mock_provider.py     # High-fidelity in-memory simulated datasets
│   └── real_provider.py     # Python backend repository & Quant engine bridge
│
└── mock/
    ├── market_data.py       # Geometric Brownian Motion OHLCV & bid/ask quotes
    ├── portfolio.py         # Simulated portfolios & position holdings
    ├── orders.py            # Order lifecycle management
    ├── trades.py            # Trade execution logs & transaction costs
    ├── strategies.py        # Strategy parameter catalogs
    └── backtests.py         # Realistic backtest equity curves & trade logs
```

---

## How to Run the Dashboard

### Prerequisites
Install core dependencies:
```bash
pip install streamlit pandas plotly mysql-connector-python
```

### Launch Dashboard
Run the Streamlit application from the project root:
```bash
streamlit run dashboard/app.py
```
Open `http://localhost:8501` in your browser.

### Run Automated Tests
Verify all service interfaces, data contracts, and fault tolerance:
```bash
python dashboard/test_suite.py
```

To run the complete backend, quant, and service tests:
```bash
pytest tests/ -v
```

---

## Mock → Real Data Architecture

The dashboard is designed so that UI pages **never** change when switching from mock data to the real backend and MySQL database.

### Switching Modes

1. **Via UI**: Toggle between **MOCK** and **REAL** directly in the persistent sidebar or Admin Console.
2. **Via Environment Variable**:
   ```bash
   # Development / Offline Mock Data (Default)
   export DATA_MODE=mock

   # Production / Real MySQL & Quant Services
   export DATA_MODE=real
   ```

### Real Provider Integration

The `dashboard/providers/real_provider.py` connects to the finalized backend services in `src/services/` and repository in `src/database/`:

1. **Market Data & Securities**:
   - `src.database.repository.repository.get_securities() -> List[Dict]`
   - `src.services.market_service.get_market_data(security_id, start_date, end_date) -> pd.DataFrame`
2. **Orders & Trading**:
   - `src.services.trading_service.create_order(user_id, security_id, side, order_type, quantity, order_price) -> Order`
   - `src.services.trading_service.execute_order(order, execution_price) -> Trade`
   - `src.services.trading_service.get_orders() -> List[Dict]`
   - `src.services.trading_service.get_trades() -> List[Dict]`
3. **Portfolios & Positions**:
   - `src.services.portfolio_service.get_portfolio_summary(portfolio_id) -> Dict`
   - `src.services.portfolio_service.get_positions(portfolio_id) -> List[Dict]`
   - `src.services.portfolio_service.update_position(portfolio_id, security_id, quantity, price, side) -> Dict`
4. **Quant Engine & Backtesting**:
   - `src.services.backtest_service.run_backtest(strategy, security, historical_data, initial_capital, transaction_cost, strategy_parameters) -> Dict`
   - `src.backtesting.engine.BacktestEngine`
5. **Risk Metrics & Analytics**:
   - `src.services.analytics_service.calculate_returns(prices) -> pd.Series`
   - `src.services.analytics_service.calculate_risk_metrics(returns) -> Dict`
   - `src.services.analytics_service.calculate_performance(trades, returns, equity) -> Dict`
   - `src.services.analytics_service.calculate_microstructure(bid_price, ask_price) -> Dict`

If the database or backend is temporarily unreachable when `DATA_MODE=real` is selected, `RealProvider` gracefully handles exceptions and displays clean warning states without crashing the UI.
