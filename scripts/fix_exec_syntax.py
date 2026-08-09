"""Corrige parentesis en executive_report.py (secciones 6 y 7)."""
from pathlib import Path

p = Path("core/reports/executive_report.py")
c = p.read_text(encoding="utf-8")

pares = [
    ('st_["Heading2")] + h +', 'st_["Heading2"])] + h +'),
    ('st_["Heading2"]) + r +', 'st_["Heading2"])] + r +'),
    ('cm)]))', 'cm)])'),
]
for old, new in pares:
    c = c.replace(old, new)

p.write_text(c, encoding="utf-8")
print("[OK] executive_report.py corregido")