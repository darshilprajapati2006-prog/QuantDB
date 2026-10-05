"""
QuantDB Portfolio Service

Provides backend interfaces for portfolio and position tracking.
Reuses `PortfolioManager` from `src.trading.portfolio` and
`PositionManager` from `src.trading.positions`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.trading.portfolio import PortfolioManager
from src.trading.positions import PositionManager

# In-memory registry for simulation and testing environments
_active_portfolios: Dict[int, PortfolioManager] = {}


def _get_or_create_portfolio_manager(
    portfolio_id: int,
    user_id: int = 1,
    name: str = "Default Portfolio",
    initial_capital: float = 100000.0,
) -> PortfolioManager:
    """Retrieve or initialize an in-memory PortfolioManager instance."""
    if portfolio_id not in _active_portfolios:
        _active_portfolios[portfolio_id] = PortfolioManager(
            portfolio_id=portfolio_id,
            user_id=user_id,
            initial_capital=initial_capital,
        )
    return _active_portfolios[portfolio_id]


def create_portfolio(
    user_id: int,
    portfolio_name: str = "Default Portfolio",
    initial_capital: float = 100000.0,
    portfolio_id: Optional[int] = None,
    repo: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Create a new simulated portfolio.

    Parameters
    ----------
    user_id : int
        User identifier.
    portfolio_name : str, default='Default Portfolio'
        Descriptive portfolio name.
    initial_capital : float, default=100000.0
        Starting cash balance.
    portfolio_id : int, optional
        Explicit ID if assigned.
    repo : Repository, optional
        Database repository instance.

    Returns
    -------
    dict
        Created portfolio summary.
    """
    if initial_capital <= 0:
        raise ValueError("initial_capital must be greater than zero.")

    assigned_id = portfolio_id or (len(_active_portfolios) + 1)

    if repo is not None:
        try:
            db_id = repo.create_portfolio(
                user_id=user_id,
                portfolio_name=portfolio_name,
                initial_capital=initial_capital,
                current_cash=initial_capital,
                created_at=None,
                status="ACTIVE",
            )
            if db_id:
                assigned_id = db_id
        except Exception:
            pass

    pm = PortfolioManager(
        portfolio_id=assigned_id,
        user_id=user_id,
        initial_capital=initial_capital,
    )
    _active_portfolios[assigned_id] = pm

    summary = pm.get_portfolio_summary()
    summary["cash"] = summary.get("current_cash", initial_capital)
    summary["portfolio_name"] = portfolio_name
    return summary


def get_portfolio(
    portfolio_id: int,
    repo: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Retrieve portfolio details by portfolio ID.

    Parameters
    ----------
    portfolio_id : int
        Portfolio identifier.
    repo : Repository, optional
        Database repository instance.

    Returns
    -------
    dict
        Portfolio metadata and current metrics.
    """
    if repo is not None:
        try:
            db_port = repo.get_portfolio(portfolio_id)
            if db_port:
                return db_port
        except Exception:
            pass

    if portfolio_id in _active_portfolios:
        return _active_portfolios[portfolio_id].get_portfolio_summary()

    # If neither DB nor active manager exists, return initialized default summary
    pm = _get_or_create_portfolio_manager(portfolio_id)
    return pm.get_portfolio_summary()


def get_positions(
    portfolio_id: int,
    repo: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve all current positions in a portfolio.

    Parameters
    ----------
    portfolio_id : int
        Portfolio identifier.
    repo : Repository, optional
        Database repository instance.

    Returns
    -------
    list of dict
        List of position records.
    """
    if repo is not None:
        try:
            db_positions = repo.get_positions(portfolio_id)
            if db_positions:
                return db_positions
        except Exception:
            pass

    pm = _get_or_create_portfolio_manager(portfolio_id)
    return pm.get_positions()


def get_portfolio_summary(
    portfolio_id: int,
    repo: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Retrieve a comprehensive summary of portfolio balances, equity, and P&L.

    Parameters
    ----------
    portfolio_id : int
        Portfolio identifier.
    repo : Repository, optional
        Database repository instance.

    Returns
    -------
    dict
        portfolio_id, cash, market_value, total_equity,
        realized_pnl, unrealized_pnl, total_pnl, return_percentage.
    """
    if repo is not None:
        try:
            db_summary = repo.get_portfolio(portfolio_id)
            if db_summary:
                # If DB record returned, supplement with calculated positions
                positions = repo.get_positions(portfolio_id) or []
                realized = sum(float(p.get("realized_pnl", 0.0)) for p in positions)
                unrealized = sum(float(p.get("unrealized_pnl", 0.0)) for p in positions)
                cash = float(db_summary.get("current_cash", 0.0))
                init_cap = float(db_summary.get("initial_capital", 1.0))
                total_equity = cash + unrealized
                total_pnl = realized + unrealized
                ret_pct = (total_pnl / init_cap * 100.0) if init_cap > 0 else 0.0

                return {
                    "portfolio_id": portfolio_id,
                    "portfolio_name": db_summary.get("portfolio_name", "Portfolio"),
                    "initial_capital": init_cap,
                    "cash": cash,
                    "realized_pnl": realized,
                    "unrealized_pnl": unrealized,
                    "total_pnl": total_pnl,
                    "total_equity": total_equity,
                    "return_percentage": ret_pct,
                }
        except Exception:
            pass

    pm = _get_or_create_portfolio_manager(portfolio_id)
    summary = pm.get_portfolio_summary()
    summary["cash"] = summary.get("current_cash", 0.0)
    return summary


def update_position(
    portfolio_id: int,
    security_id: int,
    quantity: float,
    price: float,
    side: str = "BUY",
) -> Dict[str, Any]:
    """
    Update position in portfolio following simulated execution.

    Parameters
    ----------
    portfolio_id : int
        Portfolio identifier.
    security_id : int
        Security identifier.
    quantity : float
        Quantity traded.
    price : float
        Trade price.
    side : str, default='BUY'
        'BUY' or 'SELL'.

    Returns
    -------
    dict
        Updated position details.
    """
    pm = _get_or_create_portfolio_manager(portfolio_id)
    side = side.upper().strip()

    if side == "BUY":
        return pm.add_position(
            security_id=security_id,
            quantity=quantity,
            price=price,
        )
    elif side == "SELL":
        return pm.remove_position(
            security_id=security_id,
            quantity=quantity,
            price=price,
        )
    else:
        raise ValueError(f"Invalid trade side: {side}. Must be 'BUY' or 'SELL'.")
