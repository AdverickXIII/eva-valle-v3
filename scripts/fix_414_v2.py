"""Fix robusto 4.14: reemplazo linea por linea en 2_Descriptivo.py."""
from pathlib import Path

p = Path("ui/pages/2_Descriptivo.py")
c = p.read_text(encoding="utf-8")
cambios = 0

lines = c.splitlines(keepends=True)
out = []
i = 0
while i < len(lines):
    l = lines[i]
    # 1) scatter -> barras agrupadas
    if "plot_cuadrantes(df_dec)" in l:
        l = l.replace("plot_cuadrantes(df_dec)", "plot_motor_barras(df_dec)")
        cambios += 1
    # 2) tabla ordenada por volumen (no por CAGR)
    if 'sort_values("cagr_prod", ascending=False)' in l:
        l = l.replace('sort_values("cagr_prod", ascending=False)',
                      'sort_values("prod_total", ascending=False)')
        cambios += 1
    # 3) caption viejo -> caption nuevo (consume sus lineas de continuacion)
    if 'st.caption("Arriba-derecha' in l:
        out.append('        st.caption("Por cultivo: si la barra **azul** (rendimiento) supera a la "\n')
        out.append('                   "**naranja** (area), el crecimiento es intensivo; si domina la "\n')
        out.append('                   "naranja, es extensivo.")\n')
        cambios += 1
        i += 1
        while i < len(lines) and lines[i].strip().startswith('"'):
            i += 1
        continue
    out.append(l)
    i += 1

c2 = "".join(out)

# 4) import (solo si falta)
if "plot_motor_barras" not in c2:
    antes = c2
    c2 = c2.replace(
        "from ui.charts.growth_decomp import descomponer_crecimiento, plot_cuadrantes",
        "from ui.charts.growth_decomp import descomponer_crecimiento, plot_cuadrantes, plot_motor_barras")
    c2 = c2.replace(
        "from ui.charts.growth_decomp import (descomponer_crecimiento, plot_cuadrantes,",
        "from ui.charts.growth_decomp import (descomponer_crecimiento, plot_cuadrantes, plot_motor_barras,")
    if c2 != antes:
        cambios += 1

p.write_text(c2, encoding="utf-8")
print(f"[OK] {cambios} cambios aplicados a ui/pages/2_Descriptivo.py")
print("Sigue: Ctrl+C en Streamlit -> streamlit run app.py -> Ctrl+F5 en el navegador")