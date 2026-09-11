"""AUD-UI-014: cards de navegacion clickeables con filtrado por rol.
- style.css: agrega reglas .eva-nav-card
- 0_Home.py: reemplaza cards estaticas por st.page_link() con filtro min_rol
Fail-safe: pre-chequeos, backups, py_compile, rollback, auditoria JSONL.
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HOME = RAIZ / "ui" / "pages" / "0_Home.py"
CSS = RAIZ / "ui" / "assets" / "css" / "style.css"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

NUEVO_CSS = '''/* ---------- Home: cards de navegación clicables (Paso 12/13) ---------- */
.eva-nav-card [data-testid="stPageLink"] {
    background: var(--eva-card);
    border: 1px solid var(--eva-border);
    border-radius: var(--eva-radius);
    padding: 1.1rem 1.3rem;
    box-shadow: var(--eva-shadow);
    transition: box-shadow .15s ease, transform .15s ease;
    display: block;
    text-decoration: none;
}
.eva-nav-card [data-testid="stPageLink"]:hover {
    box-shadow: var(--eva-shadow-hover);
    transform: translateY(-1px);
    border-color: var(--eva-primary);
}
.eva-nav-card .nav-card-icon { font-size: 1.6rem; margin-bottom: .35rem; line-height: 1; }
.eva-nav-card .nav-card-label {
    color: var(--eva-muted); font-size: .8rem; text-transform: uppercase;
    letter-spacing: .05em; font-weight: 600;
}
.eva-nav-card .nav-card-desc { color: var(--eva-text); font-size: 1rem; font-weight: 500; margin-top: .1rem; }
'''

FUNCION_NAV_CARD = '''
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
            label=f"**{label.upper()}**  \\n{desc}",
            icon=icon,
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


'''

NUEVO_BLOQUE_CARDS = '''col1, col2, col3 = st.columns(3)
_nav_card(col1, "ui/pages/1_Dashboard.py", "📊", "Dashboard", "Vista general con KPIs", min_rol=0)
_nav_card(col2, "ui/pages/2_Descriptivo.py", "📈", "Descriptivo", "12 análisis estadísticos", min_rol=1)
_nav_card(col3, "ui/pages/3_Diagnostico.py", "🔬", "Diagnostico", "5 análisis causales", min_rol=1)

st.markdown("---")
col4, col5, col6 = st.columns(3)
_nav_card(col4, "ui/pages/4_Predictivo.py", "🤖", "Predictivo", "Modelos ML y proyecciones", min_rol=1)
_nav_card(col5, "ui/pages/5_Auditoria.py", "🔍", "Auditoria", "Calidad de datos", min_rol=2)
_nav_card(col6, "ui/pages/6_Configuracion.py", "⚙️", "Configuracion", "Descarga y parámetros", min_rol=2)

st.markdown("---")
'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    # ---------- 1. style.css: agregar reglas .eva-nav-card ----------
    css = CSS.read_text(encoding="utf-8")
    if ".eva-nav-card" not in css:
        css_nuevo = css.rstrip() + "\n\n" + NUEVO_CSS
        bak_css = CSS.with_suffix(".css.bak")
        shutil.copy2(CSS, bak_css)
        CSS.write_text(css_nuevo, encoding="utf-8")
        print(f"[OK] style.css: reglas .eva-nav-card agregadas | backup: {bak_css.name}")
    else:
        print("[INFO] style.css ya tiene .eva-nav-card")

    # ---------- 2. 0_Home.py: agregar funcion + reemplazar cards ----------
    lineas = HOME.read_text(encoding="utf-8").splitlines(keepends=True)

    # 2a. Insertar funcion _nav_card si no existe
    if "_nav_card" not in "".join(lineas):
        # Buscar la primera linea que no sea import ni comentario (donde empieza el codigo)
        idx_codigo = next((i for i, l in enumerate(lineas) 
                          if l.strip() and not l.strip().startswith(('#', 'import', 'from', '"""', "'''"))), 0)
        lineas[idx_codigo:idx_codigo] = FUNCION_NAV_CARD.splitlines(keepends=True)
        print(f"[OK] funcion _nav_card insertada en linea {idx_codigo+1}")

    # 2b. Reemplazar bloque de cards (lineas 49-84 del original, ahora desplazadas)
    texto = "".join(lineas)
    
    # Buscar el patron: desde "col1, col2, col3 = st.columns(3)" hasta el segundo "st.markdown(\"---\")"
    # que precede a "st.info"
    patron = re.compile(
        r'col1, col2, col3 = st\.columns\(3\).*?st\.markdown\("---"\)\n(?=st\.info)',
        re.S
    )
    match = patron.search(texto)
    if not match:
        print("[ERROR] bloque de cards no coincide con el patron esperado")
        return 1
    
    texto_nuevo = texto[:match.start()] + NUEVO_BLOQUE_CARDS + texto[match.end():]
    
    # Verificaciones
    if texto_nuevo.count("_nav_card(") < 6:
        print("[ERROR] no se insertaron las 6 llamadas a _nav_card")
        return 1
    if "eva-nav-card" not in texto_nuevo:
        print("[ERROR] clase eva-nav-card no quedo en el archivo")
        return 1
    for token in ("min_rol=0", "min_rol=1", "min_rol=2"):
        if token not in texto_nuevo:
            print(f"[ERROR] falta {token} en las llamadas")
            return 1

    bak_home = HOME.with_suffix(".py.bak")
    shutil.copy2(HOME, bak_home)
    HOME.write_text(texto_nuevo, encoding="utf-8")
    print(f"[OK] 0_Home.py: cards reemplazadas con filtrado por rol | backup: {bak_home.name}")

    # py_compile + rollback
    r = subprocess.run([sys.executable, "-m", "py_compile", str(HOME)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak_home, HOME)
        audit("AUD-UI-014", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-014", "OK", "Home con cards clickeables y filtrado por rol")
    print("[OK] AUD-UI-014 aplicado y compilado")
    print("Siguiente: streamlit run app.py -> verificar cards con diferentes roles")
    return 0


if __name__ == "__main__":
    sys.exit(main())