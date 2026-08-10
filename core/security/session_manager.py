"""Timeout de sesion por inactividad (30 min)."""
from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

SESSION_TIMEOUT_MINUTES = 30
_KEYS = ("authenticated", "username", "role", "last_activity")


def check_session_timeout() -> bool:
    """Retorna True si la sesion sigue activa; False si expiro."""
    if not st.session_state.get("authenticated", False):
        return True
    if "last_activity" not in st.session_state:
        st.session_state["last_activity"] = datetime.now()
        return True
    elapsed = datetime.now() - st.session_state["last_activity"]
    if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        for k in _KEYS:
            st.session_state.pop(k, None)
        return False
    st.session_state["last_activity"] = datetime.now()
    return True
