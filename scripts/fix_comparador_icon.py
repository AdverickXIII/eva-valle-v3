"""Corrige set_page_config: icon -> page_icon."""
from pathlib import Path

p = Path("ui/pages/11_Comparador.py")
c = p.read_text(encoding="utf-8")
if ', icon="' in c:
    c = c.replace(', icon="', ', page_icon="', 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Corregido: page_icon")
else:
    print("[INFO] Ya estaba correcto")