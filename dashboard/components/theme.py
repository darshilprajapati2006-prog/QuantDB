"""
QuantDB Terminal Design System and Theme Utilities.
Injects custom CSS to achieve a high-density, professional Bloomberg-inspired
quantitative terminal aesthetic.
"""

import streamlit as st


def apply_terminal_theme():
    """Injects high-grade dark quantitative finance styling into the Streamlit session."""
    st.markdown("""
        <style>
        /* Base typography & terminal background styling */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #E2E8F0;
            background-color: #080D1A;
        }

        /* Number fonts in tables and metrics */
        .q-mono, .stMetric, table, code, pre {
            font-family: 'JetBrains Mono', 'Roboto Mono', monospace !important;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #080D1A;
        }
        ::-webkit-scrollbar-thumb {
            background: #1E293B;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #334155;
        }

        /* Glassmorphic Card Container styling */
        .quant-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.5) 100%);
            border: 1px solid rgba(148, 163, 184, 0.12);
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 14px;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .quant-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.4), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .quant-card:hover {
            border-color: rgba(6, 182, 212, 0.35);
            transform: translateY(-2px);
            box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.5), 0 0 16px -2px rgba(6, 182, 212, 0.15);
        }

        .quant-card:hover::before {
            opacity: 1;
        }

        .quant-card-title {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: #94A3B8;
            font-weight: 600;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .quant-card-value {
            font-size: 1.65rem;
            font-weight: 700;
            color: #F8FAFC;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1.15;
            letter-spacing: -0.02em;
        }

        .quant-card-delta-pos {
            font-size: 0.80rem;
            color: #10B981;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .quant-card-delta-neg {
            font-size: 0.80rem;
            color: #F43F5E;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .quant-card-delta-neutral {
            font-size: 0.80rem;
            color: #06B6D4;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .quant-card-desc {
            font-size: 0.72rem;
            color: #64748B;
            margin-top: 6px;
            font-weight: 400;
        }

        /* Status Pills & Badges */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.70rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.05em;
        }

        .status-pill-green {
            background-color: rgba(16, 185, 129, 0.12);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }

        .status-pill-amber {
            background-color: rgba(245, 158, 11, 0.12);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.35);
        }

        .status-pill-red {
            background-color: rgba(244, 63, 94, 0.12);
            color: #FB7185;
            border: 1px solid rgba(244, 63, 94, 0.35);
        }

        .status-pill-cyan {
            background-color: rgba(6, 182, 212, 0.12);
            color: #22D3EE;
            border: 1px solid rgba(6, 182, 212, 0.35);
        }

        /* Pulsing Live Dot */
        @keyframes live-pulse {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .pulse-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #10B981;
            display: inline-block;
            animation: live-pulse 2s infinite;
        }

        /* Paper trading header banner */
        .sim-banner {
            background: linear-gradient(90deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.4) 100%);
            border-left: 3px solid #06B6D4;
            padding: 9px 16px;
            margin-bottom: 18px;
            border-radius: 0 6px 6px 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-top: 1px solid rgba(148, 163, 184, 0.08);
            border-bottom: 1px solid rgba(148, 163, 184, 0.08);
            border-right: 1px solid rgba(148, 163, 184, 0.08);
        }

        .sim-banner-text {
            color: #38BDF8;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            font-family: 'JetBrains Mono', monospace;
        }

        .sim-banner-sub {
            color: #94A3B8;
            font-size: 0.75rem;
        }

        /* Streamlit native widget refinement */
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #0B1120 !important;
            border-right: 1px solid rgba(148, 163, 184, 0.1) !important;
        }

        .stDataFrame {
            border: 1px solid rgba(148, 163, 184, 0.12) !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }

        /* Buttons Styling */
        div.stButton > button {
            border-radius: 6px !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            transition: all 0.2s ease !important;
            font-family: 'Inter', sans-serif !important;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #06B6D4 0%, #2563EB 100%) !important;
            border: none !important;
            box-shadow: 0 4px 14px -2px rgba(6, 182, 212, 0.35) !important;
        }

        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px -2px rgba(6, 182, 212, 0.55) !important;
            transform: translateY(-1px) !important;
        }

        div.stButton > button[kind="secondary"] {
            background: #1E293B !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            color: #E2E8F0 !important;
        }

        div.stButton > button[kind="secondary"]:hover {
            border-color: #06B6D4 !important;
            color: #06B6D4 !important;
        }

        /* Section divider */
        .quant-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.15), transparent);
            margin: 18px 0;
        }

        /* Custom Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent !important;
            border: none !important;
            color: #94A3B8 !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            padding: 8px 16px !important;
            border-radius: 6px 6px 0 0 !important;
        }

        .stTabs [aria-selected="true"] {
            color: #06B6D4 !important;
            border-bottom: 2px solid #06B6D4 !important;
        }
        </style>
    """, unsafe_allow_html=True)
