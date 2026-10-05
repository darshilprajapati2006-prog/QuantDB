"""
Tests for QuantDB backtesting module.

Covers:
- Strategy signal generation
- Backtesting engine
- Trade simulator
- BUY / SELL execution
- Transaction costs
- Cash and position updates
- P&L calculation
- End-to-end backtesting flow
"""

import numpy as np
import pandas as pd
import pytest

from src.backtesting.strategies import (
    moving_average_strategy,
    momentum_strategy,
    mean_reversion_strategy,
    generate_signals,
    strategy_result,
)

from src.backtesting.engine import run_backtest

from src.backtesting.simulator import TradeSimulator


# ============================================================
# TEST DATA
# ============================================================


@pytest.fixture
def price_series():
    """Simple deterministic price series for strategy tests."""
    return pd.Series(
        [
            100,
            102,
            104,
            106,
            108,
            110,
            108,
            106,
            104,
            102,
            100,
            98,
            96,
            98,
            100,
            103,
            106,
            109,
            112,
            115,
        ],
        dtype=float,
    )


@pytest.fixture
def historical_data():
    """Historical OHLC-style data for backtesting."""
    dates = pd.date_range(
        start="2026-01-01",
        periods=30,
        freq="D",
    )

    prices = [
        100,
        101,
        102,
        104,
        103,
        105,
        108,
        110,
        109,
        112,
        115,
        114,
        117,
        120,
        118,
        121,
        125,
        123,
        126,
        129,
        127,
        130,
        133,
        131,
        135,
        138,
        136,
        140,
        143,
        145,
    ]

    return pd.DataFrame(
        {
            "timestamp": dates,
            "close_price": prices,
        }
    )


# ============================================================
# STRATEGY TESTS
# ============================================================


class TestStrategies:
    """Tests for predefined quantitative strategies."""

    def test_moving_average_returns_valid_signals(self, price_series):
        result = moving_average_strategy(
            price_series,
            short_window=3,
            long_window=7,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(price_series)

        valid_signals = {"BUY", "SELL", "HOLD"}
        assert set(result.unique()).issubset(valid_signals)

    def test_moving_average_initial_values_are_hold(self, price_series):
        result = moving_average_strategy(
            price_series,
            short_window=3,
            long_window=7,
        )

        # Long MA is not available initially.
        assert (result.iloc[:6] == "HOLD").all()

    def test_moving_average_detects_buy_signal(self):
        prices = pd.Series(
            [100, 101, 102, 103, 104, 105, 110, 115, 120]
        )

        result = moving_average_strategy(
            prices,
            short_window=2,
            long_window=4,
        )

        assert "BUY" in result.values

    def test_momentum_returns_valid_signals(self, price_series):
        result = momentum_strategy(
            price_series,
            lookback=3,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(price_series)

        valid_signals = {"BUY", "SELL", "HOLD"}
        assert set(result.unique()).issubset(valid_signals)

    def test_momentum_initial_values_are_hold(self, price_series):
        result = momentum_strategy(
            price_series,
            lookback=3,
        )

        assert (result.iloc[:3] == "HOLD").all()

    def test_momentum_buy_signal(self):
        prices = pd.Series([100, 101, 102, 110])

        result = momentum_strategy(
            prices,
            lookback=2,
        )

        assert result.iloc[-1] == "BUY"

    def test_momentum_sell_signal(self):
        prices = pd.Series([110, 105, 100, 95])

        result = momentum_strategy(
            prices,
            lookback=2,
        )

        assert result.iloc[-1] == "SELL"

    def test_mean_reversion_returns_valid_signals(self, price_series):
        result = mean_reversion_strategy(
            price_series,
            window=5,
            threshold=0.02,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(price_series)

        valid_signals = {"BUY", "SELL", "HOLD"}
        assert set(result.unique()).issubset(valid_signals)

    def test_generate_signals_dispatcher(self, price_series):
        moving_average = generate_signals(
            price_series,
            "moving_average",
            short_window=3,
            long_window=7,
        )

        momentum = generate_signals(
            price_series,
            "momentum",
            lookback=3,
        )

        mean_reversion = generate_signals(
            price_series,
            "mean_reversion",
            window=5,
            threshold=0.02,
        )

        assert isinstance(moving_average, pd.Series)
        assert isinstance(momentum, pd.Series)
        assert isinstance(mean_reversion, pd.Series)

    def test_strategy_aliases(self, price_series):
        result_1 = generate_signals(
            price_series,
            "moving_average",
            short_window=3,
            long_window=7,
        )

        result_2 = generate_signals(
            price_series,
            "moving-average",
            short_window=3,
            long_window=7,
        )

        result_3 = generate_signals(
            price_series,
            "ma",
            short_window=3,
            long_window=7,
        )

        pd.testing.assert_series_equal(result_1, result_2)
        pd.testing.assert_series_equal(result_1, result_3)

    def test_invalid_strategy_raises_error(self, price_series):
        with pytest.raises(ValueError):
            generate_signals(
                price_series,
                "invalid_strategy",
            )

    def test_invalid_moving_average_parameters(self, price_series):
        with pytest.raises(ValueError):
            moving_average_strategy(
                price_series,
                short_window=10,
                long_window=5,
            )

    def test_invalid_momentum_parameter(self, price_series):
        with pytest.raises(ValueError):
            momentum_strategy(
                price_series,
                lookback=0,
            )

    def test_invalid_mean_reversion_parameter(self, price_series):
        with pytest.raises(ValueError):
            mean_reversion_strategy(
                price_series,
                window=5,
                threshold=-0.01,
            )

    def test_strategy_result_structure(self, price_series):
        result = strategy_result(
            price_series,
            "momentum",
            lookback=3,
        )

        assert isinstance(result, pd.DataFrame)
        assert "price" in result.columns
        assert "signal" in result.columns

        assert len(result) == len(price_series)


# ============================================================
# TRADE SIMULATOR TESTS
# ============================================================


class TestTradeSimulator:
    """Tests for paper-trading simulation."""

    def test_initial_state(self):
        simulator = TradeSimulator(
            initial_capital=10_000.0,
            transaction_cost_rate=0.001,
        )

        summary = simulator.portfolio_summary()

        assert summary["initial_capital"] == pytest.approx(10_000.0)
        assert summary["cash"] == pytest.approx(10_000.0)
        assert summary["total_pnl"] == pytest.approx(0.0)

    def test_buy_order(self):
        simulator = TradeSimulator(
            initial_capital=10_000.0,
            transaction_cost_rate=0.001,
        )

        result = simulator.execute_order(
            security="TEST",
            side="BUY",
            quantity=10,
            price=100,
        )

        assert result["side"] == "BUY"
        assert result["quantity"] == pytest.approx(10.0)
        assert result["execution_price"] == pytest.approx(100.0)
        assert result["gross_value"] == pytest.approx(1000.0)

        assert simulator.positions["TEST"].quantity == pytest.approx(10.0)

    def test_sell_order(self):
        simulator = TradeSimulator(
            initial_capital=10_000.0,
            transaction_cost_rate=0.001,
        )

        simulator.execute_order(
            security="TEST",
            side="BUY",
            quantity=10,
            price=100,
        )

        result = simulator.execute_order(
            security="TEST",
            side="SELL",
            quantity=10,
            price=110,
        )

        assert result["side"] == "SELL"
        assert result["execution_price"] == pytest.approx(110.0)
        assert result["pnl"] == pytest.approx(98.9)

    def test_transaction_cost_is_applied(self):
        simulator = TradeSimulator(
            initial_capital=10_000.0,
            transaction_cost_rate=0.001,
        )

        result = simulator.execute_order(
            security="TEST",
            side="BUY",
            quantity=10,
            price=100,
        )

        assert result["transaction_cost"] == pytest.approx(1.0)

    def test_cash_decreases_after_buy(self):
        simulator = TradeSimulator(
            initial_capital=10_000.0,
            transaction_cost_rate=0.001,
        )

        simulator.execute_order(
            security="TEST",
            side="BUY",
            quantity=10,
            price=100,
        )

        summary = simulator.portfolio_summary()

        assert summary["cash"] == pytest.approx(8_999.0)

    def test_cash_increases_after_sell(self):
        simulator = TradeSimulator(
            initial_capital=10_000.0,
            transaction_cost_rate=0.001,
        )

        simulator.execute_order(
            security="TEST",
            side="BUY",
            quantity=10,
            price=100,
        )

        simulator.execute_order(
            security="TEST",
            side="SELL",
            quantity=10,
            price=110,
        )

        summary = simulator.portfolio_summary()

        assert summary["cash"] == pytest.approx(10_097.9)

    def test_position_average_price(self):
        simulator = TradeSimulator(
            initial_capital=20_000.0,
            transaction_cost_rate=0.0,
        )

        simulator.execute_order(
            security="TEST",
            side="BUY",
            quantity=10,
            price=100,
        )

        simulator.execute_order(
            security="TEST",
            side="BUY",
            quantity=10,
            price=120,
        )

        position = simulator.positions["TEST"]

        assert position.quantity == pytest.approx(20.0)
        assert position.average_price == pytest.approx(110.0)

    def test_position_is_closed_after_full_sell(self):
        simulator = TradeSimulator(
            initial_capital=10_000.0,
            transaction_cost_rate=0.0,
        )

        simulator.execute_order(
            security="TEST",
            side="BUY",
            quantity=10,
            price=100,
        )

        simulator.execute_order(
            security="TEST",
            side="SELL",
            quantity=10,
            price=110,
        )

        position = simulator.positions["TEST"]

        assert position.quantity == pytest.approx(0.0)

    def test_invalid_side_raises_error(self):
        simulator = TradeSimulator(10_000.0)

        with pytest.raises(ValueError):
            simulator.execute_order(
                security="TEST",
                side="INVALID",
                quantity=10,
                price=100,
            )

    def test_invalid_quantity_raises_error(self):
        simulator = TradeSimulator(10_000.0)

        with pytest.raises(ValueError):
            simulator.execute_order(
                security="TEST",
                side="BUY",
                quantity=0,
                price=100,
            )

    def test_invalid_price_raises_error(self):
        simulator = TradeSimulator(10_000.0)

        with pytest.raises(ValueError):
            simulator.execute_order(
                security="TEST",
                side="BUY",
                quantity=10,
                price=0,
            )

    def test_trade_history(self):
        simulator = TradeSimulator(
            initial_capital=10_000.0,
            transaction_cost_rate=0.001,
        )

        simulator.execute_order(
            security="TEST",
            side="BUY",
            quantity=10,
            price=100,
        )

        simulator.execute_order(
            security="TEST",
            side="SELL",
            quantity=10,
            price=110,
        )

        history = simulator.trade_history()

        assert len(history) == 2
        assert "side" in history.columns
        assert "quantity" in history.columns
        assert "execution_price" in history.columns
        assert "transaction_cost" in history.columns
        assert "pnl" in history.columns


# ============================================================
# BACKTEST ENGINE TESTS
# ============================================================


class TestBacktestEngine:
    """Tests for the complete backtesting engine."""

    def test_run_backtest_returns_result(self, historical_data):
        result = run_backtest(
            strategy="moving_average",
            security="TEST",
            historical_data=historical_data,
            initial_capital=10_000.0,
            strategy_parameters={
                "short_window": 3,
                "long_window": 7,
            },
        )

        assert isinstance(result, dict)

    def test_backtest_contains_required_metrics(self, historical_data):
        result = run_backtest(
            strategy="moving_average",
            security="TEST",
            historical_data=historical_data,
            initial_capital=10_000.0,
            strategy_parameters={
                "short_window": 3,
                "long_window": 7,
            },
        )

        required_metrics = {
            "total_return",
            "total_pnl",
            "volatility",
            "sharpe_ratio",
            "max_drawdown",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
        }

        assert required_metrics.issubset(result.keys())

    def test_backtest_trade_output(self, historical_data):
        result = run_backtest(
            strategy="moving_average",
            security="TEST",
            historical_data=historical_data,
            initial_capital=10_000.0,
            strategy_parameters={
                "short_window": 3,
                "long_window": 7,
            },
        )

        assert "trades" in result
        assert isinstance(result["trades"], pd.DataFrame)

    def test_backtest_capital_is_positive(self, historical_data):
        result = run_backtest(
            strategy="moving_average",
            security="TEST",
            historical_data=historical_data,
            initial_capital=10_000.0,
            strategy_parameters={
                "short_window": 3,
                "long_window": 7,
            },
        )

        assert result["initial_capital"] == pytest.approx(10_000.0)

    def test_backtest_metrics_are_numeric(self, historical_data):
        result = run_backtest(
            strategy="momentum",
            security="TEST",
            historical_data=historical_data,
            initial_capital=10_000.0,
            strategy_parameters={
                "lookback": 3,
            },
        )

        metrics = [
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

        for metric in metrics:
            assert metric in result
            assert isinstance(
                result[metric],
                (int, float, np.integer, np.floating),
            )

    def test_backtest_trade_count_matches_output(self, historical_data):
        result = run_backtest(
            strategy="moving_average",
            security="TEST",
            historical_data=historical_data,
            initial_capital=10_000.0,
            strategy_parameters={
                "short_window": 3,
                "long_window": 7,
            },
        )

        assert result["total_trades"] == len(result["trades"])

    def test_backtest_win_loss_consistency(self, historical_data):
        result = run_backtest(
            strategy="momentum",
            security="TEST",
            historical_data=historical_data,
            initial_capital=10_000.0,
            strategy_parameters={
                "lookback": 3,
            },
        )

        assert (
            result["winning_trades"] + result["losing_trades"]
            <= result["total_trades"]
        )

    def test_backtest_win_rate_range(self, historical_data):
        result = run_backtest(
            strategy="momentum",
            security="TEST",
            historical_data=historical_data,
            initial_capital=10_000.0,
            strategy_parameters={
                "lookback": 3,
            },
        )

        assert 0.0 <= result["win_rate"] <= 100.0

    def test_backtest_with_mean_reversion(self, historical_data):
        result = run_backtest(
            strategy="mean_reversion",
            security="TEST",
            historical_data=historical_data,
            initial_capital=10_000.0,
            strategy_parameters={
                "window": 5,
                "threshold": 0.02,
            },
        )

        assert isinstance(result, dict)
        assert "total_pnl" in result
        assert "trades" in result

    def test_invalid_strategy_fails_backtest(self, historical_data):
        with pytest.raises(ValueError):
            run_backtest(
                strategy="invalid_strategy",
                security="TEST",
                historical_data=historical_data,
                initial_capital=10_000.0,
            )

    def test_invalid_initial_capital(self, historical_data):
        with pytest.raises(ValueError):
            run_backtest(
                strategy="momentum",
                security="TEST",
                historical_data=historical_data,
                initial_capital=0.0,
                strategy_parameters={
                    "lookback": 3,
                },
            )


# ============================================================
# END-TO-END TEST
# ============================================================


def test_complete_backtesting_flow(historical_data):
    """
    Verify the complete QuantDB quantitative research flow:

    Historical Data
        ↓
    Strategy
        ↓
    Signals
        ↓
    Simulated Orders
        ↓
    Simulated Trades
        ↓
    Portfolio
        ↓
    P&L
        ↓
    Risk Metrics
        ↓
    Backtest Result
    """

    result = run_backtest(
        strategy="moving_average",
        security="TEST",
        historical_data=historical_data,
        initial_capital=10_000.0,
        strategy_parameters={
            "short_window": 3,
            "long_window": 7,
        },
    )

    assert isinstance(result, dict)

    # Performance metrics
    assert "total_return" in result
    assert "total_pnl" in result

    # Risk metrics
    assert "volatility" in result
    assert "sharpe_ratio" in result
    assert "max_drawdown" in result

    # Trading statistics
    assert "total_trades" in result
    assert "winning_trades" in result
    assert "losing_trades" in result
    assert "win_rate" in result

    # Trade-level results
    assert "trades" in result
    assert isinstance(result["trades"], pd.DataFrame)

    # Basic sanity checks
    assert result["initial_capital"] == pytest.approx(10_000.0)
    assert result["total_trades"] >= 0
    assert result["winning_trades"] >= 0
    assert result["losing_trades"] >= 0
    assert 0 <= result["win_rate"] <= 100