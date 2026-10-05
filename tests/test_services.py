"""
QuantDB Service Layer Integration Tests

Comprehensive test suite covering:
- Market Data Service (retrieval, filtering, sorting, validation)
- Analytics Service (returns, risk, performance, microstructure, summary)
- Backtest Service (orchestration, validation, engine integration, result contract)
- Trading Service (paper order creation, execution, cancellation, retrieval)
- Portfolio Service (portfolio tracking, positions, equity summary)
"""

from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

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
    create_portfolio,
    get_portfolio,
    get_positions,
    get_portfolio_summary,
    update_position,
)


# ======================================================================
# FIXTURES
# ======================================================================

@pytest.fixture
def sample_market_records():
    """Sample raw database records as returned by repository."""
    return [
        {
            "market_data_id": 1,
            "security_id": 1,
            "timestamp": "2026-01-01 09:30:00",
            "open_price": 100.0,
            "high_price": 105.0,
            "low_price": 99.0,
            "close_price": 102.0,
            "volume": 1000,
            "bid_price": 101.9,
            "ask_price": 102.1,
        },
        {
            "market_data_id": 2,
            "security_id": 1,
            "timestamp": "2026-01-02 09:30:00",
            "open_price": 102.0,
            "high_price": 108.0,
            "low_price": 101.0,
            "close_price": 107.0,
            "volume": 1500,
            "bid_price": 106.9,
            "ask_price": 107.1,
        },
        {
            "market_data_id": 3,
            "security_id": 1,
            "timestamp": "2026-01-03 09:30:00",
            "open_price": 107.0,
            "high_price": 110.0,
            "low_price": 104.0,
            "close_price": 105.0,
            "volume": 1200,
            "bid_price": 104.9,
            "ask_price": 105.1,
        },
        {
            "market_data_id": 4,
            "security_id": 1,
            "timestamp": "2026-01-04 09:30:00",
            "open_price": 105.0,
            "high_price": 112.0,
            "low_price": 105.0,
            "close_price": 110.0,
            "volume": 1800,
            "bid_price": 109.9,
            "ask_price": 110.1,
        },
    ]


@pytest.fixture
def mock_repo(sample_market_records):
    """Mock repository returning sample market data."""
    repo = MagicMock()
    repo.get_market_data.return_value = sample_market_records
    return repo


@pytest.fixture
def backtest_market_data():
    """Generates 40 periods of historical market data suitable for backtesting."""
    dates = pd.date_range("2026-01-01", periods=40, freq="D")
    prices = [
        100.0, 101.0, 102.0, 101.5, 103.0, 104.5, 106.0, 108.0, 107.0, 109.0,
        111.0, 112.5, 114.0, 113.0, 115.0, 116.0, 114.5, 113.0, 111.0, 110.0,
        108.5, 107.0, 105.0, 104.0, 106.0, 108.0, 110.0, 112.0, 115.0, 118.0,
        120.0, 122.0, 121.0, 119.0, 117.0, 115.0, 116.0, 118.0, 120.0, 122.0,
    ]
    return pd.DataFrame(
        {
            "timestamp": dates,
            "open_price": prices,
            "high_price": [p + 2.0 for p in prices],
            "low_price": [p - 2.0 for p in prices],
            "close_price": prices,
            "volume": [1000] * 40,
        }
    )


# ======================================================================
# 1. MARKET SERVICE TESTS
# ======================================================================

class TestMarketService:
    """Tests for market data service."""

    def test_valid_market_data_retrieval(self, mock_repo):
        df = get_market_data(security_id=1, repo=mock_repo)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4
        assert "timestamp" in df.columns
        assert "close_price" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert df["close_price"].iloc[0] == 102.0
        mock_repo.get_market_data.assert_called_once()

    def test_empty_market_data_raises_error(self):
        empty_repo = MagicMock()
        empty_repo.get_market_data.return_value = []
        with pytest.raises(ValueError, match="No market data found"):
            get_market_data(security_id=1, repo=empty_repo)

    def test_date_filtering(self, mock_repo):
        df = get_market_data(
            security_id=1,
            start_date="2026-01-02",
            end_date="2026-01-03 23:59:59",
            repo=mock_repo,
        )
        assert len(df) == 2
        assert df["timestamp"].min() >= pd.to_datetime("2026-01-02")
        assert df["timestamp"].max() <= pd.to_datetime("2026-01-03 23:59:59")

    def test_invalid_date_range(self, mock_repo):
        with pytest.raises(ValueError, match="cannot be greater than end_date"):
            get_market_data(
                security_id=1,
                start_date="2026-01-10",
                end_date="2026-01-01",
                repo=mock_repo,
            )

    def test_invalid_security_id(self, mock_repo):
        with pytest.raises(ValueError, match="security_id must be a positive integer"):
            get_market_data(security_id=0, repo=mock_repo)
        with pytest.raises(ValueError, match="security_id must be a positive integer"):
            get_market_data(security_id=-5, repo=mock_repo)

    def test_chronological_sorting_and_deduplication(self):
        shuffled_records = [
            {"timestamp": "2026-01-03", "close_price": 105.0},
            {"timestamp": "2026-01-01", "close_price": 100.0},
            {"timestamp": "2026-01-02", "close_price": 102.0},
            {"timestamp": "2026-01-02", "close_price": 103.0},  # Duplicate
        ]
        repo = MagicMock()
        repo.get_market_data.return_value = shuffled_records

        df = get_market_data(security_id=1, repo=repo)
        assert len(df) == 3
        assert list(df["close_price"]) == [100.0, 103.0, 105.0]
        assert df["timestamp"].is_monotonic_increasing

    def test_validate_market_data_ohlc_violation(self):
        bad_df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2026-01-01", periods=2),
                "open_price": [100.0, 100.0],
                "high_price": [95.0, 105.0],  # High < open -> invalid
                "low_price": [90.0, 95.0],
                "close_price": [98.0, 102.0],
            }
        )
        with pytest.raises(ValueError, match="high_price cannot be lower"):
            validate_market_data(bad_df)


# ======================================================================
# 2. ANALYTICS SERVICE TESTS
# ======================================================================

class TestAnalyticsService:
    """Tests for analytics service integration."""

    def test_returns_integration(self):
        prices = pd.Series([100.0, 105.0, 110.0, 108.0])

        simple_ret = calculate_returns(prices, return_type="simple")
        assert isinstance(simple_ret, pd.Series)
        assert pytest.approx(simple_ret.iloc[1], 1e-4) == 0.05

        log_ret = calculate_returns(prices, return_type="log")
        assert isinstance(log_ret, pd.Series)

        cum_ret = calculate_returns(prices, return_type="cumulative")
        assert isinstance(cum_ret, pd.Series)
        assert pytest.approx(cum_ret.iloc[-1], 1e-4) == 0.08

        tot_ret = calculate_returns(prices, return_type="total")
        assert pytest.approx(tot_ret, 1e-4) == 0.08

        summary = calculate_returns(prices, return_type="summary")
        assert isinstance(summary, dict)
        assert "total_return" in summary
        assert "initial_price" in summary

    def test_returns_with_dataframe_input(self):
        df = pd.DataFrame({"close_price": [100.0, 110.0, 120.0]})
        tot = calculate_returns(df, return_type="total")
        assert pytest.approx(tot, 1e-4) == 0.20

    def test_risk_metrics_integration(self):
        returns = pd.Series([0.01, -0.02, 0.015, 0.005, -0.01, 0.02])
        risk = calculate_risk_metrics(returns)

        assert "volatility" in risk
        assert "sharpe_ratio" in risk
        assert "max_drawdown" in risk
        assert isinstance(risk["volatility"], float)
        assert isinstance(risk["sharpe_ratio"], float)
        assert isinstance(risk["max_drawdown"], float)
        assert risk["max_drawdown"] <= 0.0

    def test_performance_integration(self):
        trades = pd.DataFrame(
            {
                "pnl": [50.0, -20.0, 80.0, -10.0, 30.0],
            }
        )
        perf = calculate_performance(trades=trades)

        assert perf["total_pnl"] == 130.0
        assert perf["winning_trades"] == 3
        assert perf["losing_trades"] == 2
        assert perf["total_trades"] == 5
        assert perf["win_rate"] == 60.0

    def test_microstructure_integration(self):
        micro = calculate_microstructure(
            bid_price=100.0,
            ask_price=100.5,
            bid_size=500.0,
            ask_size=300.0,
        )

        assert pytest.approx(micro["bid_ask_spread"], 1e-4) == 0.5
        assert micro["bid_depth"] == 500.0
        assert micro["ask_depth"] == 300.0
        assert micro["total_depth"] == 800.0
        assert pytest.approx(micro["order_book_imbalance"], 1e-4) == 0.25

    def test_composite_analytics_summary(self):
        prices = pd.Series([100.0, 102.0, 105.0, 103.0, 108.0, 110.0])
        trades = pd.DataFrame({"pnl": [20.0, -5.0, 15.0]})

        summary = calculate_analytics_summary(prices=prices, trades=trades)

        required_keys = [
            "total_return",
            "total_pnl",
            "volatility",
            "sharpe_ratio",
            "max_drawdown",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
        ]
        for key in required_keys:
            assert key in summary, f"Missing key: {key}"
        assert summary["total_trades"] == 3
        assert summary["winning_trades"] == 2
        assert summary["losing_trades"] == 1


# ======================================================================
# 3. BACKTEST SERVICE TESTS
# ======================================================================

class TestBacktestService:
    """Tests for backtest service integration."""

    def test_valid_backtest_with_moving_average(self, backtest_market_data):
        result = run_backtest(
            strategy="moving_average",
            security="TEST_SEC",
            historical_data=backtest_market_data,
            initial_capital=50000.0,
            strategy_parameters={"short_window": 5, "long_window": 15},
        )

        # Check required return contract
        required_fields = [
            "strategy",
            "security",
            "initial_capital",
            "final_equity",
            "total_return",
            "total_pnl",
            "volatility",
            "sharpe_ratio",
            "max_drawdown",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
            "trades",
            "equity_curve",
        ]
        for field in required_fields:
            assert field in result, f"Missing result field: {field}"

        assert result["strategy"] == "moving_average"
        assert result["security"] == "TEST_SEC"
        assert result["initial_capital"] == 50000.0
        assert isinstance(result["trades"], pd.DataFrame)
        assert isinstance(result["equity_curve"], pd.DataFrame)
        assert isinstance(result["total_return"], float)
        assert isinstance(result["total_pnl"], float)

    def test_valid_backtest_with_momentum(self, backtest_market_data):
        result = run_backtest(
            strategy="momentum",
            security="MOM_SEC",
            historical_data=backtest_market_data,
            strategy_parameters={"lookback": 5},
        )
        assert result["strategy"] == "momentum"
        assert "trades" in result

    def test_valid_backtest_with_mean_reversion(self, backtest_market_data):
        result = run_backtest(
            strategy="mean_reversion",
            security="MR_SEC",
            historical_data=backtest_market_data,
            strategy_parameters={"window": 10, "threshold": 0.01},
        )
        assert result["strategy"] == "mean_reversion"

    def test_backtest_with_repository_fetch(self, backtest_market_data):
        repo = MagicMock()
        repo.get_market_data.return_value = backtest_market_data.to_dict("records")

        result = run_backtest(
            strategy="moving_average",
            security=1,
            historical_data=None,  # Automatically fetch via market_service
            initial_capital=10000.0,
            strategy_parameters={"short_window": 5, "long_window": 15},
            repo=repo,
        )
        assert result["initial_capital"] == 10000.0
        repo.get_market_data.assert_called_once()

    def test_invalid_strategy_raises_error(self, backtest_market_data):
        with pytest.raises(ValueError, match="Unsupported strategy"):
            run_backtest(
                strategy="non_existent_strategy",
                security="TEST",
                historical_data=backtest_market_data,
            )

    def test_invalid_initial_capital(self, backtest_market_data):
        with pytest.raises(ValueError, match="initial_capital must be positive"):
            run_backtest(
                strategy="moving_average",
                security="TEST",
                historical_data=backtest_market_data,
                initial_capital=-1000.0,
            )

    def test_invalid_date_range(self, backtest_market_data):
        with pytest.raises(ValueError, match="cannot be greater than end_date"):
            run_backtest(
                strategy="moving_average",
                security="TEST",
                historical_data=backtest_market_data,
                start_date="2026-05-01",
                end_date="2026-01-01",
            )

    def test_empty_historical_data(self):
        with pytest.raises(ValueError, match="historical_data cannot be empty"):
            run_backtest(
                strategy="moving_average",
                security="TEST",
                historical_data=pd.DataFrame(),
            )

    def test_insufficient_data_for_window(self):
        short_data = pd.DataFrame(
            {
                "timestamp": pd.date_range("2026-01-01", periods=5),
                "close_price": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )
        with pytest.raises(ValueError, match="Insufficient historical data"):
            run_backtest(
                strategy="moving_average",
                security="TEST",
                historical_data=short_data,
                strategy_parameters={"short_window": 5, "long_window": 20},
            )


# ======================================================================
# 4. TRADING SERVICE TESTS
# ======================================================================

class TestTradingService:
    """Tests for simulated trading service."""

    def test_create_order_market_and_limit(self):
        order_mkt = create_order(
            user_id=1,
            security_id=1,
            side="BUY",
            order_type="MARKET",
            quantity=100.0,
        )
        assert order_mkt.side == "BUY"
        assert order_mkt.order_type == "MARKET"
        assert order_mkt.order_status == "PENDING"
        assert order_mkt.order_id is not None

        order_lmt = create_order(
            user_id=1,
            security_id=1,
            side="SELL",
            order_type="LIMIT",
            quantity=50.0,
            order_price=105.0,
        )
        assert order_lmt.side == "SELL"
        assert order_lmt.order_price == 105.0

    def test_execute_order(self):
        order = create_order(
            user_id=2,
            security_id=1,
            side="BUY",
            order_type="MARKET",
            quantity=20.0,
        )
        trade = execute_order(order, execution_price=100.0)

        assert trade.order_id == order.order_id
        assert trade.execution_price == 100.0
        assert trade.quantity == 20.0
        assert trade.transaction_cost > 0.0
        assert order.order_status == "FILLED"

    def test_cancel_order(self):
        order = create_order(
            user_id=3,
            security_id=2,
            side="BUY",
            order_type="LIMIT",
            quantity=10.0,
            order_price=95.0,
        )
        cancelled = cancel_order(order)
        assert cancelled.order_status == "CANCELLED"

    def test_get_orders_and_trades(self):
        order = create_order(
            user_id=99,
            security_id=5,
            side="BUY",
            order_type="MARKET",
            quantity=10.0,
        )
        orders = get_orders(user_id=99)
        assert len(orders) >= 1
        assert any(o["user_id"] == 99 for o in orders)

        trade = execute_order(order, execution_price=50.0)
        trades = get_trades(security_id=5)
        assert len(trades) >= 1
        assert any(t["security_id"] == 5 for t in trades)

    def test_order_and_trade_summaries(self):
        order = create_order(
            user_id=1,
            security_id=1,
            side="BUY",
            order_type="MARKET",
            quantity=10.0,
        )
        o_sum = get_order_summary(order)
        assert "order_id" in o_sum
        assert o_sum["side"] == "BUY"

        trade = execute_order(order, execution_price=10.0)
        t_sum = get_trade_summary(trade)
        assert "trade_id" in t_sum
        assert t_sum["execution_price"] == 10.0


# ======================================================================
# 5. PORTFOLIO SERVICE TESTS
# ======================================================================

class TestPortfolioService:
    """Tests for portfolio service."""

    def test_create_and_get_portfolio(self):
        port = create_portfolio(
            user_id=10,
            portfolio_name="Alpha Fund",
            initial_capital=75000.0,
            portfolio_id=101,
        )
        assert port["portfolio_id"] == 101
        assert port["initial_capital"] == 75000.0
        assert port["cash"] == 75000.0

        retrieved = get_portfolio(101)
        assert retrieved["portfolio_id"] == 101

    def test_update_position_buy_and_sell(self):
        create_portfolio(
            user_id=11,
            portfolio_name="Beta Fund",
            initial_capital=50000.0,
            portfolio_id=102,
        )

        # BUY 100 shares at 100.0
        pos_after_buy = update_position(
            portfolio_id=102,
            security_id=1,
            quantity=100.0,
            price=100.0,
            side="BUY",
        )
        assert pos_after_buy["quantity"] == 100.0

        positions = get_positions(102)
        assert len(positions) == 1
        assert positions[0]["security_id"] == 1

        # SELL 50 shares at 110.0
        pos_after_sell = update_position(
            portfolio_id=102,
            security_id=1,
            quantity=50.0,
            price=110.0,
            side="SELL",
        )
        assert pos_after_sell["quantity"] == 50.0
        assert pos_after_sell["realized_pnl"] == 500.0

    def test_get_portfolio_summary(self):
        summary = get_portfolio_summary(102)
        assert "portfolio_id" in summary
        assert "cash" in summary
        assert "total_equity" in summary
        assert "realized_pnl" in summary
        assert "return_percentage" in summary

    def test_invalid_initial_capital(self):
        with pytest.raises(ValueError, match="must be greater than zero"):
            create_portfolio(user_id=1, initial_capital=-100.0)
