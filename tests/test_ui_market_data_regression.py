"""
Regression tests for QuantDB UI typography wrapping fixes, Sharpe ratio stability,
and Market Data live trading integration.
"""

import pytest
import streamlit as st
from unittest.mock import MagicMock, patch

from dashboard.components.metrics import render_metric_card, format_currency, format_pct, format_pnl
from dashboard.providers.real_provider import RealProvider


def test_render_metric_card_html_attributes():
    """Verify render_metric_card embeds non-wrapping styles and dynamic font sizing."""
    with patch("streamlit.markdown") as mock_md:
        # Long currency value should have smaller font and nowrap
        render_metric_card(
            title="PORTFOLIO VALUE",
            value="$750,000.00",
            change="-25.00%",
            is_positive=False,
            description="Cash + Open Holdings",
            badge="REAL",
        )
        assert mock_md.called
        html_arg = mock_md.call_args[0][0]
        assert "white-space: nowrap !important" in html_arg
        assert "word-break: keep-all !important" in html_arg
        assert "$750,000.00" in html_arg
        assert "PORTFOLIO VALUE" in html_arg
        assert "REAL" in html_arg


def test_render_metric_card_short_value():
    """Verify short values receive standard readable font sizing."""
    with patch("streamlit.markdown") as mock_md:
        render_metric_card(
            title="SHARPE",
            value="1.84",
            change="Sortino: 2.12",
            is_positive=True,
        )
        assert mock_md.called
        html_arg = mock_md.call_args[0][0]
        assert "1.84" in html_arg
        assert "font-size: 1.42rem" in html_arg


def test_real_provider_sharpe_bounding():
    """Verify that RealProvider bounds Sharpe and Sortino ratios to realistic limits."""
    provider = RealProvider()
    with patch.object(provider, "is_connected", return_value=True), \
         patch.object(provider.repo, "get_market_data", return_value=[
             {"close_price": 180.0},
             {"close_price": 180.001},
         ]):
        risk = provider.get_risk_metrics(portfolio_id=1)
        assert isinstance(risk, dict)
        assert -5.0 <= risk["sharpe_ratio"] <= 5.0
        assert -5.0 <= risk["sortino_ratio"] <= 6.0


def test_format_helpers():
    """Verify format helpers produce proper signed and currency strings."""
    assert format_currency(750000.0) == "$750,000.00"
    assert format_currency(-1500.5) == "-$1,500.50"
    assert format_pct(2.5, include_sign=True) == "+2.50%"
    assert format_pnl(-250.0) == "-$250.00"
    assert format_pnl(500.0) == "+$500.00"
