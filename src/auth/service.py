"""
QuantDB Core Authentication & Authorization Service.

Handles credential verification, account state enforcement, role resolution,
security permission checks, user registration, and email OTP verification for QuantDB.
"""

from datetime import datetime, timedelta
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from src.auth.email_service import send_otp_email
from src.auth.otp import generate_otp, hash_otp, verify_otp_hash
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

# Constants
OTP_EXPIRY_SECONDS = 300  # 5 minutes
OTP_COOLDOWN_SECONDS = 60  # 60 seconds resend cooldown
OTP_MAX_ATTEMPTS = 5


class AuthenticationError(Exception):
    """Raised when authentication fails due to invalid credentials or user state."""
    pass


class AccountInactiveError(AuthenticationError):
    """Raised when an account is inactive, disabled, or suspended."""
    pass


class UnverifiedEmailError(AuthenticationError):
    """Raised when an unverified account attempts to authenticate."""

    def __init__(
        self,
        message: str = "Please verify your email before signing in.",
        email: str = "",
        username: str = "",
        user_id: Optional[int] = None,
    ):
        super().__init__(message)
        self.email = email
        self.username = username
        self.user_id = user_id


class AuthorizationError(Exception):
    """Raised when an authenticated user attempts an unauthorized operation."""
    pass


class RegistrationError(Exception):
    """Raised when registration input validation or database persistence fails."""
    pass


class OTPError(Exception):
    """Base exception for OTP-related failures."""
    pass


class OTPExpiredError(OTPError):
    """Raised when an OTP has passed its expiration time."""
    pass


class OTPCooldownError(OTPError):
    """Raised when an OTP resend request violates the cooldown window."""

    def __init__(self, message: str, seconds_remaining: int = 0):
        super().__init__(message)
        self.seconds_remaining = seconds_remaining


class OTPVerificationError(OTPError):
    """Raised when an invalid OTP is entered or attempts are exceeded."""
    pass


def _parse_datetime(val: Any) -> Optional[datetime]:
    """Safely parses a datetime object or formatted string."""
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue
    return None


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validates minimum password complexity requirements:
    - At least 8 characters
    - At least one letter
    - At least one digit
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    return True, ""


def validate_registration_data(
    name: str,
    username: str,
    email: str,
    password: str,
    confirm_password: str,
    phone: Optional[str] = None,
) -> None:
    """
    Strict server-side validation for user registration data.
    Raises RegistrationError if any validation check fails.
    """
    if not name or not name.strip():
        raise RegistrationError("Full Name is required.")
    if len(name.strip()) < 2:
        raise RegistrationError("Full Name must be at least 2 characters.")
    if len(name.strip()) > 100:
        raise RegistrationError("Full Name must not exceed 100 characters.")

    if not username or not username.strip():
        raise RegistrationError("Username is required.")
    clean_uname = username.strip()
    if not re.match(r"^[a-zA-Z0-9_]{3,30}$", clean_uname):
        raise RegistrationError(
            "Username must be 3-30 characters and contain only letters, numbers, and underscores."
        )

    if not email or not email.strip():
        raise RegistrationError("Email Address is required.")
    clean_email = email.strip().lower()
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, clean_email):
        raise RegistrationError("Please enter a valid email address.")

    if not password:
        raise RegistrationError("Password is required.")
    if password != confirm_password:
        raise RegistrationError("Passwords do not match.")

    valid_pwd, pwd_msg = validate_password_strength(password)
    if not valid_pwd:
        raise RegistrationError(pwd_msg)

    if phone and phone.strip():
        clean_phone = phone.strip()
        if not re.match(r"^\+?[0-9\s\-\(\)]{7,20}$", clean_phone):
            raise RegistrationError("Please enter a valid phone number.")


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
        4. Account verification check (is_verified must be True)
        5. Account status verification (must be 'ACTIVE')
        6. Role resolution and normalization
        7. Return sanitized user session payload (NEVER returns password hash)
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

    # Check email verification status
    is_verified = user.get("is_verified")
    # If is_verified is explicitly False or 0, block sign in
    if is_verified is False or is_verified == 0:
        raise UnverifiedEmailError(
            message="Please verify your email before signing in.",
            email=user.get("email") or "",
            username=user.get("username") or "",
            user_id=user.get("user_id"),
        )

    status = str(user.get("status", "")).upper()
    if status != "ACTIVE":
        if status == "SUSPENDED":
            raise AccountInactiveError("This account has been suspended. Please contact administrator.")
        raise AccountInactiveError("This account is inactive. Please contact administrator.")

    raw_role = user.get("role", Role.USER)
    canonical_role = normalize_role(raw_role)

    # Synthetic username for UI and backward compatibility (mapped to email/name when column is absent)
    synthetic_username = (
        user.get("username")
        or (clean_id if "@" not in clean_id else "")
        or (user.get("email", "").split("@")[0] if user.get("email") else "")
        or user.get("name")
        or clean_id
    )

    # Return safe user profile for session state (strictly omitting credentials)
    return {
        "user_id": user["user_id"],
        "username": synthetic_username,
        "name": user.get("name") or clean_id,
        "email": user.get("email") or "",
        "role": canonical_role,
        "role_display": get_role_display_name(canonical_role),
        "status": status,
        "is_verified": bool(user.get("is_verified", True)),
        "created_at": str(user.get("created_at", "")),
    }


def issue_and_send_otp(
    user_id: int,
    email: str,
    name: str,
    repo: Optional[Repository] = None,
) -> Dict[str, Any]:
    """
    Generates a secure 6-digit OTP, hashes it, stores the record in MySQL,
    and dispatches the verification email. Enforces a 60-second resend cooldown.
    """
    if repo is None:
        repo = Repository()

    # Check resend cooldown against latest active OTP
    try:
        latest_otp = repo.get_latest_otp_for_user(user_id, purpose="REGISTRATION")
    except Exception as e:
        logger.error(f"Database error checking latest OTP: {e}")
        raise OTPError(f"Database error during verification code check: {e}")

    if latest_otp and not latest_otp.get("is_used"):
        created_at_dt = _parse_datetime(latest_otp.get("created_at"))
        if created_at_dt:
            elapsed = (datetime.now() - created_at_dt).total_seconds()
            if elapsed < OTP_COOLDOWN_SECONDS:
                remaining = int(OTP_COOLDOWN_SECONDS - elapsed)
                raise OTPCooldownError(
                    f"Please wait {max(1, remaining)} seconds before requesting a new code.",
                    seconds_remaining=max(1, remaining),
                )

    # Generate cryptographically secure 6-digit OTP
    otp = generate_otp(length=6)
    otp_hash = hash_otp(otp)

    # Store OTP in database with 5 minute expiry
    expires_at = (datetime.now() + timedelta(seconds=OTP_EXPIRY_SECONDS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    try:
        # Invalidate previous OTPs for this registration
        repo.invalidate_user_otps(user_id, purpose="REGISTRATION")
        repo.insert_email_otp(
            user_id=user_id,
            otp_hash=otp_hash,
            purpose="REGISTRATION",
            expires_at=expires_at,
            max_attempts=OTP_MAX_ATTEMPTS,
        )
    except Exception as e:
        logger.error(f"Database error persisting OTP: {e}")
        raise OTPError(f"Database error saving verification code: {e}")

    # Dispatch email
    sent = send_otp_email(
        recipient_email=email,
        recipient_name=name,
        otp=otp,
        expiry_minutes=OTP_EXPIRY_SECONDS // 60,
    )
    if not sent:
        logger.warning(f"OTP email dispatch reported failure for user_id={user_id}")

    return {
        "user_id": user_id,
        "email": email,
        "expires_in_seconds": OTP_EXPIRY_SECONDS,
    }


def register_user(
    name: str,
    username: str,
    email: str,
    password: str,
    confirm_password: str,
    phone: Optional[str] = None,
    role: Optional[str] = None,
    repo: Optional[Repository] = None,
) -> Dict[str, Any]:
    """
    Registers a new user and dispatches an email OTP for verification.

    Security Rules:
        - Default role is strictly Role.USER.
        - Public registration cannot assign privileged roles (Admin, Trader, Researcher).
        - Account starts unverified (is_verified = False).
        - Passwords are encrypted using PBKDF2-HMAC-SHA256 before persistence.
        - Plaintext OTP is never stored in the database.
    """
    if repo is None:
        repo = Repository()

    # Step 1: Validate registration data server-side
    validate_registration_data(
        name=name,
        username=username,
        email=email,
        password=password,
        confirm_password=confirm_password,
        phone=phone,
    )

    clean_name = name.strip()
    clean_username = username.strip()
    clean_email = email.strip().lower()

    # Step 2: Role security enforcement: public registration is ALWAYS Role.USER
    target_role = Role.USER
    if role and normalize_role(role) != Role.USER:
        logger.warning(
            f"Privilege escalation attempt blocked during signup for username '{clean_username}'. Defaulting to USER."
        )

    # Step 3: Check for existing accounts
    try:
        existing_by_uname = repo.get_user_by_username(clean_username) if clean_username else None
        existing_by_email = repo.get_user_by_email(clean_email)
    except Exception as e:
        logger.error(f"Database error during registration lookup: {e}")
        raise RegistrationError(f"Registration database error: {e}")

    # Check for username collision (in mocks/environments where distinct username is provided)
    if existing_by_uname and existing_by_uname.get("is_verified") and existing_by_uname.get("email") != clean_email:
        # Only block if it is explicitly a different user's verified account
        if existing_by_uname.get("username", "").lower() == clean_username.lower():
            raise RegistrationError("Username is already taken. Please choose another.")
    if existing_by_email and existing_by_email.get("is_verified"):
        raise RegistrationError("An account with this email address already exists.")

    pwd_hash = hash_password(password)

    # Step 4: Handle pending unverified accounts or create new account
    try:
        if existing_by_email and not existing_by_email.get("is_verified"):
            user_id = existing_by_email["user_id"]
            repo.update_unverified_user(
                user_id=user_id,
                name=clean_name,
                username=clean_username,
                password_hash=pwd_hash,
            )
        elif existing_by_uname and not existing_by_uname.get("is_verified"):
            user_id = existing_by_uname["user_id"]
            repo.update_unverified_user(
                user_id=user_id,
                name=clean_name,
                username=clean_username,
                password_hash=pwd_hash,
            )
        else:
            # Create fresh record strictly adhering to actual QuantDB schema contract
            user_id = repo.create_user(
                name=clean_name,
                email=clean_email,
                password_hash=pwd_hash,
                role=target_role,
                status="ACTIVE",
                username=clean_username,
                is_verified=False,
            )
    except Exception as e:
        logger.error(f"Database error during registration persistence: {e}")
        raise RegistrationError(f"Registration database error: {e}")

    # Step 5: Issue and send OTP
    otp_info = issue_and_send_otp(
        user_id=user_id,
        email=clean_email,
        name=clean_name,
        repo=repo,
    )

    return {
        "user_id": user_id,
        "username": clean_username,
        "email": clean_email,
        "name": clean_name,
        "role": target_role,
        "is_verified": False,
        "expires_in_seconds": otp_info["expires_in_seconds"],
    }


def verify_registration_otp(
    user_id: int,
    entered_otp: str,
    repo: Optional[Repository] = None,
) -> bool:
    """
    Validates a submitted 6-digit OTP against the stored hash in MySQL.

    Enforces:
        - OTP hash matching (constant-time)
        - Expiration time (5 minutes)
        - Maximum attempt count (5 attempts)
        - Post-verification invalidation
        - Marks user account as verified (is_verified = True)
    """
    if repo is None:
        repo = Repository()

    if not entered_otp or not str(entered_otp).strip():
        raise OTPVerificationError("Please enter the verification code.")

    clean_otp = str(entered_otp).strip()
    if not clean_otp.isdigit() or len(clean_otp) != 6:
        raise OTPVerificationError("Verification code must be exactly 6 digits.")

    try:
        latest_otp = repo.get_latest_otp_for_user(user_id, purpose="REGISTRATION")
    except Exception as e:
        logger.error(f"Database error during OTP lookup: {e}")
        raise OTPVerificationError(f"Database error during verification code lookup: {e}")

    if not latest_otp or latest_otp.get("is_used"):
        raise OTPVerificationError(
            "No active verification code found. Please request a new code."
        )

    attempt_count = int(latest_otp.get("attempt_count", 0))
    max_attempts = int(latest_otp.get("max_attempts", OTP_MAX_ATTEMPTS))

    if attempt_count >= max_attempts:
        try:
            repo.invalidate_user_otps(user_id, purpose="REGISTRATION")
        except Exception:
            pass
        raise OTPVerificationError(
            "Maximum verification attempts exceeded. Please request a new code."
        )

    # Check expiration
    expires_at_dt = _parse_datetime(latest_otp.get("expires_at"))
    if expires_at_dt and datetime.now() > expires_at_dt:
        raise OTPExpiredError(
            "Verification code has expired. Please request a new code."
        )

    # Compare hash
    otp_hash = latest_otp.get("otp_hash", "")
    if not verify_otp_hash(clean_otp, otp_hash):
        try:
            repo.increment_otp_attempts(latest_otp["otp_id"])
        except Exception:
            pass
        new_attempts = attempt_count + 1
        if new_attempts >= max_attempts:
            try:
                repo.invalidate_user_otps(user_id, purpose="REGISTRATION")
            except Exception:
                pass
            raise OTPVerificationError(
                "Incorrect verification code. Maximum attempts exceeded. Please request a new code."
            )
        remaining = max_attempts - new_attempts
        raise OTPVerificationError(
            f"Incorrect verification code. {remaining} attempt(s) remaining."
        )

    # Match confirmed! Mark OTP as used and mark user account as verified
    try:
        repo.mark_otp_verified(latest_otp["otp_id"])
        repo.update_user_verified(user_id, is_verified=True)
    except Exception as e:
        logger.error(f"Database error finalizing verification: {e}")
        raise OTPVerificationError(f"Database error finalizing verification: {e}")
    logger.info(f"User user_id={user_id} successfully verified email.")
    return True


def resend_registration_otp(
    identifier_or_user_id: Any,
    repo: Optional[Repository] = None,
) -> Dict[str, Any]:
    """
    Resends an OTP to an unverified user's email address subject to cooldown.
    """
    if repo is None:
        repo = Repository()

    try:
        if isinstance(identifier_or_user_id, int):
            user = repo.get_user(identifier_or_user_id)
        else:
            user = repo.get_user_by_identifier(str(identifier_or_user_id).strip())
    except Exception as e:
        logger.error(f"Database error during OTP resend user lookup: {e}")
        raise RegistrationError(f"Database error during code resend: {e}")

    if not user:
        raise RegistrationError("User account not found.")

    if user.get("is_verified"):
        raise RegistrationError("Account is already verified. Please sign in.")

    return issue_and_send_otp(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        repo=repo,
    )


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
