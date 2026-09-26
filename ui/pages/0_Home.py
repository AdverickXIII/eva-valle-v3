"""Pagina 0: Inicio - Hub de navegacion."""
from __future__ import annotations

# ---------- Hero banner (visible aun sin imagen) ----------
import base64 as _b64
from pathlib import Path as _Path

import streamlit as st


def _nav_card(col, page_path: str, icon: str, label: str, desc: str, min_rol: int = 0) -> None:
    """Renderiza una card de navegacion si el usuario tiene el rol minimo requerido.
    
    Args:
        col: columna de Streamlit donde renderizar
        page_path: ruta de la pagina (ej: "ui/pages/1_Dashboard.py")
        icon: emoji del icono
        label: categoria en mayusculas
        desc: descripcion breve
        min_rol: nivel minimo requerido (0=user, 1=analista, 2=admin)
    """
    from ui.services.auth import current_role
    
    role = current_role()
    nivel = {"user": 0, "usuario": 0, "analista": 1, "admin": 2}.get(role, 0)
    
    if nivel < min_rol:
        return  # No renderizar si no tiene permiso
    
    with col:
        st.markdown('<div class="eva-nav-card">', unsafe_allow_html=True)
        st.page_link(
            page_path,
            label=f"**{label.upper()}**  \n{desc}",
            icon=icon,
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


_hero = _Path(__file__).parent.parent / "assets" / "img" / "hero.png"
if _hero.exists():
    _img = _b64.b64encode(_hero.read_bytes()).decode()
    _capa = f'url("data:image/png;base64,{_img}") center 18% / cover no-repeat'
else:
    _capa = "none"

st.markdown(
    f"""<style id="hero_banner">
.hero-banner {{
    background: linear-gradient(90deg,
        rgba(15,50,35,0.85) 0%, rgba(15,50,35,0.45) 55%, rgba(15,50,35,0.10) 100%),
        {_capa};
    border-radius: 16px;
    padding: 84px 40px;
    margin: -8px 0 22px;
}}
.hero-banner h2 {{ color: #ffffff; margin: 0; font-size: 1.7rem; }}
.hero-banner p {{ color: #DFF3E7; margin: 6px 0 0; }}
</style>
<div class="hero-banner">
<h2>El dato oficial, al servicio de quien siembra</h2>
<p>Inteligencia analitica del agro vallecaucano &middot; UPRA &middot; EVA 2019-2025</p>
</div>""",
    unsafe_allow_html=True,
)

from ui.components.metrics_cards import render_kpi_row

_logo_path = _Path(__file__).parent.parent / "assets" / "img" / "logo.png"
_logo_html = ""
if _logo_path.exists():
    _logo_b64 = _b64.b64encode(_logo_path.read_bytes()).decode()
    _logo_html = f'<img src="data:image/png;base64,{_logo_b64}" width="42" style="vertical-align:middle; margin-right:.6rem;" />'

st.markdown(
    f"""<div class="eva-header" style="border-bottom:none; margin-bottom:.2rem;">
    <h1 style="display:flex; align-items:center; gap:.5rem;">
        {_logo_html}EVA Agrícola 2019-2025 - Valle del Cauca
    </h1>
    </div>""",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="color:var(--eva-muted); margin-top:0;">'
    'Dashboard analítico de producción agrícola basado en datos de la UPRA.</p>',
    unsafe_allow_html=True,
)

render_kpi_row([
    {"label": "Municipios", "value": "42", "icon": "\U0001F4CD"},
    {"label": "Cultivos", "value": "78", "icon": "\U0001F33F"},
    {"label": "Años de datos", "value": "7", "icon": "\U0001F4C5"},
], cols=3)

st.markdown("---")

col1, col2, col3 = st.columns(3)
_nav_card(col1, "ui/pages/1_Dashboard.py", "📊", "Dashboard", "Vista general con KPIs", min_rol=0)
_nav_card(col2, "ui/pages/2_Descriptivo.py", "📈", "Descriptivo", "12 análisis estadísticos", min_rol=1)
_nav_card(col3, "ui/pages/3_Diagnostico.py", "🔬", "Diagnostico", "5 análisis causales", min_rol=1)

st.markdown("---")
col4, col5, col6 = st.columns(3)
_nav_card(col4, "ui/pages/4_Predictivo.py", "🤖", "Predictivo", "Modelos ML y proyecciones", min_rol=1)
_nav_card(col5, "ui/pages/5_Auditoria.py", "🔍", "Auditoria", "Calidad de datos", min_rol=2)
_nav_card(col6, "ui/pages/6_Configuracion.py", "⚙️", "Configuracion", "Descarga y parámetros", min_rol=2)

st.markdown("---")
st.info("\U0001F4A1 **Navega usando la barra lateral** para acceder a cada pagina.")

st.markdown('<div class="eva-footer">EVA Valle v3.0 | UPRA | Arquitectura Hexagonal Modular</div>',
    unsafe_allow_html=True)
