"""Login limpio: oculta sidebar residual + enlace Contactenos abajo-derecha."""
from pathlib import Path

p = Path("app.py")
c = p.read_text(encoding="utf-8")
cambios = 0

# 1) Constante de contacto institucional
if "CONTACTO_EMAIL" not in c:
    c = c.replace(
        "st.set_page_config(",
        "# Correo institucional de contacto (editar si cambia)\n"
        'CONTACTO_EMAIL = "contacto.eva@upra.gov.co"\n\n'
        "st.set_page_config(",
        1,
    )
    cambios += 1
    print("[OK] constante CONTACTO_EMAIL agregada")

# 2) Login sin sidebar + contacto fijo abajo-derecha
old_login = '''def render_login() -> None:
    """Pantalla de login centrada con rate limiting y validacion."""
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)'''
new_login = '''def render_login() -> None:
    """Pantalla de login centrada con rate limiting y validacion."""
    # Oculta el sidebar residual (la ultima navegacion queda congelada
    # en el frontend cuando este run no llama st.navigation)
    st.markdown(
        "<style>section[data-testid='stSidebar']{display:none;}"
        "[data-testid='stSidebarCollapsedControl']{display:none;}</style>",
        unsafe_allow_html=True,
    )
    # Contacto institucional discreto, solo en la pantalla de acceso
    st.markdown(
        "<div style='position:fixed; bottom:0.9rem; right:1.4rem; "
        "font-size:0.78rem; color:#718096; z-index:999;'>"
        "&#191;Problemas de acceso? "
        f"<a href='mailto:{CONTACTO_EMAIL}?subject=Acceso%20EVA%20Valle%20v3.0'>"
        "Cont&#225;ctenos</a> &nbsp;&middot;&nbsp; v3.0 &middot; UPRA</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)'''
if "stSidebar']{display:none" not in c:
    c = c.replace(old_login, new_login, 1)
    cambios += 1
    print("[OK] render_login: sidebar oculto + Contactenos abajo-derecha")

p.write_text(c, encoding="utf-8")
print(f"[OK] app.py actualizado ({cambios} cambios)")