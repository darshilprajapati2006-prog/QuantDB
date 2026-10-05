"""
QuantDB — Quantitative Strategy Library & Parameter Configuration
Displays registered algorithmic trading strategies and their parameter schemas.
The UI collects and configures parameters without executing quantitative logic locally.
"""

from pathlib import Path
import sys
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
from dashboard.services.strategy_service import (
    get_strategies,
    get_strategy_by_id,
    get_strategies_dataframe,
)

# Page configuration
st.set_page_config(
    page_title="QuantDB — Strategy Library",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system and sidebar
apply_terminal_theme()
render_sidebar(current_page="Strategies")

# Top Disclaimer
render_simulation_banner("Quantitative Strategy Specifications • Analytical Quant Engine Interface")

# Page Header
st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; align-items: baseline; gap: 10px;">
            <h1 style="margin: 0; font-size: 1.75rem; font-weight: 800; color: #F8FAFC;">
                STRATEGY <span style="color: #06B6D4;">LIBRARY</span>
            </h1>
            <span style="color: #64748B; font-size: 0.90rem;">
                Algorithmic Models & Parameter Registry
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

strategies = get_strategies()
if not strategies:
    st.error("No strategies registered in the system.")
    st.stop()

# -------------------------------------------------------------
# SUMMARY METRIC CARDS
# -------------------------------------------------------------
sm1, sm2, sm3, sm4 = st.columns(4)

with sm1:
    render_metric_card(
        title="TOTAL STRATEGIES",
        value=str(len(strategies)),
        change="Registered Models",
        is_positive=None,
        description="Quant Strategy Registry"
    )

with sm2:
    active_count = sum(1 for s in strategies if s.get("status") == "ACTIVE")
    render_metric_card(
        title="PRODUCTION ACTIVE",
        value=str(active_count),
        change="Ready for Backtest",
        is_positive=True,
        description="Validated Alpha Models"
    )

with sm3:
    research_count = sum(1 for s in strategies if s.get("status") == "RESEARCH")
    render_metric_card(
        title="RESEARCH / EXPERIMENTAL",
        value=str(research_count),
        change="In Development",
        is_positive=None,
        description="Under Statistical Review"
    )

with sm4:
    strat_types = len(set(s.get("type") for s in strategies))
    render_metric_card(
        title="STRATEGY FAMILIES",
        value=str(strat_types),
        change="Diversified Archetypes",
        is_positive=None,
        description="Trend, Momentum, Mean-Rev, Arb"
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# STRATEGY SELECTION & PARAMETER CONFIGURATION
# -------------------------------------------------------------
strat_col, param_col = st.columns([5, 5])

with strat_col:
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Strategy Library Catalog
        </div>
    """, unsafe_allow_html=True)

    strat_map = {f"#{s['strategy_id']} {s['name']} [{s['type']}]": s["strategy_id"] for s in strategies}
    sel_label = st.selectbox("Select Strategy to Inspect", options=list(strat_map.keys()), index=0)
    selected_id = strat_map[sel_label]
    curr_strat = get_strategy_by_id(selected_id) or strategies[0]

    # Render strategy detail card
    status_class = "status-pill-green" if curr_strat.get("status") == "ACTIVE" else "status-pill-amber"
    st.markdown(f"""
        <div class="quant-card" style="margin-top: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC;">{curr_strat['name']}</span>
                <span class="status-pill {status_class}">{curr_strat.get('status', 'ACTIVE')}</span>
            </div>
            <div style="font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; color: #06B6D4; margin-bottom: 8px;">
                STRATEGY TYPE: {curr_strat.get('type', 'ALGORITHMIC').upper()}
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                {curr_strat.get('description', '')}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Strategy Table Overview
    st.markdown("""
        <div style="font-size: 0.78rem; text-transform: uppercase; color: #64748B; font-weight: 700; letter-spacing: 0.08em; margin: 16px 0 6px 0;">
            All Registered Strategy Entities
        </div>
    """, unsafe_allow_html=True)
    df_strats = get_strategies_dataframe()
    st.dataframe(
        df_strats,
        column_config={
            "strategy_id": st.column_config.NumberColumn("ID", format="#%d", width="small"),
            "name": st.column_config.TextColumn("Strategy Name", width="medium"),
            "type": st.column_config.TextColumn("Class", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "parameter_count": st.column_config.NumberColumn("Params", format="%d"),
        },
        use_container_width=True,
        hide_index=True,
    )

with param_col:
    st.markdown("""
        <div style="font-size: 0.85rem; text-transform: uppercase; color: #E2E8F0; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">
            Parameter Specification & Configuration Schema
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 12px; font-family: 'JetBrains Mono', monospace;">
            Parameters defined by the Quant Analytics Engine interface.
        </div>
    """, unsafe_allow_html=True)

    params = curr_strat.get("parameters", [])
    collected_params = {}

    if not params:
        st.info("This strategy operates with fixed parameters.")
    else:
        with st.container():
            st.markdown("<div class='quant-card' style='padding: 18px;'>", unsafe_allow_html=True)
            for p in params:
                p_name = p["name"]
                p_type = p.get("type", "int")
                p_default = p.get("default")
                p_desc = p.get("description", "")
                p_min = p.get("min")
                p_max = p.get("max")

                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace; margin-top: 4px;">
                        <span style="color: #F8FAFC; font-weight: 600;">{p_name}</span>
                        <span style="color: #64748B;">{p_type} • [{p_min} .. {p_max}]</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8; margin-bottom: 4px;">{p_desc}</div>
                """, unsafe_allow_html=True)

                if p_type == "int":
                    val = st.slider(
                        f"Set {p_name}",
                        min_value=int(p_min if p_min is not None else 1),
                        max_value=int(p_max if p_max is not None else 200),
                        value=int(p_default if p_default is not None else 20),
                        key=f"param_{curr_strat['strategy_id']}_{p_name}",
                        label_visibility="collapsed"
                    )
                    collected_params[p_name] = val
                elif p_type == "float":
                    val = st.slider(
                        f"Set {p_name}",
                        min_value=float(p_min if p_min is not None else 0.1),
                        max_value=float(p_max if p_max is not None else 10.0),
                        value=float(p_default if p_default is not None else 2.0),
                        step=0.1,
                        key=f"param_{curr_strat['strategy_id']}_{p_name}",
                        label_visibility="collapsed"
                    )
                    collected_params[p_name] = val
                elif p_type == "bool":
                    val = st.checkbox(
                        f"Enable {p_name}",
                        value=bool(p_default),
                        key=f"param_{curr_strat['strategy_id']}_{p_name}",
                    )
                    collected_params[p_name] = val

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            # Action button to push parameters directly to the Backtesting Page
            if st.button("SEND PARAMETERS TO BACKTESTING ENGINE", use_container_width=True, type="primary"):
                st.session_state["backtest_strategy_id"] = curr_strat["strategy_id"]
                st.session_state["backtest_params"] = collected_params
                st.success(f"Parameters for '{curr_strat['name']}' staged. Launching Backtest Terminal...")
                try:
                    st.switch_page("pages/backtesting.py")
                except Exception:
                    try:
                        st.switch_page("dashboard/pages/backtesting.py")
                    except Exception:
                        pass

            st.markdown("</div>", unsafe_allow_html=True)
