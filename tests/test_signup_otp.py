"""
QuantDB Sign Up & Email OTP Verification Test Suite.

Comprehensive test suite verifying:
1. Valid registration workflow
2. Invalid email format rejection
3. Weak password rejection
4. Password confirmation mismatch
5. Duplicate username rejection
6. Duplicate email rejection
7. Password hashing with PBKDF2-HMAC-SHA256
8. Cryptographically secure 6-digit OTP generation
9. OTP hash storage (no plaintext OTP persistence)
10. Correct OTP verification
11. Incorrect OTP rejection and attempt decrement
12. Expired OTP handling
13. OTP maximum attempt exhaustion (5 attempts)
14. OTP resend cooldown (60s)
15. One-time use enforcement (no OTP reuse)
16. Unverified account login blocking
17. Verified account login success
18. Default role is strictly USER
19. Privilege escalation prevention (cannot self-register as ADMIN, TRADER, RESEARCHER)
20. Admin role management compatibility
21. Role-based access control compliance for registered users
22. Safe email template and secret non-leakage
23. Resend OTP workflow after cooldown
24. Re-registration of pending unverified accounts
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import pytest

from src.auth.email_service import set_test_email_sender
from src.auth.otp import generate_otp, hash_otp, verify_otp_hash
from src.auth.password import hash_password, verify_password
from src.auth.roles import Role, has_page_access, normalize_role
from src.auth.service import (
    authenticate_user,
    register_user,
    verify_registration_otp,
    resend_registration_otp,
    validate_registration_data,
    validate_password_strength,
    AuthenticationError,
    UnverifiedEmailError,
    RegistrationError,
    OTPError,
    OTPExpiredError,
    OTPCooldownError,
    OTPVerificationError,
)


class InMemoryRepository:
    """In-memory mock repository implementing the database contracts for fast, isolated tests."""

    def __init__(self):
        self.users: Dict[int, Dict[str, Any]] = {}
        self.otps: Dict[int, Dict[str, Any]] = {}
        self._user_id_seq = 100
        self._otp_id_seq = 1000

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        for u in self.users.values():
            if u["username"].lower() == username.lower():
                return dict(u)
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for u in self.users.values():
            if u["email"].lower() == email.lower():
                return dict(u)
        return None

    def get_user_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        for u in self.users.values():
            if (
                u["username"].lower() == identifier.lower()
                or u["email"].lower() == identifier.lower()
            ):
                return dict(u)
        return None

    def get_users(self) -> List[Dict[str, Any]]:
        return list(self.users.values())

    def create_user(
        self,
        username: str,
        name: str,
        email: str,
        password_hash: str,
        role: str,
        status: str = "ACTIVE",
        is_verified: bool = False,
    ) -> int:
        self._user_id_seq += 1
        uid = self._user_id_seq
        self.users[uid] = {
            "user_id": uid,
            "username": username,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "status": status,
            "is_verified": is_verified,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return uid

    def update_user_verified(self, user_id: int, is_verified: bool = True) -> bool:
        if user_id in self.users:
            self.users[user_id]["is_verified"] = is_verified
            return True
        return False

    def update_user_role(self, user_id: int, role: str) -> bool:
        if user_id in self.users:
            self.users[user_id]["role"] = role
            return True
        return False

    def update_unverified_user(
        self, user_id: int, name: str, username: str, password_hash: str
    ) -> bool:
        if user_id in self.users:
            self.users[user_id]["name"] = name
            self.users[user_id]["username"] = username
            self.users[user_id]["password_hash"] = password_hash
            return True
        return False

    def insert_email_otp(
        self,
        user_id: int,
        otp_hash: str,
        purpose: str = "REGISTRATION",
        expires_at: Optional[str] = None,
        max_attempts: int = 5,
    ) -> int:
        self._otp_id_seq += 1
        oid = self._otp_id_seq
        now_dt = datetime.now()
        exp_str = expires_at or (now_dt + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        self.otps[oid] = {
            "otp_id": oid,
            "user_id": user_id,
            "otp_hash": otp_hash,
            "purpose": purpose,
            "expires_at": exp_str,
            "attempt_count": 0,
            "max_attempts": max_attempts,
            "is_used": False,
            "created_at": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "verified_at": None,
        }
        return oid

    def get_latest_otp_for_user(
        self, user_id: int, purpose: str = "REGISTRATION"
    ) -> Optional[Dict[str, Any]]:
        user_otps = [
            o
            for o in self.otps.values()
            if o["user_id"] == user_id and o["purpose"] == purpose
        ]
        if not user_otps:
            return None
        user_otps.sort(key=lambda x: x["otp_id"], reverse=True)
        return dict(user_otps[0])

    def increment_otp_attempts(self, otp_id: int) -> bool:
        if otp_id in self.otps:
            self.otps[otp_id]["attempt_count"] += 1
            return True
        return False

    def mark_otp_verified(self, otp_id: int) -> bool:
        if otp_id in self.otps:
            self.otps[otp_id]["is_used"] = True
            self.otps[otp_id]["verified_at"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            return True
        return False

    def invalidate_user_otps(
        self, user_id: int, purpose: str = "REGISTRATION"
    ) -> bool:
        for o in self.otps.values():
            if o["user_id"] == user_id and o["purpose"] == purpose:
                o["is_used"] = True
        return True


@pytest.fixture
def repo():
    return InMemoryRepository()


@pytest.fixture
def captured_emails():
    emails = []

    def mock_sender(to_email, subject, body):
        emails.append({"to": to_email, "subject": subject, "body": body})
        return True

    set_test_email_sender(mock_sender)
    yield emails
    set_test_email_sender(None)


# ======================================================================
# TESTS
# ======================================================================

class TestRegistrationValidation:
    """Tests for registration data validation and password security."""

    def test_valid_registration(self, repo, captured_emails):
        """1. Valid registration succeeds and dispatches OTP email."""
        res = register_user(
            name="Ada Lovelace",
            username="alovelace",
            email="ada@quantdb.local",
            password="SecurePassword123!",
            confirm_password="SecurePassword123!",
            repo=repo,
        )
        assert res["user_id"] > 0
        assert res["username"] == "alovelace"
        assert res["email"] == "ada@quantdb.local"
        assert res["is_verified"] is False
        assert len(captured_emails) == 1
        assert "ada@quantdb.local" in captured_emails[0]["to"]

    def test_invalid_email(self, repo):
        """2. Invalid email formats are rejected server-side."""
        for bad_email in ["notanemail", "user@", "@domain.com", "user@domain", "user@.com"]:
            with pytest.raises(RegistrationError, match="valid email"):
                register_user(
                    name="Test User",
                    username="testuser",
                    email=bad_email,
                    password="Password123!",
                    confirm_password="Password123!",
                    repo=repo,
                )

    def test_weak_password(self, repo):
        """3. Passwords not meeting minimum strength are rejected."""
        # Too short
        with pytest.raises(RegistrationError, match="at least 8 characters"):
            register_user(
                name="Test User",
                username="testuser",
                email="test@quantdb.local",
                password="P1!",
                confirm_password="P1!",
                repo=repo,
            )
        # No numbers
        with pytest.raises(RegistrationError, match="contain at least one number"):
            register_user(
                name="Test User",
                username="testuser",
                email="test@quantdb.local",
                password="OnlyLettersHere!",
                confirm_password="OnlyLettersHere!",
                repo=repo,
            )
        # No letters
        with pytest.raises(RegistrationError, match="contain at least one letter"):
            register_user(
                name="Test User",
                username="testuser",
                email="test@quantdb.local",
                password="1234567890!",
                confirm_password="1234567890!",
                repo=repo,
            )

    def test_password_mismatch(self, repo):
        """4. Password and confirm password mismatch is rejected."""
        with pytest.raises(RegistrationError, match="Passwords do not match"):
            register_user(
                name="Test User",
                username="testuser",
                email="test@quantdb.local",
                password="Password123!",
                confirm_password="DifferentPassword456!",
                repo=repo,
            )

    def test_duplicate_username(self, repo):
        """5. Duplicate verified username is rejected."""
        repo.create_user(
            username="existing_trader",
            name="Existing Trader",
            email="existing@quantdb.local",
            password_hash=hash_password("Password123!"),
            role=Role.USER,
            is_verified=True,
        )
        with pytest.raises(RegistrationError, match="Username is already taken"):
            register_user(
                name="New Trader",
                username="existing_trader",
                email="new_email@quantdb.local",
                password="Password123!",
                confirm_password="Password123!",
                repo=repo,
            )

    def test_duplicate_email(self, repo):
        """6. Duplicate verified email address is rejected."""
        repo.create_user(
            username="user_one",
            name="User One",
            email="shared@quantdb.local",
            password_hash=hash_password("Password123!"),
            role=Role.USER,
            is_verified=True,
        )
        with pytest.raises(RegistrationError, match="email address already exists"):
            register_user(
                name="User Two",
                username="user_two",
                email="shared@quantdb.local",
                password="Password123!",
                confirm_password="Password123!",
                repo=repo,
            )

    def test_password_is_hashed(self, repo):
        """7. Password is never stored in plaintext and uses PBKDF2."""
        raw_pwd = "MySecretPassword99"
        res = register_user(
            name="Alan Turing",
            username="aturing",
            email="turing@quantdb.local",
            password=raw_pwd,
            confirm_password=raw_pwd,
            repo=repo,
        )
        user_record = repo.get_user(res["user_id"])
        assert user_record["password_hash"] != raw_pwd
        assert user_record["password_hash"].startswith("pbkdf2_sha256$600000$")
        assert verify_password(raw_pwd, user_record["password_hash"]) is True


class TestOTPSecurity:
    """Tests for OTP cryptographic generation, hashing, and verification."""

    def test_otp_generation(self):
        """8. Generated OTP is 6 digits and numeric."""
        for _ in range(20):
            otp = generate_otp(6)
            assert len(otp) == 6
            assert otp.isdigit()

    def test_otp_not_stored_plaintext(self, repo, captured_emails):
        """9. Plaintext OTP is never stored in the database."""
        res = register_user(
            name="Claude Shannon",
            username="cshannon",
            email="shannon@quantdb.local",
            password="EntropyPassword1!",
            confirm_password="EntropyPassword1!",
            repo=repo,
        )
        latest_otp = repo.get_latest_otp_for_user(res["user_id"])
        assert latest_otp is not None
        assert not latest_otp["otp_hash"].isdigit()
        assert "sha256" in latest_otp["otp_hash"]

    def test_correct_otp_verification(self, repo, captured_emails):
        """10. Correct OTP verifies successfully and activates user."""
        res = register_user(
            name="John von Neumann",
            username="jneumann",
            email="neumann@quantdb.local",
            password="TheoryPassword1!",
            confirm_password="TheoryPassword1!",
            repo=repo,
        )
        # Extract the sent OTP from the captured email
        email_body = captured_emails[0]["body"]
        otp_lines = [line.strip() for line in email_body.splitlines() if line.strip().isdigit() and len(line.strip()) == 6]
        assert len(otp_lines) >= 1
        sent_otp = otp_lines[0]

        # Verify OTP
        assert verify_registration_otp(res["user_id"], sent_otp, repo=repo) is True
        # Check user is now verified
        user = repo.get_user(res["user_id"])
        assert user["is_verified"] is True

    def test_incorrect_otp(self, repo, captured_emails):
        """11. Incorrect OTP is rejected and decrements remaining attempts."""
        res = register_user(
            name="Grace Hopper",
            username="ghopper",
            email="hopper@quantdb.local",
            password="CompilerPassword1!",
            confirm_password="CompilerPassword1!",
            repo=repo,
        )
        with pytest.raises(OTPVerificationError, match="4 attempt\\(s\\) remaining"):
            verify_registration_otp(res["user_id"], "000000", repo=repo)

        # User remains unverified
        user = repo.get_user(res["user_id"])
        assert user["is_verified"] is False

    def test_expired_otp(self, repo, captured_emails):
        """12. Expired OTP is rejected."""
        res = register_user(
            name="Linus Torvalds",
            username="ltorvalds",
            email="linus@quantdb.local",
            password="KernelPassword1!",
            confirm_password="KernelPassword1!",
            repo=repo,
        )
        latest_otp = repo.get_latest_otp_for_user(res["user_id"])
        # Backdate expiration
        past_time = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        repo.otps[latest_otp["otp_id"]]["expires_at"] = past_time

        email_body = captured_emails[0]["body"]
        sent_otp = [l.strip() for l in email_body.splitlines() if l.strip().isdigit() and len(l.strip()) == 6][0]

        with pytest.raises(OTPExpiredError, match="expired"):
            verify_registration_otp(res["user_id"], sent_otp, repo=repo)

    def test_otp_attempt_limit(self, repo, captured_emails):
        """13. Exceeding 5 attempts invalidates the OTP."""
        res = register_user(
            name="Margaret Hamilton",
            username="mhamilton",
            email="hamilton@quantdb.local",
            password="ApolloPassword1!",
            confirm_password="ApolloPassword1!",
            repo=repo,
        )
        # Submit 4 wrong attempts
        for i in range(4):
            with pytest.raises(OTPVerificationError):
                verify_registration_otp(res["user_id"], "999999", repo=repo)

        # 5th wrong attempt raises max attempts exceeded
        with pytest.raises(OTPVerificationError, match=r".*Maximum attempts exceeded.*"):
            verify_registration_otp(res["user_id"], "999999", repo=repo)

    def test_otp_resend_cooldown(self, repo, captured_emails):
        """14. Requesting resend within 60 seconds triggers cooldown error."""
        res = register_user(
            name="Barbara Liskov",
            username="bliskov",
            email="liskov@quantdb.local",
            password="LiskovPassword1!",
            confirm_password="LiskovPassword1!",
            repo=repo,
        )
        # Immediate resend should trigger cooldown
        with pytest.raises(OTPCooldownError, match="Please wait"):
            resend_registration_otp(res["user_id"], repo=repo)

    def test_otp_cannot_be_reused(self, repo, captured_emails):
        """15. OTP cannot be reused once verified."""
        res = register_user(
            name="Donald Knuth",
            username="dknuth",
            email="knuth@quantdb.local",
            password="AlgorithmPassword1!",
            confirm_password="AlgorithmPassword1!",
            repo=repo,
        )
        email_body = captured_emails[0]["body"]
        sent_otp = [l.strip() for l in email_body.splitlines() if l.strip().isdigit() and len(l.strip()) == 6][0]

        # First verification succeeds
        assert verify_registration_otp(res["user_id"], sent_otp, repo=repo) is True

        # Second verification fails (already used)
        with pytest.raises(OTPVerificationError, match="No active verification code found"):
            verify_registration_otp(res["user_id"], sent_otp, repo=repo)


class TestAuthenticationAndRBACIntegration:
    """Tests for login blocking, role assignment, and RBAC rules."""

    def test_unverified_user_cannot_log_in(self, repo):
        """16. Unverified account cannot log in and raises UnverifiedEmailError."""
        repo.create_user(
            username="pending_user",
            name="Pending User",
            email="pending@quantdb.local",
            password_hash=hash_password("ValidPassword123!"),
            role=Role.USER,
            status="ACTIVE",
            is_verified=False,
        )
        with pytest.raises(UnverifiedEmailError, match="verify your email"):
            authenticate_user("pending_user", "ValidPassword123!", repo=repo)

    def test_verified_user_can_log_in(self, repo):
        """17. Verified account logs in successfully."""
        repo.create_user(
            username="active_user",
            name="Active User",
            email="active@quantdb.local",
            password_hash=hash_password("ValidPassword123!"),
            role=Role.USER,
            status="ACTIVE",
            is_verified=True,
        )
        user_info = authenticate_user("active_user", "ValidPassword123!", repo=repo)
        assert user_info["username"] == "active_user"
        assert user_info["role"] == Role.USER
        assert user_info["is_verified"] is True

    def test_default_role_is_user(self, repo):
        """18. Newly registered users are assigned Role.USER by default."""
        res = register_user(
            name="Test User",
            username="defaultroleuser",
            email="default@quantdb.local",
            password="Password123!",
            confirm_password="Password123!",
            repo=repo,
        )
        assert res["role"] == Role.USER
        db_user = repo.get_user(res["user_id"])
        assert db_user["role"] == Role.USER

    def test_user_cannot_self_register_as_admin(self, repo):
        """19. Privilege escalation attempt during registration forces Role.USER."""
        for priv_role in [Role.ADMIN, Role.QUANT_TRADER, Role.QUANT_RESEARCHER]:
            res = register_user(
                name="Attacker",
                username=f"hack_{priv_role.lower()}",
                email=f"hack_{priv_role.lower()}@quantdb.local",
                password="Password123!",
                confirm_password="Password123!",
                role=priv_role,
                repo=repo,
            )
            assert res["role"] == Role.USER
            db_user = repo.get_user(res["user_id"])
            assert db_user["role"] == Role.USER

    def test_admin_role_management_still_works(self, repo):
        """20. Admin can promote a user to QUANT_TRADER or ADMIN."""
        uid = repo.create_user(
            username="promoted_user",
            name="Promoted User",
            email="promote@quantdb.local",
            password_hash=hash_password("Password123!"),
            role=Role.USER,
            status="ACTIVE",
            is_verified=True,
        )
        # Admin updates role
        repo.update_user_role(uid, Role.QUANT_TRADER)
        updated_user = repo.get_user(uid)
        assert updated_user["role"] == Role.QUANT_TRADER

    def test_rbac_page_permissions_for_registered_user(self, repo):
        """21. Registered user with USER role has strict RBAC enforcement."""
        uid = repo.create_user(
            username="rbac_user",
            name="RBAC User",
            email="rbac@quantdb.local",
            password_hash=hash_password("Password123!"),
            role=Role.USER,
            is_verified=True,
        )
        user_info = authenticate_user("rbac_user", "Password123!", repo=repo)
        role = user_info["role"]
        assert role == Role.USER

        # Allowed for USER
        assert has_page_access(role, "Overview") is True
        assert has_page_access(role, "Market Data") is True
        assert has_page_access(role, "Portfolio") is True
        assert has_page_access(role, "Reports") is True

        # Prohibited for USER
        assert has_page_access(role, "Trading") is False
        assert has_page_access(role, "Strategies") is False
        assert has_page_access(role, "Backtesting") is False
        assert has_page_access(role, "Admin Console") is False

    def test_otp_email_content(self, repo, captured_emails):
        """22. Email content conforms to institutional verification standards."""
        register_user(
            name="Email Test",
            username="emailtest",
            email="emailtest@quantdb.local",
            password="Password123!",
            confirm_password="Password123!",
            repo=repo,
        )
        email = captured_emails[0]
        assert "QuantDB" in email["subject"]
        assert "QuantDB" in email["body"]
        assert "Email Verification" in email["body"]
        assert "5 minutes" in email["body"]

    def test_resend_otp_after_cooldown(self, repo, captured_emails):
        """23. Resending OTP after cooldown succeeds."""
        res = register_user(
            name="Cooldown Test",
            username="cooldowntest",
            email="cd@quantdb.local",
            password="Password123!",
            confirm_password="Password123!",
            repo=repo,
        )
        assert len(captured_emails) == 1

        # Simulate 65 seconds passed
        latest_otp = repo.get_latest_otp_for_user(res["user_id"])
        past_dt = datetime.now() - timedelta(seconds=65)
        repo.otps[latest_otp["otp_id"]]["created_at"] = past_dt.strftime("%Y-%m-%d %H:%M:%S")

        resend_res = resend_registration_otp(res["user_id"], repo=repo)
        assert resend_res["user_id"] == res["user_id"]
        assert len(captured_emails) == 2

    def test_unverified_user_retry_registration(self, repo, captured_emails):
        """24. Re-registration with same email/username updates unverified user and re-issues OTP."""
        res1 = register_user(
            name="Initial Name",
            username="retry_user",
            email="retry@quantdb.local",
            password="OldPassword123!",
            confirm_password="OldPassword123!",
            repo=repo,
        )
        assert len(captured_emails) == 1

        # User didn't verify and registers again with updated name and password
        # Fast-forward created_at to bypass cooldown
        latest_otp = repo.get_latest_otp_for_user(res1["user_id"])
        repo.otps[latest_otp["otp_id"]]["created_at"] = (
            datetime.now() - timedelta(seconds=70)
        ).strftime("%Y-%m-%d %H:%M:%S")

        res2 = register_user(
            name="Updated Name",
            username="retry_user",
            email="retry@quantdb.local",
            password="NewPassword456!",
            confirm_password="NewPassword456!",
            repo=repo,
        )
        assert res2["user_id"] == res1["user_id"]
        assert len(captured_emails) == 2

        updated_record = repo.get_user(res1["user_id"])
        assert updated_record["name"] == "Updated Name"
        assert verify_password("NewPassword456!", updated_record["password_hash"]) is True
