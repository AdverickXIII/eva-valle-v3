"""Reemplaza el scatter de 4.14 (Descriptivo) por barras agrupadas, igual que Cultivos."""
from pathlib import Path

p = Path("ui/pages/2_Descriptivo.py")
c = p.read_text(encoding="utf-8")

# 1) Import
old_imp = "from ui.charts.growth_decomp import descomponer_crecimiento, plot_cuadrantes"
new_imp = ("from ui.charts.growth_decomp import (descomponer_crecimiento, plot_cuadrantes,\n"
           "                                      plot_motor_barras)")
if old_imp in c:
    c = c.replace(old_imp, new_imp, 1)
    print("[OK] Import actualizado")

# 2) Scatter -> barras agrupadas + tabla ordenada por volumen
old_blk = """        st.plotly_chart(plot_cuadrantes(df_dec), use_container_width=True)
        st.dataframe(df_dec.sort_values("cagr_prod", ascending=False).head(25),
                     use_container_width=True, hide_index=True)
        st.caption("Arriba-derecha = expansion con tecnologia; derecha-abajo = extensivo; "
                   "arriba-izquierda = intensificacion; abajo-izquierda = colapso. "
                   "Tamano de burbuja = volumen total.")"""
new_blk = """        st.plotly_chart(plot_motor_barras(df_dec), use_container_width=True)
        st.dataframe(df_dec.sort_values("prod_total", ascending=False).head(25),
                     use_container_width=True, hide_index=True)
        st.caption("Por cultivo: si la barra **azul** (rendimiento) supera a la "
                   "**naranja** (area), el crecimiento es intensivo; si domina la "
                   "naranja, es extensivo.")"""
if old_blk in c:
    c = c.replace(old_blk, new_blk, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] 4.14 ahora con barras agrupadas + tabla por volumen")
else:
    p.write_text(c, encoding="utf-8")
    print("[AVISO] Bloque 4.14 distinto; revisa manualmente")

print("Reinicia Streamlit y luego PUSH para que el Cloud se actualice")