"""Conecta el mapeo oficial de zonas (Ord. 513) al Recomendador IRS."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))

import core.analytics.zonas as Z

cands = [n for n in dir(Z) if not n.startswith("_")]
print("Atributos de core.analytics.zonas:", cands)

mapping = None
for n in cands:
    obj = getattr(Z, n)
    if isinstance(obj, dict) and obj and all(
        isinstance(v, (list, tuple, set)) and all(isinstance(x, str) for x in v)
        for v in obj.values()):
        mapping = obj
        print(f"[OK] Mapeo oficial encontrado: {n} ({len(obj)} zonas)")
        break

if not mapping:
    print("[AVISO] No se encontro el dict zona->municipios en zonas.py.")
    print("         Ejecuta:  findstr /N /I \"Norte\" core\\analytics\\zonas.py ui\\pages\\19_Zonas.py")
    print("         y pegame la salida para ubicar el mapeo.")
    raise SystemExit(1)

p = Path("core/analytics/irs.py")
c = p.read_text(encoding="utf-8")

# 1) Loader del mapeo al inicio del modulo
if "_cargar_zonas" not in c:
    loader = '''def _cargar_zonas():
    try:
        import core.analytics.zonas as _Z
    except Exception:
        return {}
    for _n in dir(_Z):
        _o = getattr(_Z, _n)
        if isinstance(_o, dict) and _o and all(
            isinstance(v, (list, tuple, set)) and all(isinstance(x, str) for x in v)
            for v in _o.values()):
            return {m: z for z, ms in _o.items() for m in ms}
    return {}


_ZONA_MUNICIPIO = _cargar_zonas()

PESOS = {'''
    c = c.replace("PESOS = {", loader, 1)
    print("[OK] Loader de zonas agregado a irs.py")

# 2) Usar el mapeo cuando el CSV no trae la columna
old = '''    if "zona" in df.columns:
        zona = df.drop_duplicates("municipio").set_index("municipio")["zona"]
    else:
        zona = pd.Series(dtype=str)'''
new = '''    if "zona" in df.columns:
        zona = df.drop_duplicates("municipio").set_index("municipio")["zona"]
    else:
        zona = pd.Series(_ZONA_MUNICIPIO)'''
if old in c:
    c = c.replace(old, new, 1)
    print("[OK] IRS usa el mapeo oficial de zonas")

p.write_text(c, encoding="utf-8")
print(f"[OK] Mapeo cargado: {len(mapping)} zonas, "
      f"{sum(len(v) for v in mapping.values())} municipios")