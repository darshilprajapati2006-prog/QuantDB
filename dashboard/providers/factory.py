"""
QuantDB Provider Factory.
Instantiates and delivers the appropriate Provider (Mock or Real) based on system configuration.
"""

import os
from typing import Union
from dashboard.providers.mock_provider import MockProvider
from dashboard.providers.real_provider import RealProvider

# Cached instances
_mock_instance: Union[MockProvider, None] = None
_real_instance: Union[RealProvider, None] = None


def get_current_data_mode() -> str:
    """
    Returns the currently active DATA_MODE.
    Defaults to 'mock' as specified in requirements.
    Can be overridden via Streamlit session state, environment variable, or Streamlit secrets.
    """
    try:
        import streamlit as st
        if hasattr(st, "session_state") and "DATA_MODE" in st.session_state:
            return st.session_state["DATA_MODE"].lower()
        if hasattr(st, "secrets") and "DATA_MODE" in st.secrets:
            return str(st.secrets["DATA_MODE"]).lower()
    except Exception:
        pass
    return os.environ.get("DATA_MODE", "mock").lower()


def set_data_mode(mode: str) -> None:
    """Sets the active data mode ('mock' or 'real')."""
    cleaned = mode.lower()
    if cleaned not in ["mock", "real"]:
        raise ValueError(f"Invalid DATA_MODE: {mode}. Must be 'mock' or 'real'.")
    os.environ["DATA_MODE"] = cleaned
    try:
        import streamlit as st
        st.session_state["DATA_MODE"] = cleaned
    except Exception:
        pass


def get_provider() -> Union[MockProvider, RealProvider]:
    """
    Returns the active data provider instance.
    Pages never call this directly; they call the corresponding service in dashboard.services.
    """
    global _mock_instance, _real_instance
    mode = get_current_data_mode()

    if mode == "real":
        if _real_instance is None:
            _real_instance = RealProvider()
        return _real_instance
    else:
        if _mock_instance is None:
            _mock_instance = MockProvider()
        return _mock_instance
