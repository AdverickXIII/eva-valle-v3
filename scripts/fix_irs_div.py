"""Evita la colision con el metodo DataFrame.div usando corchetes."""
from pathlib import Path

p = Path("core/analytics/irs.py")
c = p.read_text(encoding="utf-8")
old = '+ PESOS["div"] * m.div) * 100'
new = '+ PESOS["div"] * m["div"]) * 100'
if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] m.div -> m['div']")
else:
    print("[AVISO] Patron no encontrado; revisa irs.py")