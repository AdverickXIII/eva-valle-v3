"""Cultivos v3: orden Top20 con/sin cana + tabla al final + barras agrupadas en vez de scatter."""
from pathlib import Path

# ---------- 1) growth_decomp: agregar plot_motor_barras ----------
pg = Path("ui/charts/growth_decomp.py")
cg = pg.read_text(encoding="utf-8")
if "def plot_motor_barras" not in cg:
    cg += '''

def plot_motor_barras(df_dec, top_n: int = 12):
    """Barras agrupadas: CAGR produccion vs area vs rendimiento (Top por volumen)."""
    import plotly.graph_objects as go
    d = df_dec.sort_values("prod_total", ascending=False).head(top_n)
    d = d.sort_values("cagr_prod", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="CAGR produccion", x=d["cultivo"], y=d["cagr_prod"],
                         marker_color="#2E8B57"))
    fig.add_trace(go.Bar(name="CAGR area sembrada", x=d["cultivo"], y=d["cagr_area"],
                         marker_color="#F4A261"))
    fig.add_trace(go.Bar(name="CAGR rendimiento", x=d["cultivo"], y=d["cagr_rend"],
                         marker_color="#5FA8DC"))
    fig.update_layout(barmode="group", height=520, xaxis_tickangle=-45,
                      yaxis_title="CAGR (%)", legend=dict(orientation="h", y=-0.22),
                      margin=dict(t=40, b=10))
    return apply_theme(fig, "Motor del crecimiento: produccion vs area vs rendimiento")
'''
    pg.write_text(cg, encoding="utf-8")
    print("[OK] plot_motor_barras agregado a growth_decomp.py")

# ---------- 2) Pagina: reordenar Tab 1 + reemplazar scatter ----------
p = Path("ui/pages/7_Cultivos.py")
c = p.read_text(encoding="utf-8")

# 2a) import
c = c.replace("from ui.charts.growth_decomp import descomponer_crecimiento, plot_cuadrantes",
              "from ui.charts.growth_decomp import (descomponer_crecimiento, plot_cuadrantes,\n"
              "                                      plot_motor_barras)")

# 2b) quitar la tabla de su posicion actual (queda solo el grafico con cana)
old_tabla = """        st.plotly_chart(fig_rank, use_container_width=True)
        st.dataframe(top20.rename(columns={"cultivo": "Cultivo",
                                           "produccion_t": "Produccion (t)",
                                           "share_pct": "% del Dpto.",
                                           "acumulado_pct": "% Acumulado"}),
                     use_container_width=True, hide_index=True)"""
new_tabla = "        st.plotly_chart(fig_rank, use_container_width=True)"
if old_tabla in c:
    c = c.replace(old_tabla, new_tabla, 1)
    print("[OK] Tabla removida de en medio de los graficos")

# 2c) tabla al final, despues del grafico sin cana
old_cap = '''        st.caption("Sin la caña, la escala revela la economia real: plátano, piña, "
                   "maíz y frutales pasan a ser visibles y comparables.")'''
new_cap = old_cap + '''

        st.markdown("#### 📋 Detalle de produccion y participacion (con caña)")
        st.dataframe(top20.rename(columns={"cultivo": "Cultivo",
                                           "produccion_t": "Produccion (t)",
                                           "share_pct": "% del Dpto.",
                                           "acumulado_pct": "% Acumulado"}),
                     use_container_width=True, hide_index=True)'''
if old_cap in c:
    c = c.replace(old_cap, new_cap, 1)
    print("[OK] Tabla movida despues de los dos graficos")

# 2d) scatter -> barras agrupadas + tabla de clasificacion
old_scatter = """        # Cuadrantes area vs rendimiento
        st.markdown("#### 🎯 Motor del crecimiento (area vs rendimiento)")
        df_dec = descomponer_crecimiento(df_f)
        st.plotly_chart(plot_cuadrantes(df_dec), use_container_width=True)
        st.caption("Tamano de burbuja = volumen total. Arriba-derecha = virtuoso; "
                   "abajo-izquierda = colapso.")"""
new_scatter = """        # Motor del crecimiento: barras agrupadas (legibles sin manual)
        st.markdown("#### 🎯 Motor del crecimiento por cultivo (Top 12 por volumen)")
        df_dec = descomponer_crecimiento(df_f)
        st.plotly_chart(plot_motor_barras(df_dec), use_container_width=True)
        st.caption("Por cultivo: si la barra **azul** (rendimiento) supera a la "
                   "**naranja** (area), el crecimiento es intensivo; si domina la "
                   "naranja, es extensivo.")
        st.dataframe(df_dec.sort_values("prod_total", ascending=False).head(15)
                     [["cultivo", "cagr_prod", "cagr_area", "cagr_rend", "tipo", "prod_total"]],
                     use_container_width=True, hide_index=True)"""
if old_scatter in c:
    c = c.replace(old_scatter, new_scatter, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Scatter reemplazado por barras agrupadas + tabla de clasificacion")
else:
    p.write_text(c, encoding="utf-8")
    print("[AVISO] Bloque del scatter distinto; revisa manualmente")

print("Reinicia Streamlit y revisa Cultivos -> Panoramica")