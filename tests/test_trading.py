import pytest

from src.trading.orders import (
    Order,
    create_order,
    validate_order,
    update_order_status,
    cancel_order,
    fill_order,
    reject_order,
    get_order_summary,
)

from src.trading.positions import PositionManager

from src.trading.portfolio import PortfolioManager


# ============================================================
# ORDER TESTS
# ============================================================

class TestOrder:

    def test_create_market_buy_order(self):
        order = create_order(
            user_id=1,
            security_id=101,
            side="BUY",
            order_type="MARKET",
            quantity=10,
        )

        assert isinstance(order, Order)
        assert order.user_id == 1
        assert order.security_id == 101
        assert order.side == "BUY"
        assert order.order_type == "MARKET"
        assert order.quantity == 10
        assert order.order_status == "PENDING"
        assert order.order_time is not None

    def test_create_limit_sell_order(self):
        order = create_order(
            user_id=1,
            security_id=101,
            side="SELL",
            order_type="LIMIT",
            quantity=5,
            order_price=100.50,
        )

        assert order.side == "SELL"
        assert order.order_type == "LIMIT"
        assert order.quantity == 5
        assert order.order_price == 100.50
        assert order.order_status == "PENDING"

    def test_invalid_user_id(self):
        with pytest.raises(ValueError):
            create_order(
                user_id=0,
                security_id=101,
                side="BUY",
                order_type="MARKET",
                quantity=10,
            )

    def test_invalid_security_id(self):
        with pytest.raises(ValueError):
            create_order(
                user_id=1,
                security_id=0,
                side="BUY",
                order_type="MARKET",
                quantity=10,
            )

    def test_invalid_side(self):
        with pytest.raises(ValueError):
            create_order(
                user_id=1,
                security_id=101,
                side="INVALID",
                order_type="MARKET",
                quantity=10,
            )

    def test_invalid_order_type(self):
        with pytest.raises(ValueError):
            create_order(
                user_id=1,
                security_id=101,
                side="BUY",
                order_type="INVALID",
                quantity=10,
            )

    def test_invalid_quantity(self):
        with pytest.raises(ValueError):
            create_order(
                user_id=1,
                security_id=101,
                side="BUY",
                order_type="MARKET",
                quantity=0,
            )

    def test_limit_order_requires_price(self):
        with pytest.raises(ValueError):
            create_order(
                user_id=1,
                security_id=101,
                side="BUY",
                order_type="LIMIT",
                quantity=10,
            )

    def test_limit_order_rejects_negative_price(self):
        with pytest.raises(ValueError):
            create_order(
                user_id=1,
                security_id=101,
                side="BUY",
                order_type="LIMIT",
                quantity=10,
                order_price=-100,
            )

    def test_market_order_with_valid_price(self):
        order = create_order(
            user_id=1,
            security_id=101,
            side="BUY",
            order_type="MARKET",
            quantity=10,
            order_price=100,
        )

        assert order.order_type == "MARKET"


# ============================================================
# ORDER STATUS TESTS
# ============================================================

class TestOrderStatus:

    def test_pending_to_open(self):
        order = create_order(
            1, 101, "BUY", "MARKET", 10
        )

        update_order_status(order, "OPEN")

        assert order.order_status == "OPEN"

    def test_open_to_filled(self):
        order = create_order(
            1, 101, "BUY", "MARKET", 10
        )

        update_order_status(order, "OPEN")
        fill_order(order, 100.0)

        assert order.order_status == "FILLED"

    def test_cancel_order(self):
        order = create_order(
            1, 101, "BUY", "MARKET", 10
        )

        cancel_order(order)

        assert order.order_status == "CANCELLED"

    def test_reject_order(self):
        order = create_order(
            1, 101, "BUY", "MARKET", 10
        )

        reject_order(order, "Insufficient funds")

        assert order.order_status == "REJECTED"

    def test_cannot_cancel_filled_order(self):
        order = create_order(
            1, 101, "BUY", "MARKET", 10
        )

        fill_order(order, 100.0)

        with pytest.raises(ValueError):
            cancel_order(order)

    def test_cannot_fill_cancelled_order(self):
        order = create_order(
            1, 101, "BUY", "MARKET", 10
        )

        cancel_order(order)

        with pytest.raises(ValueError):
            fill_order(order, 100.0)


# ============================================================
# LIMIT ORDER EXECUTION TESTS
# ============================================================

class TestLimitOrderExecution:

    def test_buy_limit_valid_execution(self):
        order = create_order(
            1,
            101,
            "BUY",
            "LIMIT",
            10,
            100.0,
        )

        fill_order(order, 99.0)

        assert order.order_status == "FILLED"

    def test_buy_limit_invalid_execution(self):
        order = create_order(
            1,
            101,
            "BUY",
            "LIMIT",
            10,
            100.0,
        )

        with pytest.raises(ValueError):
            fill_order(order, 101.0)

    def test_sell_limit_valid_execution(self):
        order = create_order(
            1,
            101,
            "SELL",
            "LIMIT",
            10,
            100.0,
        )

        fill_order(order, 101.0)

        assert order.order_status == "FILLED"

    def test_sell_limit_invalid_execution(self):
        order = create_order(
            1,
            101,
            "SELL",
            "LIMIT",
            10,
            100.0,
        )

        with pytest.raises(ValueError):
            fill_order(order, 99.0)


# ============================================================
# ORDER SUMMARY TESTS
# ============================================================

class TestOrderSummary:

    def test_order_to_dict(self):
        order = create_order(
            1,
            101,
            "BUY",
            "LIMIT",
            10,
            100.0,
        )

        data = order.to_dict()

        assert isinstance(data, dict)
        assert data["user_id"] == 1
        assert data["security_id"] == 101
        assert data["side"] == "BUY"
        assert data["order_type"] == "LIMIT"
        assert data["quantity"] == 10

    def test_get_order_summary(self):
        order = create_order(
            1,
            101,
            "BUY",
            "MARKET",
            10,
        )

        summary = get_order_summary(order)

        assert isinstance(summary, dict)
        assert summary["user_id"] == 1
        assert summary["security_id"] == 101
        assert summary["side"] == "BUY"
        assert summary["order_status"] == "PENDING"


# ============================================================
# POSITION MANAGER TESTS
# ============================================================

class TestPositionManager:

    def test_position_manager_initialization(self):
        manager = PositionManager()

        assert manager is not None

    def test_buy_position(self):
        manager = PositionManager()

        position = manager.process_trade(
            portfolio_id=1,
            security_id=101,
            trade_side="BUY",
            quantity=10,
            execution_price=100.0,
        )

        assert position is not None

        current = manager.get_position(1, 101)

        assert current is not None
        assert current["quantity"] == 10

    def test_sell_position(self):
        manager = PositionManager()

        manager.process_trade(
            portfolio_id=1,
            security_id=101,
            trade_side="BUY",
            quantity=10,
            execution_price=100.0,
        )

        position = manager.process_trade(
            portfolio_id=1,
            security_id=101,
            trade_side="SELL",
            quantity=5,
            execution_price=110.0,
        )

        assert position is not None

        current = manager.get_position(1, 101)

        assert current is not None
        assert current["quantity"] == 5

    def test_position_summary(self):
        manager = PositionManager()

        manager.process_trade(
            portfolio_id=1,
            security_id=101,
            trade_side="BUY",
            quantity=10,
            execution_price=100.0,
        )

        summary = manager.get_position_summary(1, 101)

        assert summary is not None

    def test_total_pnl_initially_zero(self):
        manager = PositionManager()

        total_pnl = manager.get_total_pnl(1)

        assert total_pnl == 0.0

    def test_invalid_trade_side(self):
        manager = PositionManager()

        with pytest.raises(ValueError):
            manager.process_trade(
                portfolio_id=1,
                security_id=101,
                trade_side="INVALID",
                quantity=10,
                execution_price=100.0,
            )


# ============================================================
# PORTFOLIO MANAGER TESTS
# ============================================================

class TestPortfolioManager:

    def test_portfolio_initialization(self):
        portfolio = PortfolioManager(           
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        assert portfolio.portfolio_id == 1
        assert portfolio.initial_capital == 10000.0
        assert portfolio.current_cash == 10000.0

    def test_deposit(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        result = portfolio.deposit(2000.0)

        assert result["amount"] == 2000.0
        assert result["current_cash"] == 12000.0

    def test_withdraw(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        result = portfolio.withdraw(2000.0)

        assert result["amount"] == 2000.0
        assert result["current_cash"] == 8000.0

    def test_invalid_deposit(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        with pytest.raises(ValueError):
            portfolio.deposit(0)

    def test_invalid_withdraw(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        with pytest.raises(ValueError):
            portfolio.withdraw(0)

    def test_insufficient_cash(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=1000.0,
        )

        with pytest.raises(ValueError):
            portfolio.withdraw(2000.0)

    def test_market_value_initially_zero(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        assert portfolio.get_market_value() == 0.0

    def test_total_equity(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        assert portfolio.get_total_equity() == 10000.0

    def test_total_pnl_initially_zero(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        assert portfolio.get_total_pnl() == 0.0

    def test_return_percentage_initially_zero(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        assert portfolio.get_return_percentage() == 0.0

    def test_empty_positions(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        assert portfolio.get_positions() == []

    def test_portfolio_summary(self):
        portfolio = PortfolioManager(
            portfolio_id=1,
            user_id=1,
            initial_capital=10000.0,
        )

        summary = portfolio.get_portfolio_summary()

        assert isinstance(summary, dict)
        assert summary["portfolio_id"] == 1
        assert summary["initial_capital"] == 10000.0
        assert summary["current_cash"] == 10000.0