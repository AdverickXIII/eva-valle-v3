"""Diagnostico: donde vive el mapeo zona->municipio y si coincide con el CSV."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))

import core.analytics.zonas as Z
import core.analytics.irs as I

print("--- 1) Que hay en irs.py ahora ---")
print("_ZONA_MUNICIPIO cargado:", len(getattr(I, "_ZONA_MUNICIPIO", {})), "municipios")

print("\n--- 2) Atributos de core/analytics/zonas.py ---")
for n in dir(Z):
    if not n.startswith("_"):
        print(f"  {n}: {type(getattr(Z, n)).__name__}")

munis_csv = set(I.load_df()["municipio"].dropna().unique())

print("\n--- 3) Buscando dicts zona->municipios y coincidencia con CSV ---")
encontrado = False
for n in dir(Z):
    o = getattr(Z, n)
    if isinstance(o, dict) and o and all(isinstance(v, (list, tuple, set)) for v in o.values()):
        flat = {m: z for z, ms in o.items() for m in ms}
        match = munis_csv & set(flat)
        encontrado = True
        print(f"  {n}: {len(o)} zonas / {len(flat)} municipios -> "
              f"coinciden {len(match)} de {len(munis_csv)}")
        print("  ejemplo mapping:", list(flat.items())[:4])
        print("  CSV sin zona:", sorted(munis_csv - set(flat))[:8])

if not encontrado:
    print("  [!] Ningun dict zona->municipios en zonas.py")
    print("      Ejecuta:  findstr /N /I \"Norte\" core\\analytics\\zonas.py ui\\pages\\19_Zonas.py")