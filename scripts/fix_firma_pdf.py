"""Compatibilidad: build_ficha_pdf acepta figs=None para que Cultivos no falle."""
from pathlib import Path

p = Path("core/reports/ficha_pdf.py")
c = p.read_text(encoding="utf-8")
old = "def build_ficha_pdf(cultivo, ambito, agg, diag) -> bytes:"
new = "def build_ficha_pdf(cultivo, ambito, agg, diag, figs=None) -> bytes:"
if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] build_ficha_pdf ahora acepta figs=None (Cultivos quedara sin error)")
else:
    print("[INFO] La firma ya era compatible")