"""
QuantDB Strategy Service.
Manages quantitative strategy catalog metadata, parameter schemas, and descriptions.
The service layer passes configuration to the Quant Engine and NEVER implements
computational quantitative algorithms directly.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import streamlit as st

from dashboard.providers.factory import get_provider, get_current_data_mode

logger = logging.getLogger(__name__)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_get_strategies(data_mode: str) -> List[Dict]:
    provider = get_provider()
    return provider.get_strategies()


def get_strategies() -> List[Dict]:
    """Retrieves full catalog of quantitative trading strategies."""
    try:
        mode = get_current_data_mode()
        return _cached_get_strategies(mode)
    except Exception as e:
        logger.error(f"Error fetching strategies: {e}")
        try:
            return get_provider().get_strategies()
        except Exception:
            return []


def get_strategy_by_id(strategy_id: int) -> Optional[Dict]:
    """Retrieves metadata and parameter schema for a specific strategy."""
    strats = get_strategies()
    for s in strats:
        if s.get("strategy_id") == strategy_id:
            return s
    return None


def get_strategies_dataframe() -> pd.DataFrame:
    """Returns a high-level summary DataFrame suitable for rendering in strategy tables."""
    strats = get_strategies()
    if not strats:
        return pd.DataFrame(columns=["strategy_id", "name", "type", "description", "status"])
    rows = []
    for s in strats:
        rows.append({
            "strategy_id": s["strategy_id"],
            "name": s["name"],
            "type": s["type"],
            "description": s["description"],
            "status": s["status"],
            "parameter_count": len(s.get("parameters", [])),
        })
    return pd.DataFrame(rows)


def clear_strategy_service_cache() -> None:
    """Explicitly invalidates all cached strategy queries."""
    try:
        _cached_get_strategies.clear()
    except Exception as e:
        logger.debug(f"Failed to clear strategy service cache: {e}")

