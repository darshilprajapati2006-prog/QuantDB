"""
QuantDB - Portfolio Management Service

Responsibilities:
- Manage simulated portfolio cash
- Track portfolio positions
- Calculate market value
- Calculate realized and unrealized P&L
- Calculate total portfolio P&L
- Provide portfolio summaries

Simulation only. No real-money trading.
"""

from datetime import datetime
from typing import Dict, List, Optional


class PortfolioManager:
    """Manage a simulated trading portfolio."""

    def __init__(
        self,
        portfolio_id: int,
        user_id: int,
        initial_capital: float,
    ):
        if initial_capital < 0:
            raise ValueError("Initial capital cannot be negative.")

        self.portfolio_id = portfolio_id
        self.user_id = user_id

        self.initial_capital = float(initial_capital)
        self.current_cash = float(initial_capital)

        # security_id -> position information
        self.positions: Dict[int, Dict] = {}

        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    # ============================================================
    # CASH MANAGEMENT
    # ============================================================

    def deposit(self, amount: float) -> Dict:
        """Add cash to the simulated portfolio."""

        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")

        self.current_cash += float(amount)
        self.updated_at = datetime.now()

        return {
            "portfolio_id": self.portfolio_id,
            "amount": float(amount),
            "current_cash": self.current_cash,
        }

    def withdraw(self, amount: float) -> Dict:
        """Withdraw cash from the simulated portfolio."""

        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")

        if amount > self.current_cash:
            raise ValueError("Insufficient portfolio cash.")

        self.current_cash -= float(amount)
        self.updated_at = datetime.now()

        return {
            "portfolio_id": self.portfolio_id,
            "amount": float(amount),
            "current_cash": self.current_cash,
        }

    # ============================================================
    # POSITION MANAGEMENT
    # ============================================================

    def add_position(
        self,
        security_id: int,
        quantity: float,
        price: float,
        transaction_cost: float = 0.0,
    ) -> Dict:
        """
        Add a BUY position to the portfolio.

        Updates:
        - cash
        - quantity
        - average price
        - market value
        """

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        if price <= 0:
            raise ValueError("Price must be positive.")

        if transaction_cost < 0:
            raise ValueError("Transaction cost cannot be negative.")

        trade_value = quantity * price
        total_cost = trade_value + transaction_cost

        if total_cost > self.current_cash:
            raise ValueError("Insufficient cash for this position.")

        self.current_cash -= total_cost

        if security_id not in self.positions:
            self.positions[security_id] = {
                "security_id": security_id,
                "quantity": 0.0,
                "average_price": 0.0,
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "market_price": price,
                "market_value": 0.0,
            }

        position = self.positions[security_id]

        old_quantity = position["quantity"]
        old_average_price = position["average_price"]

        new_quantity = old_quantity + quantity

        if new_quantity > 0:
            new_average_price = (
                (old_quantity * old_average_price)
                + (quantity * price)
            ) / new_quantity
        else:
            new_average_price = 0.0

        position["quantity"] = new_quantity
        position["average_price"] = new_average_price
        position["market_price"] = price
        position["market_value"] = new_quantity * price

        self._update_unrealized_pnl(security_id)

        self.updated_at = datetime.now()

        return position.copy()

    def remove_position(
        self,
        security_id: int,
        quantity: float,
        price: float,
        transaction_cost: float = 0.0,
    ) -> Dict:
        """
        Sell an existing position.

        Updates:
        - cash
        - quantity
        - realized P&L
        - market value
        """

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        if price <= 0:
            raise ValueError("Price must be positive.")

        if transaction_cost < 0:
            raise ValueError("Transaction cost cannot be negative.")

        if security_id not in self.positions:
            raise ValueError("Position does not exist.")

        position = self.positions[security_id]

        if quantity > position["quantity"]:
            raise ValueError("Cannot sell more than current position.")

        proceeds = quantity * price
        net_proceeds = proceeds - transaction_cost

        realized_pnl = (
            (price - position["average_price"]) * quantity
            - transaction_cost
        )

        position["realized_pnl"] += realized_pnl
        position["quantity"] -= quantity
        position["market_price"] = price

        self.current_cash += net_proceeds

        if position["quantity"] == 0:
            position["average_price"] = 0.0
            position["unrealized_pnl"] = 0.0
            position["market_value"] = 0.0
        else:
            position["market_value"] = (
                position["quantity"] * price
            )
            self._update_unrealized_pnl(security_id)

        self.updated_at = datetime.now()

        return position.copy()

    # ============================================================
    # MARKET PRICE / P&L
    # ============================================================

    def update_market_price(
        self,
        security_id: int,
        market_price: float,
    ) -> Dict:
        """Update market price and unrealized P&L."""

        if market_price <= 0:
            raise ValueError("Market price must be positive.")

        if security_id not in self.positions:
            raise ValueError("Position does not exist.")

        position = self.positions[security_id]

        position["market_price"] = market_price
        position["market_value"] = (
            position["quantity"] * market_price
        )

        self._update_unrealized_pnl(security_id)

        self.updated_at = datetime.now()

        return position.copy()

    def _update_unrealized_pnl(self, security_id: int) -> None:
        """Calculate unrealized P&L for a position."""

        position = self.positions[security_id]

        position["unrealized_pnl"] = (
            position["market_price"]
            - position["average_price"]
        ) * position["quantity"]

    # ============================================================
    # PORTFOLIO CALCULATIONS
    # ============================================================

    def get_market_value(self) -> float:
        """Return total market value of all positions."""

        return sum(
            position["market_value"]
            for position in self.positions.values()
        )

    def get_realized_pnl(self) -> float:
        """Return total realized P&L."""

        return sum(
            position["realized_pnl"]
            for position in self.positions.values()
        )

    def get_unrealized_pnl(self) -> float:
        """Return total unrealized P&L."""

        return sum(
            position["unrealized_pnl"]
            for position in self.positions.values()
        )

    def get_total_pnl(self) -> float:
        """Return realized + unrealized P&L."""

        return (
            self.get_realized_pnl()
            + self.get_unrealized_pnl()
        )

    def get_total_equity(self) -> float:
        """
        Total portfolio equity.

        Equity = Cash + Market Value of Positions
        """

        return self.current_cash + self.get_market_value()

    def get_return_percentage(self) -> float:
        """Calculate portfolio return percentage."""

        if self.initial_capital == 0:
            return 0.0

        return (
            self.get_total_pnl()
            / self.initial_capital
        ) * 100

    # ============================================================
    # POSITION / PORTFOLIO SUMMARY
    # ============================================================

    def get_position(
        self,
        security_id: int,
    ) -> Optional[Dict]:
        """Return a single position."""

        position = self.positions.get(security_id)

        if position is None:
            return None

        return position.copy()

    def get_positions(self) -> List[Dict]:
        """Return all portfolio positions."""

        return [
            position.copy()
            for position in self.positions.values()
        ]

    def get_portfolio_summary(self) -> Dict:
        """Return complete portfolio summary."""

        return {
            "portfolio_id": self.portfolio_id,
            "user_id": self.user_id,
            "initial_capital": round(self.initial_capital, 2),
            "current_cash": round(self.current_cash, 2),
            "market_value": round(self.get_market_value(), 2),
            "total_equity": round(self.get_total_equity(), 2),
            "realized_pnl": round(self.get_realized_pnl(), 2),
            "unrealized_pnl": round(self.get_unrealized_pnl(), 2),
            "total_pnl": round(self.get_total_pnl(), 2),
            "return_percentage": round(
                self.get_return_percentage(),
                2,
            ),
            "number_of_positions": len(self.positions),
            "updated_at": self.updated_at,
        }


# ================================================================
# TEST / DEMONSTRATION
# ================================================================

if __name__ == "__main__":

    print("=" * 65)
    print("QUANTDB PORTFOLIO MANAGEMENT TEST")
    print("=" * 65)

    # ------------------------------------------------------------
    # 1. CREATE PORTFOLIO
    # ------------------------------------------------------------

    portfolio = PortfolioManager(
        portfolio_id=1,
        user_id=1,
        initial_capital=100000.0,
    )

    print("\n1. INITIAL PORTFOLIO")
    print(portfolio.get_portfolio_summary())

    # ------------------------------------------------------------
    # 2. BUY SECURITY
    # ------------------------------------------------------------

    portfolio.add_position(
        security_id=1,
        quantity=100,
        price=100.0,
        transaction_cost=10.0,
    )

    print("\n2. AFTER BUY")
    print(portfolio.get_position(1))

    # ------------------------------------------------------------
    # 3. UPDATE MARKET PRICE
    # ------------------------------------------------------------

    portfolio.update_market_price(
        security_id=1,
        market_price=110.0,
    )

    print("\n3. AFTER MARKET PRICE UPDATE")
    print(portfolio.get_position(1))

    # ------------------------------------------------------------
    # 4. SELL PART OF POSITION
    # ------------------------------------------------------------

    portfolio.remove_position(
        security_id=1,
        quantity=40,
        price=115.0,
        transaction_cost=5.0,
    )

    print("\n4. AFTER PARTIAL SELL")
    print(portfolio.get_position(1))

    # ------------------------------------------------------------
    # 5. FINAL MARKET PRICE
    # ------------------------------------------------------------

    portfolio.update_market_price(
        security_id=1,
        market_price=120.0,
    )

    # ------------------------------------------------------------
    # 6. FINAL PORTFOLIO SUMMARY
    # ------------------------------------------------------------

    print("\n5. FINAL PORTFOLIO SUMMARY")
    print("-" * 65)

    summary = portfolio.get_portfolio_summary()

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 65)
    print("PORTFOLIO TEST COMPLETED SUCCESSFULLY")
    print("=" * 65)