"""Reorganiza app.py con 3 perfiles: usuario (8) / analista (14) / admin (todo)."""
from pathlib import Path

NEW_APP = '''"""
EVA Valle v3.0 - Dashboard con autenticacion y 3 roles.
Seguridad: rate limiting + session timeout + input validation.
"""
from __future__ import annotations

import streamlit as st
from pathlib import Path

from core.security.input_validator import sanitize_password, sanitize_username
from core.security.rate_limiter import login_limiter
from core.security.session_manager import check_session_timeout
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
    """Pantalla de login centrada con rate limiting y validacion."""
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
            u = sanitize_username(usuario)
            p = sanitize_password(password)
            if not u or not p:
                st.error("\\u26a0\\ufe0f Usuario o contrase\\u00f1a invalidos.")
            elif not login_limiter.is_allowed(u):
                st.error("\\u26a0\\ufe0f Demasiados intentos fallidos. Espera 15 minutos.")
            elif verify(u, p):
                login_limiter.reset(u)
                login(u)
                st.rerun()
            else:
                st.error("\\u26d4 Usuario o contrase\\u00f1a incorrectos.")


# --- Gate de autenticacion --------------------------------------------
if not is_authenticated():
    render_login()
    st.stop()

# --- Session timeout (30 min de inactividad) --------------------------
if not check_session_timeout():
    st.rerun()

# --- Sidebar con usuario y cierre de sesion ---------------------------
with st.sidebar:
    st.title("\\U0001F33E EVA Valle")
    role = current_role()
    role_icon = {"admin": "\\U0001F451", "analista": "\\U0001F9ED", "user": "\\U0001F464"}.get(role, "\\U0001F464")
    role_label = {"admin": "Admin", "analista": "Analista", "user": "Usuario"}.get(role, role)
    st.caption(f"{role_icon} {st.session_state.get('username')} ({role_label})")
    if st.button("\\U0001F6AA Cerrar sesion"):
        logout()
        st.rerun()
    st.markdown("---")
    st.caption("UPRA - Unidad de Planificacion Rural y Agropecuaria")

# --- Navegacion por rol (3 perfiles) ----------------------------------
# Grupo 1: USUARIO (8) - productos y descargas
PAGINAS_USUARIO = [
    st.Page("ui/pages/0_Home.py", title="Inicio", icon="\\U0001F3E0", default=True),
    st.Page("ui/pages/1_Dashboard.py", title="Dashboard", icon="\\U0001F4CA"),
    st.Page("ui/pages/8_Mapa.py", title="Mapa", icon="\\U0001F5FA\\uFE0F"),
    st.Page("ui/pages/7_Cultivos.py", title="Cultivos", icon="\\U0001F331"),
    st.Page("ui/pages/11_Comparador.py", title="Comparador", icon="\\u2696\\uFE0F"),
    st.Page("ui/pages/13_Treemap.py", title="Treemap", icon="\\U0001F333"),
    st.Page("ui/pages/10_Reportes.py", title="Reportes", icon="\\U0001F4C4"),
    st.Page("ui/pages/15_Ejecutivo.py", title="Resumen Ejecutivo", icon="\\U0001F4CB"),
]

# Grupo 2: ANALISTA (+6) - analisis sensible interno
PAGINAS_ANALISTA = [
    st.Page("ui/pages/2_Descriptivo.py", title="Descriptivo", icon="\\U0001F4C8"),
    st.Page("ui/pages/12_Alertas.py", title="Alertas", icon="\\U0001F6A8"),
    st.Page("ui/pages/19_Zonas.py", title="Zonas", icon="\\U0001F5FA\\uFE0F"),
    st.Page("ui/pages/18_Satelite.py", title="Validacion Satelital", icon="\\U0001F6F0\\uFE0F"),
    st.Page("ui/pages/3_Diagnostico.py", title="Diagnostico", icon="\\U0001F52C"),
    st.Page("ui/pages/4_Predictivo.py", title="Predictivo", icon="\\U0001F916"),
]

# Grupo 3: ADMIN (+4) - sala de maquinas del sistema
PAGINAS_ADMIN = [
    st.Page("ui/pages/5_Auditoria.py", title="Auditoria", icon="\\U0001F50D"),
    st.Page("ui/pages/6_Configuracion.py", title="Configuracion", icon="\\u2699\\uFE0F"),
    st.Page("ui/pages/9_Admin.py", title="Panel Admin", icon="\\U0001F510"),
]

if role == "admin":
    pages = PAGINAS_USUARIO + PAGINAS_ANALISTA + PAGINAS_ADMIN
elif role == "analista":
    pages = PAGINAS_USUARIO + PAGINAS_ANALISTA
else:
    pages = PAGINAS_USUARIO

pg = st.navigation(pages)
pg.run()
'''

Path("app.py").write_text(NEW_APP, encoding="utf-8")
print("[OK] app.py reescrito con 3 perfiles (usuario/analista/admin)")
print("     Usuario: 8 pestanas (productos y descargas)")
print("     Analista: +6 pestanas (analisis sensible interno)")
print("     Admin: +4 pestanas (sala de maquinas)")
print("     Ficha Tecnica (14) removida del menu (ya vive en Cultivos)")
print()
print("Siguiente paso: necesito ver ui/services/auth.py para agregar el rol")
print("'analista' al sistema de usuarios.")