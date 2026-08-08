"""Crea auth.py, users.json, 9_Admin.py y reescribe app.py con login+roles."""
import hashlib
import json
import secrets
from pathlib import Path

# ────────────────────────────────────────────────────────────
# ui/services/auth.py
# ────────────────────────────────────────────────────────────
AUTH = '''"""Servicio de autenticacion con roles (admin / usuario)."""
from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path

import streamlit as st

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


# ── Sesion ──────────────────────────────────────────────────
def login(username: str) -> None:
    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = get_role(username)


def logout() -> None:
    for k in ("authenticated", "username", "role"):
        st.session_state.pop(k, None)


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def current_role() -> str:
    return st.session_state.get("role", "usuario")
'''

# ────────────────────────────────────────────────────────────
# ui/pages/9_Admin.py
# ────────────────────────────────────────────────────────────
ADMIN = '''"""Pagina 9: Panel de Administracion (solo admin)."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.services.auth import add_user, current_role, list_users, remove_user

st.set_page_config(page_title="Admin | EVA Valle", page_icon="\\U0001F510", layout="wide")

if current_role() != "admin":
    st.error("\\u26D4 Acceso restringido a administradores.")
    st.stop()

st.title("\\U0001F510 Panel de Administracion")
st.caption("Gestion de usuarios y estado del sistema")
st.markdown("---")

tab1, tab2 = st.tabs(["\\U0001F465 Usuarios", "\\u2699\\uFE0F Sistema"])

with tab1:
    st.subheader("Usuarios registrados")
    usuarios = list_users()
    df_users = pd.DataFrame(
        [{"usuario": u, "rol": r} for u, r in usuarios.items()]
    )
    st.dataframe(df_users, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("\\u2795 Agregar usuario")
    with st.form("add_user"):
        c1, c2, c3 = st.columns(3)
        with c1:
            nuevo_u = st.text_input("Usuario")
        with c2:
            nuevo_p = st.text_input("Contrase\\u00f1a", type="password")
        with c3:
            nuevo_r = st.selectbox("Rol", ["usuario", "admin"])
        crear = st.form_submit_button("Crear usuario")
    if crear:
        if nuevo_u and nuevo_p:
            add_user(nuevo_u, nuevo_p, nuevo_r)
            st.success(f"\\u2705 Usuario '{nuevo_u}' creado con rol '{nuevo_r}'.")
            st.rerun()
        else:
            st.warning("Completa usuario y contrase\\u00f1a.")

    st.markdown("---")
    st.subheader("\\U0001F5D1 Eliminar usuario")
    eliminar_de = [u for u in usuarios if u != "admin"]
    if eliminar_de:
        sel = st.selectbox("Usuario a eliminar", eliminar_de)
        if st.button("\\U0001F5D1 Eliminar"):
            remove_user(sel)
            st.success(f"\\u2705 Usuario '{sel}' eliminado.")
            st.rerun()
    else:
        st.info("No hay usuarios eliminables (solo existe el admin).")

with tab2:
    st.subheader("Estado del sistema")
    st.markdown(f"**Proyecto:** {settings.PROJECT_NAME}")
    st.markdown(f"**Entorno:** {settings.ENV}")
    st.markdown(f"**Ruta raiz:** `{settings.PROJECT_ROOT}`")
    st.markdown("---")
    st.markdown("**Datos:**")
    st.code(
        f"Modelo conceptual: {settings.DATA_MODEL_PATH}\\n"
        f"Tablas de salida: {settings.OUTPUTS_TABLES_PATH}",
        language=None,
    )
'''

# ────────────────────────────────────────────────────────────
# app.py (reescribe con login + roles)
# ────────────────────────────────────────────────────────────
APP = '''"""
EVA Valle v3.0 - Dashboard con autenticacion y roles.
Primera pantalla: Login centrado. Luego navegacion segun rol.
"""
from __future__ import annotations

import streamlit as st
from pathlib import Path

from ui.services.auth import (
    current_role, is_authenticated, login, logout, verify,
)

st.set_page_config(
    page_title="EVA Valle del Cauca",
    page_icon="\\U0001F33E",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS (tema claro)
css_path = Path(__file__).parent / "ui" / "assets" / "css" / "style.css"
if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


def render_login() -> None:
    """Pantalla de login centrada."""
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown(
            "<h1 style='text-align:center; color:#2E8B57;'>\\U0001F33E EVA Valle v3.0</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#4A5568;'>"
            "Dashboard Analitico UPRA - Valle del Cauca</p>",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contrase\\u00f1a", type="password")
            entrar = st.form_submit_button("Ingresar", use_container_width=True)
        if entrar:
            if verify(usuario, password):
                login(usuario)
                st.rerun()
            else:
                st.error("\\u26D4 Usuario o contrase\\u00f1a incorrectos.")


# ── Gate de autenticacion ───────────────────────────────────
if not is_authenticated():
    render_login()
    st.stop()

# ── Sidebar con usuario y cierre de sesion ──────────────────
with st.sidebar:
    st.title("\\U0001F33E EVA Valle")
    st.caption(f"\\U0001F464 {st.session_state.get('username')} "
               f"({current_role()})")
    if st.button("\\U0001F6AA Cerrar sesion"):
        logout()
        st.rerun()
    st.markdown("---")
    st.caption("UPRA - Unidad de Planificacion Rural y Agropecuaria")

# ── Navegacion segun rol ────────────────────────────────────
role = current_role()

pages = [
    st.Page("ui/pages/0_Home.py", title="Inicio", icon="\\U0001F3E0", default=True),
    st.Page("ui/pages/1_Dashboard.py", title="Dashboard", icon="\\U0001F4CA"),
    st.Page("ui/pages/2_Descriptivo.py", title="Descriptivo", icon="\\U0001F4C8"),
    st.Page("ui/pages/8_Mapa.py", title="Mapa", icon="\\U0001F5FA\\uFE0F"),
    st.Page("ui/pages/7_Cultivos.py", title="Cultivos", icon="\\U0001F331"),
]

if role == "admin":
    pages += [
        st.Page("ui/pages/3_Diagnostico.py", title="Diagnostico", icon="\\U0001F52C"),
        st.Page("ui/pages/4_Predictivo.py", title="Predictivo", icon="\\U0001F916"),
        st.Page("ui/pages/5_Auditoria.py", title="Auditoria", icon="\\U0001F50D"),
        st.Page("ui/pages/6_Configuracion.py", title="Configuracion", icon="\\u2699\\uFE0F"),
        st.Page("ui/pages/9_Admin.py", title="Panel Admin", icon="\\U0001F510"),
    ]

pg = st.navigation(pages)
pg.run()
'''

if __name__ == "__main__":
    # 1. auth.py
    p = Path("ui/services/auth.py")
    p.write_text(AUTH, encoding="utf-8")
    print(f"[OK] {p}")

    # 2. users.json (admin / usuario) con hashes
    users = {}
    for u, pw, rol in [("admin", "admin123", "admin"), ("usuario", "usuario123", "usuario")]:
        salt = secrets.token_hex(8)
        users[u] = {"salt": salt, "hash": hashlib.sha256((salt + pw).encode()).hexdigest(), "role": rol}
    Path("config").mkdir(parents=True, exist_ok=True)
    Path("config/users.json").write_text(json.dumps(users, indent=2), encoding="utf-8")
    print("[OK] config/users.json (admin/admin123, usuario/usuario123)")

    # 3. 9_Admin.py
    p2 = Path("ui/pages/9_Admin.py")
    p2.write_text(ADMIN, encoding="utf-8")
    print(f"[OK] {p2}")

    # 4. app.py
    Path("app.py").write_text(APP, encoding="utf-8")
    print("[OK] app.py (login + roles)")

    print("\nParte 1 lista. Ejecuta: python scripts\\setup_auth_theme.py")