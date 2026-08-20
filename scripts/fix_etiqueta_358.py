"""Mini-parche: etiquetas externas solo >= 5% (evita choque con el titulo)."""
from pathlib import Path

p = Path("ui/charts/concentration.py")
c = p.read_text(encoding="utf-8")
old = 'pos.append("none" if share < 1 else ("inside" if share >= 10 else "outside"))'
new = 'pos.append("none" if share < 5 else ("inside" if share >= 10 else "outside"))'
if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] Umbral de etiquetas externas subido a 5%")
else:
    print("[INFO] Linea no encontrada (puede ya estar ajustada)")