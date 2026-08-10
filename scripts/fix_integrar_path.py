"""Agrega sys.path a integrar_eva_2025.py para que encuentre config."""
from pathlib import Path

p = Path("scripts/integrar_eva_2025.py")
c = p.read_text(encoding="utf-8")

old = "from config.settings import settings"
new = ("import sys\n"
       "from pathlib import Path as _ROOT\n"
       "sys.path.insert(0, str(_ROOT(__file__).resolve().parent.parent))\n"
       "\n"
       "from config.settings import settings")

if old in c and "sys.path.insert" not in c:
    c = c.replace(old, new, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] sys.path agregado a integrar_eva_2025.py")
else:
    print("[INFO] ya tenia sys.path o no encontro la linea")