"""
QuantDB Role-Based Access Control (RBAC) Module.

Defines the four core platform roles, their hierarchical permission boundaries,
human-readable display representations, and page navigation access controls.
"""

from typing import Dict, List, Set


class Role:
    """Canonical QuantDB platform role constants."""
    USER = "USER"
    QUANT_TRADER = "QUANT_TRADER"
    QUANT_RESEARCHER = "QUANT_RESEARCHER"
    ADMIN = "ADMIN"

    # Legacy compatibility alias
    SIMULATED_TRADER = "SIMULATED_TRADER"

    ALL_ROLES = [USER, QUANT_TRADER, QUANT_RESEARCHER, ADMIN]


ROLE_DISPLAY_NAMES: Dict[str, str] = {
    Role.USER: "User",
    Role.QUANT_TRADER: "Quant Trader",
    Role.QUANT_RESEARCHER: "Quant Researcher",
    Role.ADMIN: "Admin",
    Role.SIMULATED_TRADER: "Quant Trader",
}


# Permitted modules/pages per role
ROLE_ALLOWED_PAGES: Dict[str, List[str]] = {
    Role.USER: [
        "Overview",
        "Market Data",
        "Portfolio",
        "Reports",
    ],
    Role.QUANT_TRADER: [
        "Overview",
        "Market Data",
        "Trading",
        "Portfolio",
        "Strategies",
        "Reports",
    ],
    Role.QUANT_RESEARCHER: [
        "Overview",
        "Market Data",
        "Portfolio",
        "Strategies",
        "Backtesting",
        "Reports",
    ],
    Role.ADMIN: [
        "Overview",
        "Market Data",
        "Trading",
        "Portfolio",
        "Strategies",
        "Backtesting",
        "Reports",
        "Admin",
    ],
}


def normalize_role(role: str) -> str:
    """Normalizes role strings to canonical role names (e.g., SIMULATED_TRADER -> QUANT_TRADER)."""
    if not role:
        return Role.USER
    cleaned = str(role).strip().upper()
    if cleaned == Role.SIMULATED_TRADER:
        return Role.QUANT_TRADER
    if cleaned in Role.ALL_ROLES:
        return cleaned
    return Role.USER


def get_role_display_name(role: str) -> str:
    """Returns a friendly display label for a role code."""
    canon = normalize_role(role)
    return ROLE_DISPLAY_NAMES.get(canon, "User")


def get_allowed_pages(role: str) -> List[str]:
    """Returns the list of dashboard pages accessible to the given role."""
    canon = normalize_role(role)
    return ROLE_ALLOWED_PAGES.get(canon, ROLE_ALLOWED_PAGES[Role.USER])


def has_page_access(role: str, page_name: str) -> bool:
    """Checks whether the given role has permission to access a specific page."""
    allowed = get_allowed_pages(role)
    return page_name in allowed


def can_trade(role: str) -> bool:
    """Checks whether the role is permitted to perform simulated paper trading."""
    canon = normalize_role(role)
    return canon in (Role.QUANT_TRADER, Role.ADMIN)


def can_backtest(role: str) -> bool:
    """Checks whether the role is permitted to execute strategy backtests."""
    canon = normalize_role(role)
    return canon in (Role.QUANT_RESEARCHER, Role.ADMIN)


def can_manage_strategies(role: str) -> bool:
    """Checks whether the role is permitted to create and modify quantitative strategies."""
    canon = normalize_role(role)
    return canon in (Role.QUANT_RESEARCHER, Role.ADMIN)


def can_manage_users(role: str) -> bool:
    """Checks whether the role is permitted to administer users and RBAC permissions."""
    canon = normalize_role(role)
    return canon == Role.ADMIN
