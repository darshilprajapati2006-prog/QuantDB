"""
QuantDB - Simulated Order Management

Handles:
- BUY / SELL orders
- MARKET / LIMIT orders
- Order validation
- Order status management
- Simulated order creation
- Order cancellation
- Order summary

This module is for paper/simulated trading only.
No real-money trading or broker API is used.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


# ============================================================
# CONSTANTS
# ============================================================

VALID_SIDES = {"BUY", "SELL"}

VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

VALID_ORDER_STATUSES = {
    "PENDING",
    "OPEN",
    "FILLED",
    "CANCELLED",
    "REJECTED",
}


# ============================================================
# ORDER DATA MODEL
# ============================================================

@dataclass
class Order:
    """
    Represents a simulated trading order.
    """

    user_id: int
    security_id: int
    side: str
    order_type: str
    quantity: float

    order_price: Optional[float] = None

    order_id: Optional[int] = None
    order_status: str = "PENDING"
    order_time: Optional[datetime] = None

    def __post_init__(self):
        """Normalize and validate basic order fields."""

        self.side = self.side.upper()
        self.order_type = self.order_type.upper()
        self.order_status = self.order_status.upper()

        if self.order_time is None:
            self.order_time = datetime.now()

        validate_order(
            user_id=self.user_id,
            security_id=self.security_id,
            side=self.side,
            order_type=self.order_type,
            quantity=self.quantity,
            order_price=self.order_price,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert order object into dictionary."""

        return asdict(self)


# ============================================================
# VALIDATION
# ============================================================

def validate_order(
    user_id: int,
    security_id: int,
    side: str,
    order_type: str,
    quantity: float,
    order_price: Optional[float] = None,
) -> bool:
    """
    Validate a simulated order.

    Returns:
        True if order is valid.

    Raises:
        ValueError if any validation fails.
    """

    # --------------------------------------------------------
    # User validation
    # --------------------------------------------------------

    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer.")

    # --------------------------------------------------------
    # Security validation
    # --------------------------------------------------------

    if not isinstance(security_id, int) or security_id <= 0:
        raise ValueError("security_id must be a positive integer.")

    # --------------------------------------------------------
    # Side validation
    # --------------------------------------------------------

    side = str(side).upper()

    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid order side: {side}. "
            f"Allowed values: {sorted(VALID_SIDES)}"
        )

    # --------------------------------------------------------
    # Order type validation
    # --------------------------------------------------------

    order_type = str(order_type).upper()

    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type: {order_type}. "
            f"Allowed values: {sorted(VALID_ORDER_TYPES)}"
        )

    # --------------------------------------------------------
    # Quantity validation
    # --------------------------------------------------------

    if quantity is None:
        raise ValueError("Order quantity cannot be None.")

    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValueError("Order quantity must be numeric.")

    if quantity <= 0:
        raise ValueError("Order quantity must be greater than zero.")

    # --------------------------------------------------------
    # Price validation
    # --------------------------------------------------------

    if order_type == "LIMIT":

        if order_price is None:
            raise ValueError(
                "LIMIT order requires an order_price."
            )

        try:
            order_price = float(order_price)
        except (TypeError, ValueError):
            raise ValueError("order_price must be numeric.")

        if order_price <= 0:
            raise ValueError(
                "LIMIT order price must be greater than zero."
            )

    elif order_type == "MARKET":

        # Market order does not require a price.
        # If a price is supplied, it is ignored by the
        # simulated execution engine.

        if order_price is not None:

            try:
                order_price = float(order_price)
            except (TypeError, ValueError):
                raise ValueError(
                    "order_price must be numeric when provided."
                )

            if order_price <= 0:
                raise ValueError(
                    "Provided order_price must be greater than zero."
                )

    return True


# ============================================================
# ORDER CREATION
# ============================================================

def create_order(
    user_id: int,
    security_id: int,
    side: str,
    order_type: str,
    quantity: float,
    order_price: Optional[float] = None,
) -> Order:
    """
    Create a new simulated order.

    The order is initially created with PENDING status.

    Returns:
        Order object.
    """

    order = Order(
        user_id=user_id,
        security_id=security_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        order_price=order_price,
        order_status="PENDING",
    )

    return order


# ============================================================
# ORDER STATUS MANAGEMENT
# ============================================================

def update_order_status(
    order: Order,
    new_status: str,
) -> Order:
    """
    Update the status of an existing order.
    """

    new_status = new_status.upper()

    if new_status not in VALID_ORDER_STATUSES:
        raise ValueError(
            f"Invalid order status: {new_status}. "
            f"Allowed values: {sorted(VALID_ORDER_STATUSES)}"
        )

    # --------------------------------------------------------
    # Prevent changes to completed orders
    # --------------------------------------------------------

    if order.order_status in {"FILLED", "CANCELLED", "REJECTED"}:

        raise ValueError(
            f"Cannot change status of a "
            f"{order.order_status} order."
        )

    order.order_status = new_status

    return order


# ============================================================
# ORDER CANCELLATION
# ============================================================

def cancel_order(order: Order) -> Order:
    """
    Cancel a pending/open simulated order.
    """

    if order.order_status in {
        "FILLED",
        "CANCELLED",
        "REJECTED",
    }:
        raise ValueError(
            f"Cannot cancel an order with status "
            f"{order.order_status}."
        )

    order.order_status = "CANCELLED"

    return order


# ============================================================
# ORDER FILL
# ============================================================

def fill_order(
    order: Order,
    execution_price: float,
) -> Order:
    """
    Mark an order as FILLED.

    For a MARKET order, execution_price represents
    the simulated market execution price.

    For a LIMIT order, execution_price represents
    the actual simulated fill price.
    """

    if order.order_status in {
        "FILLED",
        "CANCELLED",
        "REJECTED",
    }:
        raise ValueError(
            f"Cannot fill an order with status "
            f"{order.order_status}."
        )

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
    # LIMIT order execution validation
    # --------------------------------------------------------

    if order.order_type == "LIMIT":

        if order.side == "BUY":
            if execution_price > order.order_price:
                raise ValueError(
                    "BUY LIMIT order cannot execute "
                    "above the limit price."
                )

        elif order.side == "SELL":
            if execution_price < order.order_price:
                raise ValueError(
                    "SELL LIMIT order cannot execute "
                    "below the limit price."
                )

    order.order_status = "FILLED"

    return order


# ============================================================
# ORDER REJECTION
# ============================================================

def reject_order(
    order: Order,
    reason: Optional[str] = None,
) -> Order:
    """
    Mark an order as REJECTED.
    """

    if order.order_status in {
        "FILLED",
        "CANCELLED",
    }:
        raise ValueError(
            f"Cannot reject an order with status "
            f"{order.order_status}."
        )

    order.order_status = "REJECTED"

    if reason:
        print(f"Order rejected: {reason}")

    return order


# ============================================================
# ORDER SUMMARY
# ============================================================

def get_order_summary(order: Order) -> Dict[str, Any]:
    """
    Return a clean summary of an order.
    """

    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "security_id": order.security_id,
        "side": order.side,
        "order_type": order.order_type,
        "quantity": order.quantity,
        "order_price": order.order_price,
        "order_status": order.order_status,
        "order_time": order.order_time,
    }


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("QUANTDB SIMULATED ORDER MANAGEMENT TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Create BUY LIMIT order
    # --------------------------------------------------------

    order = create_order(
        user_id=1,
        security_id=1,
        side="BUY",
        order_type="LIMIT",
        quantity=100,
        order_price=100.50,
    )

    print("\nCreated Order:")
    print(order.to_dict())

    # --------------------------------------------------------
    # Open order
    # --------------------------------------------------------

    update_order_status(order, "OPEN")

    print("\nAfter OPEN:")
    print(order.to_dict())

    # --------------------------------------------------------
    # Fill order
    # --------------------------------------------------------

    fill_order(
        order,
        execution_price=100.40,
    )

    print("\nAfter FILL:")
    print(order.to_dict())

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\nOrder Summary:")
    print(get_order_summary(order))

    print("\n" + "=" * 60)
    print("ORDER TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)