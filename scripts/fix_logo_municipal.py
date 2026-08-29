"""Encadena el logo en generadores cuyo build() pisa onPage con onFirstPage/onLaterPages."""
import re
from pathlib import Path

parches = 0
for f in sorted(Path("core/reports").glob("*.py")):
    c = f.read_text(encoding="utf-8")
    m = re.search(r"onFirstPage\s*=\s*([A-Za-z_]\w*)", c)
    if not m:
        continue
    fn = m.group(1)
    d = re.search(r"def\s+%s\s*\(\s*([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)" % fn, c)
    if not d:
        print(f"[AVISO] {f.name}: no encontre def {fn}")
        continue
    a, b = d.group(1), d.group(2)
    if f"pagina_con_logo({a}, {b})" in c:
        print(f"[INFO] {f.name}: ya estaba encadenado")
        continue
    eol = c.find("\n", d.start())
    idx = c.rfind(":", d.start(), eol) + 1
    c = c[:idx] + f"\n    pagina_con_logo({a}, {b})" + c[idx:]
    if "from core.reports.branding import" not in c:
        i = c.find("from reportlab")
        if i != -1:
            c = c[:i] + "from core.reports.branding import pagina_con_logo\n" + c[i:]
    f.write_text(c, encoding="utf-8")
    parches += 1
    print(f"[OK] {f.name}: logo encadenado dentro de {fn}")

if not parches:
    print("[!] Ningun archivo con onFirstPage; pega la salida de:")
    print('    findstr /N /I "build(" core\\reports\\pdf_report.py')