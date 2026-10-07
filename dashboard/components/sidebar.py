"""
QuantDB Persistent Terminal Sidebar.
Provides unified navigation, branding, authenticated user badge, RBAC navigation filtering,
quick data mode switcher, and live system status.
Seamlessly routes across pages with st.switch_page.
"""

from typing import Optional
import streamlit as st
from dashboard.components.status import render_sidebar_status
from dashboard.providers.factory import get_current_data_mode, set_data_mode
from src.auth.roles import get_allowed_pages, normalize_role, Role
from dashboard.services.auth_service import is_authenticated, get_current_user, logout

ALL_NAV_PAGES = [
    "Overview",
    "Market Data",
    "Trading",
    "Portfolio",
    "Strategies",
    "Backtesting",
    "Reports",
    "Admin",
]

PAGE_ICONS = {
    "Overview": "📊",
    "Market Data": "📈",
    "Trading": "⚡",
    "Portfolio": "💼",
    "Strategies": "🧠",
    "Backtesting": "🔬",
    "Reports": "📋",
    "Admin": "⚙️",
}

PAGE_ROUTES = {
    "Overview": "app.py",
    "Market Data": "pages/market_data.py",
    "Trading": "pages/trading.py",
    "Portfolio": "pages/portfolio.py",
    "Strategies": "pages/strategies.py",
    "Backtesting": "pages/backtesting.py",
    "Reports": "pages/reports.py",
    "Admin": "pages/admin.py",
}


def render_sidebar(current_page: str = "Overview") -> str:
    """
    Renders the QuantDB persistent terminal sidebar on every page.
    Filters navigation options dynamically based on the authenticated user's RBAC role.
    """
    with st.sidebar:
        # QuantDB Terminal Branding Header
        st.markdown("""
            <div style="padding: 6px 0 14px 0; border-bottom: 1px solid #1F2937;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%); width: 26px; height: 26px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 15px; color: #0B0F19;">Q</div>
                    <div style="font-size: 1.2rem; font-weight: 800; letter-spacing: 0.12em; color: #F8FAFC; font-family: 'JetBrains Mono', monospace;">QUANT<span style="color: #06B6D4;">DB</span></div>
                </div>
                <div style="font-size: 0.70rem; color: #94A3B8; margin-top: 4px; letter-spacing: 0.04em;">
                    QUANT FINANCE & SIMULATION
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Authenticated User Badge & Logout
        if is_authenticated():
            curr_user = get_current_user() or {}
            display_name = curr_user.get("display_name") or curr_user.get("username") or "User"
            role_display = curr_user.get("role_display") or "User"
            role = curr_user.get("role") or Role.USER

            st.markdown(f"""
                <div style="padding: 10px 12px; background: #111827; border: 1px solid #1F2937; border-radius: 6px; margin-bottom: 10px;">
                    <div style="font-size: 0.65rem; text-transform: uppercase; color: #64748B; font-weight: 700; letter-spacing: 0.06em;">Logged in as:</div>
                    <div style="font-size: 0.88rem; font-weight: 700; color: #F8FAFC; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{display_name}</div>
                    <div style="font-size: 0.65rem; text-transform: uppercase; color: #64748B; font-weight: 700; letter-spacing: 0.06em; margin-top: 5px;">Role:</div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 1px;">
                        <span style="font-size: 0.78rem; font-weight: 600; color: #38BDF8; font-family: 'JetBrains Mono', monospace;">{role_display}</span>
                        <span style="font-size: 0.62rem; color: #10B981; background: rgba(16, 185, 129, 0.12); padding: 1px 5px; border-radius: 3px; border: 1px solid rgba(16, 185, 129, 0.25);">ACTIVE</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if st.button("Logout", key="btn_auth_logout", use_container_width=True, type="secondary"):
                logout()
                st.rerun()

            # Filter visible navigation pages strictly to those permitted for this role
            nav_pages = get_allowed_pages(role)
        else:
            nav_pages = ALL_NAV_PAGES

        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        # Radio navigation selector with RBAC-filtered items
        curr_idx = nav_pages.index(current_page) if current_page in nav_pages else 0

        selected = st.radio(
            "Terminal Navigation",
            options=nav_pages,
            index=curr_idx,
            format_func=lambda x: f"{PAGE_ICONS.get(x, '•')}  {x}",
            label_visibility="collapsed",
            key=f"nav_radio_{current_page}"
        )

        if selected != current_page:
            target_route = PAGE_ROUTES.get(selected)
            if target_route:
                try:
                    st.switch_page(target_route)
                except Exception:
                    try:
                        st.switch_page(f"dashboard/{target_route}")
                    except Exception:
                        pass

        # Data Mode Switcher (Research/Development Utility)
        st.markdown("<div class='quant-divider'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.72rem; text-transform: uppercase; color: #64748B; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 6px;'>Data Mode Provider</div>", unsafe_allow_html=True)

        curr_mode = get_current_data_mode()
        cols = st.columns(2)
        with cols[0]:
            if st.button("MOCK", use_container_width=True, type="primary" if curr_mode == "mock" else "secondary", key="btn_mode_mock"):
                set_data_mode("mock")
                st.rerun()
        with cols[1]:
            if st.button("REAL", use_container_width=True, type="primary" if curr_mode == "real" else "secondary", key="btn_mode_real"):
                set_data_mode("real")
                st.rerun()

        # Bottom System Status Widget
        render_sidebar_status()

    return selected
