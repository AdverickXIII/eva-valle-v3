"""Ranking del Mapa: quita la columna duplicada 'valor' y agrega posicion, % y acumulado."""
from pathlib import Path

p = Path("ui/pages/8_Mapa.py")
c = p.read_text(encoding="utf-8")

old_rank = '''    # Ranking de apoyo
    st.subheader("\\U0001F3C6 Ranking de Municipios")
    rank = _valor_muni(df_map, metrica).sort_values("valor", ascending=False)
    st.dataframe(rank, use_container_width=True, height=350)
    render_download_button(rank, f"mapa_{metrica}.csv")'''

new_rank = '''    # Ranking de apoyo: metrica + posicion + peso + rendimiento
    st.subheader("\\U0001F3C6 Ranking de Municipios")
    rank = _valor_muni(df_map, metrica).sort_values("valor", ascending=False).reset_index(drop=True)
    rank.insert(0, "posicion", range(1, len(rank) + 1))
    total_val = float(rank["valor"].sum()) or 1.0
    rank["pct_del_total"] = (rank["valor"] / total_val * 100).round(2)
    rank["pct_acumulado"] = rank["pct_del_total"].cumsum().round(2)
    # Rendimiento medio del municipio (contexto complementario al volumen)
    rend_muni = (df_map.groupby("municipio")
                 .agg(prod=("produccion_t", "sum"), cos=("area_cosechada_ha", "sum"))
                 .reset_index())
    rend_muni["rendimiento_t_ha"] = (rend_muni["prod"] / rend_muni["cos"]
                                     .replace(0, 1)).replace([float("inf"), float("-inf")], 0).round(1)
    rank = rank.merge(rend_muni[["municipio", "rendimiento_t_ha"]], on="municipio", how="left")

    # Columnas legibles segun metrica
    label_metrica = {
        "produccion_t": "Produccion (t)",
        "area_sembrada_ha": "Area sembrada (ha)",
        "area_cosechada_ha": "Area cosechada (ha)",
        "rendimiento_t_ha": "Rendimiento (t/ha)",
    }.get(metrica, metrica)
    rank_show = rank.rename(columns={
        "posicion": "Puesto",
        "municipio": "Municipio",
        "valor": label_metrica,
        "pct_del_total": "% del total",
        "pct_acumulado": "% acumulado",
        "rendimiento_t_ha": "Rend. promedio (t/ha)",
    })[["Puesto", "Municipio", label_metrica, "% del total", "% acumulado", "Rend. promedio (t/ha)"]]

    st.dataframe(rank_show, use_container_width=True, height=400, hide_index=True)
    render_download_button(rank_show, f"mapa_{metrica}.csv")'''

if old_rank in c:
    c = c.replace(old_rank, new_rank, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Ranking con posicion, % del total, % acumulado y rendimiento promedio")
    print("Reinicia Streamlit y revisa Mapa -> Ranking")
else:
    print("[AVISO] Bloque de ranking distinto al esperado; revisa manualmente 8_Mapa.py")