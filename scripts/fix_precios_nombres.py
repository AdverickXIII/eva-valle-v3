"""Sincroniza nombres oficiales de cultivos (Caña/Banano) en economic.py."""
from pathlib import Path

p = Path("core/analytics/economic.py")
c = p.read_text(encoding="utf-8")
old = '    "Caña de azúcar": 160000, "Plátano": 1200000, "Naranja": 700000,'
new = ('    "Caña": 160000, "Caña de azúcar": 160000,\n'
       '    "Plátano": 1200000, "Banano": 1200000, "Naranja": 700000,')
if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] economic.py sincronizado con nombres oficiales")
else:
    print("[AVISO] patron no encontrado")