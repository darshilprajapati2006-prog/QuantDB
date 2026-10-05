"""
QuantDB Strategy Service.
Manages quantitative strategy catalog metadata, parameter schemas, and descriptions.
The service layer passes configuration to the Quant Engine and NEVER implements
computational quantitative algorithms directly.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
from dashboard.providers.factory import get_provider

logger = logging.getLogger(__name__)


def get_strategies() -> List[Dict]:
    """Retrieves full catalog of quantitative trading strategies."""
    try:
        provider = get_provider()
        return provider.get_strategies()
    except Exception as e:
        logger.error(f"Error fetching strategies: {e}")
        return []


def get_strategy_by_id(strategy_id: int) -> Optional[Dict]:
    """Retrieves metadata and parameter schema for a specific strategy."""
    try:
        provider = get_provider()
        return provider.get_strategy(strategy_id)
    except Exception as e:
        logger.error(f"Error fetching strategy {strategy_id}: {e}")
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
