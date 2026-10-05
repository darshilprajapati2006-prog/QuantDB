"""
QuantDB Real Data Provider.
Connects the Service Layer to the actual Python Backend, MySQL database repositories,
and Quant Analytics engine once available.
Handles disconnection gracefully and adheres strictly to the data contracts.
"""

from datetime import datetime
import os
from typing import Dict, List, Optional
import pandas as pd


class RealProvider:
    """
    Real Data Provider connecting to MySQL database and Quant Analytics engine.
    Designed according to Section 5 & 24 of the QuantDB specification.
    """

    def __init__(self):
        self.mode_name = "REAL"
        self._connected = False
        self._check_connection()

    def _check_connection(self):
        """Checks whether database / backend services are reachable."""
        # Check environment or database connectivity
        # Will connect to src.database once backend developer Bharat & Darshil integrate
        db_host = os.environ.get("DB_HOST", "localhost")
        self._connected = False  # Set to False by default until backend services are live

    def is_connected(self) -> bool:
        return self._connected

    def get_securities(self) -> List[Dict]:
        """Fetches securities from real database repository."""
        # Interface Contract with Backend Team:
        # Expected: src.database.repository.get_all_securities() -> List[Dict]
        try:
            from src.trading.securities import get_all_securities  # type: ignore
            return get_all_securities()
        except ImportError:
            # Fallback for safe interface discovery
            return []

    def get_exchanges(self) -> List[Dict]:
        try:
            from src.trading.securities import get_all_exchanges  # type: ignore
            return get_all_exchanges()
        except ImportError:
            return []

    def get_market_data(
        self,
        security_id: int,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1D"
    ) -> pd.DataFrame:
        """
        Fetches historical OHLCV from real MySQL market_data table.
        Expected interface: src.database.repository.get_market_data(security_id, start_date, end_date)
        """
        try:
            from src.database.repository import MarketDataRepository  # type: ignore
            repo = MarketDataRepository()
            return repo.get_historical_ohlcv(security_id, start_date, end_date)
        except Exception:
            # Return empty DataFrame conforming to contract columns
            return pd.DataFrame(columns=[
                "timestamp", "security_id", "symbol", "open_price", "high_price",
                "low_price", "close_price", "volume", "bid_price", "ask_price",
                "spread", "mid_price", "relative_spread_bps", "order_book_imbalance"
            ])

    def get_market_overview(self) -> pd.DataFrame:
        try:
            from src.database.repository import MarketDataRepository  # type: ignore
            return MarketDataRepository().get_latest_summary()
        except Exception:
            return pd.DataFrame()

    def get_portfolios(self) -> List[Dict]:
        try:
            from src.trading.portfolio_service import list_portfolios  # type: ignore
            return list_portfolios()
        except Exception:
            return []

    def get_portfolio(self, portfolio_id: int) -> Optional[Dict]:
        try:
            from src.trading.portfolio_service import get_portfolio_summary  # type: ignore
            return get_portfolio_summary(portfolio_id)
        except Exception:
            return None

    def get_positions(self, portfolio_id: int) -> pd.DataFrame:
        try:
            from src.trading.portfolio_service import get_positions  # type: ignore
            return get_positions(portfolio_id)
        except Exception:
            return pd.DataFrame(columns=[
                "security_id", "symbol", "quantity", "average_price", "current_price",
                "market_value", "unrealized_pnl", "weight"
            ])

    def get_portfolio_equity_curve(self, portfolio_id: int, days: int = 180) -> pd.DataFrame:
        try:
            from src.analytics.portfolio import get_equity_history  # type: ignore
            return get_equity_history(portfolio_id, days)
        except Exception:
            return pd.DataFrame()

    def get_orders(self, portfolio_id: Optional[int] = None, status: Optional[str] = None) -> pd.DataFrame:
        try:
            from src.trading.order_service import get_orders  # type: ignore
            return get_orders(portfolio_id, status)
        except Exception:
            return pd.DataFrame(columns=[
                "order_id", "portfolio_id", "security_id", "symbol",
                "timestamp", "side", "order_type", "quantity", "price", "status"
            ])

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
        try:
            from src.trading.order_service import place_order  # type: ignore
            return place_order(portfolio_id, security_id, symbol, side, order_type, quantity, price)
        except Exception as e:
            return {"error": f"Failed to submit order to real backend: {str(e)}"}

    def get_trades(self, portfolio_id: Optional[int] = None) -> pd.DataFrame:
        try:
            from src.trading.trade_service import get_trades  # type: ignore
            return get_trades(portfolio_id)
        except Exception:
            return pd.DataFrame(columns=[
                "trade_id", "order_id", "security_id", "symbol",
                "timestamp", "side", "quantity", "execution_price", "pnl", "transaction_cost"
            ])

    def get_strategies(self) -> List[Dict]:
        try:
            from src.backtesting.strategy_registry import get_strategies  # type: ignore
            return get_strategies()
        except Exception:
            return []

    def get_strategy(self, strategy_id: int) -> Optional[Dict]:
        try:
            from src.backtesting.strategy_registry import get_strategy  # type: ignore
            return get_strategy(strategy_id)
        except Exception:
            return None

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
        try:
            from src.backtesting.engine import BacktestEngine  # type: ignore
            engine = BacktestEngine()
            return engine.run(
                strategy_id=strategy_id,
                security_id=security_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                transaction_cost_pct=transaction_cost_pct,
                parameters=parameters
            )
        except Exception as e:
            return {"error": f"Real Quant Engine unavailable: {str(e)}"}

    def get_system_status(self) -> Dict:
        return {
            "data_mode": "REAL",
            "backend_status": "Connecting to src.database" if self._connected else "Offline (Waiting for backend integration)",
            "database_status": "Online" if self._connected else "Offline",
            "quant_engine_status": "Online" if self._connected else "Offline",
            "version": "1.0.0-prod",
            "connected": self._connected,
        }

    def get_risk_metrics(self, portfolio_id: int = 1) -> Dict:
        try:
            from src.analytics.risk import compute_risk_metrics  # type: ignore
            return compute_risk_metrics(portfolio_id)
        except Exception:
            return {}
