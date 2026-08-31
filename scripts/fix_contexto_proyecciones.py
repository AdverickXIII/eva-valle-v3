"""Corrige CONTEXTO.md: las proyecciones son nuestras, no oficiales."""
from pathlib import Path

p = Path("CONTEXTO.md")
c = p.read_text(encoding="utf-8")

old = "  - Hallazgo: PM5A supera PM3A en total municipal Alcala (MAPE 3.48% vs 7.62%)"
new = "  - Hallazgo: PM5A supera PM3A (nuestro baseline inicial) en total municipal Alcala\n    (MAPE 3.48% vs 7.62%). Nota: las proyecciones del PDF son nuestras (forecast.py), no oficiales del Estado"

c = c.replace(old, new)
p.write_text(c, encoding="utf-8")
print("[OK] CONTEXTO.md corregido: proyecciones son nuestras")