"""
QuantDB Dashboard Authentication & Authorization Service.

Integrates the presentation layer with backend authentication, handles Streamlit
session state, user profile caching, enforces Role-Based Access Control (RBAC),
and provides the Sign Up registration and Email OTP verification workflows.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import streamlit as st

from src.auth.password import hash_password, verify_password
from src.auth.roles import (
    Role,
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
    authenticate_user as backend_authenticate,
    register_user as backend_register_user,
    verify_registration_otp as backend_verify_otp,
    resend_registration_otp as backend_resend_otp,
    AuthenticationError,
    AccountInactiveError,
    UnverifiedEmailError,
    AuthorizationError,
    RegistrationError,
    OTPError,
    OTPExpiredError,
    OTPCooldownError,
    OTPVerificationError,
)
from src.database.repository import Repository
from dashboard.providers.factory import get_current_data_mode
from src.auth import firebase_auth

logger = logging.getLogger(__name__)

# Fallback in-memory credentials for offline development when database is unavailable
MOCK_USERS_SEED: List[Dict[str, Any]] = [
    {
        "user_id": 101,
        "username": "user01",
        "name": "Standard User",
        "email": "user01@quantdb.local",
        "password": "User01@QuantDB",
        "role": Role.USER,
        "status": "ACTIVE",
        "is_verified": True,
    },
    {
        "user_id": 102,
        "username": "trader01",
        "name": "Quant Trader Demo",
        "email": "trader01@quantdb.local",
        "password": "Trader01@QuantDB",
        "role": Role.QUANT_TRADER,
        "status": "ACTIVE",
        "is_verified": True,
    },
    {
        "user_id": 103,
        "username": "researcher01",
        "name": "Quant Researcher Demo",
        "email": "researcher01@quantdb.local",
        "password": "Researcher01@QuantDB",
        "role": Role.QUANT_RESEARCHER,
        "status": "ACTIVE",
        "is_verified": True,
    },
    {
        "user_id": 105,
        "username": "developer01",
        "name": "Quant Developer Demo",
        "email": "developer01@quantdb.local",
        "password": "Developer01@QuantDB",
        "role": Role.QUANT_DEVELOPER,
        "status": "ACTIVE",
        "is_verified": True,
    },
    {
        "user_id": 104,
        "username": "admin01",
        "name": "Admin Demo",
        "email": "admin01@quantdb.local",
        "password": "Admin01@QuantDB",
        "role": Role.ADMIN,
        "status": "ACTIVE",
        "is_verified": True,
    },
]


def init_session_state() -> None:
    """Ensures authentication and verification keys are initialized in Streamlit session state."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "display_name" not in st.session_state:
        st.session_state["display_name"] = None
    if "email" not in st.session_state:
        st.session_state["email"] = None
    if "role" not in st.session_state:
        st.session_state["role"] = None
    if "role_display" not in st.session_state:
        st.session_state["role_display"] = None
    if "auth_screen" not in st.session_state:
        st.session_state["auth_screen"] = "signin"
    if "pending_verification" not in st.session_state:
        st.session_state["pending_verification"] = None
    if "otp_msg" not in st.session_state:
        st.session_state["otp_msg"] = None


def is_authenticated() -> bool:
    """Returns True if the current browser session has an active authenticated user."""
    init_session_state()
    return bool(st.session_state.get("authenticated", False))


def get_current_user() -> Optional[Dict[str, Any]]:
    """Returns dictionary of currently logged-in user profile, or None."""
    if not is_authenticated():
        return None
    return {
        "user_id": st.session_state.get("user_id"),
        "username": st.session_state.get("username"),
        "display_name": st.session_state.get("display_name"),
        "email": st.session_state.get("email"),
        "role": st.session_state.get("role"),
        "role_display": st.session_state.get("role_display"),
    }


def get_current_role() -> str:
    """Returns the normalized role of the authenticated session, defaulting to USER."""
    if not is_authenticated():
        return Role.USER
    return normalize_role(st.session_state.get("role", Role.USER))


def update_current_username(username: str) -> Tuple[bool, str]:
    """Persist the signed-in user's username to the authoritative MySQL row."""
    clean_username = (username or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", clean_username):
        return False, "Username must be 3-30 characters and use only letters, numbers, or underscores."
    user_id = st.session_state.get("user_id")
    if not is_authenticated() or not user_id:
        return False, "Please sign in again before changing your username."
    try:
        repo = Repository()
        repo.update_user_username(user_id, clean_username)
        st.session_state["username"] = clean_username
        return True, "Username saved to the QuantDB database."
    except Exception as exc:
        logger.warning("Could not update username for user_id=%s: %s", user_id, exc)
        message = str(exc).lower()
        if "duplicate" in message or "1062" in message:
            return False, "That username is already taken. Choose another one."
        return False, "Could not save the username. Check the MySQL connection and try again."


ROLE_OPTION_MAP: Dict[str, str] = {
    "User": Role.USER,
    "Quant Trader": Role.QUANT_TRADER,
    "Quant Developer": Role.QUANT_DEVELOPER,
    "Quant Researcher": Role.QUANT_RESEARCHER,
    "Admin": Role.ADMIN,
    Role.USER: Role.USER,
    Role.QUANT_TRADER: Role.QUANT_TRADER,
    Role.QUANT_DEVELOPER: Role.QUANT_DEVELOPER,
    Role.QUANT_RESEARCHER: Role.QUANT_RESEARCHER,
    Role.ADMIN: Role.ADMIN,
}


def login(identifier: str, password: str, selected_role: Optional[str] = None) -> Tuple[bool, str]:
    """
    Attempts to authenticate a user by username or email.
    Stores only safe session information upon success.
    Applies selected_role if chosen by user.
    """
    init_session_state()
    if not identifier or not identifier.strip():
        return False, "Please enter your username or email."
    if not password:
        return False, "Please enter your password."

    clean_id = identifier.strip()

    # Pre-resolve username to email from MySQL repository
    db_profile = None
    try:
        repo = Repository()
        db_profile = repo.get_user_by_identifier(clean_id)
        if db_profile and db_profile.get("email"):
            clean_id = db_profile["email"]
    except Exception as e:
        logger.debug(f"Could not lookup user by identifier {clean_id}: {e}")

    # Prefer Firebase when configured. Firebase users sign in with email;
    # legacy MySQL accounts remain usable when Firebase is not configured.
    if firebase_auth.is_configured():
        try:
            user_info = firebase_auth.authenticate(clean_id, password)
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = user_info["user_id"]
            st.session_state["username"] = user_info["username"]
            st.session_state["display_name"] = user_info["name"]
            st.session_state["email"] = user_info["email"]
            st.session_state["role"] = user_info["role"]
            st.session_state["role_display"] = user_info["role_display"]
            st.session_state["auth_screen"] = "signin"
            st.session_state["pending_verification"] = None

            # Enrich from MySQL user record if available
            try:
                repo = Repository()
                existing = db_profile or repo.get_user_by_email(user_info["email"])
                if existing:
                    st.session_state["user_id"] = existing["user_id"]
                    if existing.get("username"):
                        st.session_state["username"] = existing["username"]
                    if existing.get("name"):
                        st.session_state["display_name"] = existing["name"]
                    # MySQL is the authoritative source for app roles.
                    if existing.get("role"):
                        st.session_state["role"] = existing["role"]
                        st.session_state["role_display"] = get_role_display_name(existing["role"])
                else:
                    final_role = Role.USER
                    st.session_state["role"] = final_role
                    st.session_state["role_display"] = get_role_display_name(final_role)
                    from src.auth.password import hash_password
                    uname = user_info["email"].split("@")[0]
                    database_user_id = repo.create_user(
                        username=uname,
                        name=user_info.get("name", uname),
                        email=user_info["email"],
                        password_hash=hash_password(password),
                        role=final_role,
                        status="ACTIVE",
                    )
                    st.session_state["user_id"] = database_user_id
                from dashboard.services.analytics_service import clear_analytics_service_cache
                clear_analytics_service_cache()
            except Exception as sync_err:
                logger.exception("Firebase login could not synchronize with MySQL")
                st.session_state["authenticated"] = False
                st.session_state["user_id"] = None
                st.session_state["role"] = None
                st.session_state["role_display"] = None
                return False, (
                    "Your Firebase credentials are valid, but QuantDB MySQL is "
                    "unavailable, so sign-in cannot complete. Check the database "
                    "connection and retry."
                )

            # Dispatch security login alert email to user asynchronously
            import threading
            def _async_mail_fb(to_email, u_name):
                try:
                    from src.auth.email_service import send_login_alert_email
                    send_login_alert_email(to_email=to_email, user_name=u_name)
                except Exception as mail_err:
                    logger.warning(f"Could not dispatch login alert email: {mail_err}")

            threading.Thread(target=_async_mail_fb, args=(user_info["email"], user_info.get("name", "")), daemon=True).start()

            return True, "Authentication successful."
        except firebase_auth.FirebaseAuthError as e:
            return False, str(e)
        except Exception:
            logger.exception("Firebase authentication failed unexpectedly")
            return False, "Firebase sign-in failed. Please try again."

    # Attempt MySQL Database Authentication first
    try:
        repo = Repository()
        user_info = backend_authenticate(clean_id, password, repo=repo)

        # Populate session state
        st.session_state["authenticated"] = True
        st.session_state["user_id"] = user_info["user_id"]
        st.session_state["username"] = user_info["username"]
        st.session_state["display_name"] = user_info["name"]
        st.session_state["email"] = user_info["email"]
        st.session_state["role"] = user_info["role"]
        st.session_state["role_display"] = user_info["role_display"]
        st.session_state["auth_screen"] = "signin"
        st.session_state["pending_verification"] = None

        # Dispatch security login alert email to user asynchronously
        import threading
        def _async_mail_sql(to_email, u_name):
            try:
                from src.auth.email_service import send_login_alert_email
                send_login_alert_email(to_email=to_email, user_name=u_name)
            except Exception as mail_err:
                logger.warning(f"Could not dispatch login alert email: {mail_err}")

        threading.Thread(target=_async_mail_sql, args=(user_info["email"], user_info.get("name", "")), daemon=True).start()

        return True, "Authentication successful."

    except UnverifiedEmailError as e:
        # Prompt user to verify and transition to OTP screen
        st.session_state["pending_verification"] = {
            "user_id": e.user_id,
            "email": e.email,
            "username": e.username,
        }
        st.session_state["auth_screen"] = "verify"
        st.session_state["otp_msg"] = "Please verify your email before signing in."
        return False, "Please verify your email before signing in."

    except AccountInactiveError as e:
        return False, str(e)
    except AuthenticationError as e:
        # Check if database is completely offline and we can fall back in pure mock mode
        err_msg = str(e)
        if "unavailable" in err_msg.lower():
            # Fallback for offline mock demo
            for mu in MOCK_USERS_SEED:
                if (
                    mu["username"].lower() == clean_id.lower()
                    or mu["email"].lower() == clean_id.lower()
                ) and mu["password"] == password:
                    if mu["status"] != "ACTIVE":
                        return False, "This account is inactive. Please contact administrator."
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = mu["user_id"]
                    st.session_state["username"] = mu["username"]
                    st.session_state["display_name"] = mu["name"]
                    st.session_state["email"] = mu["email"]
                    st.session_state["role"] = mu["role"]
                    st.session_state["role_display"] = get_role_display_name(mu["role"])
                    return True, "Authentication successful (offline simulation)."
        return False, err_msg
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}")
        return False, "An unexpected error occurred during login. Please try again."


def signup(
    name: str,
    username: str,
    email: str,
    password: str,
    confirm_password: str,
    phone: Optional[str] = None,
    role: str = Role.USER,
) -> Tuple[bool, str]:
    """
    Handles user registration using Firebase (password-only, no email verification required).
    """
    init_session_state()
    # Public signup can never grant elevated permissions. Roles are assigned
    # through the administrator-controlled users table after registration.
    chosen_role = Role.USER
    if firebase_auth.is_configured():
        if not email or "@" not in email:
            return False, "Please enter a valid email address."
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters."
        if password != confirm_password:
            return False, "Passwords do not match."
        try:
            clean_username = (username or "").strip()
            if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", clean_username):
                return False, "Username must be 3-30 characters and use only letters, numbers, or underscores."
            user_info = firebase_auth.sign_up(email=email, password=password, display_name=name)
            # Synchronously and reliably persist user profile into MySQL database
            try:
                repo = Repository()
                from src.auth.password import hash_password
                clean_email = email.strip().lower()
                clean_name = (name or user_info.get("name", "")).strip() or clean_email.split("@")[0]
                uname = clean_username
                existing = repo.get_user_by_email(clean_email)
                if not existing:
                    repo.create_user(
                        username=uname,
                        name=clean_name,
                        email=clean_email,
                        password_hash=hash_password(password),
                        role=Role.USER,
                        status="ACTIVE",
                    )
                else:
                    repo.update_user_username(existing["user_id"], uname)
                    repo.update_user_status(existing["user_id"], "ACTIVE")
                    repo.update_user_verified(existing["user_id"], True)
                
                from dashboard.services.analytics_service import clear_analytics_service_cache
                clear_analytics_service_cache()
            except Exception as sync_err:
                logger.exception("MySQL user sync failed after Firebase signup")
                return False, (
                    "Firebase created the account, but it could not be saved to the "
                    "QuantDB MySQL database. Check the database connection, then "
                    "sign in again to retry synchronization."
                )

            return True, f"Account created successfully! You can now sign in with your email and password."
        except firebase_auth.FirebaseAuthError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Error during Firebase registration: {e}")
            return False, f"Registration failed: {e}"

    try:
        repo = Repository()
        res = backend_register_user(
            name=name,
            username=username,
            email=email,
            password=password,
            confirm_password=confirm_password,
            phone=phone,
            role=chosen_role,
            repo=repo,
        )
        st.session_state["pending_verification"] = {
            "user_id": res["user_id"],
            "email": res["email"],
            "username": res["username"],
            "name": res["name"],
        }
        st.session_state["auth_screen"] = "verify"
        st.session_state["otp_msg"] = "Verification code sent to your email."
        return True, "Verification code sent to your email."
    except RegistrationError as e:
        return False, str(e)
    except OTPCooldownError as e:
        return False, str(e)
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return False, f"Registration failed: {e}"


def verify_otp_code(user_id: int, entered_code: str) -> Tuple[bool, str]:
    """
    Submits the 6-digit OTP to the backend service for cryptographic verification.
    """
    try:
        repo = Repository()
        backend_verify_otp(user_id=user_id, entered_otp=entered_code, repo=repo)
        st.session_state["pending_verification"] = None
        st.session_state["auth_screen"] = "verified_success"
        return True, "Email verified successfully."
    except (OTPVerificationError, OTPExpiredError, OTPError) as e:
        return False, str(e)
    except Exception as e:
        logger.error(f"Error during OTP verification: {e}")
        return False, f"Verification failed: {e}"


def resend_otp_code(user_id_or_identifier: Any) -> Tuple[bool, str]:
    """
    Requests a fresh OTP subject to 60-second cooldown.
    """
    try:
        repo = Repository()
        backend_resend_otp(user_id_or_identifier, repo=repo)
        return True, "Verification code resent to your email."
    except (OTPCooldownError, RegistrationError, OTPError) as e:
        return False, str(e)
    except Exception as e:
        logger.error(f"Error resending OTP: {e}")
        return False, f"Failed to resend code: {e}"


def logout() -> None:
    """Logs out the current session and clears all authentication state."""
    init_session_state()
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = None
    st.session_state["display_name"] = None
    st.session_state["email"] = None
    st.session_state["role"] = None
    st.session_state["role_display"] = None
    st.session_state["auth_screen"] = "signin"
    st.session_state["pending_verification"] = None


def check_page_access(page_name: str) -> bool:
    """Verifies if the current session role is allowed to view page_name."""
    if not is_authenticated():
        return False
    role = get_current_role()
    return has_page_access(role, page_name)


def render_access_restricted_banner(page_name: str) -> None:
    """Renders a polished, terminal-styled access restricted alert message."""
    curr_user = get_current_user() or {}
    role_display = curr_user.get("role_display", "User")
    username = curr_user.get("username", "Guest")

    st.markdown(
        f"""
        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 8px; padding: 24px; margin: 30px auto; max-width: 750px; text-align: center;">
            <div style="font-size: 2.2rem; margin-bottom: 12px;">🛡️</div>
            <div style="font-size: 1.35rem; font-weight: 800; color: #FCA5A5; letter-spacing: -0.01em; margin-bottom: 8px;">
                Access Restricted
            </div>
            <div style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.5; margin-bottom: 16px;">
                Your current role (<strong style="color: #38BDF8;">{role_display}</strong>) does not have permission to access the <strong>{page_name}</strong> module.
            </div>
            <div style="font-size: 0.80rem; color: #94A3B8; font-family: 'JetBrains Mono', monospace; background: #0F172A; display: inline-block; padding: 6px 14px; border-radius: 4px; border: 1px solid #1E293B;">
                SECURITY STATUS: RBAC DENIED • USER: {username} • ROLE: {role_display}
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("← Return to Overview", use_container_width=True, type="primary"):
            st.switch_page("app.py")


def render_login_screen() -> None:
    """Renders the QuantDB terminal authentication, registration, and OTP screens."""
    init_session_state()

    st.markdown(
        """
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 35px; margin-bottom: 25px;">
            <div style="background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%); width: 44px; height: 44px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 24px; color: #0B0F19; margin-bottom: 12px; box-shadow: 0 4px 14px rgba(6, 182, 212, 0.4);">Q</div>
            <h1 style="margin: 0; font-size: 2.3rem; font-weight: 900; letter-spacing: 0.08em; color: #F8FAFC; font-family: 'JetBrains Mono', monospace;">
                QUANT<span style="color: #06B6D4;">DB</span>
            </h1>
            <div style="color: #94A3B8; font-size: 0.92rem; font-weight: 500; margin-top: 4px;">
                Quantitative Finance Research & Simulation Platform
            </div>
            <div style="font-size: 0.75rem; color: #06B6D4; margin-top: 6px; letter-spacing: 0.05em; font-family: 'JetBrains Mono', monospace; background: rgba(6, 182, 212, 0.1); padding: 3px 12px; border-radius: 12px; border: 1px solid rgba(6, 182, 212, 0.25);">
                ACADEMIC SIMULATION ENVIRONMENT • SECURE ACCESS GATEWAY
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    col_l, col_center, col_r = st.columns([1, 1.4, 1])
    with col_center:
        auth_mode = st.session_state.get("auth_screen", "signin")

        # -------------------------------------------------------------
        # SCREEN 1: VERIFIED SUCCESS SCREEN
        # -------------------------------------------------------------
        if auth_mode == "verified_success":
            st.markdown(
                """
                <div style="background: #111827; border: 1px solid #10B981; border-radius: 10px; padding: 26px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); text-align: center;">
                    <div style="font-size: 2.6rem; margin-bottom: 12px;">✅</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #10B981; margin-bottom: 8px;">
                        Account Verified Successfully
                    </div>
                    <div style="color: #CBD5E1; font-size: 0.90rem; line-height: 1.5; margin-bottom: 20px;">
                        Your institutional QuantDB account is now fully active with default <strong>User</strong> permissions. You may now sign in to access the platform.
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            if st.button("Continue to Sign In", type="primary", use_container_width=True):
                st.session_state["auth_screen"] = "signin"
                st.rerun()

        # -------------------------------------------------------------
        # SCREEN 2: EMAIL OTP VERIFICATION SCREEN
        # -------------------------------------------------------------
        elif auth_mode == "verify":
            pending = st.session_state.get("pending_verification") or {}
            target_email = pending.get("email", "your email address")
            target_uid = pending.get("user_id")

            st.markdown(
                f"""
                <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 22px 26px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);">
                    <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #E2E8F0; letter-spacing: 0.06em; margin-bottom: 10px; border-bottom: 1px solid #1F2937; padding-bottom: 8px;">
                        EMAIL VERIFICATION
                    </div>
                    <div style="font-size: 0.85rem; color: #38BDF8; margin-bottom: 12px; font-weight: 600;">
                        Verification code sent to your email.
                    </div>
                    <div style="color: #94A3B8; font-size: 0.82rem; margin-bottom: 14px; line-height: 1.4;">
                        Enter the 6-digit OTP sent to: <strong style="color: #F8FAFC;">{target_email}</strong><br>
                        <span style="font-size: 0.75rem; color: #F59E0B;">⏳ This OTP expires in 5 minutes.</span>
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            with st.form("quantdb_otp_verify_form", clear_on_submit=False):
                entered_otp = st.text_input(
                    "6-Digit Verification Code",
                    max_chars=6,
                    placeholder="123456",
                    help="Enter the 6-digit verification code sent to your email.",
                )
                verify_btn = st.form_submit_button(
                    "VERIFY OTP", type="primary", use_container_width=True
                )

                if verify_btn:
                    if not target_uid:
                        st.error("Verification session expired. Please start registration again.")
                    else:
                        v_ok, v_msg = verify_otp_code(target_uid, entered_otp)
                        if v_ok:
                            st.success("Account verified successfully.")
                            st.rerun()
                        else:
                            st.error(v_msg)

            # Resend OTP and Back Controls
            col_resend, col_back = st.columns(2)
            with col_resend:
                if st.button("RESEND OTP", use_container_width=True):
                    if target_uid or target_email:
                        r_ok, r_msg = resend_otp_code(target_uid or target_email)
                        if r_ok:
                            st.success("New verification code sent!")
                        else:
                            st.warning(r_msg)
                    else:
                        st.error("No active user session to resend code.")

            with col_back:
                if st.button("← Back to Sign In", use_container_width=True):
                    st.session_state["auth_screen"] = "signin"
                    st.session_state["pending_verification"] = None
                    st.rerun()

        # -------------------------------------------------------------
        # SCREEN 3: TABBED SIGN IN & SIGN UP (CREATE ACCOUNT)
        # -------------------------------------------------------------
        else:
            st.markdown(
                """
                <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px 10px 0 0; padding: 18px 24px 8px 24px;">
                    <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #E2E8F0; letter-spacing: 0.06em; border-bottom: 1px solid #1F2937; padding-bottom: 8px;">
                        Access Gateway
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            # ── Inject Modern Role Selector Checkbox / Pill Styles ───────────
            st.markdown(
                """
                <style>
                div[data-testid="stRadio"] > div[role="radiogroup"] {
                    display: flex !important;
                    flex-wrap: wrap !important;
                    gap: 8px !important;
                    margin: 6px 0 14px 0 !important;
                }
                div[data-testid="stRadio"] > div[role="radiogroup"] > label {
                    background: #141824 !important;
                    border: 1px solid #283048 !important;
                    border-radius: 8px !important;
                    padding: 6px 14px !important;
                    color: #cbd5e1 !important;
                    font-size: 0.80rem !important;
                    font-weight: 500 !important;
                    cursor: pointer !important;
                    transition: all 0.2s ease !important;
                    margin-right: 0px !important;
                }
                div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
                    border-color: #8b5cf6 !important;
                    background: #1d2238 !important;
                    color: #ffffff !important;
                }
                div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
                    background: #281d45 !important;
                    border-color: #a855f7 !important;
                    color: #e9d5ff !important;
                    font-weight: 700 !important;
                    box-shadow: 0 0 12px rgba(168, 85, 247, 0.3) !important;
                }
                </style>
            """,
                unsafe_allow_html=True,
            )

            tab_signin, tab_signup = st.tabs(["SIGN IN", "CREATE ACCOUNT"])

            with tab_signin:
                with st.form("quantdb_login_form", clear_on_submit=False):
                    username_input = st.text_input(
                        "Email",
                        placeholder="you@example.com",
                        help="Use the email address you registered with.",
                    )
                    password_input = st.text_input(
                        "Password",
                        type="password",
                        placeholder="••••••••••••",
                    )

                    submit_btn = st.form_submit_button(
                        "LOGIN TO TERMINAL", type="primary", use_container_width=True
                    )

                    if submit_btn:
                        success, msg = login(username_input, password_input)
                        if success:
                            st.success(
                                f"Access granted as {st.session_state.get('role_display')}! Welcome back, {st.session_state.get('display_name')}!"
                            )
                            st.rerun()
                        else:
                            st.error(f"Authentication Failed: {msg}")

            with tab_signup:
                with st.form("quantdb_signup_form", clear_on_submit=False):
                    reg_name = st.text_input(
                        "Full Name",
                        placeholder="e.g. Alan Turing",
                        help="Your full legal or academic name.",
                    )
                    reg_username = st.text_input(
                        "Username",
                        placeholder="e.g. aturing",
                        help="3-30 characters: letters, numbers, and underscores only.",
                    )
                    reg_email = st.text_input(
                        "Email Address",
                        placeholder="e.g. aturing@cambridge.edu",
                        help="A valid email address used to sign in.",
                    )
                    reg_password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="••••••••••••",
                        help="Minimum 6 characters.",
                    )
                    reg_confirm_password = st.text_input(
                        "Confirm Password",
                        type="password",
                        placeholder="••••••••••••",
                        help="Re-enter your password to confirm.",
                    )
                    reg_phone = st.text_input(
                        "Mobile Number (Optional)",
                        placeholder="e.g. +1 555-0199",
                        help="Optional mobile phone number for account alerts.",
                    )

                    st.info("New accounts receive standard User access. An administrator can assign additional permissions.")

                    signup_btn = st.form_submit_button(
                        "CREATE ACCOUNT", type="primary", use_container_width=True
                    )

                    if signup_btn:
                        s_ok, s_msg = signup(
                            name=reg_name,
                            username=reg_username,
                            email=reg_email,
                            password=reg_password,
                            confirm_password=reg_confirm_password,
                            phone=reg_phone,
                            role=Role.USER,
                        )
                        if s_ok:
                            st.success(s_msg)
                            st.rerun()
                        else:
                            st.error(s_msg)

        # Demo Credentials Helper for Academic Evaluation
        with st.expander(
            "🔑 Academic Demo Accounts (Click to view test credentials)", expanded=False
        ):
            st.markdown(
                """
                <div style="font-size: 0.78rem; color: #94A3B8; margin-bottom: 8px;">
                    Pre-configured demonstration accounts representing all platform roles:
                </div>
            """,
                unsafe_allow_html=True,
            )

            demo_rows = [
                (
                    "Admin",
                    "admin01",
                    "Admin01@QuantDB",
                    "Full platform governance & simulation",
                ),
                (
                    "Quant Developer",
                    "developer01",
                    "Developer01@QuantDB",
                    "Algorithmic execution, models, API & backtesting",
                ),
                (
                    "Quant Researcher",
                    "researcher01",
                    "Researcher01@QuantDB",
                    "Backtesting, strategies, research analytics",
                ),
                (
                    "Quant Trader",
                    "trader01",
                    "Trader01@QuantDB",
                    "Simulated paper trading & order tickets",
                ),
                (
                    "User",
                    "user01",
                    "User01@QuantDB",
                    "Market data, portfolio overview & reports",
                ),
            ]

            for role_lbl, u_val, p_val, desc in demo_rows:
                st.markdown(
                    f"""
                    <div style="border-left: 3px solid #06B6D4; padding: 4px 10px; margin-bottom: 8px; background: #0F172A;">
                        <strong style="color: #38BDF8;">{role_lbl}</strong><br>
                        <span style="font-size: 0.75rem; color: #CBD5E1; font-family: 'JetBrains Mono', monospace;">
                            User: <strong>{u_val}</strong> &nbsp;|&nbsp; Pass: <strong>{p_val}</strong>
                        </span>
                        <div style="font-size: 0.70rem; color: #64748B;">{desc}</div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )


def require_auth(current_page: str = "Overview") -> bool:
    """
    Standard guard called at the top of every page.
    If unauthenticated, renders login screen and stops execution.
    If unauthorized, renders restricted alert and stops execution.
    Returns True only if authentication and authorization pass.
    """
    if not is_authenticated():
        render_login_screen()
        st.stop()

    if not check_page_access(current_page):
        render_access_restricted_banner(current_page)
        st.stop()

    return True
