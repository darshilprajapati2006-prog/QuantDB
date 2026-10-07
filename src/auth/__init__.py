"""
QuantDB Authentication & Authorization Package.
"""

from src.auth.password import hash_password, verify_password
from src.auth.roles import (
    Role,
    ROLE_DISPLAY_NAMES,
    ROLE_ALLOWED_PAGES,
    get_role_display_name,
    get_allowed_pages,
    has_page_access,
    normalize_role,
    can_trade,
    can_backtest,
    can_manage_strategies,
    can_manage_users,
)
from src.auth.service import (
    AuthenticationError,
    AccountInactiveError,
    AuthorizationError,
    authenticate_user,
    get_user_role,
    has_permission,
    require_role,
)

__all__ = [
    "hash_password",
    "verify_password",
    "Role",
    "ROLE_DISPLAY_NAMES",
    "ROLE_ALLOWED_PAGES",
    "get_role_display_name",
    "get_allowed_pages",
    "has_page_access",
    "normalize_role",
    "can_trade",
    "can_backtest",
    "can_manage_strategies",
    "can_manage_users",
    "AuthenticationError",
    "AccountInactiveError",
    "AuthorizationError",
    "authenticate_user",
    "get_user_role",
    "has_permission",
    "require_role",
]
