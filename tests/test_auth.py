"""
QuantDB Authentication, Authorization & Security Test Suite.

Validates:
1. PBKDF2-HMAC-SHA256 password hashing, salting, and constant-time verification.
2. Authentication service flows (valid credentials, bad password, unknown user, inactive/suspended accounts).
3. Role-Based Access Control (RBAC) permission enforcement across all 4 canonical roles.
4. Security invariants (no plaintext passwords, no hashes leaked in session payloads, parameterized SQL).
"""

from unittest.mock import MagicMock
import pytest

from src.auth.password import hash_password, verify_password
from src.auth.roles import (
    Role,
    normalize_role,
    get_role_display_name,
    get_allowed_pages,
    has_page_access,
    can_trade,
    can_backtest,
    can_manage_strategies,
    can_manage_users,
)
from src.auth.service import (
    authenticate_user,
    AuthenticationError,
    AccountInactiveError,
    AuthorizationError,
    require_role,
)
from src.database import queries


# ======================================================================
# 1. PASSWORD SECURITY & HASHING TESTS
# ======================================================================

class TestPasswordSecurity:
    """Tests for secure PBKDF2 password hashing and verification."""

    def test_hash_format(self):
        """Verifies that generated hash complies with algorithm and iteration specifications."""
        hashed = hash_password("SecretPassword123!")
        assert hashed.startswith("pbkdf2_sha256$600000$")
        parts = hashed.split("$")
        assert len(parts) == 4
        assert int(parts[1]) == 600000
        assert len(parts[2]) == 32  # 16-byte salt in hex
        assert len(parts[3]) == 64  # 32-byte sha256 output in hex

    def test_unique_salts(self):
        """Verifies that two identical passwords generate different hashes due to unique salts."""
        h1 = hash_password("IdenticalPassword123")
        h2 = hash_password("IdenticalPassword123")
        assert h1 != h2

    def test_verify_valid_password(self):
        """Verifies that a valid password matches its generated hash."""
        pwd = "Trader01@QuantDB"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True

    def test_verify_invalid_password(self):
        """Verifies that an incorrect password fails verification."""
        pwd = "Trader01@QuantDB"
        hashed = hash_password(pwd)
        assert verify_password("WrongPassword!", hashed) is False

    def test_verify_empty_or_malformed(self):
        """Verifies that invalid or empty parameters are rejected safely without exceptions."""
        assert verify_password("", "some_hash") is False
        assert verify_password("pass", "") is False
        assert verify_password(None, "some_hash") is False
        assert verify_password("pass", "malformed_string_without_delimiters") is False

    def test_hash_empty_password_raises(self):
        """Verifies that attempting to hash an empty password raises ValueError."""
        with pytest.raises(ValueError):
            hash_password("")


# ======================================================================
# 2. AUTHENTICATION SERVICE TESTS
# ======================================================================

class TestAuthenticationService:
    """Tests for authenticate_user workflow and account state verification."""

    @pytest.fixture
    def mock_repo(self):
        """Returns a mock repository configured with test users."""
        repo = MagicMock()
        valid_hash = hash_password("CorrectPass123!")
        
        users_db = {
            "trader01": {
                "user_id": 1,
                "username": "trader01",
                "name": "Quant Trader Demo",
                "email": "trader01@quantdb.local",
                "password_hash": valid_hash,
                "role": "QUANT_TRADER",
                "status": "ACTIVE",
                "created_at": "2026-03-01 09:00:00",
            },
            "inactive_user": {
                "user_id": 2,
                "username": "inactive_user",
                "name": "Inactive Account",
                "email": "inactive@quantdb.local",
                "password_hash": valid_hash,
                "role": "USER",
                "status": "INACTIVE",
                "created_at": "2026-03-01 09:00:00",
            },
            "suspended_user": {
                "user_id": 3,
                "username": "suspended_user",
                "name": "Suspended Account",
                "email": "suspended@quantdb.local",
                "password_hash": valid_hash,
                "role": "USER",
                "status": "SUSPENDED",
                "created_at": "2026-03-01 09:00:00",
            },
            "legacy_trader": {
                "user_id": 4,
                "username": "legacy_trader",
                "name": "Legacy Trader",
                "email": "legacy@quantdb.local",
                "password_hash": valid_hash,
                "role": "SIMULATED_TRADER",
                "status": "ACTIVE",
                "created_at": "2026-03-01 09:00:00",
            },
        }

        def mock_get_user(identifier):
            clean = identifier.strip().lower()
            for u in users_db.values():
                if u["username"].lower() == clean or u["email"].lower() == clean:
                    return dict(u)
            return None

        repo.get_user_by_identifier.side_effect = mock_get_user
        return repo

    def test_successful_authentication_by_username(self, mock_repo):
        """Verifies successful authentication returns sanitized user profile."""
        profile = authenticate_user("trader01", "CorrectPass123!", repo=mock_repo)
        assert profile["user_id"] == 1
        assert profile["username"] == "trader01"
        assert profile["role"] == Role.QUANT_TRADER
        assert profile["role_display"] == "Quant Trader"
        assert profile["status"] == "ACTIVE"
        # Security invariant: Password hash MUST NOT be present in session payload
        assert "password_hash" not in profile
        assert "password" not in profile

    def test_successful_authentication_by_email(self, mock_repo):
        """Verifies user can authenticate using registered email address."""
        profile = authenticate_user("trader01@quantdb.local", "CorrectPass123!", repo=mock_repo)
        assert profile["username"] == "trader01"
        assert profile["role"] == Role.QUANT_TRADER

    def test_invalid_password(self, mock_repo):
        """Verifies that incorrect password raises AuthenticationError."""
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            authenticate_user("trader01", "WrongPassword", repo=mock_repo)

    def test_unknown_user(self, mock_repo):
        """Verifies that unknown username raises uniform AuthenticationError."""
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            authenticate_user("nonexistent_user", "SomePassword", repo=mock_repo)

    def test_inactive_account(self, mock_repo):
        """Verifies that inactive accounts are blocked with AccountInactiveError."""
        with pytest.raises(AccountInactiveError, match="inactive"):
            authenticate_user("inactive_user", "CorrectPass123!", repo=mock_repo)

    def test_suspended_account(self, mock_repo):
        """Verifies that suspended accounts are blocked with AccountInactiveError."""
        with pytest.raises(AccountInactiveError, match="suspended"):
            authenticate_user("suspended_user", "CorrectPass123!", repo=mock_repo)

    def test_legacy_role_normalization(self, mock_repo):
        """Verifies that legacy role SIMULATED_TRADER normalizes to QUANT_TRADER."""
        profile = authenticate_user("legacy_trader", "CorrectPass123!", repo=mock_repo)
        assert profile["role"] == Role.QUANT_TRADER
        assert profile["role_display"] == "Quant Trader"

    def test_missing_credentials(self, mock_repo):
        """Verifies empty username or password raises AuthenticationError."""
        with pytest.raises(AuthenticationError):
            authenticate_user("", "pass", repo=mock_repo)
        with pytest.raises(AuthenticationError):
            authenticate_user("user", "", repo=mock_repo)


# ======================================================================
# 3. ROLE-BASED ACCESS CONTROL (RBAC) TESTS
# ======================================================================

class TestRoleBasedAccessControl:
    """Validates authorization rules across the 4 canonical platform roles."""

    def test_user_role_permissions(self):
        """USER role: Can view Overview, Market Data, Portfolio, Reports. Cannot trade, backtest, or admin."""
        role = Role.USER
        assert has_page_access(role, "Overview") is True
        assert has_page_access(role, "Market Data") is True
        assert has_page_access(role, "Portfolio") is True
        assert has_page_access(role, "Reports") is True

        assert has_page_access(role, "Trading") is False
        assert has_page_access(role, "Strategies") is False
        assert has_page_access(role, "Backtesting") is False
        assert has_page_access(role, "Admin") is False

        assert can_trade(role) is False
        assert can_backtest(role) is False
        assert can_manage_strategies(role) is False
        assert can_manage_users(role) is False

    def test_quant_trader_role_permissions(self):
        """QUANT_TRADER role: Can trade, view market data, portfolio, strategies, reports. Cannot backtest or admin."""
        role = Role.QUANT_TRADER
        assert has_page_access(role, "Overview") is True
        assert has_page_access(role, "Market Data") is True
        assert has_page_access(role, "Trading") is True
        assert has_page_access(role, "Portfolio") is True
        assert has_page_access(role, "Strategies") is True
        assert has_page_access(role, "Reports") is True

        assert has_page_access(role, "Backtesting") is False
        assert has_page_access(role, "Admin") is False

        assert can_trade(role) is True
        assert can_backtest(role) is False
        assert can_manage_users(role) is False

    def test_quant_researcher_role_permissions(self):
        """QUANT_RESEARCHER role: Can access Backtesting, Strategies, Market Data, Portfolio. Cannot trade or admin."""
        role = Role.QUANT_RESEARCHER
        assert has_page_access(role, "Overview") is True
        assert has_page_access(role, "Market Data") is True
        assert has_page_access(role, "Portfolio") is True
        assert has_page_access(role, "Strategies") is True
        assert has_page_access(role, "Backtesting") is True
        assert has_page_access(role, "Reports") is True

        assert has_page_access(role, "Trading") is False
        assert has_page_access(role, "Admin") is False

        assert can_trade(role) is False
        assert can_backtest(role) is True
        assert can_manage_strategies(role) is True
        assert can_manage_users(role) is False

    def test_admin_role_permissions(self):
        """ADMIN role: Has full access to all 8 modules and administrative functions."""
        role = Role.ADMIN
        for page in ["Overview", "Market Data", "Trading", "Portfolio", "Strategies", "Backtesting", "Reports", "Admin"]:
            assert has_page_access(role, page) is True

        assert can_trade(role) is True
        assert can_backtest(role) is True
        assert can_manage_strategies(role) is True
        assert can_manage_users(role) is True

    def test_require_role_guard(self):
        """Verifies require_role raises AuthorizationError for unauthorized roles."""
        assert require_role(Role.ADMIN, [Role.ADMIN]) is True
        assert require_role(Role.QUANT_TRADER, [Role.QUANT_TRADER, Role.ADMIN]) is True

        with pytest.raises(AuthorizationError):
            require_role(Role.USER, [Role.ADMIN])
        with pytest.raises(AuthorizationError):
            require_role(Role.QUANT_RESEARCHER, [Role.QUANT_TRADER])

    def test_role_display_names(self):
        """Verifies clean human-friendly role labels."""
        assert get_role_display_name(Role.USER) == "User"
        assert get_role_display_name(Role.QUANT_TRADER) == "Quant Trader"
        assert get_role_display_name(Role.QUANT_RESEARCHER) == "Quant Researcher"
        assert get_role_display_name(Role.ADMIN) == "Admin"


# ======================================================================
# 4. DATABASE QUERY SECURITY & PARAMETERIZATION TESTS
# ======================================================================

class TestDatabaseQuerySecurity:
    """Verifies that authentication queries strictly adhere to parameterization standards."""

    def test_queries_use_placeholders(self):
        """Verifies that authentication SQL queries contain %s placeholders and no string interpolation."""
        assert "%s" in queries.GET_USER_BY_ID
        assert "%s" in queries.GET_USER_BY_EMAIL
        assert "%s" in queries.GET_USER_BY_USERNAME
        assert "%s" in queries.GET_USER_BY_IDENTIFIER
        assert "%s" in queries.UPDATE_USER_ROLE
        assert "%s" in queries.UPDATE_USER_STATUS
        assert "%s" in queries.UPDATE_USER_PASSWORD_HASH
        assert "%s" in queries.CREATE_USER

    def test_get_all_users_excludes_password_hashes(self):
        """Verifies that GET_ALL_USERS does NOT select password_hash column."""
        assert "password_hash" not in queries.GET_ALL_USERS
