"""
QuantDB - Paper Trading Simulator

Provides a reusable simulation-only execution engine for backtesting.

Supported:
- BUY / SELL execution
- Transaction costs
- Cash management
- Position tracking
- Realized P&L
- Unrealized P&L
- Trade history

No real-money execution is performed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import pandas as pd


@dataclass
class Position:
    """Represents a simulated security position."""

    quantity: float = 0.0
    average_price: float = 0.0
    realized_pnl: float = 0.0


class TradeSimulator:
    """
    Paper-trading simulator for historical/backtest execution.

    Parameters
    ----------
    initial_capital:
        Starting simulated cash.
    transaction_cost_rate:
        Transaction cost as a fraction of trade value.
        Example: 0.001 = 0.1%.
    """

    def __init__(
        self,
        initial_capital: float,
        transaction_cost_rate: float = 0.0,
    ) -> None:

        if initial_capital < 0:
            raise ValueError("initial_capital cannot be negative.")

        if transaction_cost_rate < 0:
            raise ValueError("transaction_cost_rate cannot be negative.")

        self.initial_capital = float(initial_capital)
        self.cash = float(initial_capital)
        self.transaction_cost_rate = float(transaction_cost_rate)

        self.positions: Dict[str, Position] = {}
        self.trades = []

    # ------------------------------------------------------------------
    # Position helpers
    # ------------------------------------------------------------------

    def get_position(self, security: str) -> Position:
        """Return the current position for a security."""

        if security not in self.positions:
            self.positions[security] = Position()

        return self.positions[security]

    def get_quantity(self, security: str) -> float:
        """Return current quantity held."""

        return self.get_position(security).quantity

    # ------------------------------------------------------------------
    # Order execution
    # ------------------------------------------------------------------

    def execute_order(
        self,
        security: str,
        side: str,
        quantity: float,
        price: float,
        timestamp=None,
    ) -> dict:

        if not security:
            raise ValueError("security is required.")

        side = str(side).upper().strip()

        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL.")

        if quantity <= 0:
            raise ValueError("quantity must be greater than zero.")

        if price <= 0:
            raise ValueError("price must be greater than zero.")

        quantity = float(quantity)
        price = float(price)

        gross_value = quantity * price
        transaction_cost = gross_value * self.transaction_cost_rate

        position = self.get_position(security)

        realized_pnl = 0.0

        # --------------------------------------------------------------
        # BUY
        # --------------------------------------------------------------

        if side == "BUY":

            total_cash_required = gross_value + transaction_cost

            if total_cash_required > self.cash + 1e-12:
                raise ValueError(
                    "Insufficient cash for BUY order."
                )

            old_quantity = position.quantity
            old_average_price = position.average_price

            new_quantity = old_quantity + quantity

            if new_quantity > 0:
                position.average_price = (
                    (
                        old_quantity * old_average_price
                    )
                    + (quantity * price)
                ) / new_quantity

            position.quantity = new_quantity

            self.cash -= total_cash_required

            trade_pnl = 0.0

            reason = "BUY"

        # --------------------------------------------------------------
        # SELL
        # --------------------------------------------------------------

        else:

            if quantity > position.quantity + 1e-12:
                raise ValueError(
                    "Insufficient position quantity for SELL order."
                )

            realized_pnl = (
                quantity
                * (price - position.average_price)
            )

            position.realized_pnl += realized_pnl

            self.cash += gross_value - transaction_cost

            position.quantity -= quantity

            # Avoid tiny floating-point residuals.
            if abs(position.quantity) < 1e-12:
                position.quantity = 0.0
                position.average_price = 0.0

            trade_pnl = realized_pnl - transaction_cost

            reason = "SELL"

        trade = {
            "timestamp": timestamp,
            "security": security,
            "side": side,
            "quantity": quantity,
            "execution_price": price,
            "gross_value": gross_value,
            "transaction_cost": transaction_cost,
            "pnl": trade_pnl,
            "reason": reason,
        }

        self.trades.append(trade)

        return trade

    # ------------------------------------------------------------------
    # Portfolio valuation
    # ------------------------------------------------------------------

    def market_value(
        self,
        prices: Optional[Dict[str, float]] = None,
    ) -> float:
        """Calculate current market value of all open positions."""

        if not prices:
            return 0.0

        value = 0.0

        for security, position in self.positions.items():

            price = prices.get(security)

            if price is None:
                continue

            value += position.quantity * float(price)

        return value

    def unrealized_pnl(
        self,
        prices: Optional[Dict[str, float]] = None,
    ) -> float:
        """Calculate unrealized P&L for open positions."""

        if not prices:
            return 0.0

        pnl = 0.0

        for security, position in self.positions.items():

            price = prices.get(security)

            if price is None or position.quantity == 0:
                continue

            pnl += (
                position.quantity
                * (float(price) - position.average_price)
            )

        return pnl

    def total_realized_pnl(self) -> float:
        """Return total realized P&L."""

        return sum(
            position.realized_pnl
            for position in self.positions.values()
        )

    def total_pnl(
        self,
        prices: Optional[Dict[str, float]] = None,
    ) -> float:
        """Return realized + unrealized P&L."""

        return (
            self.total_realized_pnl()
            + self.unrealized_pnl(prices)
        )

    def total_equity(
        self,
        prices: Optional[Dict[str, float]] = None,
    ) -> float:
        """Return current simulated portfolio equity."""

        return self.cash + self.market_value(prices)

    # ------------------------------------------------------------------
    # Trade history
    # ------------------------------------------------------------------

    def trade_history(self) -> pd.DataFrame:
        """Return executed trades as a DataFrame."""

        columns = [
            "timestamp",
            "security",
            "side",
            "quantity",
            "execution_price",
            "gross_value",
            "transaction_cost",
            "pnl",
            "reason",
        ]

        if not self.trades:
            return pd.DataFrame(columns=columns)

        return pd.DataFrame(self.trades, columns=columns)

    # ------------------------------------------------------------------
    # Portfolio summary
    # ------------------------------------------------------------------

    def portfolio_summary(
        self,
        prices: Optional[Dict[str, float]] = None,
    ) -> dict:
        """Return a complete simulation summary."""

        market_value = self.market_value(prices)
        unrealized = self.unrealized_pnl(prices)
        realized = self.total_realized_pnl()
        equity = self.cash + market_value

        total_pnl = realized + unrealized

        return {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "market_value": market_value,
            "total_equity": equity,
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
            "total_pnl": total_pnl,
            "return_percentage": (
                (equity - self.initial_capital)
                / self.initial_capital
                * 100
                if self.initial_capital > 0
                else 0.0
            ),
            "number_of_trades": len(self.trades),
        }


# ----------------------------------------------------------------------
# Convenience function
# ----------------------------------------------------------------------

def simulate_trades(
    orders: Iterable[dict],
    initial_capital: float,
    transaction_cost_rate: float = 0.0,
) -> tuple[TradeSimulator, pd.DataFrame]:
    """
    Execute a collection of simulated orders.

    Each order should contain:

        security
        side
        quantity
        price

    Optional:
        timestamp

    Returns
    -------
    simulator:
        Completed TradeSimulator instance.

    trades:
        Executed trades DataFrame.
    """

    simulator = TradeSimulator(
        initial_capital=initial_capital,
        transaction_cost_rate=transaction_cost_rate,
    )

    for order in orders:

        simulator.execute_order(
            security=order["security"],
            side=order["side"],
            quantity=order["quantity"],
            price=order["price"],
            timestamp=order.get("timestamp"),
        )

    return simulator, simulator.trade_history()