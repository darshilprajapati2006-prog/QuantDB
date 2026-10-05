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
from dashboard.services.analytics_service import get_system_health
from dashboard.services.market_service import get_available_securities, get_available_exchanges
from dashboard.providers.factory import get_current_data_mode, set_data_mode

# Page configuration
st.set_page_config(
    page_title="QuantDB — Administration & System",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and sidebar
apply_terminal_theme()
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
        change="FastAPI / Python Service Layer",
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
            st.warning("REAL DATA MODE active: Waiting for backend services connection from `src.database`. Ensure MySQL is running on port 3306.")
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

    # Mock user directory matching schema: user_id, name, email, role, status, created_at
    mock_users = pd.DataFrame([
        {"user_id": 1, "name": "Darshil Prajapati", "email": "darshil@quantdb.local", "role": "ADMIN", "status": "ACTIVE", "created_at": "2024-01-01 00:00:00"},
        {"user_id": 2, "name": "Bharat", "email": "bharat@quantdb.local", "role": "QUANT_RESEARCHER", "status": "ACTIVE", "created_at": "2024-01-05 10:15:00"},
        {"user_id": 3, "name": "Sriteja", "email": "sriteja@quantdb.local", "role": "ADMIN", "status": "ACTIVE", "created_at": "2024-01-10 11:30:00"},
        {"user_id": 4, "name": "Simulated Trader 1", "email": "trader1@quantdb.local", "role": "SIMULATED_TRADER", "status": "ACTIVE", "created_at": "2024-02-01 09:00:00"},
    ])

    render_dataframe(
        mock_users,
        column_config={
            "user_id": st.column_config.NumberColumn("User ID", format="#%d"),
            "name": st.column_config.TextColumn("Full Name"),
            "email": st.column_config.TextColumn("Email Address"),
            "role": st.column_config.TextColumn("Assigned Role"),
            "status": st.column_config.TextColumn("Account Status"),
            "created_at": st.column_config.TextColumn("Created Timestamp"),
        },
        hide_index=True,
    )

with admin_tab2:
    st.markdown("""
        <div style="font-size: 0.82rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Role-Based Access Control (RBAC) Matrix
        </div>
    """, unsafe_allow_html=True)

    rbac_df = pd.DataFrame([
        {"Role": "ADMIN", "Market Data": "Full Read", "Trading": "Full Paper Trading", "Backtesting": "Full Access", "Portfolio": "All Portfolios", "Admin Console": "Full Control"},
        {"Role": "QUANT_RESEARCHER", "Market Data": "Full Read", "Trading": "Read / Simulated", "Backtesting": "Full Access", "Portfolio": "Assigned Only", "Admin Console": "View Only"},
        {"Role": "SIMULATED_TRADER", "Market Data": "Read Quotes", "Trading": "Order Entry", "Backtesting": "Restricted", "Portfolio": "Own Portfolio", "Admin Console": "No Access"},
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
