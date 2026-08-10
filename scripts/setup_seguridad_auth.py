"""Reescribe auth.py (validacion + last_activity) y session_manager.py (claves correctas)."""
from pathlib import Path

AUTH = r'''"""Servicio de autenticacion con roles (admin / usuario)."""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime
from pathlib import Path

import streamlit as st

from core.security.input_validator import sanitize_password, sanitize_username

USERS_PATH = Path(__file__).parent.parent.parent / "config" / "users.json"


def _hash(pw: str, salt: str) -> str:
    return hashlib.sha256((salt + pw).encode("utf-8")).hexdigest()


def load_users() -> dict:
    if not USERS_PATH.exists():
        return {}
    return json.loads(USERS_PATH.read_text(encoding="utf-8"))


def save_users(users: dict) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def verify(username: str, password: str) -> bool:
    """Verifica credenciales con inputs sanitizados."""
    username = sanitize_username(username)
    password = sanitize_password(password)
    rec = load_users().get(username)
    if not rec:
        return False
    return _hash(password, rec["salt"]) == rec["hash"]


def get_role(username: str) -> str:
    return load_users().get(username, {}).get("role", "usuario")


def add_user(username: str, password: str, role: str = "usuario") -> None:
    users = load_users()
    salt = secrets.token_hex(8)
    users[username] = {"salt": salt, "hash": _hash(password, salt), "role": role}
    save_users(users)


def remove_user(username: str) -> None:
    users = load_users()
    users.pop(username, None)
    save_users(users)


def list_users() -> dict:
    return {u: rec.get("role", "usuario") for u, rec in load_users().items()}


# --- Sesion -----------------------------------------------------------
def login(username: str) -> None:
    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = get_role(username)
    st.session_state["last_activity"] = datetime.now()


def logout() -> None:
    for k in ("authenticated", "username", "role", "last_activity"):
        st.session_state.pop(k, None)


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def current_role() -> str:
    return st.session_state.get("role", "usuario")
'''

SESSION = r'''"""Timeout de sesion por inactividad (30 min)."""
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
'''

Path("ui/services/auth.py").write_text(AUTH, encoding="utf-8")
print("[OK] ui/services/auth.py (validacion + last_activity)")
Path("core/security/session_manager.py").write_text(SESSION, encoding="utf-8")
print("[OK] core/security/session_manager.py (claves correctas)")
print("\nSigue: python scripts\\setup_seguridad_app.py")