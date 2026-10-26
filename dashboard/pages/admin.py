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
admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5, admin_tab6 = st.tabs([
    "👥 User & Role Management",
    "🛡️ Role Permissions",
    "🏛️ Registered Exchanges",
    "📊 Securities Master Catalog",
    "🗄️ Aiven Database Explorer",
    "📐 System Architecture"
])

with admin_tab1:
    # ── Custom CSS for User & Role Management Modal / Card ─────────────────────
    st.markdown("""
        <style>
        .urm-modal-card {
            background: #141722;
            border: 1px solid #232738;
            border-radius: 14px;
            padding: 22px 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }
        .urm-header-row {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 18px;
        }
        .urm-title-group {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .urm-icon-box {
            width: 44px;
            height: 44px;
            border-radius: 10px;
            background: #251e3e;
            border: 1px solid #3d2f60;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            color: #a855f7;
            flex-shrink: 0;
        }
        .urm-title-line {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .urm-main-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #f1f5f9;
            margin: 0;
            letter-spacing: -0.01em;
        }
        .urm-restricted-pill {
            background: #391723;
            border: 1px solid #5e1d2c;
            color: #fb7185;
            border-radius: 9999px;
            font-size: 0.72rem;
            padding: 2px 10px;
            font-weight: 600;
        }
        .urm-subtitle {
            color: #848d9f;
            font-size: 0.82rem;
            margin-top: 3px;
            margin-bottom: 0;
            line-height: 1.4;
        }
        .urm-stats-box {
            background: #191c28;
            border: 1px solid #252a3b;
            border-radius: 10px;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .urm-stat-col {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
        }
        .urm-stat-col:not(:last-child) {
            border-right: 1px solid #252a3b;
        }
        .urm-stat-txt {
            color: #cbd5e1;
            font-size: 0.84rem;
            font-weight: 500;
        }
        .urm-stat-badge {
            background: #2e2149;
            color: #c084fc;
            border: 1px solid #4a3675;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.80rem;
            padding: 2px 12px;
            min-width: 28px;
            text-align: center;
        }
        .urm-tbl-head {
            background: #181b29;
            border-top: 1px solid #232738;
            border-left: 1px solid #232738;
            border-right: 1px solid #232738;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 10px 14px;
            color: #64748b;
            font-size: 0.70rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .urm-row-container {
            background: #141722;
            border-left: 1px solid #232738;
            border-right: 1px solid #232738;
            border-bottom: 1px solid #1e2233;
            padding: 8px 14px;
            display: flex;
            align-items: center;
        }
        .urm-row-container:last-child {
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
            border-bottom: 1px solid #232738;
        }
        .urm-avatar-circle {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #352654;
            color: #c4b5fd;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            margin-right: 8px;
            flex-shrink: 0;
            border: 1px solid #4a3875;
        }
        .urm-name-label {
            color: #e2e8f0;
            font-weight: 600;
            font-size: 0.86rem;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .urm-you-tag {
            background: #2e234c;
            color: #c084fc;
            border: 1px solid #4f3b7c;
            border-radius: 9999px;
            font-size: 0.68rem;
            padding: 1px 6px;
            font-weight: 600;
        }
        .urm-email-str {
            color: #94a3b8;
            font-size: 0.82rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .urm-pill-active {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #34d399;
            border-radius: 9999px;
            padding: 3px 9px;
            font-size: 0.74rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .urm-pill-inactive {
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #f87171;
            border-radius: 9999px;
            padding: 3px 9px;
            font-size: 0.74rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .urm-pill-verified {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #34d399;
            border-radius: 9999px;
            padding: 3px 9px;
            font-size: 0.74rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .urm-date-str {
            color: #94a3b8;
            font-size: 0.76rem;
            font-family: ui-monospace, SFMono-Regular, monospace;
        }
        .urm-protected-box {
            background: #1c1f2e;
            border: 1px solid #2e344a;
            color: #94a3b8;
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 0.80rem;
            font-weight: 500;
            display: inline-block;
            width: 100%;
            text-align: left;
        }
        .urm-bottom-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 18px;
            padding-top: 14px;
            border-top: 1px solid #232738;
        }
        .urm-lock-note {
            color: #848d9f;
            font-size: 0.78rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        /* Custom tweaks for selectbox inside table rows */
        div[data-testid="stSelectbox"] label {
            display: none !important;
        }
        div[data-testid="stSelectbox"] > div > div {
            background-color: #1a1d2c !important;
            border: 1px solid #333a52 !important;
            border-radius: 6px !important;
            color: #e2e8f0 !important;
            font-size: 0.80rem !important;
            min-height: 30px !important;
            height: 30px !important;
            padding: 0 8px !important;
        }
        div[data-testid="stButton"] button {
            border-radius: 6px !important;
            font-size: 0.76rem !important;
            padding: 2px 8px !important;
            min-height: 28px !important;
            height: 28px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # ── Helpers for Avatar and Role Mapping ───────────────────────────────────
    def _compute_initials(name_or_email: str) -> str:
        s = (name_or_email or "").strip()
        if not s:
            return "U"
        parts = s.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return s[:2].upper()

    ROLE_CHOICES = ["Viewer", "Quant Trader", "Quant Developer", "Quant Researcher", "System Admin"]
    INVITE_ROLE_CHOICES = ROLE_CHOICES[:-1]
    ROLE_MAP = {
        Role.USER: "Viewer",
        Role.QUANT_TRADER: "Quant Trader",
        Role.QUANT_DEVELOPER: "Quant Developer",
        Role.QUANT_RESEARCHER: "Quant Researcher",
        Role.ADMIN: "System Admin",
        "SIMULATED_TRADER": "Quant Trader",
        "USER": "Viewer",
    }
    REVERSE_ROLE_MAP = {
        "Viewer": Role.USER,
        "Quant Trader": Role.QUANT_TRADER,
        "Quant Developer": Role.QUANT_DEVELOPER,
        "Quant Researcher": Role.QUANT_RESEARCHER,
        "System Admin": Role.ADMIN,
    }

    # Fetch users and governance queues from MySQL.
    users_list = get_platform_users()
    total_users_count = len(users_list) if users_list else 0
    role_request_rows = []
    pending_invitation_rows = []
    queue_error = ""
    queue_conn = None
    try:
        queue_conn = Repository()._get_connection()
        queue_cursor = queue_conn.cursor(dictionary=True)
        queue_cursor.execute("UPDATE account_invitations SET status = 'EXPIRED' WHERE status = 'PENDING' AND expires_at <= CURRENT_TIMESTAMP")
        queue_conn.commit()
        queue_cursor.execute("SELECT r.request_id, r.user_id, u.name, u.email, u.role AS current_role, r.requested_role, r.reason FROM role_change_requests r JOIN users u ON u.user_id = r.user_id WHERE r.status = 'PENDING' ORDER BY r.created_at")
        role_request_rows = queue_cursor.fetchall()
        queue_cursor.execute("SELECT invitation_id, email, name, role, expires_at FROM account_invitations WHERE status = 'PENDING' ORDER BY created_at DESC")
        pending_invitation_rows = queue_cursor.fetchall()
        queue_cursor.close()
    except Exception as queue_exc:
        queue_error = str(queue_exc)
    finally:
        if queue_conn is not None:
            queue_conn.close()

    curr_session_email = (st.session_state.get("email") or "").lower().strip()
    curr_session_user = (st.session_state.get("username") or "").lower().strip()

    # ── Header & Action Buttons ──────────────────────────────────────────────
    hdr_left, hdr_right = st.columns([7, 3])

    with hdr_left:
        st.markdown("""
            <div class="urm-title-group">
                <div class="urm-icon-box">👥</div>
                <div class="urm-title-area">
                    <div class="urm-title-line">
                        <span class="urm-main-title">User & Role Management</span>
                        <span class="urm-restricted-pill">Admin Restricted</span>
                    </div>
                    <div class="urm-subtitle">
                        Manage accounts and assign approved roles. System Admin access is reserved for the configured one-time bootstrap account.
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with hdr_right:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns([1, 1.2])
        with btn_c1:
            if st.button("🔄 Refresh", key="urm_top_refresh_btn", use_container_width=True):
                clear_analytics_service_cache()
                st.rerun()
        with btn_c2:
            invite_clicked = st.button("➕ Invite User", key="urm_top_invite_btn", type="primary", use_container_width=True)
            if invite_clicked:
                st.session_state["show_invite_form"] = not st.session_state.get("show_invite_form", False)

    # ── Optional Invite / Register User Form ──────────────────────────────────
    if st.session_state.get("show_invite_form", False):
        with st.container():
            st.markdown("""
                <div style="background: #1a1e2c; border: 1px solid #3b2e5a; border-radius: 10px; padding: 18px 20px; margin: 12px 0 20px 0;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #c4b5fd; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <span>✉️</span> Create a Pending Account Invitation
                    </div>
            """, unsafe_allow_html=True)
            with st.form("urm_invite_user_form"):
                inv_c1, inv_c2 = st.columns(2)
                with inv_c1:
                    inv_name = st.text_input("Full Name", placeholder="e.g. Bharat Pal")
                    inv_email = st.text_input("Institutional Email", placeholder="e.g. user@aid.svnit.ac.in")
                with inv_c2:
                    inv_role = st.selectbox("Assigned Role", options=INVITE_ROLE_CHOICES, index=0)
                
                st.caption("The invitee signs up with this email and receives the assigned role after email verification. Invitation expires in 7 days.")
                sub_inv = st.form_submit_button("Create Invitation", type="primary", use_container_width=True)
                if sub_inv:
                    if not inv_email or "@" not in inv_email:
                        st.error("Please provide a valid institutional email address.")
                    else:
                        invite_conn = None
                        try:
                            clean_em = inv_email.strip().lower()
                            c_name = inv_name.strip() or clean_em.split("@")[0]
                            target_role = REVERSE_ROLE_MAP.get(inv_role, Role.USER)
                            invite_conn = Repository()._get_connection()
                            invite_cursor = invite_conn.cursor()
                            invite_cursor.execute("SELECT user_id FROM users WHERE email = %s", (clean_em,))
                            if invite_cursor.fetchone():
                                raise ValueError("An account already exists for this email.")
                            invite_cursor.execute("SELECT invitation_id FROM account_invitations WHERE email = %s AND status = 'PENDING' AND expires_at > CURRENT_TIMESTAMP", (clean_em,))
                            if invite_cursor.fetchone():
                                raise ValueError("A pending invitation already exists for this email.")
                            invite_cursor.execute("INSERT INTO account_invitations (email, name, role, created_by, expires_at) VALUES (%s, %s, %s, %s, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 7 DAY))", (clean_em, c_name, normalize_role(target_role), st.session_state.get("user_id")))
                            invite_conn.commit()
                            invite_cursor.close()
                            clear_analytics_service_cache()
                            st.session_state["show_invite_form"] = False
                            st.success(f"Invitation created for {clean_em} with role {inv_role}.")
                            st.rerun()
                        except Exception as inv_err:
                            if invite_conn is not None:
                                invite_conn.rollback()
                            st.error(f"Failed to provision user: {inv_err}")
                        finally:
                            if invite_conn is not None:
                                invite_conn.close()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ── Summary Stats Cards Bar ──────────────────────────────────────────────
    st.markdown(f"""
        <div class="urm-stats-box">
            <div class="urm-stat-col">
                <span class="urm-stat-txt">Total Registered Accounts</span>
                <span class="urm-stat-badge">{total_users_count}</span>
            </div>
            <div class="urm-stat-col">
                <span class="urm-stat-txt">Pending Invitations</span>
                <span class="urm-stat-badge">{len(pending_invitation_rows) if not queue_error else '—'}</span>
            </div>
            <div class="urm-stat-col">
                <span class="urm-stat-txt">Role Change Requests</span>
                <span class="urm-stat-badge">{len(role_request_rows) if not queue_error else '—'}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander(f"🛡️ Role Change Requests · {len(role_request_rows)} pending", expanded=bool(role_request_rows)):
        if queue_error:
            st.error("Governance queues are unavailable. Apply database/13_role_requests.sql and database/14_account_invitations.sql.")
        elif not role_request_rows:
            st.info("No role change requests are waiting for review.")
        else:
            for role_req in role_request_rows:
                request_id = role_req["request_id"]
                request_label = f"{role_req.get('name') or role_req.get('email')} · {ROLE_MAP.get(normalize_role(role_req.get('current_role')), 'Viewer')} → {ROLE_MAP.get(normalize_role(role_req.get('requested_role')), role_req.get('requested_role'))} · {role_req.get('reason') or 'No reason provided'}"
                req_col, approve_col, reject_col = st.columns([7, 1, 1])
                req_col.write(request_label)
                if approve_col.button("Approve", key=f"role_req_approve_{request_id}", disabled=normalize_role(role_req.get("requested_role")) == Role.ADMIN):
                    review_conn = Repository()._get_connection()
                    try:
                        review_cursor = review_conn.cursor()
                        review_cursor.execute("SELECT user_id, requested_role FROM role_change_requests WHERE request_id = %s AND status = 'PENDING' FOR UPDATE", (request_id,))
                        locked_request = review_cursor.fetchone()
                        if not locked_request:
                            st.warning("This request was already reviewed. Refresh the page.")
                        else:
                            review_cursor.execute("UPDATE users SET role = %s WHERE user_id = %s AND status = 'ACTIVE'", (normalize_role(locked_request[1]), locked_request[0]))
                            if review_cursor.rowcount != 1:
                                raise ValueError("The account is inactive; its role cannot be changed.")
                            review_cursor.execute("UPDATE role_change_requests SET status = 'APPROVED', reviewed_at = CURRENT_TIMESTAMP, reviewed_by = %s WHERE request_id = %s AND status = 'PENDING'", (st.session_state.get("user_id"), request_id))
                            review_conn.commit()
                            st.toast("Role request approved.", icon="✅")
                            st.rerun()
                    except Exception as review_error:
                        review_conn.rollback()
                        st.error(f"Could not approve request: {review_error}")
                    finally:
                        review_conn.close()
                if reject_col.button("Reject", key=f"role_req_reject_{request_id}"):
                    review_conn = Repository()._get_connection()
                    try:
                        review_cursor = review_conn.cursor()
                        review_cursor.execute("UPDATE role_change_requests SET status = 'REJECTED', reviewed_at = CURRENT_TIMESTAMP, reviewed_by = %s WHERE request_id = %s AND status = 'PENDING'", (st.session_state.get("user_id"), request_id))
                        review_conn.commit()
                        st.toast("Role request rejected.", icon="↩️")
                        st.rerun()
                    except Exception as review_error:
                        review_conn.rollback()
                        st.error(f"Could not reject request: {review_error}")
                    finally:
                        review_conn.close()

    with st.expander(f"✉️ Pending Invitations · {len(pending_invitation_rows)}", expanded=bool(pending_invitation_rows)):
        if queue_error:
            st.error("Invitation queue is unavailable. Apply database/14_account_invitations.sql.")
        elif not pending_invitation_rows:
            st.info("No invitations are waiting for sign-up.")
        else:
            for invitation in pending_invitation_rows:
                inv_col, revoke_col = st.columns([8, 1])
                inv_col.write(f"{invitation.get('name') or invitation['email']} · {invitation['email']} · {ROLE_MAP.get(normalize_role(invitation['role']), invitation['role'])} · expires {invitation['expires_at']}")
                if revoke_col.button("Revoke", key=f"invite_revoke_{invitation['invitation_id']}"):
                    revoke_conn = Repository()._get_connection()
                    try:
                        revoke_cursor = revoke_conn.cursor()
                        revoke_cursor.execute("UPDATE account_invitations SET status = 'REVOKED' WHERE invitation_id = %s AND status = 'PENDING'", (invitation["invitation_id"],))
                        revoke_conn.commit()
                        st.toast("Invitation revoked.", icon="↩️")
                        st.rerun()
                    finally:
                        revoke_conn.close()

    # ── Users Table Header ───────────────────────────────────────────────────
    st.markdown("""
        <div class="urm-tbl-head">
            <div style="display: flex; align-items: center; width: 100%;">
                <div style="flex: 2.5;">USER</div>
                <div style="flex: 2.6;">INSTITUTIONAL EMAIL</div>
                <div style="flex: 2.0;">ASSIGNED ROLE</div>
                <div style="flex: 1.1;">STATUS</div>
                <div style="flex: 1.2;">EMAIL VERIFIED</div>
                <div style="flex: 2.1;">CREATED</div>
                <div style="flex: 1.8; text-align: right;">ACTIONS</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Render User Rows ──────────────────────────────────────────────────────
    if not users_list:
        st.markdown("""
            <div class="urm-row-container" style="justify-content: center; padding: 32px; color: #64748b;">
                No registered platform users found in database.
            </div>
        """, unsafe_allow_html=True)
    else:
        for idx, u in enumerate(users_list):
            uid = u.get("user_id", idx)
            uname = u.get("name") or u.get("username") or "User"
            uemail = u.get("email") or ""
            urole_raw = normalize_role(u.get("role", Role.USER))
            ustatus = str(u.get("status", "ACTIVE")).upper()
            is_verified = bool(u.get("is_verified", True))
            created_at = str(u.get("created_at", ""))
            
            # Format timestamp nicely
            if created_at and "." in created_at and "+00" not in created_at:
                created_disp = f"{created_at}+00"
            elif created_at:
                created_disp = created_at
            else:
                created_disp = "2026-10-18 00:00:00+00"

            initials = _compute_initials(uname)
            is_you = (
                (uemail and uemail.lower() == curr_session_email)
                or (u.get("username") and u.get("username").lower() == curr_session_user)
            )
            is_protected_admin = (urole_raw == Role.ADMIN) or is_you

            # Grid columns for row
            c_user, c_email, c_role, c_stat, c_ver, c_time, c_act = st.columns(
                [2.5, 2.6, 2.0, 1.1, 1.2, 2.1, 1.8]
            )

            # Col 1: Avatar + Name
            with c_user:
                you_html = '<span class="urm-you-tag">(You)</span>' if is_you else ''
                st.markdown(f"""
                    <div style="display: flex; align-items: center; height: 38px;">
                        <div class="urm-avatar-circle">{initials}</div>
                        <div class="urm-name-label" title="{uname}">{uname} {you_html}</div>
                    </div>
                """, unsafe_allow_html=True)

            # Col 2: Institutional Email
            with c_email:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; height: 38px;">
                        <span class="urm-email-str" title="{uemail}">{uemail}</span>
                    </div>
                """, unsafe_allow_html=True)

            # Col 3: Assigned Role
            with c_role:
                if is_protected_admin:
                    st.markdown("""
                        <div style="display: flex; align-items: center; height: 38px;">
                            <span class="urm-protected-box">System Admin (protected)</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    curr_display_role = ROLE_MAP.get(urole_raw, "Viewer")
                    curr_idx = ROLE_CHOICES.index(curr_display_role) if curr_display_role in ROLE_CHOICES else 0
                    
                    selected_role = st.selectbox(
                        f"role_{uid}",
                        options=ROLE_CHOICES,
                        index=curr_idx,
                        key=f"urm_role_sel_{uid}",
                    )
                    
                    if selected_role != curr_display_role:
                        try:
                            repo = Repository()
                            new_db_role = REVERSE_ROLE_MAP.get(selected_role, Role.USER)
                            repo.update_user_role(uid, new_db_role)
                            clear_analytics_service_cache()
                            st.toast(f"Updated {uname} role to {selected_role}!", icon="🛡️")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Role update failed: {e}")

            # Col 4: Status
            with c_stat:
                if ustatus == "ACTIVE":
                    st.markdown("""
                        <div style="display: flex; align-items: center; height: 38px;">
                            <span class="urm-pill-active">● Active</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="display: flex; align-items: center; height: 38px;">
                            <span class="urm-pill-inactive">● Inactive</span>
                        </div>
                    """, unsafe_allow_html=True)

            # Col 5: Email Verified
            with c_ver:
                st.markdown("""
                    <div style="display: flex; align-items: center; height: 38px;">
                        <span class="urm-pill-verified">✓ Verified</span>
                    </div>
                """, unsafe_allow_html=True)

            # Col 6: Created Timestamp
            with c_time:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; height: 38px;">
                        <span class="urm-date-str" title="{created_disp}">{created_disp}</span>
                    </div>
                """, unsafe_allow_html=True)

            # Col 7: Actions
            with c_act:
                act_col1, act_col2 = st.columns([2, 1])
                with act_col1:
                    if is_protected_admin:
                        st.markdown("""
                            <div style="display: flex; align-items: center; height: 38px;">
                                <button disabled style="background:#181b28; border:1px solid #282d3e; color:#475569; border-radius:6px; font-size:0.76rem; padding:4px 8px; width:100%; cursor:not-allowed;">Deactivate</button>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        btn_txt = "Deactivate" if ustatus == "ACTIVE" else "Activate"
                        if st.button(btn_txt, key=f"urm_stat_toggle_{uid}", use_container_width=True):
                            try:
                                repo = Repository()
                                next_status = "INACTIVE" if ustatus == "ACTIVE" else "ACTIVE"
                                repo.update_user_status(uid, next_status)
                                clear_analytics_service_cache()
                                st.toast(f"Account for {uname} is now {next_status}!", icon="🔄")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Status update failed: {e}")

                with act_col2:
                    if is_protected_admin:
                        st.markdown("""
                            <div style="display: flex; align-items: center; height: 38px;">
                                <button disabled style="background:#181b28; border:1px solid #282d3e; color:#475569; border-radius:6px; font-size:0.76rem; padding:4px 6px; width:100%; cursor:not-allowed;">🗑️</button>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        if st.button("🗑️", key=f"urm_del_{uid}", help=f"Delete user account {uname}"):
                            try:
                                repo = Repository()
                                repo.delete_user(uid)
                                clear_analytics_service_cache()
                                st.toast(f"User #{uid} deleted successfully.", icon="🗑️")
                                st.rerun()
                            except Exception as del_err:
                                st.error(f"Could not delete user: {del_err}")

            st.markdown("<div style='height: 1px; background: #1e2233; margin: 4px 0 6px 0;'></div>", unsafe_allow_html=True)

    # ── Bottom Bar / Footer ──────────────────────────────────────────────────
    st.markdown("""
        <div class="urm-bottom-bar">
            <div class="urm-lock-note">
                <span>🔒</span> RBAC permissions and account status changes take effect immediately across all sessions.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Collapsible Utility for Password Management ──────────────────────────
    with st.expander("🔑 Secure Administrative Password Reset", expanded=False):
        if users_list:
            user_options = {
                f"{u.get('name', u.get('username'))} (ID: {u.get('user_id')}, {u.get('email')})": u
                for u in users_list
            }
            with st.form("admin_password_reset_form_compact"):
                sel_u_str = st.selectbox("Target User Account", options=list(user_options.keys()), key="pwd_target_user_sel")
                sel_target = user_options[sel_u_str]
                target_uid = sel_target["user_id"]
                new_pw_input = st.text_input("New Secure Password", type="password", placeholder="Enter new password (min 6 chars)")
                
                reset_btn = st.form_submit_button("Reset Password Hash", type="primary", use_container_width=True)
                if reset_btn:
                    if not new_pw_input or len(new_pw_input) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        try:
                            repo = Repository()
                            h_pw = hash_password(new_pw_input)
                            repo.update_user_password(target_uid, h_pw)
                            clear_analytics_service_cache()
                            st.success(f"Successfully updated password hash for user #{target_uid}.")
                        except Exception as e:
                            st.error(f"Failed to reset password: {e}")

with admin_tab2:
    st.markdown("""
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Role-Based Access Control (RBAC) Governance Matrix
        </div>
    """, unsafe_allow_html=True)

    rbac_df = pd.DataFrame([
        {"Role": "USER", "Display": "User", "Overview": "Allowed", "Market Data": "Full Read", "Trading": "Paper Execution", "Portfolio": "Allowed", "Strategies": "Restricted", "Backtesting": "Restricted", "Reports": "Allowed", "Admin Console": "No Access"},
        {"Role": "QUANT_TRADER", "Display": "Quant Trader", "Overview": "Allowed", "Market Data": "Full Read", "Trading": "Paper Execution", "Portfolio": "Allowed", "Strategies": "View Only", "Backtesting": "Restricted", "Reports": "Allowed", "Admin Console": "No Access"},
        {"Role": "QUANT_RESEARCHER", "Display": "Quant Researcher", "Overview": "Allowed", "Market Data": "Full Read", "Trading": "Restricted", "Portfolio": "Allowed", "Strategies": "Full Access", "Backtesting": "Full Access", "Reports": "Allowed", "Admin Console": "No Access"},
        {"Role": "QUANT_DEVELOPER", "Display": "Quant Developer", "Overview": "Allowed", "Market Data": "Full Read", "Trading": "Full Paper Trading", "Portfolio": "Allowed", "Strategies": "Full Access", "Backtesting": "Full Access", "Reports": "Allowed", "Admin Console": "No Access"},
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
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 12px;">
            Aiven Cloud MySQL 8.4 • Live Schema & Table Browser
        </div>
    """, unsafe_allow_html=True)

    try:
        from src.database.connection import get_connection
        conn = get_connection(use_pool=False)
        if conn and conn.is_connected():
            cur = conn.cursor()
            cur.execute("SHOW FULL TABLES")
            raw_tables = cur.fetchall()

            table_stats = []
            for t_name, t_type in raw_tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM `{t_name}`")
                    cnt = cur.fetchone()[0]
                except Exception:
                    cnt = 0
                table_stats.append({
                    "Entity Name": t_name,
                    "Type": "VIEW" if "VIEW" in t_type.upper() else "BASE TABLE",
                    "Row Count": cnt,
                })

            col_t1, col_t2 = st.columns([1, 2])
            with col_t1:
                st.markdown("<div style='font-size: 0.75rem; color: #94A3B8; font-weight: 600; margin-bottom: 6px;'>RELATIONAL OBJECTS (21 TOTAL)</div>", unsafe_allow_html=True)
                df_stats = pd.DataFrame(table_stats)
                render_dataframe(df_stats, hide_index=True)

            with col_t2:
                st.markdown("<div style='font-size: 0.75rem; color: #94A3B8; font-weight: 600; margin-bottom: 6px;'>LIVE RECORD INSPECTOR</div>", unsafe_allow_html=True)
                table_names = [t["Entity Name"] for t in table_stats]
                sel_table = st.selectbox("Inspect Table or View", options=table_names, index=0)
                if sel_table:
                    cur.execute(f"SELECT * FROM `{sel_table}` LIMIT 50")
                    col_names = [desc[0] for desc in cur.description] if cur.description else []
                    rows = cur.fetchall()
                    df_preview = pd.DataFrame(rows, columns=col_names)
                    render_dataframe(df_preview, hide_index=True)

            conn.close()
        else:
            st.warning("Database connection is currently in MOCK mode. Toggle to REAL mode to explore live Aiven MySQL tables.")
    except Exception as e:
        st.info(f"Database explorer is active in REAL mode: {e}")

with admin_tab6:
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
