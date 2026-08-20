"""Fix 4.6: reemplaza los 3 metrics por tabla dual CON/SIN caña con los 4 KPIs."""
from pathlib import Path

p = Path("ui/pages/2_Descriptivo.py")
c = p.read_text(encoding="utf-8")

# Localizar el bloque tab3 actual
old_start = '    with tab3:\n        st.subheader("4.6 Concentracion (Gini, HHI)")'
if old_start not in c:
    print("[ERROR] No encontre el bloque tab3 actual")
    raise SystemExit(1)

# Encontrar el inicio del siguiente tab para saber donde termina tab3
idx_start = c.find(old_start)
idx_next_tab = c.find('    with tab4:', idx_start)
if idx_next_tab == -1:
    print("[ERROR] No encontre tab4")
    raise SystemExit(1)

NEW_TAB3 = '''    with tab3:
        st.subheader("4.6 Concentracion: con caña vs sin caña")

        # Calcular ambos escenarios
        conc_con = calculate_concentration(df_f)
        df_sin_cana = df_f[df_f["cultivo"] != "Caña"]
        conc_sin = calculate_concentration(df_sin_cana) if not df_sin_cana.empty else {}

        # Calcular N80 (cultivos que explican el 80% de la produccion)
        def calcular_n80(sub):
            if sub.empty:
                return 0
            prod = sub.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
            tot = prod.sum()
            if tot == 0:
                return 0
            cum = (prod.cumsum() / tot) * 100
            return int((cum < 80).sum() + 1)

        n80_con = calcular_n80(df_f)
        n80_sin = calcular_n80(df_sin_cana)

        # Nombre del top 1
        def top1_name(sub):
            if sub.empty:
                return "-"
            prod = sub.groupby("cultivo")["produccion_t"].sum()
            return prod.idxmax() if not prod.empty else "-"

        top1_con_name = top1_name(df_f)
        top1_sin_name = top1_name(df_sin_cana)

        # Tabla dual
        hhi_con = conc_con.get("hhi", 0)
        hhi_sin = conc_sin.get("hhi", 0)
        gini_con = conc_con.get("gini", 0)
        gini_sin = conc_sin.get("gini", 0)
        top1_con = conc_con.get("top1_share", 0)
        top1_sin = conc_sin.get("top1_share", 0)

        tabla = pd.DataFrame({
            "Indicador": ["HHI", "Gini", f"Top 1 ({top1_con_name})", f"Top 1 ({top1_sin_name})", "Cultivos que explican 80%"],
            "Con cana": [f"{hhi_con:,.0f}", f"{gini_con:.3f}", f"{top1_con:.1f}%", "-", str(n80_con)],
            "Sin cana": [f"{hhi_sin:,.0f}", f"{gini_sin:.3f}", "-", f"{top1_sin:.1f}%", str(n80_sin)],
        })
        st.dataframe(tabla, use_container_width=True, hide_index=True)

        st.info(
            "💡 **Interpretacion dual:** el HHI salta de "
            f"**{hhi_con:,.0f}** (monocultivo extremo, caña domina) a "
            f"**{hhi_sin:,.0f}** (zona diversificada). "
            f"Sin caña emergen **{n80_sin} cultivos** que explican el 80% de la producción restante."
        )

        st.plotly_chart(plot_ex_cana_donuts(df_f), use_container_width=True)

'''

c = c[:idx_start] + NEW_TAB3 + c[idx_next_tab:]
p.write_text(c, encoding="utf-8")
print("[OK] Seccion 4.6 reemplazada: tabla dual CON/SIN cana con 5 indicadores")
print("Reinicia Streamlit y revisa Descriptivo -> Concentracion")