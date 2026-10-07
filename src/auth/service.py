"""
QuantDB Core Authentication & Authorization Service.

Handles credential verification, account state enforcement, role resolution,
and security permission checks for QuantDB.
"""

from typing import Any, Dict, List, Optional
import logging

from src.auth.password import hash_password, verify_password
from src.auth.roles import (
    Role,
    get_role_display_name,
    has_page_access,
    get_allowed_pages,
    normalize_role,
    can_trade,
    can_backtest,
    can_manage_strategies,
    can_manage_users,
)
from src.database.repository import Repository

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails due to invalid credentials or user state."""
    pass


class AccountInactiveError(AuthenticationError):
    """Raised when an account is inactive, disabled, or suspended."""
    pass


class AuthorizationError(Exception):
    """Raised when an authenticated user attempts an unauthorized operation."""
    pass


def authenticate_user(
    identifier: str,
    password: str,
    repo: Optional[Repository] = None,
) -> Dict[str, Any]:
    """
    Authenticates a user by username or email and plaintext password.

    Flow:
        1. Input sanitization
        2. Database lookup by username or email
        3. Secure password hash verification
        4. Account status verification (must be 'ACTIVE')
        5. Role resolution and normalization
        6. Return sanitized user session payload (NEVER returns password hash)
    """
    if not identifier or not isinstance(identifier, str):
        raise AuthenticationError("Username or email is required.")
    if not password or not isinstance(password, str):
        raise AuthenticationError("Password is required.")

    clean_id = identifier.strip()

    if repo is None:
        repo = Repository()

    try:
        user = repo.get_user_by_identifier(clean_id)
    except Exception as e:
        logger.error(f"Database error during authentication lookup: {e}")
        raise AuthenticationError("Authentication service currently unavailable.")

    if not user:
        # Uniform error message prevents username enumeration
        raise AuthenticationError("Invalid username or password.")

    stored_hash = user.get("password_hash") or ""
    if not verify_password(password, stored_hash):
        raise AuthenticationError("Invalid username or password.")

    status = str(user.get("status", "")).upper()
    if status != "ACTIVE":
        if status == "SUSPENDED":
            raise AccountInactiveError("This account has been suspended. Please contact administrator.")
        raise AccountInactiveError("This account is inactive. Please contact administrator.")

    raw_role = user.get("role", Role.USER)
    canonical_role = normalize_role(raw_role)

    # Return safe user profile for session state (strictly omitting credentials)
    return {
        "user_id": user["user_id"],
        "username": user.get("username") or clean_id,
        "name": user.get("name") or clean_id,
        "email": user.get("email") or "",
        "role": canonical_role,
        "role_display": get_role_display_name(canonical_role),
        "status": status,
        "created_at": str(user.get("created_at", "")),
    }


def get_user_role(user: Dict[str, Any]) -> str:
    """Extracts and normalizes the role from a user dict."""
    if not user:
        return Role.USER
    return normalize_role(user.get("role", Role.USER))


def has_permission(role: str, page_or_action: str) -> bool:
    """Checks whether the role has permission for a specific page or action."""
    return has_page_access(role, page_or_action)


def require_role(current_role: str, allowed_roles: List[str]) -> bool:
    """Validates that current_role is one of the allowed roles; raises AuthorizationError if not."""
    canon = normalize_role(current_role)
    allowed_canon = [normalize_role(r) for r in allowed_roles]
    if canon not in allowed_canon:
        raise AuthorizationError(
            f"Access restricted: current role '{get_role_display_name(canon)}' is not permitted."
        )
    return True
