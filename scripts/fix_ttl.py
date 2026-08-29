"""Ajusta el cache del Recomendador: 1 hora (rapido en sesion, fresco en deploy)."""
from pathlib import Path

p = Path("ui/pages/22_Recomendador.py")
c = p.read_text(encoding="utf-8")
if "ttl=1)" in c:
    p.write_text(c.replace("ttl=1)", "ttl=3600)", 1), encoding="utf-8")
    print("[OK] ttl=3600 aplicado")
else:
    print("[INFO] nada que ajustar")