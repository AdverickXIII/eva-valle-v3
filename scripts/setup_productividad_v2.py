"""Agrega seccion de productividad economica COP/ha a la pagina Valor Economico."""
from pathlib import Path

pag = Path("ui/pages/23_Valor_Economico.py")
p = pag.read_text(encoding="utf-8")

if "Productividad economica" in p:
    print("[AVISO] la seccion ya existe; nada que hacer")
else:
    seccion = '''

st.markdown("---")
st.markdown("### Productividad economica (COP/ha/ano)")
st.caption("Valor generado por hectarea cosechada. Mide eficiencia productiva, no valor del suelo.")

prod = productividad_ha(anio, sin_cana)
if not prod.empty:
    top_prod = prod.index[0]
    v_top = prod.loc[top_prod, "cop_ha"]
    st.metric(f"Mayor productividad {anio}", top_prod, f"{v_top / 1e6:.1f} M COP/ha")

    c1, c2 = st.columns([3, 2])
    with c1:
        tp = prod.head(15).copy()
        tp["M_COP_ha"] = (tp.cop_ha / 1e6).round(2)
        tp["area_ha"] = tp.area.round(0)
        tp["M_COP_total"] = (tp.valor / 1e6).round(0)
        st.table(tp[["M_COP_ha", "area_ha", "M_COP_total"]])
    with c2:
        import plotly.graph_objects as go
        fig = go.Figure(go.Bar(
            x=(prod.head(15).cop_ha / 1e6).round(2),
            y=prod.head(15).index,
            orientation="h",
            marker_color="#C98A2B"))
        fig.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    st.caption("Fuente: PIB agro (precios oficiales UPRA 2025) / area cosechada EVA 2025.")
'''
    p += seccion
    pag.write_text(p, encoding="utf-8")
    print("[OK] seccion de productividad agregada a 23_Valor_Economico.py")

print("\nVerifica local: reinicia Streamlit y entra a Valor Economico")