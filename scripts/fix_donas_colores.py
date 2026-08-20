"""Parche cosmético 4.6: colores consistentes por grupo + etiquetas <1% al hover."""
from pathlib import Path

p = Path("ui/charts/concentration.py")
c = p.read_text(encoding="utf-8")

if "_fix_colores_y_etiquetas(fig)" in c:
    print("[INFO] El parche ya estaba aplicado.")
    raise SystemExit(0)

BLOQUE = '''_PALETA = ["#2E8B57", "#1F77B4", "#FF7F0E", "#9467BD", "#D62728",
           "#17BECF", "#BCBD22", "#8C564B", "#E377C2", "#7F7F7F"]
_COLOR_FIJO = {"Cana de azucar": "#2E8B57", "Frutales": "#1F77B4",
               "Hortalizas": "#FF7F0E", "Cereales": "#9467BD"}


def _fix_colores_y_etiquetas(fig):
    """Colores consistentes por etiqueta entre donas; etiquetas <1% solo en hover."""
    usados = {}
    n = 0
    for tr in fig.data:
        if tr.type != "pie":
            continue
        vals = [float(v) for v in tr.values]
        tot = sum(vals) or 1.0
        cols, pos = [], []
        for lab, v in zip(tr.labels, vals):
            key = str(lab)
            if key not in usados:
                usados[key] = _COLOR_FIJO.get(key, _PALETA[n % len(_PALETA)])
                n += 1
            cols.append(usados[key])
            share = v / tot * 100
            pos.append("none" if share < 1 else ("inside" if share >= 10 else "outside"))
        tr.marker.colors = cols
        tr.textposition = pos
    return fig


'''

# 1) Insertar helpers a nivel de modulo (antes de la primera funcion de donas)
i_def = c.find("def plot_ex_cana_donuts")
if i_def == -1:
    print("[ERROR] No encontre plot_ex_cana_donuts")
    raise SystemExit(1)
c = c[:i_def] + BLOQUE + c[i_def:]

# 2) Llamar el fix justo antes del apply_theme del ex-cana
marcador = 'fig = apply_theme(fig, "Analisis Ex-Cana'
if marcador not in c:
    print("[ERROR] No encontre la linea de apply_theme del ex-cana")
    raise SystemExit(1)
c = c.replace(marcador,
              "fig = _fix_colores_y_etiquetas(fig)\n    " + marcador, 1)

p.write_text(c, encoding="utf-8")
print("[OK] Parche aplicado a ui/charts/concentration.py")
print("Reinicia Streamlit y revisa la seccion 4.6")