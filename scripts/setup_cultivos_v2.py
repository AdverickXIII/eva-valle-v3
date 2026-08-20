"""Cultivos v2: Top20 sin cana + serie a ancho completo + indice 2019=100 (adios motor de barras)."""
from pathlib import Path

# ---------- 1) crop_card: nueva funcion plot_crop_indice ----------
pc = Path("ui/charts/crop_card.py")
cc = pc.read_text(encoding="utf-8")
if "def plot_crop_indice" not in cc:
    cc += '''

def plot_crop_indice(diag: dict, titulo: str):
    """Lineas indexadas 2019=100: produccion vs area vs rendimiento."""
    agg = diag["agg"]
    base_p = float(agg.p.iloc[0])
    base_a = float(agg.a.iloc[0])
    base_r = float((agg.p / agg.c).iloc[0])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=agg.index, y=agg.p / base_p * 100,
                             mode="lines+markers", name="Produccion",
                             line=dict(color="#2E8B57", width=3)))
    fig.add_trace(go.Scatter(x=agg.index, y=agg.a / base_a * 100,
                             mode="lines+markers", name="Area sembrada",
                             line=dict(color="#F4A261", width=2)))
    fig.add_trace(go.Scatter(x=agg.index, y=(agg.p / agg.c) / base_r * 100,
                             mode="lines+markers", name="Rendimiento",
                             line=dict(color="#5FA8DC", width=2)))
    fig.add_hline(y=100, line_dash="dash", line_color="gray")
    fig.update_layout(yaxis_title="Indice (2019=100)", height=460,
                      legend=dict(orientation="h", y=-0.15),
                      hovermode="x unified", margin=dict(t=40, b=10))
    return apply_theme(fig, titulo)
'''
    pc.write_text(cc, encoding="utf-8")
    print("[OK] plot_crop_indice agregado")

# ---------- 2) pdf_charts: indice_png reemplaza motor_png ----------
CHARTS = '''"""Graficos matplotlib para el PDF (deterministas, sin kaleido)."""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VERDE = "#2E8B57"
AZUL = "#5FA8DC"
NARANJA = "#F4A261"


def serie_png(agg) -> bytes:
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 6.2), sharex=True)
    axes[0].plot(agg.index, agg.p / 1000.0, marker="o", color=VERDE, lw=2)
    axes[0].set_title("Produccion (miles de t)")
    axes[0].grid(alpha=0.3)
    axes[1].plot(agg.index, agg.p / agg.c, marker="o", color=AZUL, lw=2)
    axes[1].set_title("Rendimiento (t/ha)")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()


def indice_png(agg) -> bytes:
    base_p = float(agg.p.iloc[0])
    base_a = float(agg.a.iloc[0])
    base_r = float((agg.p / agg.c).iloc[0])
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.plot(agg.index, agg.p / base_p * 100, marker="o", color=VERDE, lw=2,
            label="Produccion")
    ax.plot(agg.index, agg.a / base_a * 100, marker="o", color=NARANJA, lw=2,
            label="Area sembrada")
    ax.plot(agg.index, (agg.p / agg.c) / base_r * 100, marker="o", color=AZUL, lw=2,
            label="Rendimiento")
    ax.axhline(100, color="gray", ls="--", lw=0.8)
    ax.set_title("Motor del crecimiento (indice 2019=100)")
    ax.set_ylabel("Indice (2019=100)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()
'''
Path("core/reports/pdf_charts.py").write_text(CHARTS, encoding="utf-8")
print("[OK] pdf_charts.py con indice_png")

# ---------- 3) ficha_pdf: usar indice_png ----------
pf = Path("core/reports/ficha_pdf.py")
cf = pf.read_text(encoding="utf-8")
cf = cf.replace("from core.reports.pdf_charts import motor_png, serie_png",
                "from core.reports.pdf_charts import indice_png, serie_png")
cf = cf.replace('story.append(Paragraph("<b>Motor del crecimiento</b>", body))\n        _add_png(story, motor_png(diag))',
                'story.append(Paragraph("<b>Motor del crecimiento (indice 2019=100)</b>", body))\n        _add_png(story, indice_png(diag["agg"]))')
pf.write_text(cf, encoding="utf-8")
print("[OK] ficha_pdf.py con grafico indexado")

# ---------- 4) 7_Cultivos: los 3 cambios de layout ----------
p = Path("ui/pages/7_Cultivos.py")
c = p.read_text(encoding="utf-8")

# 4a) import: motor -> indice
c = c.replace("from ui.charts.crop_card import (diagnostic_subset, plot_crop_motor,",
              "from ui.charts.crop_card import (diagnostic_subset, plot_crop_indice,")

# 4b) Tab 1: Top 20 sin cana despues de la tabla del Top 20
marcador_top = "                     use_container_width=True, hide_index=True)\n\n        # CAGR divergente"
sin_cana = """                     use_container_width=True, hide_index=True)

        st.markdown("#### 🏆 Top 20 cultivos por produccion (SIN cana)")
        df_sc = df_f[df_f["cultivo"] != "Caña"]
        top20s = (df_sc.groupby("cultivo")["produccion_t"].sum()
                  .sort_values(ascending=False).head(20).reset_index())
        total_s = df_sc["produccion_t"].sum()
        top20s["share_pct"] = (top20s["produccion_t"] / total_s * 100).round(2)
        fig_rank2 = go.Figure(go.Bar(
            x=top20s["cultivo"], y=top20s["produccion_t"] / 1000,
            marker_color=PALETTE[1],
            text=top20s["share_pct"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside"))
        fig_rank2.update_layout(template="plotly_white",
                                title="Produccion Top 20 sin cana (miles de t)",
                                yaxis_title="Miles de t", height=420,
                                xaxis_tickangle=-45)
        st.plotly_chart(fig_rank2, use_container_width=True)
        st.caption("Sin la caña, la escala revela la economia real: plátano, piña, "
                   "maíz y frutales pasan a ser visibles y comparables.")

        # CAGR divergente"""
if marcador_top in c:
    c = c.replace(marcador_top, sin_cana, 1)
    print("[OK] Tab 1 con Top 20 sin cana")
else:
    print("[AVISO] No encontre el ancla del Top 20; revisa manualmente")

# 4c) Tab 2: serie a ancho completo + indice en vez de motor
viejo = """        cA, cB = st.columns([3, 2])
        with cA:
            st.plotly_chart(
                plot_crop_serie(diag, f"Serie historica: {cultivo_sel} ({muni_sel})"),
                use_container_width=True)
        with cB:
            st.plotly_chart(plot_crop_motor(diag), use_container_width=True)

        if muni_sel == "Todo el departamento":
            st.plotly_chart(plot_top_municipios(df_c, cultivo_sel),
                            use_container_width=True)"""
nuevo = """        st.plotly_chart(
            plot_crop_serie(diag, f"Serie historica: {cultivo_sel} ({muni_sel})"),
            use_container_width=True)

        st.plotly_chart(
            plot_crop_indice(diag, f"Motor del crecimiento (2019=100): {cultivo_sel}"),
            use_container_width=True)
        st.caption("🟢 Produccion vs 🟠 area vs 🔵 rendimiento (base 2019=100). "
                   "Si el rendimiento acompana a la produccion con el area plana = "
                   "**intensificacion**; si el area acompana a la produccion = "
                   "**expansion extensiva**.")

        if muni_sel == "Todo el departamento":
            st.plotly_chart(plot_top_municipios(df_c, cultivo_sel),
                            use_container_width=True)"""
if viejo in c:
    c = c.replace(viejo, nuevo, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Tab 2: serie a ancho completo + indice 2019=100")
else:
    p.write_text(c, encoding="utf-8")
    print("[AVISO] Bloque de graficos distinto; revisa manualmente")

print("Reinicia Streamlit y revisa la pagina Cultivos")