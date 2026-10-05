"""
QuantDB Reusable Metric Components.
Renders consistent, high-density terminal-grade metric cards.
Supports finance-specific positive/negative/neutral coloring and formatting.
"""

from typing import Optional
import streamlit as st


def render_metric_card(
    title: str,
    value: str,
    change: Optional[str] = None,
    is_positive: Optional[bool] = None,
    description: Optional[str] = None,
    badge: Optional[str] = None,
):
    """
    Renders a terminal-styled metric card.
    
    Args:
        title: Metric label (e.g. "Total P&L", "Sharpe Ratio")
        value: Formatted display string (e.g. "$1,240,500.00", "1.84")
        change: Optional delta indicator (e.g. "+$14,250 (+1.2%)", "-3.5%")
        is_positive: True -> green, False -> red, None -> cyan/neutral
        description: Optional sub-label text
        badge: Optional badge tag (e.g. "ANNUALIZED", "252D")
    """
    delta_html = ""
    if change:
        if is_positive is True:
            delta_class = "quant-card-delta-pos"
            arrow = "▲ "
        elif is_positive is False:
            delta_class = "quant-card-delta-neg"
            arrow = "▼ "
        else:
            delta_class = "quant-card-delta-neutral"
            arrow = "● "
        delta_html = f'<div class="{delta_class}">{arrow}{change}</div>'

    badge_html = f'<span class="status-pill status-pill-cyan" style="float: right; font-size: 0.65rem;">{badge}</span>' if badge else ""
    desc_html = f'<div class="quant-card-desc">{description}</div>' if description else ""

    html = f"""
    <div class="quant-card">
        <div class="quant-card-title">{title} {badge_html}</div>
        <div class="quant-card-value">{value}</div>
        {delta_html}
        {desc_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def format_currency(val: float, precision: int = 2) -> str:
    """Formats float as clean USD string."""
    if val >= 0:
        return f"${val:,.{precision}f}"
    else:
        return f"-${abs(val):,.{precision}f}"


def format_pct(val: float, precision: int = 2, include_sign: bool = False) -> str:
    """Formats float as clean percentage string."""
    if include_sign and val > 0:
        return f"+{val:.{precision}f}%"
    return f"{val:.{precision}f}%"


def format_pnl(val: float, precision: int = 2) -> str:
    """Formats float as signed P&L string."""
    if val > 0:
        return f"+${val:,.{precision}f}"
    elif val < 0:
        return f"-${abs(val):,.{precision}f}"
    else:
        return f"${val:,.{precision}f}"
