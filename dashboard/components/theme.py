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
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #E2E8F0;
        }

        /* Number fonts in tables and metrics */
        .q-mono, .stMetric, table, code {
            font-family: 'JetBrains Mono', 'Roboto Mono', monospace !important;
        }

        /* Card Container styling */
        .quant-card {
            background-color: #111827;
            border: 1px solid #1F2937;
            border-radius: 6px;
            padding: 14px 18px;
            margin-bottom: 12px;
        }

        .quant-card:hover {
            border-color: #374151;
        }

        .quant-card-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94A3B8;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .quant-card-value {
            font-size: 1.55rem;
            font-weight: 700;
            color: #F8FAFC;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1.2;
        }

        .quant-card-delta-pos {
            font-size: 0.8rem;
            color: #10B981;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            margin-top: 4px;
        }

        .quant-card-delta-neg {
            font-size: 0.8rem;
            color: #EF4444;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            margin-top: 4px;
        }

        .quant-card-delta-neutral {
            font-size: 0.8rem;
            color: #06B6D4;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            margin-top: 4px;
        }

        .quant-card-desc {
            font-size: 0.72rem;
            color: #64748B;
            margin-top: 4px;
        }

        /* Status Pills */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.05em;
        }

        .status-pill-green {
            background-color: rgba(16, 185, 129, 0.15);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .status-pill-amber {
            background-color: rgba(245, 158, 11, 0.15);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .status-pill-red {
            background-color: rgba(239, 68, 68, 0.15);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .status-pill-cyan {
            background-color: rgba(6, 182, 212, 0.15);
            color: #22D3EE;
            border: 1px solid rgba(6, 182, 212, 0.3);
        }

        /* Paper trading header banner */
        .sim-banner {
            background: linear-gradient(90deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.03) 100%);
            border-left: 3px solid #F59E0B;
            padding: 8px 14px;
            margin-bottom: 16px;
            border-radius: 0 4px 4px 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .sim-banner-text {
            color: #FBBF24;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .sim-banner-sub {
            color: #94A3B8;
            font-size: 0.75rem;
        }

        /* Streamlit native widget refinement */
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }

        .stDataFrame {
            border: 1px solid #1F2937 !important;
            border-radius: 6px !important;
        }

        /* Section divider */
        .quant-divider {
            height: 1px;
            background: #1F2937;
            margin: 18px 0;
        }
        </style>
    """, unsafe_allow_html=True)
