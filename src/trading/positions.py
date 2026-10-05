"""
QuantDB - Position Management

Responsibilities:
- Create and manage portfolio positions
- Process BUY and SELL trades
- Maintain quantity and average price
- Calculate realized P&L
- Calculate unrealized P&L
- Provide position summaries
- Validate position inputs

Simulation only - no real-money trading.
"""

from datetime import datetime
from typing import Dict, Optional


class PositionManager:
    """Manage simulated portfolio positions."""

    def __init__(self):
        # Key: (portfolio_id, security_id)
        self.positions: Dict[tuple, dict] = {}

    # ============================================================
    # VALIDATION
    # ============================================================

    @staticmethod
    def _validate_trade(
        trade_side: str,
        quantity: float,
        execution_price: float
    ) -> None:
        """Validate trade information."""

        if trade_side not in {"BUY", "SELL"}:
            raise ValueError("trade_side must be BUY or SELL")

        if quantity <= 0:
            raise ValueError("quantity must be greater than 0")

        if execution_price <= 0:
            raise ValueError("execution_price must be greater than 0")

    @staticmethod
    def _validate_ids(
        portfolio_id: int,
        security_id: int
    ) -> None:
        """Validate portfolio and security IDs."""

        if portfolio_id <= 0:
            raise ValueError("portfolio_id must be positive")

        if security_id <= 0:
            raise ValueError("security_id must be positive")

    # ============================================================
    # POSITION CREATION
    # ============================================================

    def _create_position(
        self,
        portfolio_id: int,
        security_id: int
    ) -> dict:
        """Create an empty position."""

        position = {
            "position_id": None,
            "portfolio_id": portfolio_id,
            "security_id": security_id,
            "quantity": 0.0,
            "average_price": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "updated_at": datetime.now(),
        }

        self.positions[(portfolio_id, security_id)] = position

        return position

    def get_position(
        self,
        portfolio_id: int,
        security_id: int
    ) -> Optional[dict]:
        """Return a position if it exists."""

        return self.positions.get((portfolio_id, security_id))

    # ============================================================
    # BUY
    # ============================================================

    def _process_buy(
        self,
        position: dict,
        quantity: float,
        execution_price: float
    ) -> dict:
        """
        Process BUY trade.

        New average price:

        ((old_qty * old_avg_price) +
         (new_qty * new_price))
        /
        (old_qty + new_qty)
        """

        old_quantity = position["quantity"]
        old_average_price = position["average_price"]

        new_quantity = old_quantity + quantity

        if new_quantity > 0:
            total_cost = (
                old_quantity * old_average_price
                + quantity * execution_price
            )

            new_average_price = total_cost / new_quantity
        else:
            new_average_price = 0.0

        position["quantity"] = new_quantity
        position["average_price"] = new_average_price
        position["updated_at"] = datetime.now()

        # Unrealized P&L will be calculated when market price is available.
        position["unrealized_pnl"] = 0.0

        return position

    # ============================================================
    # SELL
    # ============================================================

    def _process_sell(
        self,
        position: dict,
        quantity: float,
        execution_price: float
    ) -> dict:
        """
        Process SELL trade.

        Realized P&L:

        (execution_price - average_price) * quantity
        """

        current_quantity = position["quantity"]
        average_price = position["average_price"]

        if quantity > current_quantity:
            raise ValueError(
                "Cannot sell more quantity than current position"
            )

        realized_pnl = (
            execution_price - average_price
        ) * quantity

        position["realized_pnl"] += realized_pnl
        position["quantity"] -= quantity

        # Position completely closed.
        if position["quantity"] == 0:
            position["average_price"] = 0.0
            position["unrealized_pnl"] = 0.0

        position["updated_at"] = datetime.now()

        return position

    # ============================================================
    # PROCESS TRADE
    # ============================================================

    def process_trade(
        self,
        portfolio_id: int,
        security_id: int,
        trade_side: str,
        quantity: float,
        execution_price: float
    ) -> dict:
        """
        Apply a BUY or SELL trade to a portfolio position.
        """

        self._validate_ids(portfolio_id, security_id)

        trade_side = trade_side.upper()

        self._validate_trade(
            trade_side,
            quantity,
            execution_price
        )

        position = self.get_position(
            portfolio_id,
            security_id
        )

        if position is None:
            position = self._create_position(
                portfolio_id,
                security_id
            )

        if trade_side == "BUY":
            position = self._process_buy(
                position,
                quantity,
                execution_price
            )

        elif trade_side == "SELL":
            position = self._process_sell(
                position,
                quantity,
                execution_price
            )

        return position.copy()

    # ============================================================
    # UNREALIZED P&L
    # ============================================================

    def update_unrealized_pnl(
        self,
        portfolio_id: int,
        security_id: int,
        current_price: float
    ) -> dict:
        """
        Update unrealized P&L using current market price.

        Unrealized P&L:
        (current_price - average_price) * quantity
        """

        if current_price <= 0:
            raise ValueError(
                "current_price must be greater than 0"
            )

        position = self.get_position(
            portfolio_id,
            security_id
        )

        if position is None:
            raise ValueError(
                "Position does not exist"
            )

        position["unrealized_pnl"] = (
            current_price - position["average_price"]
        ) * position["quantity"]

        position["updated_at"] = datetime.now()

        return position.copy()

    # ============================================================
    # POSITION SUMMARY
    # ============================================================

    def get_position_summary(
        self,
        portfolio_id: int,
        security_id: int,
        current_price: Optional[float] = None
    ) -> dict:
        """Return a complete position summary."""

        position = self.get_position(
            portfolio_id,
            security_id
        )

        if position is None:
            raise ValueError(
                "Position does not exist"
            )

        if current_price is not None:
            self.update_unrealized_pnl(
                portfolio_id,
                security_id,
                current_price
            )

        total_pnl = (
            position["realized_pnl"]
            + position["unrealized_pnl"]
        )

        market_value = (
            position["quantity"] * current_price
            if current_price is not None
            else None
        )

        return {
            "portfolio_id": position["portfolio_id"],
            "security_id": position["security_id"],
            "quantity": position["quantity"],
            "average_price": position["average_price"],
            "realized_pnl": position["realized_pnl"],
            "unrealized_pnl": position["unrealized_pnl"],
            "total_pnl": total_pnl,
            "market_value": market_value,
            "updated_at": position["updated_at"],
        }

    # ============================================================
    # ALL POSITIONS
    # ============================================================

    def get_all_positions(
        self,
        portfolio_id: Optional[int] = None
    ) -> list:
        """Return all positions or positions for one portfolio."""

        positions = list(self.positions.values())

        if portfolio_id is not None:
            positions = [
                position
                for position in positions
                if position["portfolio_id"] == portfolio_id
            ]

        return [position.copy() for position in positions]

    # ============================================================
    # TOTAL PORTFOLIO P&L
    # ============================================================

    def get_total_pnl(
        self,
        portfolio_id: int
    ) -> float:
        """Calculate total realized + unrealized P&L."""

        positions = self.get_all_positions(portfolio_id)

        return sum(
            position["realized_pnl"]
            + position["unrealized_pnl"]
            for position in positions
        )


# =================================================================
# DEFAULT INSTANCE
# =================================================================

position_manager = PositionManager()


# =================================================================
# TEST / DEMO
# =================================================================

if __name__ == "__main__":

    print("=" * 65)
    print("QuantDB POSITION MANAGEMENT TEST")
    print("=" * 65)

    manager = PositionManager()

    portfolio_id = 1
    security_id = 1

    # ------------------------------------------------------------
    # 1. BUY 100 @ 100
    # ------------------------------------------------------------

    position = manager.process_trade(
        portfolio_id=portfolio_id,
        security_id=security_id,
        trade_side="BUY",
        quantity=100,
        execution_price=100.0,
    )

    print("\n1. AFTER BUY 100 @ 100")
    print(position)

    # ------------------------------------------------------------
    # 2. BUY 50 @ 110
    # ------------------------------------------------------------

    position = manager.process_trade(
        portfolio_id=portfolio_id,
        security_id=security_id,
        trade_side="BUY",
        quantity=50,
        execution_price=110.0,
    )

    print("\n2. AFTER BUY 50 @ 110")
    print(position)

    # Expected average price:
    # (100*100 + 50*110) / 150 = 103.3333

    # ------------------------------------------------------------
    # 3. Update unrealized P&L
    # ------------------------------------------------------------

    position = manager.update_unrealized_pnl(
        portfolio_id=portfolio_id,
        security_id=security_id,
        current_price=120.0,
    )

    print("\n3. AFTER MARKET PRICE = 120")
    print(position)

    # Expected unrealized P&L:
    # (120 - 103.3333) * 150
    # = 2500 approximately

    # ------------------------------------------------------------
    # 4. SELL 50 @ 120
    # ------------------------------------------------------------

    position = manager.process_trade(
        portfolio_id=portfolio_id,
        security_id=security_id,
        trade_side="SELL",
        quantity=50,
        execution_price=120.0,
    )

    print("\n4. AFTER SELL 50 @ 120")
    print(position)

    # ------------------------------------------------------------
    # 5. Update remaining unrealized P&L
    # ------------------------------------------------------------

    position = manager.update_unrealized_pnl(
        portfolio_id=portfolio_id,
        security_id=security_id,
        current_price=125.0,
    )

    print("\n5. AFTER MARKET PRICE = 125")
    print(position)

    # ------------------------------------------------------------
    # 6. Position Summary
    # ------------------------------------------------------------

    summary = manager.get_position_summary(
        portfolio_id=portfolio_id,
        security_id=security_id,
        current_price=125.0,
    )

    print("\n6. POSITION SUMMARY")
    print(summary)

    # ------------------------------------------------------------
    # 7. Total Portfolio P&L
    # ------------------------------------------------------------

    total_pnl = manager.get_total_pnl(
        portfolio_id
    )

    print("\n7. TOTAL PORTFOLIO P&L")
    print(f"Total P&L: {total_pnl:.2f}")

    print("\n" + "=" * 65)
    print("POSITION TEST COMPLETED SUCCESSFULLY")
    print("=" * 65)