"""Encadena el logo en generadores de PDF que ya tenian onPage propio."""
import re
from pathlib import Path

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

cambios = 0
for f in list(Path("core/reports").glob("*.py")) + list(Path("ui/pages").glob("*.py")):
    c = f.read_text(encoding="utf-8")
    if "SimpleDocTemplate(" not in c or "onPage=pagina_con_logo" in c:
        continue

    m = re.search(r"onPage\s*=\s*([A-Za-z_]\w*)", c)
    if m and m.group(1) != "pagina_con_logo":
        # Ya tiene callback propio (pie de pagina): encadenar el logo dentro de el
        fn = m.group(1)
        d = re.search(r"def\s+%s\s*\(\s*([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)" % fn, c)
        if d:
            a, b = d.group(1), d.group(2)
            idx = c.find("):", d.start()) + 1
            c = c[:idx] + f"\n    pagina_con_logo({a}, {b})" + c[idx:]
            f.write_text(add_import(c), encoding="utf-8")
            cambios += 1
            print(f"[OK] {f.name}: logo encadenado al pie existente ({fn})")
    else:
        # Sin callback: agregar onPage directo
        pat = re.compile(r"SimpleDocTemplate\(\s*([A-Za-z_]\w*)")
        c2, n = pat.subn(lambda mm: f"SimpleDocTemplate({mm.group(1)}, onPage=pagina_con_logo", c)
        if n:
            f.write_text(add_import(c2), encoding="utf-8")
            cambios += 1
            print(f"[OK] {f.name}: onPage=pagina_con_logo agregado")

print(f"-> {cambios} archivos ajustados")
print("\n--- Generadores detectados en core/reports ---")
for f in Path("core/reports").glob("*.py"):
    c = f.read_text(encoding="utf-8")
    if "SimpleDocTemplate(" in c or "Canvas(" in c:
        print(f"  {f.name}: onPage={'si' if 'onPage' in c else 'no'}")