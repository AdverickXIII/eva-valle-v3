"""Corrige el parametro de set_page_config en la pagina del Asistente."""
from pathlib import Path

p = Path("ui/pages/21_Asistente.py")
c = p.read_text(encoding="utf-8")
if ", icon=" in c:
    p.write_text(c.replace(", icon=", ", page_icon=", 1), encoding="utf-8")
    print("[OK] icon -> page_icon corregido")
else:
    print("[INFO] Ya estaba correcto")