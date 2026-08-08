"""
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
    page_icon="\U0001F33E",
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
            "<h1 style='text-align:center; color:#2E8B57;'>\U0001F33E EVA Valle v3.0</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#4A5568;'>"
            "Dashboard Analitico UPRA - Valle del Cauca</p>",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contrase\u00f1a", type="password")
            entrar = st.form_submit_button("Ingresar", use_container_width=True)
        if entrar:
            if verify(usuario, password):
                login(usuario)
                st.rerun()
            else:
                st.error("\u26D4 Usuario o contrase\u00f1a incorrectos.")


# ── Gate de autenticacion ───────────────────────────────────
if not is_authenticated():
    render_login()
    st.stop()

# ── Sidebar con usuario y cierre de sesion ──────────────────
with st.sidebar:
    st.title("\U0001F33E EVA Valle")
    st.caption(f"\U0001F464 {st.session_state.get('username')} "
               f"({current_role()})")
    if st.button("\U0001F6AA Cerrar sesion"):
        logout()
        st.rerun()
    st.markdown("---")
    st.caption("UPRA - Unidad de Planificacion Rural y Agropecuaria")

# ── Navegacion segun rol ────────────────────────────────────
role = current_role()

pages = [
    st.Page("ui/pages/0_Home.py", title="Inicio", icon="\U0001F3E0", default=True),
    st.Page("ui/pages/1_Dashboard.py", title="Dashboard", icon="\U0001F4CA"),
    st.Page("ui/pages/2_Descriptivo.py", title="Descriptivo", icon="\U0001F4C8"),
    st.Page("ui/pages/8_Mapa.py", title="Mapa", icon="\U0001F5FA\uFE0F"),
    st.Page("ui/pages/7_Cultivos.py", title="Cultivos", icon="\U0001F331"),
]

if role == "admin":
    pages += [
        st.Page("ui/pages/3_Diagnostico.py", title="Diagnostico", icon="\U0001F52C"),
        st.Page("ui/pages/4_Predictivo.py", title="Predictivo", icon="\U0001F916"),
        st.Page("ui/pages/5_Auditoria.py", title="Auditoria", icon="\U0001F50D"),
        st.Page("ui/pages/6_Configuracion.py", title="Configuracion", icon="\u2699\uFE0F"),
        st.Page("ui/pages/9_Admin.py", title="Panel Admin", icon="\U0001F510"),
    ]

pg = st.navigation(pages)
pg.run()
