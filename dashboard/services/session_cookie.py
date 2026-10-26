"""Signed browser session restoration for Streamlit authentication."""

import base64
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import os
import secrets
import time

try:
    import extra_streamlit_components as stx
except ImportError:
    stx = None
import streamlit as st

from src.database.repository import Repository
from src.auth.roles import get_role_display_name

COOKIE_NAME = "quantdb_session"
COOKIE_MANAGER_KEY = "quantdb_session_cookie_manager"
SESSION_TTL_SECONDS = 14 * 24 * 60 * 60
_PROCESS_SECRET = secrets.token_bytes(32)


def _secret() -> bytes:
    configured = os.getenv("QUANTDB_SESSION_SECRET", "").strip()
    if not configured:
        try:
            configured = str(st.secrets.get("QUANTDB_SESSION_SECRET", "")).strip()
        except Exception:
            configured = ""
    return configured.encode("utf-8") if configured else _PROCESS_SECRET


def _cookie_manager():
    if stx is None:
        return None
    return stx.CookieManager(key=COOKIE_MANAGER_KEY)


def _encode_session(user_id: int) -> str:
    payload = {"user_id": int(user_id), "expires_at": int(time.time()) + SESSION_TTL_SECONDS}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_secret(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def _decode_session(value: str) -> int | None:
    try:
        encoded, signature = value.split(".", 1)
        expected = hmac.new(_secret(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        user_id = int(payload["user_id"])
        if int(payload["expires_at"]) <= int(time.time()) or user_id <= 0:
            return None
        return user_id
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def persist_login_session() -> None:
    user_id = st.session_state.get("user_id")
    manager = _cookie_manager()
    if not user_id or manager is None:
        return
    token = _encode_session(int(user_id))
    secure = os.getenv("QUANTDB_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes"}
    manager.set(
        COOKIE_NAME,
        token,
        expires_at=datetime.now() + timedelta(seconds=SESSION_TTL_SECONDS),
        secure=secure,
        same_site="lax",
        key="quantdb-session-cookie-set",
    )


def restore_login_session() -> bool:
    manager = _cookie_manager()
    if manager is None:
        return False
    token = manager.get(COOKIE_NAME)
    if not token:
        return False
    user_id = _decode_session(str(token))
    if user_id is None:
        manager.delete(COOKIE_NAME)
        return False
    try:
        user = Repository().get_user(user_id)
    except Exception:
        return False
    if not user or str(user.get("status", "ACTIVE")).upper() != "ACTIVE" or not bool(user.get("is_verified", True)):
        manager.delete(COOKIE_NAME)
        return False
    role = user.get("role", "USER")
    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user["user_id"]
    st.session_state["username"] = user.get("username") or user.get("email", "").split("@", 1)[0]
    st.session_state["display_name"] = user.get("name") or st.session_state["username"]
    st.session_state["email"] = user.get("email")
    st.session_state["role"] = role
    st.session_state["role_display"] = get_role_display_name(role)
    st.session_state["auth_screen"] = "signin"
    st.session_state["pending_verification"] = None
    return True


def clear_login_session() -> None:
    manager = _cookie_manager()
    if manager is not None:
        manager.delete(COOKIE_NAME)
