"""Banner +2 cm de altura (padding vertical 46 -> 84 px)."""
from pathlib import Path

p = Path("ui/pages/0_Home.py")
c = p.read_text(encoding="utf-8")
old = "padding: 46px 40px;"
new = "padding: 84px 40px;"
if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] Banner +2 cm de altura")
else:
    print("[INFO] Patron no encontrado; revisa 0_Home.py")