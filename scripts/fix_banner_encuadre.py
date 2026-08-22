"""Baja el encuadre del hero para mostrar los rostros completos."""
from pathlib import Path

p = Path("ui/pages/0_Home.py")
c = p.read_text(encoding="utf-8")
old = "center 30% / cover no-repeat"
new = "center 18% / cover no-repeat"
if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] Encuadre del banner: 30% -> 18% (imagen mas baja, caras visibles)")
else:
    print("[INFO] Patron no encontrado; revisa 0_Home.py")