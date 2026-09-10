"""
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

# Correo institucional de contacto (editar si cambia)
CONTACTO_EMAIL = "moises.zuniga.grueso@gmail.com"
CONTACTO_TELEFONO = "+57 3167197764"

st.set_page_config(
    page_title="EVA Valle del Cauca",
    page_icon=str(Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"),
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
    """Pantalla de login institucional con rate limiting y validacion."""
    st.markdown(
        "<style>section[data-testid='stSidebar']{display:none;}"
        "[data-testid='stSidebarCollapsedControl']{display:none;}</style>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <!-- CONTACTO_V2 -->
        <div id="eva-contacto">
          📧 <a href="mailto:moises.zuniga.grueso@gmail.com?subject=Acceso%20EVA%20Valle%20v3.0">Escríbenos</a><br>
          📞 <a href="tel:+573167197764">+57 3167197764</a><br>
          💬 <a href="https://wa.me/573167197764" target="_blank">WhatsApp</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Fondo del panel de marca: reutiliza hero.png si existe (mismo asset del Home)
    import base64 as _b64
    _hero = Path(__file__).parent / "ui" / "assets" / "img" / "hero.png"
    if _hero.exists():
        _img = _b64.b64encode(_hero.read_bytes()).decode()
        st.markdown(
            f"<style>:root{{--eva-login-bg: url('data:image/png;base64,{_img}');}}</style>",
            unsafe_allow_html=True,
        )

    logo_path = Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"
    logo_b64 = ""
    if logo_path.exists():
        import base64 as _b64_logo
        logo_b64 = _b64_logo.b64encode(logo_path.read_bytes()).decode()

    col_brand, col_form = st.columns([1.1, 1], gap="small")

    with col_brand:
        logo_html = (
            f'<img src="data:image/png;base64,{logo_b64}" width="56" />'
            if logo_b64 else ""
        )
        st.markdown(
            f"""
            <div class="eva-login-brand">
                <div class="eva-brand-top">
                    {logo_html}
                    <h1>EVA Valle</h1>
                    <p>Inteligencia Agrícola Territorial</p>
                </div>
                <div class="eva-brand-quote">
                    "El dato oficial, al servicio de quien siembra"
                </div>
                <div>
                    <div class="eva-brand-stats">
                        <span>42 municipios</span>
                        <span>78 cultivos</span>
                        <span>2019–2025</span>
                    </div>
                    <div class="eva-brand-version" style="margin-top:.8rem;">
                        Plataforma analítica · UPRA · EVA 2019-2025 &nbsp;·&nbsp; v3.0
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_form:
        st.markdown(
            "<div style='margin-bottom:1.5rem;'>"
            "<div style='font-size:1.3rem; font-weight:700; color:var(--eva-text); margin-bottom:.3rem;'>"
            "Acceso a la plataforma</div>"
            "<p class='eva-login-sub' style='margin:0;'>Ingresa tus credenciales institucionales.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            entrar = st.form_submit_button("Ingresar", use_container_width=True)
        if entrar:
            u = sanitize_username(usuario)
            p = sanitize_password(password)
            if not u or not p:
                st.error("⚠️ Usuario o contraseña invalidos.")
            elif not login_limiter.is_allowed(u):
                st.error("⚠️ Demasiados intentos fallidos. Espera 15 minutos.")
            elif verify(u, p):
                login_limiter.reset(u)
                login(u)
                st.rerun()
            else:
                st.error("⛔ Usuario o contraseña incorrectos.")
        st.markdown(
            "<div class='eva-login-security'>🔒 Conexión protegida · datos oficiales UPRA</div>"
            "<div class='eva-login-footer'>EVA Valle v3.0 · Valle del Cauca, Colombia</div>",
            unsafe_allow_html=True,
        )

# --- Gate de autenticacion --------------------------------------------
if not is_authenticated():
    render_login()
    st.stop()

# --- Session timeout (30 min de inactividad) --------------------------
if not check_session_timeout():
    st.rerun()

# --- Sidebar con usuario y cierre de sesion ---------------------------
with st.sidebar:
    st.image(str(Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"), width=84)
    st.title("EVA Valle")
    role = current_role()
    role_icon = {"admin": "\U0001F451", "analista": "\U0001F9ED", "user": "\U0001F464"}.get(role, "\U0001F464")
    role_label = {"admin": "Admin", "analista": "Analista", "user": "Usuario"}.get(role, role)
    st.markdown(
        f'<div class="eva-sidebar-user">{role_icon} <b>{st.session_state.get("username")}</b>'
        f'<br><span style="color:var(--eva-muted);">{role_label}</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("\U0001F6AA Cerrar sesion", use_container_width=True):
        logout()
        st.rerun()
    st.markdown("---")
    st.caption("UPRA - Unidad de Planificacion Rural y Agropecuaria")

# --- Navegacion por nivel analitico (mismo control de roles) ----------
# Orden del sidebar: Panorama -> 1 Descriptivo -> 2 Diagnostico ->
# 3 Predictivo -> 4 Prescriptivo -> Entregables -> Gobernanza.
def _build_navigation(role: str):
    nivel = {"user": 0, "usuario": 0, "analista": 1, "admin": 2}.get(role, 0)
    todas = [
        # (seccion, rol minimo, pagina)
        ("🏠 Panorama", 0, st.Page("ui/pages/0_Home.py", title="Inicio", icon="🏠", default=True)),
        ("🏠 Panorama", 0, st.Page("ui/pages/15_Ejecutivo.py", title="Resumen Ejecutivo", icon="📋")),
        ("🏠 Panorama", 0, st.Page("ui/pages/1_Dashboard.py", title="Dashboard", icon="📊")),

        ("📊 1 · Descriptivo — ¿que paso?", 0, st.Page("ui/pages/7_Cultivos.py", title="Cultivos", icon="🌱")),
        ("📊 1 · Descriptivo — ¿que paso?", 0, st.Page("ui/pages/13_Treemap.py", title="Treemap", icon="🌳")),
        ("📊 1 · Descriptivo — ¿que paso?", 0, st.Page("ui/pages/8_Mapa.py", title="Mapa", icon="🗺️")),
        ("📊 1 · Descriptivo — ¿que paso?", 0, st.Page("ui/pages/11_Comparador.py", title="Comparador", icon="⚖️")),
        ("📊 1 · Descriptivo — ¿que paso?", 1, st.Page("ui/pages/2_Descriptivo.py", title="Descriptivo", icon="📈")),

        ("🔬 2 · Diagnostico — ¿por que paso?", 1, st.Page("ui/pages/3_Diagnostico.py", title="Diagnostico", icon="🔬")),

        ("🔮 3 · Predictivo — ¿que pasara?", 1, st.Page("ui/pages/4_Predictivo.py", title="Predictivo", icon="🤖")),
        ("🔮 3 · Predictivo — ¿que pasara?", 1, st.Page("ui/pages/12_Alertas.py", title="Alertas", icon="🚨")),

        ("🎯 4 · Prescriptivo — ¿que hacer?", 1, st.Page("ui/pages/19_Zonas.py", title="Zonas", icon="🎯")),
        ("\U0001F3AF 4 \u00b7 Prescriptivo \u2014 \u00bfque hacer?", 1, st.Page("ui/pages/22_Recomendador.py", title="Recomendador", icon="\U0001F3AF")),
        ("💰 5 · Económico — ¿cuánto vale?", 1, st.Page("ui/pages/23_Valor_Economico.py", title="Valor Economico", icon="💰")),
        ("🎰 6 · Adaptativo — ¿qué modelo confiar?", 1, st.Page("ui/pages/24_Selector_Modelos.py", title="Selector de Modelos", icon="🎰")),

        ("💬 Asistente", 0, st.Page("ui/pages/21_Asistente.py", title="Asistente", icon="💬")),
        ("📦 Entregables", 0, st.Page("ui/pages/10_Reportes.py", title="Reportes", icon="📄")),

        ("🛡️ Gobernanza del dato", 1, st.Page("ui/pages/18_Satelite.py", title="Validacion Satelital", icon="🛰️")),
        ("🛡️ Gobernanza del dato", 2, st.Page("ui/pages/5_Auditoria.py", title="Auditoria", icon="🔍")),
        ("🛡️ Gobernanza del dato", 2, st.Page("ui/pages/6_Configuracion.py", title="Configuracion", icon="⚙️")),
        ("🛡️ Gobernanza del dato", 2, st.Page("ui/pages/9_Admin.py", title="Panel Admin", icon="🔐")),
    ]
    nav = {}
    for seccion, min_rol, page in todas:
        if min_rol <= nivel:
            nav.setdefault(seccion, []).append(page)
    return nav


pg = st.navigation(_build_navigation(role))
pg.run()
