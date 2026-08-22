"""Reorganiza el sidebar por nivel analitico (sin cambiar permisos por rol)."""
from pathlib import Path

p = Path("app.py")
c = p.read_text(encoding="utf-8")

marker = "# --- Navegacion por rol"
i = c.find(marker)
if i == -1:
    print("[ERROR] No encontre el bloque de navegacion en app.py")
    raise SystemExit(1)

NEW_TAIL = '''# --- Navegacion por nivel analitico (mismo control de roles) ----------
# Orden del sidebar: Panorama -> 1 Descriptivo -> 2 Diagnostico ->
# 3 Predictivo -> 4 Prescriptivo -> Entregables -> Gobernanza.
def _build_navigation(role: str):
    nivel = {"user": 0, "analista": 1, "admin": 2}[role]
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
'''

c = c[:i] + NEW_TAIL
p.write_text(c, encoding="utf-8")
print("[OK] app.py reorganizado por nivel analitico (roles intactos)")
print("Reinicia Streamlit y revisa el sidebar")