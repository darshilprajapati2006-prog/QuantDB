"""
Market microstructure analytics for QuantDB.

Provides basic academic/simulation-level metrics:
- Bid-Ask Spread
- Market Depth
- Order-Book Imbalance
"""

from __future__ import annotations

from typing import Iterable, Mapping, Optional


def bid_ask_spread(
    bid_price: float,
    ask_price: float,
    *,
    relative: bool = False,
) -> float:
    """
    Calculate the bid-ask spread.

    Absolute spread:
        ask_price - bid_price

    Relative spread:
        (ask_price - bid_price) / mid_price
    """
    bid = float(bid_price)
    ask = float(ask_price)

    if bid < 0 or ask < 0:
        raise ValueError("Bid and ask prices must be non-negative.")

    if ask < bid:
        raise ValueError("Ask price cannot be lower than bid price.")

    spread = ask - bid

    if not relative:
        return spread

    mid_price = (bid + ask) / 2

    if mid_price == 0:
        return 0.0

    return spread / mid_price


def market_depth(
    bid_sizes: Optional[Iterable[float]] = None,
    ask_sizes: Optional[Iterable[float]] = None,
) -> Mapping[str, float]:
    """
    Calculate basic market depth from bid and ask quantities.

    Parameters
    ----------
    bid_sizes:
        Quantities available on the bid side.
    ask_sizes:
        Quantities available on the ask side.

    Returns
    -------
    dict
        Total bid depth, total ask depth and total market depth.
    """
    bid_levels = list(bid_sizes or [])
    ask_levels = list(ask_sizes or [])

    if any(float(size) < 0 for size in bid_levels):
        raise ValueError("Bid sizes must be non-negative.")

    if any(float(size) < 0 for size in ask_levels):
        raise ValueError("Ask sizes must be non-negative.")

    total_bid_depth = sum(float(size) for size in bid_levels)
    total_ask_depth = sum(float(size) for size in ask_levels)

    return {
        "bid_depth": total_bid_depth,
        "ask_depth": total_ask_depth,
        "total_depth": total_bid_depth + total_ask_depth,
    }


def order_book_imbalance(
    bid_size: float,
    ask_size: float,
) -> float:
    """
    Calculate order-book imbalance.

    Formula:
        (Bid Size - Ask Size) / (Bid Size + Ask Size)

    Range:
        [-1, 1]

    Positive value -> more bid-side liquidity.
    Negative value -> more ask-side liquidity.
    """
    bid = float(bid_size)
    ask = float(ask_size)

    if bid < 0 or ask < 0:
        raise ValueError("Bid and ask sizes must be non-negative.")

    total = bid + ask

    if total == 0:
        return 0.0

    return (bid - ask) / total


def microstructure_summary(
    bid_price: float,
    ask_price: float,
    bid_size: float = 0.0,
    ask_size: float = 0.0,
) -> dict:
    """
    Return a combined market microstructure summary.
    """
    depth = market_depth([bid_size], [ask_size])

    return {
        "bid_price": float(bid_price),
        "ask_price": float(ask_price),
        "bid_ask_spread": bid_ask_spread(bid_price, ask_price),
        "relative_spread": bid_ask_spread(
            bid_price,
            ask_price,
            relative=True,
        ),
        "bid_depth": depth["bid_depth"],
        "ask_depth": depth["ask_depth"],
        "total_depth": depth["total_depth"],
        "order_book_imbalance": order_book_imbalance(
            bid_size,
            ask_size,
        ),
    }