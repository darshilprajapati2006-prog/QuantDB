"""
QuantDB - Simulated Trade Management

Handles:
- Simulated trade execution
- Filled order conversion into trade
- Execution price validation
- Transaction cost calculation
- Trade records
- Trade summaries

This module is for paper/simulated trading only.
No real-money trading or broker API is used.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any

from .orders import Order


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_TRANSACTION_COST_RATE = 0.001


# ============================================================
# TRADE DATA MODEL
# ============================================================

@dataclass
class Trade:
    """
    Represents a simulated executed trade.
    """

    order_id: int
    security_id: int
    trade_side: str
    quantity: float
    execution_price: float

    transaction_cost: float = 0.0
    trade_id: Optional[int] = None
    trade_time: Optional[datetime] = None

    def __post_init__(self):
        """Normalize and validate trade fields."""

        self.trade_side = self.trade_side.upper()

        if self.trade_time is None:
            self.trade_time = datetime.now()

        validate_trade(
            order_id=self.order_id,
            security_id=self.security_id,
            trade_side=self.trade_side,
            quantity=self.quantity,
            execution_price=self.execution_price,
            transaction_cost=self.transaction_cost,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert trade object into dictionary."""

        return asdict(self)


# ============================================================
# TRADE VALIDATION
# ============================================================

def validate_trade(
    order_id: int,
    security_id: int,
    trade_side: str,
    quantity: float,
    execution_price: float,
    transaction_cost: float = 0.0,
) -> bool:
    """
    Validate simulated trade data.
    """

    # --------------------------------------------------------
    # Order ID
    # --------------------------------------------------------

    if not isinstance(order_id, int) or order_id <= 0:
        raise ValueError(
            "order_id must be a positive integer."
        )

    # --------------------------------------------------------
    # Security ID
    # --------------------------------------------------------

    if not isinstance(security_id, int) or security_id <= 0:
        raise ValueError(
            "security_id must be a positive integer."
        )

    # --------------------------------------------------------
    # Trade side
    # --------------------------------------------------------

    trade_side = str(trade_side).upper()

    if trade_side not in {"BUY", "SELL"}:
        raise ValueError(
            "trade_side must be either BUY or SELL."
        )

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(
            "Trade quantity must be numeric."
        )

    if quantity <= 0:
        raise ValueError(
            "Trade quantity must be greater than zero."
        )

    # --------------------------------------------------------
    # Execution price
    # --------------------------------------------------------

    try:
        execution_price = float(execution_price)
    except (TypeError, ValueError):
        raise ValueError(
            "execution_price must be numeric."
        )

    if execution_price <= 0:
        raise ValueError(
            "execution_price must be greater than zero."
        )

    # --------------------------------------------------------
    # Transaction cost
    # --------------------------------------------------------

    try:
        transaction_cost = float(transaction_cost)
    except (TypeError, ValueError):
        raise ValueError(
            "transaction_cost must be numeric."
        )

    if transaction_cost < 0:
        raise ValueError(
            "transaction_cost cannot be negative."
        )

    return True


# ============================================================
# TRANSACTION COST
# ============================================================

def calculate_transaction_cost(
    quantity: float,
    execution_price: float,
    cost_rate: float = DEFAULT_TRANSACTION_COST_RATE,
) -> float:
    """
    Calculate simulated transaction cost.

    Formula:

        transaction_cost =
            quantity × execution_price × cost_rate
    """

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if execution_price <= 0:
        raise ValueError(
            "Execution price must be greater than zero."
        )

    if cost_rate < 0:
        raise ValueError(
            "Transaction cost rate cannot be negative."
        )

    trade_value = quantity * execution_price

    transaction_cost = trade_value * cost_rate

    return round(transaction_cost, 4)


# ============================================================
# EXECUTE ORDER
# ============================================================

def execute_order(
    order: Order,
    execution_price: float,
    cost_rate: float = DEFAULT_TRANSACTION_COST_RATE,
) -> Trade:
    """
    Convert a FILLED order into a simulated trade.

    The supplied order must already have FILLED status.

    Returns:
        Trade object.
    """

    # --------------------------------------------------------
    # Order status validation
    # --------------------------------------------------------

    if order.order_status != "FILLED":
        raise ValueError(
            "Only FILLED orders can be converted into trades."
        )

    # --------------------------------------------------------
    # Order ID validation
    # --------------------------------------------------------

    if order.order_id is None:
        raise ValueError(
            "A filled order must have an order_id "
            "before trade execution."
        )

    # --------------------------------------------------------
    # Execution price validation
    # --------------------------------------------------------

    try:
        execution_price = float(execution_price)
    except (TypeError, ValueError):
        raise ValueError(
            "execution_price must be numeric."
        )

    if execution_price <= 0:
        raise ValueError(
            "execution_price must be greater than zero."
        )

    # --------------------------------------------------------
    # Calculate transaction cost
    # --------------------------------------------------------

    transaction_cost = calculate_transaction_cost(
        quantity=order.quantity,
        execution_price=execution_price,
        cost_rate=cost_rate,
    )

    # --------------------------------------------------------
    # Create trade
    # --------------------------------------------------------

    trade = Trade(
        order_id=order.order_id,
        security_id=order.security_id,
        trade_side=order.side,
        quantity=order.quantity,
        execution_price=execution_price,
        transaction_cost=transaction_cost,
    )

    return trade


# ============================================================
# DIRECT TRADE CREATION
# ============================================================

def create_trade(
    order_id: int,
    security_id: int,
    trade_side: str,
    quantity: float,
    execution_price: float,
    cost_rate: float = DEFAULT_TRANSACTION_COST_RATE,
) -> Trade:
    """
    Create a simulated trade directly.

    Useful for testing and backtesting.
    """

    transaction_cost = calculate_transaction_cost(
        quantity=quantity,
        execution_price=execution_price,
        cost_rate=cost_rate,
    )

    return Trade(
        order_id=order_id,
        security_id=security_id,
        trade_side=trade_side,
        quantity=quantity,
        execution_price=execution_price,
        transaction_cost=transaction_cost,
    )


# ============================================================
# TRADE VALUE
# ============================================================

def calculate_trade_value(
    quantity: float,
    execution_price: float,
) -> float:
    """
    Calculate gross trade value.
    """

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if execution_price <= 0:
        raise ValueError(
            "Execution price must be greater than zero."
        )

    return round(
        quantity * execution_price,
        4,
    )


# ============================================================
# NET TRADE VALUE
# ============================================================

def calculate_net_trade_value(
    trade: Trade,
) -> float:
    """
    Calculate net trade value after transaction cost.

    For BUY:
        gross value + transaction cost

    For SELL:
        gross value - transaction cost
    """

    gross_value = calculate_trade_value(
        trade.quantity,
        trade.execution_price,
    )

    if trade.trade_side == "BUY":
        return round(
            gross_value + trade.transaction_cost,
            4,
        )

    return round(
        gross_value - trade.transaction_cost,
        4,
    )


# ============================================================
# TRADE SUMMARY
# ============================================================

def get_trade_summary(
    trade: Trade,
) -> Dict[str, Any]:
    """
    Return a clean trade summary.
    """

    gross_value = calculate_trade_value(
        trade.quantity,
        trade.execution_price,
    )

    net_value = calculate_net_trade_value(trade)

    return {
        "trade_id": trade.trade_id,
        "order_id": trade.order_id,
        "security_id": trade.security_id,
        "trade_side": trade.trade_side,
        "quantity": trade.quantity,
        "execution_price": trade.execution_price,
        "gross_value": gross_value,
        "transaction_cost": trade.transaction_cost,
        "net_value": net_value,
        "trade_time": trade.trade_time,
    }


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 65)
    print("QUANTDB SIMULATED TRADE MANAGEMENT TEST")
    print("=" * 65)

    # --------------------------------------------------------
    # Import order creation functions
    # --------------------------------------------------------

    from .orders import create_order
    from .orders import update_order_status
    from .orders import fill_order

    # --------------------------------------------------------
    # Create simulated BUY LIMIT order
    # --------------------------------------------------------

    order = create_order(
        user_id=1,
        security_id=1,
        side="BUY",
        order_type="LIMIT",
        quantity=100,
        order_price=100.50,
    )

    # Database-generated ID will normally be assigned later.
    # For local simulation testing we assign one manually.
    order.order_id = 1001

    print("\n1. ORDER CREATED")
    print(order.to_dict())

    # --------------------------------------------------------
    # Open order
    # --------------------------------------------------------

    update_order_status(
        order,
        "OPEN",
    )

    print("\n2. ORDER OPENED")
    print(order.to_dict())

    # --------------------------------------------------------
    # Fill order
    # --------------------------------------------------------

    fill_order(
        order,
        execution_price=100.40,
    )

    print("\n3. ORDER FILLED")
    print(order.to_dict())

    # --------------------------------------------------------
    # Execute trade
    # --------------------------------------------------------

    trade = execute_order(
        order=order,
        execution_price=100.40,
    )

    print("\n4. TRADE EXECUTED")
    print(trade.to_dict())

    # --------------------------------------------------------
    # Trade summary
    # --------------------------------------------------------

    print("\n5. TRADE SUMMARY")
    print(get_trade_summary(trade))

    # --------------------------------------------------------
    # Trade values
    # --------------------------------------------------------

    print("\n6. TRADE VALUES")

    print(
        "Gross Trade Value:",
        calculate_trade_value(
            trade.quantity,
            trade.execution_price,
        ),
    )

    print(
        "Transaction Cost:",
        trade.transaction_cost,
    )

    print(
        "Net Trade Value:",
        calculate_net_trade_value(trade),
    )

    print("\n" + "=" * 65)
    print("TRADE TEST COMPLETED SUCCESSFULLY")
    print("=" * 65)