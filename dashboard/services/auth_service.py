"""
QuantDB Dashboard Authentication & Authorization Service.

Integrates the presentation layer with backend authentication, handles Streamlit
session state, user profile caching, and enforces Role-Based Access Control (RBAC).
"""

import logging
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
    AuthenticationError,
    AccountInactiveError,
    AuthorizationError,
)
from src.database.repository import Repository
from dashboard.providers.factory import get_current_data_mode

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
    },
    {
        "user_id": 102,
        "username": "trader01",
        "name": "Quant Trader Demo",
        "email": "trader01@quantdb.local",
        "password": "Trader01@QuantDB",
        "role": Role.QUANT_TRADER,
        "status": "ACTIVE",
    },
    {
        "user_id": 103,
        "username": "researcher01",
        "name": "Quant Researcher Demo",
        "email": "researcher01@quantdb.local",
        "password": "Researcher01@QuantDB",
        "role": Role.QUANT_RESEARCHER,
        "status": "ACTIVE",
    },
    {
        "user_id": 104,
        "username": "admin01",
        "name": "Admin Demo",
        "email": "admin01@quantdb.local",
        "password": "Admin01@QuantDB",
        "role": Role.ADMIN,
        "status": "ACTIVE",
    },
]


def init_session_state() -> None:
    """Ensures authentication keys are initialized in Streamlit session state."""
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


def login(identifier: str, password: str) -> Tuple[bool, str]:
    """
    Attempts to authenticate a user by username or email.
    Stores only safe session information upon success.
    """
    init_session_state()
    if not identifier or not identifier.strip():
        return False, "Please enter your username or email."
    if not password:
        return False, "Please enter your password."

    clean_id = identifier.strip()

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
        return True, "Authentication successful."

    except AccountInactiveError as e:
        return False, str(e)
    except AuthenticationError as e:
        # Check if database is completely offline and we can fall back in pure mock mode
        err_msg = str(e)
        if "unavailable" in err_msg.lower():
            # Fallback for offline mock demo
            for mu in MOCK_USERS_SEED:
                if (mu["username"].lower() == clean_id.lower() or mu["email"].lower() == clean_id.lower()) and mu["password"] == password:
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

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("← Return to Overview", use_container_width=True, type="primary"):
            st.switch_page("app.py")


def render_login_screen() -> None:
    """Renders the QuantDB terminal login screen matching the platform's visual design."""
    st.markdown("""
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
    """, unsafe_allow_html=True)

    # Centered Login Card
    col_l, col_center, col_r = st.columns([1, 1.25, 1])
    with col_center:
        st.markdown("""
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 22px 26px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);">
                <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #E2E8F0; letter-spacing: 0.06em; margin-bottom: 14px; border-bottom: 1px solid #1F2937; padding-bottom: 8px;">
                    Terminal Authentication
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("quantdb_login_form", clear_on_submit=False):
            username_input = st.text_input(
                "Username or Email",
                placeholder="e.g. admin01 or user@quantdb.local",
                help="Enter your registered platform username or institutional email."
            )
            password_input = st.text_input(
                "Password",
                type="password",
                placeholder="••••••••••••",
                help="Database-backed secure password authentication."
            )

            submit_btn = st.form_submit_button("LOGIN TO TERMINAL", type="primary", use_container_width=True)

            if submit_btn:
                success, msg = login(username_input, password_input)
                if success:
                    st.success(f"Access granted. Welcome back, {st.session_state.get('display_name')}!")
                    st.rerun()
                else:
                    st.error(f"Authentication Failed: {msg}")

        # Demo Credentials Helper for Academic Evaluation
        with st.expander("🔑 Academic Demo Accounts (Click to view test credentials)", expanded=False):
            st.markdown("""
                <div style="font-size: 0.78rem; color: #94A3B8; margin-bottom: 8px;">
                    Pre-configured demonstration accounts representing all four platform roles:
                </div>
            """, unsafe_allow_html=True)

            demo_rows = [
                ("Admin", "admin01", "Admin01@QuantDB", "Full platform governance & simulation"),
                ("Quant Researcher", "researcher01", "Researcher01@QuantDB", "Backtesting, strategies, research analytics"),
                ("Quant Trader", "trader01", "Trader01@QuantDB", "Simulated paper trading & order tickets"),
                ("Standard User", "user01", "User01@QuantDB", "Market data, portfolio overview & reports"),
            ]

            for role_lbl, u_val, p_val, desc in demo_rows:
                st.markdown(f"""
                    <div style="border-left: 3px solid #06B6D4; padding: 4px 10px; margin-bottom: 8px; background: #0F172A;">
                        <strong style="color: #38BDF8;">{role_lbl}</strong><br>
                        <span style="font-size: 0.75rem; color: #CBD5E1; font-family: 'JetBrains Mono', monospace;">
                            User: <strong>{u_val}</strong> &nbsp;|&nbsp; Pass: <strong>{p_val}</strong>
                        </span>
                        <div style="font-size: 0.70rem; color: #64748B;">{desc}</div>
                    </div>
                """, unsafe_allow_html=True)


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
