"""
QuantDB Service Layer

Acts as the integration bridge connecting:
- MySQL Database / Repository Layer
- Quantitative Analytics and Backtesting Engine
- Paper/Simulated Trading and Portfolio Management
- Streamlit Presentation Dashboard
"""

from src.services.market_service import (
    get_market_data,
    validate_market_data,
)
from src.services.analytics_service import (
    calculate_returns,
    calculate_risk_metrics,
    calculate_performance,
    calculate_microstructure,
    calculate_analytics_summary,
)
from src.services.backtest_service import (
    run_backtest,
)
from src.services.trading_service import (
    create_order,
    execute_order,
    cancel_order,
    get_orders,
    get_trades,
    get_order_summary,
    get_trade_summary,
)
from src.services.portfolio_service import (
    get_portfolio,
    get_positions,
    get_portfolio_summary,
    create_portfolio,
    update_position,
)

__all__ = [
    # Market service
    "get_market_data",
    "validate_market_data",
    # Analytics service
    "calculate_returns",
    "calculate_risk_metrics",
    "calculate_performance",
    "calculate_microstructure",
    "calculate_analytics_summary",
    # Backtest service
    "run_backtest",
    # Trading service
    "create_order",
    "execute_order",
    "cancel_order",
    "get_orders",
    "get_trades",
    "get_order_summary",
    "get_trade_summary",
    # Portfolio service
    "get_portfolio",
    "get_positions",
    "get_portfolio_summary",
    "create_portfolio",
    "update_position",
]
