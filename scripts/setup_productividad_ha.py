"""Agrega modulo de productividad economica $/ha a la pagina Valor Economico."""
from pathlib import Path

# 1) Agregar funcion de productividad al modulo economic
econ = Path("core/analytics/economic.py")
c = econ.read_text(encoding="utf-8")

if "def productividad_ha" not in c:
    nueva_func = '''

def productividad_ha(anio=2025, excluye_cana=False):
    """COP/ha/año: PIB agro municipal / area cosechada total."""
    import unicodedata
    def _es_cana(nombre):
        return "cana" in "".join(c for c in unicodedata.normalize("NFD", str(nombre).lower())
                                  if unicodedata.category(c) != "Mn")
    df = load_df()
    d = valorizar(df)
    d = d[d.ano == anio]
    if excluye_cana:
        d = d[~d.cultivo.map(_es_cana)]
    g = d.groupby("municipio").agg(valor=("valor", "sum"), area=("area_cosechada_ha", "sum"))
    g = g[(g.valor > 0) & (g.area > 10)]
    g["cop_ha"] = g.valor / g.area
    return g.sort_values("cop_ha", ascending=False)
'''
    c += nueva_func
    econ.write_text(c, encoding="utf-8")
    print("[OK] Funcion productividad_ha agregada a economic.py")

# 2) Actualizar pagina Valor Economico para incluir seccion de productividad
pag = Path("ui/pages/23_Valor_Economico.py")
p = pag.read_text(encoding="utf-8")

# Actualizar import
if "productividad_ha" not in p:
    p = p.replace(
        "from core.analytics.economic import serie_pib, tabla_rank",
        "from core.analytics.economic import serie_pib, tabla_rank, productividad_ha"
    )

# Agregar seccion de productividad antes del cierre
if "Productividad economica" not in p:
    seccion = '''

st.markdown("---")
st.markdown("### Productividad economica (COP/ha/ano)")
st.caption("Valor generado por hectarea cosechada. Mide eficiencia productiva, no valor del suelo.")

prod = productividad_ha(anio, sin_cana)
if not prod.empty:
    top_prod = prod.index[0]
    v_top = prod.loc[top_prod, "cop_ha"]
    st.metric(f"Mayor productividad {anio}", top_prod, f"{v_top / 1e6:.1f} M COP/ha")
    
    st.markdown("#### Top 15 municipios por productividad (COP/ha)")
    c1, c2 = st.columns([3, 2])
    with c1:
        tp = prod.head(15).copy()
        tp["M_COP_ha"] = (tp.cop_ha / 1e6).round(2)
        tp["area_ha"] = tp.area.round(0)
        tp["M_COP_total"] = (tp.valor / 1e6).round(0)
        st.table(tp[["M_COP_ha", "area_ha", "M_COP_total"]])
    with c2:
        fig = go.Figure(go.Bar(
            x=(prod.head(15).cop_ha / 1e6).round(2),
            y=prod.head(15).index,
            orientation="h",
            marker_color="#C98A2B"
        ))
        fig.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    
    # Cruce: productividad vs PIB total
    st.markdown("#### Analisis cruzado: PIB total vs Productividad $/ha")
    st.caption("Municipios 'ricos por volumen' vs 'eficientes por hectarea'")
    merged = tabla_rank(anio, sin_cana).head(20).merge(
        prod[["cop_ha"]], left_index=True, right_index=True, how="left"
    )
    merged["cop_ha"] = (merged.cop_ha / 1e6).round(2)
    merged["M_COP"] = (merged.valor / 1e6).round(0)
    merged["area_ha"] = merged.ton.round(0) / 12  # aproximacion
    st.table(merged[["M_COP", "cop_ha", "area_ha", "rank_pesos"]])
'''
    # Insertar antes del ultimo st.info o al final
    last_info_idx = p.rfind("st.info(")
    if last_info_idx != -1:
        p = p[:last_info_idx] + seccion + "\n" + p[last_info_idx:]
    else:
        p += seccion
    
    pag.write_text(p, encoding="utf-8")
    print("[OK] Seccion de productividad agregada a 23_Valor_Economico.py")

print("\nReinicia Streamlit y entra a 💰 Valor Economico")
print("Nueva seccion: Productividad economica COP/ha/ano")