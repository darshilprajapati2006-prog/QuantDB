"""
Unit tests for QuantDB analytics modules.

Covers:
- Returns analysis
- Risk analysis
- Performance analysis
- Market microstructure analysis

Run:
    python -m pytest tests/test_analytics.py -v
"""

import numpy as np
import pandas as pd
import pytest

from src.analytics.returns import (
    simple_return,
    log_return,
    cumulative_return,
    cumulative_return_from_returns,
    total_return as price_total_return,
    return_summary,
)

from src.analytics.risk import (
    volatility,
    sharpe_ratio,
    maximum_drawdown,
    risk_summary,
)

from src.analytics.performance import (
    total_return,
    total_pnl,
    winning_trades,
    losing_trades,
    win_rate,
    portfolio_performance,
    performance_summary,
)

from src.analytics.microstructure import (
    bid_ask_spread,
    market_depth,
    order_book_imbalance,
    microstructure_summary,
)


# ============================================================
# RETURNS TESTS
# ============================================================

class TestReturns:

    def test_simple_return(self):
        prices = pd.Series([100, 110, 105, 120])

        result = simple_return(prices)

        assert np.isnan(result.iloc[0])
        assert result.iloc[1] == pytest.approx(0.10)
        assert result.iloc[2] == pytest.approx(-1 / 22)
        assert result.iloc[3] == pytest.approx(0.1428571)

    def test_log_return(self):
        prices = pd.Series([100, 110])

        result = log_return(prices)

        assert np.isnan(result.iloc[0])
        assert result.iloc[1] == pytest.approx(np.log(1.10))

    def test_cumulative_return(self):
        prices = pd.Series([100, 110, 120])

        result = cumulative_return(prices)

        assert result.iloc[0] == pytest.approx(0.0)
        assert result.iloc[1] == pytest.approx(0.10)
        assert result.iloc[2] == pytest.approx(0.20)

    def test_cumulative_return_from_returns(self):
        returns = pd.Series([0.10, 0.05, -0.02])

        result = cumulative_return_from_returns(returns)

        expected_final = (1.10 * 1.05 * 0.98) - 1

        assert result.iloc[-1] == pytest.approx(expected_final)

    def test_price_total_return(self):
        prices = pd.Series([100, 110, 120])

        result = price_total_return(prices)

        assert result == pytest.approx(0.20)

    def test_return_summary(self):
        prices = pd.Series([100, 110, 120])

        result = return_summary(prices)

        assert result["initial_price"] == pytest.approx(100.0)
        assert result["final_price"] == pytest.approx(120.0)
        assert result["total_return"] == pytest.approx(0.20)
        assert result["number_of_observations"] == 3

    def test_invalid_price(self):
        prices = pd.Series([100, -10, 120])

        with pytest.raises(ValueError):
            simple_return(prices)

    def test_empty_price_series(self):
        prices = pd.Series(dtype=float)

        result = return_summary(prices)

        assert result["initial_price"] is None
        assert result["final_price"] is None
        assert result["total_return"] == 0.0
        assert result["number_of_observations"] == 0


# ============================================================
# RISK TESTS
# ============================================================

class TestRisk:

    def test_volatility(self):
        returns = pd.Series([0.01, 0.02, -0.01, 0.03])

        result = volatility(
            returns,
            annualize=False,
        )

        expected = returns.std(ddof=1)

        assert result == pytest.approx(expected)

    def test_annualized_volatility(self):
        returns = pd.Series([0.01, 0.02, -0.01, 0.03])

        result = volatility(
            returns,
            annualize=True,
            periods_per_year=252,
        )

        expected = returns.std(ddof=1) * np.sqrt(252)

        assert result == pytest.approx(expected)

    def test_sharpe_ratio(self):
        returns = pd.Series([0.01, 0.02, 0.015, 0.025])

        result = sharpe_ratio(
            returns,
            risk_free_rate=0.0,
            annualize=False,
        )

        expected = returns.mean() / returns.std(ddof=1)

        assert result == pytest.approx(expected)

    def test_maximum_drawdown(self):
        returns = pd.Series([0.10, 0.05, -0.20, 0.10])

        result = maximum_drawdown(returns)

        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        expected = (cumulative / peak - 1).min()

        assert result == pytest.approx(expected)

    def test_empty_risk_series(self):
        returns = pd.Series(dtype=float)

        assert volatility(returns) == 0.0
        assert sharpe_ratio(returns) == 0.0
        assert maximum_drawdown(returns) == 0.0

    def test_risk_summary(self):
        returns = pd.Series([0.10, -0.05, 0.02, 0.08])

        result = risk_summary(
            returns,
            risk_free_rate=0.0,
            periods_per_year=252,
        )

        assert "volatility" in result
        assert "sharpe_ratio" in result
        assert "maximum_drawdown" in result

        assert result["volatility"] >= 0
        assert isinstance(result["sharpe_ratio"], float)
        assert result["maximum_drawdown"] <= 0


# ============================================================
# PERFORMANCE TESTS
# ============================================================

class TestPerformance:

    @pytest.fixture
    def trades(self):
        return pd.DataFrame(
            {
                "pnl": [100.0, -50.0, 200.0, -25.0, 75.0]
            }
        )

    def test_total_return(self):
        returns = pd.Series([0.10, 0.05, -0.02])

        result = total_return(returns)

        expected = (1.10 * 1.05 * 0.98) - 1

        assert result == pytest.approx(expected)

    def test_total_pnl(self, trades):
        result = total_pnl(trades)

        assert result == pytest.approx(300.0)

    def test_winning_trades(self, trades):
        result = winning_trades(trades)

        assert result == 3

    def test_losing_trades(self, trades):
        result = losing_trades(trades)

        assert result == 2

    def test_win_rate(self, trades):
        result = win_rate(trades)

        assert result == pytest.approx(60.0)

    def test_portfolio_performance(self):
        equity = pd.Series([10000, 10100, 10050, 10325])

        result = portfolio_performance(equity)

        assert result["initial_equity"] == pytest.approx(10000.0)
        assert result["final_equity"] == pytest.approx(10325.0)
        assert result["total_pnl"] == pytest.approx(325.0)
        assert result["total_return"] == pytest.approx(3.25)

    def test_performance_summary(self, trades):
        returns = pd.Series([0.10, 0.05, -0.02])
        equity = pd.Series([10000, 10100, 10325])

        result = performance_summary(
            returns=returns,
            trades=trades,
            equity=equity,
        )

        assert result["total_return"] == pytest.approx(
            (1.10 * 1.05 * 0.98) - 1
        )

        assert result["total_pnl"] == pytest.approx(300.0)
        assert result["winning_trades"] == 3
        assert result["losing_trades"] == 2
        assert result["win_rate"] == pytest.approx(60.0)

        assert "portfolio_performance" in result

        portfolio = result["portfolio_performance"]

        assert portfolio["initial_equity"] == pytest.approx(10000.0)
        assert portfolio["final_equity"] == pytest.approx(10325.0)

    def test_empty_trades(self):
        trades = pd.DataFrame({"pnl": []})

        assert total_pnl(trades) == 0.0
        assert winning_trades(trades) == 0
        assert losing_trades(trades) == 0
        assert win_rate(trades) == 0.0

    def test_missing_pnl_column(self):
        trades = pd.DataFrame(
            {
                "profit": [100, 200]
            }
        )

        with pytest.raises(ValueError):
            total_pnl(trades)


# ============================================================
# MICROSTRUCTURE TESTS
# ============================================================

class TestMicrostructure:

    def test_bid_ask_spread(self):
        result = bid_ask_spread(100, 101)

        assert result == pytest.approx(1.0)

    def test_relative_bid_ask_spread(self):
        result = bid_ask_spread(
            100,
            101,
            relative=True,
        )

        expected = 1 / 100.5

        assert result == pytest.approx(expected)

    def test_market_depth(self):
        result = market_depth(
            bid_sizes=[100, 150, 200],
            ask_sizes=[120, 180, 100],
        )

        assert result["bid_depth"] == pytest.approx(450.0)
        assert result["ask_depth"] == pytest.approx(400.0)
        assert result["total_depth"] == pytest.approx(850.0)

    def test_order_book_imbalance(self):
        result = order_book_imbalance(
            bid_size=450,
            ask_size=400,
        )

        expected = (450 - 400) / (450 + 400)

        assert result == pytest.approx(expected)

    def test_zero_order_book_imbalance(self):
        result = order_book_imbalance(
            bid_size=0,
            ask_size=0,
        )

        assert result == 0.0

    def test_microstructure_summary(self):
        result = microstructure_summary(
            bid_price=100,
            ask_price=101,
            bid_size=450,
            ask_size=400,
        )

        assert result["bid_price"] == pytest.approx(100.0)
        assert result["ask_price"] == pytest.approx(101.0)
        assert result["bid_ask_spread"] == pytest.approx(1.0)

        assert result["bid_depth"] == pytest.approx(450.0)
        assert result["ask_depth"] == pytest.approx(400.0)
        assert result["total_depth"] == pytest.approx(850.0)

        expected_imbalance = (450 - 400) / (450 + 400)

        assert result["order_book_imbalance"] == pytest.approx(
            expected_imbalance
        )

    def test_invalid_bid_ask_prices(self):
        with pytest.raises(ValueError):
            bid_ask_spread(101, 100)

    def test_negative_bid_size(self):
        with pytest.raises(ValueError):
            market_depth(
                bid_sizes=[100, -50],
                ask_sizes=[100],
            )


# ============================================================
# CROSS-MODULE INTEGRATION TEST
# ============================================================

def test_complete_analytics_flow():
    """
    Basic integration-style test showing how
    QuantDB analytics modules work together.
    """

    prices = pd.Series(
        [100, 105, 102, 110, 115]
    )

    # Return analysis
    returns = simple_return(prices).dropna()

    # Performance
    total_ret = total_return(returns)

    # Risk
    vol = volatility(
        returns,
        annualize=False,
    )

    sharpe = sharpe_ratio(
        returns,
        annualize=False,
    )

    drawdown = maximum_drawdown(returns)

    assert isinstance(total_ret, float)
    assert isinstance(vol, float)
    assert isinstance(sharpe, float)
    assert isinstance(drawdown, float)

    assert total_ret > 0
    assert vol >= 0
    assert drawdown <= 0