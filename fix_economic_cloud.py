"""Repara economic.py: comprensiones a prueba de formato + productividad_ha."""
from pathlib import Path

p = Path("core/analytics/economic.py")
c = p.read_text(encoding="utf-8")

old1 = 'PRECIOS_REF = {c: v["cop_t"] for c, v in PRECIO_OFICIAL_V1.items()}'
new1 = ('PRECIOS_REF = {c: (v["cop_t"] if isinstance(v, dict) else v) '
        'for c, v in PRECIO_OFICIAL_V1.items()}')
if old1 in c:
    c = c.replace(old1, new1)
    print("[OK] PRECIOS_REF reparado")

old2 = 'FUENTES_PRECIO = {c: v["fuente"] for c, v in PRECIO_OFICIAL_V1.items()}'
new2 = ('FUENTES_PRECIO = {c: (v.get("fuente", "UPRA 2025") if isinstance(v, dict) '
        'else "UPRA 2025") for c, v in PRECIO_OFICIAL_V1.items()}')
if old2 in c:
    c = c.replace(old2, new2)
    print("[OK] FUENTES_PRECIO reparado")

if "def productividad_ha" not in c:
    c += '''

def productividad_ha(anio=2025, excluye_cana=False):
    """COP/ha/ano: PIB agro municipal / area cosechada total."""
    import unicodedata

    def _es_cana(nombre):
        return "cana" in "".join(ch for ch in unicodedata.normalize("NFD", str(nombre).lower())
                                 if unicodedata.category(ch) != "Mn")
    df = load_df()
    d = valorizar(df)
    d = d[d.ano == anio]
    if excluye_cana:
        d = d[~d.cultivo.map(_es_cana)]
    g = d.groupby("municipio").agg(valor=("valor", "sum"),
                                   area=("area_cosechada_ha", "sum"))
    g = g[(g.valor > 0) & (g.area > 10)]
    g["cop_ha"] = g.valor / g.area
    return g.sort_values("cop_ha", ascending=False)
'''
    print("[OK] productividad_ha agregada")

p.write_text(c, encoding="utf-8")

# Verificacion local inmediata (misma importacion que usa la pagina 23)
import subprocess
r = subprocess.run(
    ["python", "-c",
     "from core.analytics.economic import serie_pib, tabla_rank, productividad_ha, PRECIOS_REF; "
     "print('IMPORT OK | cultivos con precio:', len(PRECIOS_REF))"],
    capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())