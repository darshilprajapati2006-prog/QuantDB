"""
QuantDB Mock Provider.
Implements data provider methods using realistic generated mock datasets.
Provides the primary data feed during development and offline testing.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from dashboard.mock.market_data import (
    get_securities_list,
    get_exchanges_list,
    generate_ohlcv_data,
    get_market_overview_summary,
)
from dashboard.mock.portfolio import (
    get_portfolios_list,
    get_portfolio_by_id,
    get_portfolio_positions,
    get_historical_equity_curve,
)
from dashboard.mock.orders import (
    get_orders as mock_get_orders,
    submit_simulated_order as mock_submit_order,
)
from dashboard.mock.trades import (
    get_trades as mock_get_trades,
    record_simulated_trade as mock_record_trade,
)
from dashboard.mock.strategies import (
    get_strategies_catalog,
    get_strategy_by_id,
)
from dashboard.mock.backtests import (
    generate_mock_backtest_run,
    get_latest_backtest_summary,
)


class MockProvider:
    """Mock Data Provider supplying simulated quantitative market and execution data."""

    def __init__(self):
        self.mode_name = "MOCK"

    def get_securities(self) -> List[Dict]:
        return get_securities_list()

    def get_users(self) -> List[Dict]:
        return [
            {"user_id": 1, "username": "admin01", "name": "Darshil Prajapati", "email": "darshil@quantdb.local", "role": "ADMIN", "status": "ACTIVE", "is_verified": True, "created_at": "2024-01-01 00:00:00"},
            {"user_id": 2, "username": "researcher01", "name": "Bharat", "email": "bharat@quantdb.local", "role": "QUANT_RESEARCHER", "status": "ACTIVE", "is_verified": True, "created_at": "2024-01-05 10:15:00"},
            {"user_id": 3, "username": "trader01", "name": "Simulated Trader 1", "email": "trader1@quantdb.local", "role": "QUANT_TRADER", "status": "ACTIVE", "is_verified": True, "created_at": "2024-02-01 09:00:00"},
            {"user_id": 4, "username": "user01", "name": "Standard User", "email": "user01@quantdb.local", "role": "USER", "status": "ACTIVE", "is_verified": True, "created_at": "2024-02-15 11:30:00"},
        ]

    def get_exchanges(self) -> List[Dict]:
        return get_exchanges_list()

    def get_market_data(
        self,
        security_id: int,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1D"
    ) -> pd.DataFrame:
        return generate_ohlcv_data(symbol, start_date, end_date, interval)

    def get_market_overview(self) -> pd.DataFrame:
        return get_market_overview_summary()

    def get_portfolios(self) -> List[Dict]:
        return get_portfolios_list()

    def get_portfolio(self, portfolio_id: int) -> Optional[Dict]:
        return get_portfolio_by_id(portfolio_id)

    def get_positions(self, portfolio_id: int) -> pd.DataFrame:
        return get_portfolio_positions(portfolio_id)

    def get_portfolio_equity_curve(self, portfolio_id: int, days: int = 180) -> pd.DataFrame:
        return get_historical_equity_curve(portfolio_id, days)

    def get_orders(self, portfolio_id: Optional[int] = None, status: Optional[str] = None) -> pd.DataFrame:
        return mock_get_orders(portfolio_id, status)

    def submit_order(
        self,
        portfolio_id: int,
        security_id: int,
        symbol: str,
        side: str,
        order_type: str,
        quantity: int,
        price: float
    ) -> Dict:
        order = mock_submit_order(portfolio_id, security_id, symbol, side, order_type, quantity, price)
        if order["status"] == "FILLED":
            # Auto-record matching trade for filled orders
            mock_record_trade(
                order_id=order["order_id"],
                security_id=security_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                execution_price=price,
                pnl=0.0,
                transaction_cost=round(quantity * price * 0.0001, 2)
            )
        return order

    def get_trades(self, portfolio_id: Optional[int] = None) -> pd.DataFrame:
        return mock_get_trades(portfolio_id)

    def get_strategies(self) -> List[Dict]:
        return get_strategies_catalog()

    def get_strategy(self, strategy_id: int) -> Optional[Dict]:
        return get_strategy_by_id(strategy_id)

    def run_backtest(
        self,
        strategy_id: int,
        security_id: int,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0,
        transaction_cost_pct: float = 0.05,
        parameters: Optional[Dict] = None
    ) -> Dict:
        return generate_mock_backtest_run(
            strategy_id=strategy_id,
            security_id=security_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            transaction_cost_pct=transaction_cost_pct,
            parameters=parameters
        )

    def get_system_status(self) -> Dict:
        return {
            "data_mode": "MOCK",
            "backend_status": "Simulated (Mock Provider)",
            "database_status": "Simulated (In-Memory)",
            "quant_engine_status": "Simulated (Analytical Models)",
            "version": "1.0.0-beta",
            "connected": True,
        }

    def get_risk_metrics(self, portfolio_id: int = 1) -> Dict:
        p = get_portfolio_by_id(portfolio_id)
        return {
            "portfolio_id": portfolio_id,
            "sharpe_ratio": p.get("sharpe_ratio", 1.84),
            "sortino_ratio": 2.15,
            "max_drawdown": p.get("max_drawdown", -6.8),
            "annualized_volatility": p.get("volatility", 14.2),
            "beta_vs_sp500": 1.08,
            "var_95_daily": -1.45,
            "cvar_95_daily": -2.10,
        }
