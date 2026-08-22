"""Logo institucional en TODOS los PDF + favicon + sidebar."""
import re
from pathlib import Path

# ---------- 1) Modulo de marca ----------
BRAND = '''"""Marca institucional: logo en cada pagina de todos los PDF."""
from pathlib import Path

from reportlab.lib.units import cm

LOGO = Path(__file__).resolve().parents[2] / "ui" / "assets" / "img" / "logo.png"


def pagina_con_logo(canvas, doc):
    if not LOGO.exists():
        return
    canvas.saveState()
    canvas.drawImage(str(LOGO), 18.4 * cm, 24.4 * cm,
                     width=2.2 * cm, height=2.2 * cm,
                     preserveAspectRatio=True, mask="auto")
    canvas.restoreState()
'''
Path("core/reports/branding.py").write_text(BRAND, encoding="utf-8")
print("[OK] core/reports/branding.py creado")

# ---------- 2) Inyectar onPage en cada generador de PDF ----------
pat = re.compile(r"SimpleDocTemplate\(\s*([A-Za-z_]\w*)")

def add_import(c: str) -> str:
    linea = "from core.reports.branding import pagina_con_logo\n"
    if "from core.reports.branding" in c:
        return c
    idx = c.find("from reportlab")
    if idx != -1:
        return c[:idx] + linea + c[idx:]
    idx = c.find("import ")
    if idx != -1:
        eol = c.find("\n", idx)
        return c[:eol + 1] + linea + c[eol + 1:]
    return linea + c

n_pdf = 0
for f in list(Path("core/reports").glob("*.py")) + list(Path("ui/pages").glob("*.py")):
    c = f.read_text(encoding="utf-8")
    if "SimpleDocTemplate(" in c and "onPage=" not in c:
        c2, n = pat.subn(lambda m: f"SimpleDocTemplate({m.group(1)}, onPage=pagina_con_logo", c)
        if n:
            f.write_text(add_import(c2), encoding="utf-8")
            n_pdf += 1
            print(f"[OK] {f.name}: logo en cada pagina del PDF")
print(f"    -> {n_pdf} generadores de PDF marcados")

# ---------- 3) Favicon (pestana del navegador) ----------
app = Path("app.py")
c = app.read_text(encoding="utf-8")
old_icon = 'page_icon="\\U0001F33E",'
new_icon = 'page_icon=str(Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"),'
if old_icon in c:
    c = c.replace(old_icon, new_icon, 1)
    print("[OK] Favicon = logo")

# ---------- 4) Sidebar con logo ----------
old_sb = '    st.title("\\U0001F33E EVA Valle")'
new_sb = ('    st.image(str(Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"), width=84)\n'
          '    st.title("EVA Valle")')
if old_sb in c:
    c = c.replace(old_sb, new_sb, 1)
    print("[OK] Sidebar con logo sobre el titulo")

app.write_text(c, encoding="utf-8")
print("\nReinicia Streamlit y descarga cualquier PDF para verificar")