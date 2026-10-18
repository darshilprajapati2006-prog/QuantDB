"""
QuantDB Status & Simulation Indicators.
Provides persistent status badges, mode switchers, and regulatory simulation banners.
"""

from typing import Dict, Optional
import streamlit as st
from dashboard.providers.factory import get_current_data_mode, set_data_mode
from dashboard.services.analytics_service import get_system_health


def render_simulation_banner(context_note: Optional[str] = None):
    """Renders mandatory paper-trading simulation disclaimer across pages."""
    subtext = context_note or "Academic Quantitative Finance Simulation • No Real-Money Trades Executed"
    st.markdown(f"""
        <div class="sim-banner">
            <div>
                <span class="sim-banner-text">● PAPER TRADING / SIMULATION MODE</span>
                <span style="margin: 0 8px; color: #4B5563;">|</span>
                <span class="sim-banner-sub">{subtext}</span>
            </div>
            <div>
                <span class="status-pill status-pill-amber">SIMULATED ENVIRONMENT</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_sidebar_status():
    """Renders the persistent bottom status widget in the sidebar."""
    health = get_system_health()
    curr_mode = get_current_data_mode().upper()

    st.markdown("<div class='quant-divider'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.72rem; text-transform: uppercase; color: #64748B; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;'>System Status</div>", unsafe_allow_html=True)

    # Data Mode indicator
    if curr_mode == "MOCK":
        mode_pill = '<span class="status-pill status-pill-cyan">MOCK MODE</span>'
        backend_pill = '<span class="status-pill status-pill-green">IN-MEMORY</span>'
        db_pill = '<span class="status-pill status-pill-green">SIMULATED</span>'
        db_desc = "Local Synthetic Data"
    else:
        conn = health.get("connected", False)
        mode_pill = '<span class="status-pill status-pill-green"><span class="pulse-dot"></span> REAL DATA</span>'
        backend_pill = '<span class="status-pill status-pill-green">ACTIVE</span>' if conn else '<span class="status-pill status-pill-red">OFFLINE</span>'
        db_pill = '<span class="status-pill status-pill-green">ONLINE</span>' if conn else '<span class="status-pill status-pill-red">OFFLINE</span>'
        db_desc = "Aiven Cloud MySQL 8.4"

    st.markdown(f"""
        <div style="font-size: 0.74rem; line-height: 1.8; font-family: 'JetBrains Mono', monospace; background: rgba(15, 23, 42, 0.75); padding: 12px; border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.12); backdrop-filter: blur(8px);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: #94A3B8;">DATA_MODE</span>
                {mode_pill}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: #94A3B8;">Database</span>
                {db_pill}
            </div>
            <div style="font-size: 0.68rem; color: #64748B; margin-bottom: 6px; border-bottom: 1px dashed rgba(148, 163, 184, 0.15); padding-bottom: 4px;">
                ☁️ {db_desc}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #94A3B8;">Quant Engine</span>
                {backend_pill}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Sync & Clear Cache", use_container_width=True, help="Refreshes live data from Aiven database immediately"):
        st.cache_data.clear()
        st.rerun()
