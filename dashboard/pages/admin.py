"""
QuantDB — Administrative Console & System Topology
Inspects platform users, role permissions, exchange connections,
security instruments catalog, and real-time backend/database integration status.
No sensitive credentials or raw connection strings are exposed.
"""

from pathlib import Path
import sys
import pandas as pd
import streamlit as st

# Setup sys.path for clean imports
_current_dir = Path(__file__).resolve().parent.parent
_root_dir = _current_dir.parent
for _p in [str(_root_dir), str(_current_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dashboard.components.theme import apply_terminal_theme
from dashboard.components.sidebar import render_sidebar
from dashboard.components.status import render_simulation_banner
from dashboard.components.metrics import render_metric_card
from dashboard.components.tables import render_dataframe
from dashboard.services.analytics_service import get_system_health, get_platform_users, clear_analytics_service_cache
from dashboard.services.market_service import get_available_securities, get_available_exchanges
from dashboard.providers.factory import get_current_data_mode, set_data_mode
from dashboard.services.auth_service import require_auth
from src.auth.password import hash_password
from src.auth.roles import Role, get_role_display_name, normalize_role
from src.database.repository import Repository

# Page configuration
st.set_page_config(
    page_title="QuantDB — Administration & System",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and authentication guard
apply_terminal_theme()
require_auth("Admin")
render_sidebar(current_page="Admin")

# Top Disclaimer
render_simulation_banner("Administrative Console • Platform Governance & Service Health")

# Page Header
st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; align-items: baseline; gap: 10px;">
            <h1 style="margin: 0; font-size: 1.75rem; font-weight: 800; color: #F8FAFC;">
                ADMIN <span style="color: #06B6D4;">CONSOLE</span>
            </h1>
            <span style="color: #64748B; font-size: 0.90rem;">
                Platform Topology, Role Governance & Service Connectivity
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# SYSTEM INFORMATION STATUS SUMMARY
# -------------------------------------------------------------
health = get_system_health()
curr_mode = get_current_data_mode().upper()

st.markdown("""
    <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
        Platform Health & Connectivity
    </div>
""", unsafe_allow_html=True)

adm_c1, adm_c2, adm_c3, adm_c4 = st.columns(4)

with adm_c1:
    render_metric_card(
        title="DATA MODE PROVIDER",
        value=curr_mode,
        change="Simulated In-Memory" if curr_mode == "MOCK" else "MySQL & Quant Engine",
        is_positive=curr_mode == "MOCK",
        description="Active provider routing"
    )

with adm_c2:
    backend_ok = health.get("connected", False) or curr_mode == "MOCK"
    render_metric_card(
        title="BACKEND SERVICES",
        value="ONLINE (MOCK)" if curr_mode == "MOCK" else ("CONNECTED" if backend_ok else "OFFLINE"),
        change="Python Service & Quant Layer",
        is_positive=backend_ok,
        description="Repository & Trading Services"
    )

with adm_c3:
    db_ok = health.get("connected", False) or curr_mode == "MOCK"
    render_metric_card(
        title="DATABASE (MYSQL)",
        value="IN-MEMORY (MOCK)" if curr_mode == "MOCK" else ("CONNECTED" if db_ok else "OFFLINE"),
        change="QuantDB Relational Schema",
        is_positive=db_ok,
        description="12 Normalized Entities"
    )

with adm_c4:
    render_metric_card(
        title="APPLICATION VERSION",
        value=health.get("version", "1.0.0-beta"),
        change="Streamlit + Pandas + Plotly",
        is_positive=True,
        description="QuantDB Academic Edition"
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# DATA MODE CONTROLLER CONTAINER
# -------------------------------------------------------------
with st.container():
    st.markdown("<div class='quant-card' style='padding: 16px;'>", unsafe_allow_html=True)
    st.markdown("""
        <div style="font-size: 0.82rem; font-weight: 700; color: #F8FAFC; text-transform: uppercase; margin-bottom: 6px;">
            Data Provider Mode Switcher
        </div>
        <div style="font-size: 0.78rem; color: #94A3B8; margin-bottom: 12px; line-height: 1.4;">
            Switch seamlessly between <b>MOCK</b> (in-memory realistic time series and execution simulation) 
            and <b>REAL</b> (direct Python repository and MySQL database connection). The UI pages remain identical.
        </div>
    """, unsafe_allow_html=True)

    mode_c1, mode_c2 = st.columns([2, 8])
    with mode_c1:
        new_mode = st.radio(
            "Select Global DATA_MODE",
            options=["mock", "real"],
            index=0 if curr_mode.lower() == "mock" else 1,
            horizontal=True
        )
        if new_mode.lower() != curr_mode.lower():
            set_data_mode(new_mode)
            st.success(f"Global DATA_MODE updated to: {new_mode.upper()}")
            st.rerun()

    with mode_c2:
        if curr_mode == "REAL":
            if health.get("connected", False):
                st.success("REAL DATA MODE active: Successfully connected to MySQL QuantDB and Python backend services.")
            else:
                st.warning("REAL DATA MODE active: Database connection unreachable. Ensure MySQL is running on port 3306.")
        else:
            st.info("MOCK DATA MODE active: Platform is operating autonomously with high-fidelity financial data.")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='quant-divider'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# ADMINISTRATIVE SECTIONS: USERS, ROLES, EXCHANGES, SECURITIES
# -------------------------------------------------------------
admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs([
    "👤 Platform Users",
    "🛡️ Role Permissions",
    "🏛️ Registered Exchanges",
    "📊 Securities Master Catalog",
    "📐 System Architecture"
])

with admin_tab1:
    st.markdown("""
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            User Accounts Table (Schema: users)
        </div>
    """, unsafe_allow_html=True)

    # Retrieve platform users via active provider (MySQL QuantDB in REAL mode, mock in MOCK mode)
    users_list = get_platform_users()
    if users_list:
        users_df = pd.DataFrame(users_list)
        # Ensure display columns match schema; strictly omit password hashes and OTP hashes
        display_cols = [c for c in ["user_id", "username", "name", "email", "role", "is_verified", "status", "created_at"] if c in users_df.columns]
        users_df = users_df[display_cols]
    else:
        users_df = pd.DataFrame(columns=["user_id", "username", "name", "email", "role", "is_verified", "status", "created_at"])

    render_dataframe(
        users_df,
        column_config={
            "user_id": st.column_config.NumberColumn("User ID", format="#%d"),
            "username": st.column_config.TextColumn("Username"),
            "name": st.column_config.TextColumn("Full Name"),
            "email": st.column_config.TextColumn("Email Address"),
            "role": st.column_config.TextColumn("Assigned Role"),
            "is_verified": st.column_config.CheckboxColumn("Verified"),
            "status": st.column_config.TextColumn("Account Status"),
            "created_at": st.column_config.TextColumn("Created Timestamp"),
        },
        hide_index=True,
    )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 10px;">
            Account Administration & Governance Controls
        </div>
    """, unsafe_allow_html=True)

    if users_list:
        user_options = {
            f"{u.get('username', u.get('name'))} (ID: {u.get('user_id')}, {u.get('email')})": u
            for u in users_list
        }
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.markdown("<div style='font-size: 0.76rem; font-weight: 700; color: #94A3B8; margin-bottom: 6px;'>UPDATE ROLE & ACCOUNT STATUS</div>", unsafe_allow_html=True)
            with st.form("admin_update_role_status_form"):
                sel_user_str = st.selectbox("Select Target User", options=list(user_options.keys()), key="sel_user_edit")
                sel_u = user_options[sel_user_str]
                current_role = normalize_role(sel_u.get("role", Role.USER))
                current_status = sel_u.get("status", "ACTIVE")

                role_choices = [Role.USER, Role.QUANT_TRADER, Role.QUANT_RESEARCHER, Role.ADMIN]
                new_role = st.selectbox(
                    "Assign Role",
                    options=role_choices,
                    index=role_choices.index(current_role) if current_role in role_choices else 0,
                    format_func=lambda r: f"{get_role_display_name(r)} ({r})"
                )

                status_choices = ["ACTIVE", "INACTIVE", "SUSPENDED"]
                new_status = st.selectbox(
                    "Account Status",
                    options=status_choices,
                    index=status_choices.index(current_status) if current_status in status_choices else 0,
                )

                submit_update = st.form_submit_button("Save Role & Status", type="primary", use_container_width=True)
                if submit_update:
                    try:
                        repo = Repository()
                        target_id = sel_u["user_id"]
                        repo.update_user_role(target_id, new_role)
                        repo.update_user_status(target_id, new_status)
                        clear_analytics_service_cache()
                        st.success(f"Successfully updated user #{target_id} to Role: {new_role}, Status: {new_status}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update user: {e}")

        with col_m2:
            st.markdown("<div style='font-size: 0.76rem; font-weight: 700; color: #94A3B8; margin-bottom: 6px;'>SECURE PASSWORD RESET</div>", unsafe_allow_html=True)
            with st.form("admin_password_reset_form"):
                pwd_user_str = st.selectbox("Select Target User", options=list(user_options.keys()), key="sel_user_pwd")
                pwd_u = user_options[pwd_user_str]
                new_pw = st.text_input("New Password", type="password", placeholder="Enter secure new password", help="Password will be securely hashed with PBKDF2-HMAC-SHA256.")

                submit_pwd = st.form_submit_button("Update Password Hash", type="secondary", use_container_width=True)
                if submit_pwd:
                    if not new_pw or len(new_pw) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        try:
                            repo = Repository()
                            target_id = pwd_u["user_id"]
                            hashed = hash_password(new_pw)
                            repo.update_user_password(target_id, hashed)
                            clear_analytics_service_cache()
                            st.success(f"Password for user #{target_id} securely updated and hashed.")
                        except Exception as e:
                            st.error(f"Failed to reset password: {e}")

        with st.expander("➕ Register New Platform User", expanded=False):
            with st.form("admin_create_user_form"):
                c_u1, c_u2 = st.columns(2)
                with c_u1:
                    new_uname = st.text_input("Username", placeholder="e.g. trader02")
                    new_fullname = st.text_input("Full Name", placeholder="e.g. John Doe")
                    new_uemail = st.text_input("Email", placeholder="e.g. john@quantdb.local")
                with c_u2:
                    new_urole = st.selectbox("Role", options=[Role.USER, Role.QUANT_TRADER, Role.QUANT_RESEARCHER, Role.ADMIN], format_func=lambda r: f"{get_role_display_name(r)} ({r})")
                    new_ustatus = st.selectbox("Initial Status", options=["ACTIVE", "INACTIVE", "SUSPENDED"])
                    new_upass = st.text_input("Initial Password", type="password", placeholder="Temporary secure password")

                create_btn = st.form_submit_button("Create User Account", type="primary", use_container_width=True)
                if create_btn:
                    if not new_uname or not new_fullname or not new_uemail or not new_upass:
                        st.error("All user fields are required.")
                    else:
                        try:
                            repo = Repository()
                            hashed = hash_password(new_upass)
                            new_id = repo.create_user(
                                username=new_uname.strip().lower(),
                                name=new_fullname.strip(),
                                email=new_uemail.strip().lower(),
                                password_hash=hashed,
                                role=new_urole,
                                status=new_ustatus,
                            )
                            clear_analytics_service_cache()
                            st.success(f"User account created successfully (User ID #{new_id}).")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to create user: {e}")

with admin_tab2:
    st.markdown("""
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Role-Based Access Control (RBAC) Governance Matrix
        </div>
    """, unsafe_allow_html=True)

    rbac_df = pd.DataFrame([
        {"Role": "USER", "Display": "User", "Overview": "Allowed", "Market Data": "Full Read", "Trading": "Restricted", "Portfolio": "Allowed", "Strategies": "Restricted", "Backtesting": "Restricted", "Reports": "Allowed", "Admin Console": "No Access"},
        {"Role": "QUANT_TRADER", "Display": "Quant Trader", "Overview": "Allowed", "Market Data": "Full Read", "Trading": "Paper Execution", "Portfolio": "Allowed", "Strategies": "View Only", "Backtesting": "Restricted", "Reports": "Allowed", "Admin Console": "No Access"},
        {"Role": "QUANT_RESEARCHER", "Display": "Quant Researcher", "Overview": "Allowed", "Market Data": "Full Read", "Trading": "Restricted", "Portfolio": "Allowed", "Strategies": "Full Access", "Backtesting": "Full Access", "Reports": "Allowed", "Admin Console": "No Access"},
        {"Role": "ADMIN", "Display": "Admin", "Overview": "Allowed", "Market Data": "Full Read", "Trading": "Full Paper Trading", "Portfolio": "All Portfolios", "Strategies": "Full Access", "Backtesting": "Full Access", "Reports": "Allowed", "Admin Console": "Full Control"},
    ])
    render_dataframe(rbac_df, hide_index=True)

with admin_tab3:
    st.markdown("""
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Configured Exchanges (Schema: exchanges)
        </div>
    """, unsafe_allow_html=True)

    exchanges = get_available_exchanges()
    df_exch = pd.DataFrame(exchanges)
    render_dataframe(
        df_exch,
        column_config={
            "exchange_id": st.column_config.NumberColumn("ID", format="#%d"),
            "exchange_code": st.column_config.TextColumn("Code"),
            "exchange_name": st.column_config.TextColumn("Exchange Name"),
            "country": st.column_config.TextColumn("Country"),
            "timezone": st.column_config.TextColumn("Timezone"),
        },
        hide_index=True,
    )

with admin_tab4:
    st.markdown("""
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Securities Master Catalog (Schema: securities)
        </div>
    """, unsafe_allow_html=True)

    securities = get_available_securities()
    df_sec = pd.DataFrame(securities)
    render_dataframe(
        df_sec,
        column_config={
            "security_id": st.column_config.NumberColumn("ID", format="#%d"),
            "symbol": st.column_config.TextColumn("Ticker"),
            "security_name": st.column_config.TextColumn("Security Name"),
            "security_type": st.column_config.TextColumn("Asset Class"),
            "currency": st.column_config.TextColumn("Currency"),
            "base_price": st.column_config.NumberColumn("Base Reference Price", format="$%.2f"),
            "volatility": st.column_config.NumberColumn("Annual Volatility", format="%.3f"),
        },
        hide_index=True,
    )

with admin_tab5:
    st.markdown("""
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            QuantDB Layered Architecture & Separation of Concerns
        </div>
        <pre style="background: #0d131f; padding: 14px; border-radius: 6px; border: 1px solid #1F2937; color: #38BDF8; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;">
                               QUANTDB
                                  |
                                  v
                        Streamlit Dashboard
                       (Terminal UI Pages)
                                  |
                                  v
                          Frontend Services
                    (market, trading, portfolio,
                     strategy, backtest, analytics)
                                  |
                                  v
                          Provider Factory
                     (DATA_MODE = mock | real)
                                  |
                     +------------+------------+
                     |                         |
                     v                         v
               Mock Provider             Real Provider
           (Realistic In-Memory)    (Backend & Quant Bridge)
                                               |
                                  +------------+------------+
                                  |                         |
                                  v                         v
                           Backend Services          Quant Services
                                  |                         |
                                  v                         v
                                MySQL                Analytics Engine
                                                            |
                                                            v
                                                       Backtesting
                                                            |
                                                            v
                                                       Risk Metrics
        </pre>
    """, unsafe_allow_html=True)
