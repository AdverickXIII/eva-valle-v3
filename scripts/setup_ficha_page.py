"""Crea pagina 20_Ficha: selectores cultivo+municipio, graficos y PDF."""
from pathlib import Path

CARD = '''"""Diagnostico por cultivo: serie, motor CAGR con leyenda, elasticidad y top municipios."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.charts.theme import apply_theme


def diagnostic_subset(sub: pd.DataFrame, total_ref: float) -> dict:
    agg = (sub.groupby("ano")
           .agg(p=("produccion_t", "sum"), a=("area_sembrada_ha", "sum"),
                c=("area_cosechada_ha", "sum"))
           .sort_index())
    agg = agg[(agg.p > 0) & (agg.c > 0)]
    f, l = agg.iloc[0], agg.iloc[-1]
    n = max(len(agg) - 1, 1)
    cagr_p = ((l.p / f.p) ** (1 / n) - 1) * 100
    cagr_a = ((l.a / f.a) ** (1 / n) - 1) * 100 if (l.a > 0 and f.a > 0) else 0.0
    cagr_r = (((l.p / l.c) / (f.p / f.c)) ** (1 / n) - 1) * 100

    elast = None
    if len(agg) >= 4 and agg.a.nunique() > 1 and (agg.a > 0).all():
        elast = float(np.polyfit(np.log(agg.a.values), np.log(agg.p.values), 1)[0])

    prod_total = sub["produccion_t"].sum()
    if cagr_p <= -5:
        tipo = "Colapso"
    elif cagr_a > 2 and cagr_r > 2:
        tipo = "Expansion con tecnologia"
    elif cagr_a > 2:
        tipo = "Expansion extensiva"
    elif cagr_r > 2:
        tipo = "Intensificacion"
    else:
        tipo = "Estable"

    top_mun = (sub.groupby("municipio")["produccion_t"].sum()
               .sort_values(ascending=False).head(5))
    top_df = pd.DataFrame({"municipio": top_mun.index, "produccion_t": top_mun.values})
    top_df["share_pct"] = (top_df["produccion_t"] / prod_total * 100).round(1)

    narrativa = (
        f"{prod_total:,.0f} t acumuladas "
        f"({prod_total / total_ref * 100:.1f}% del ambito de referencia). "
        f"CAGR {cagr_p:+.1f}% anual. "
        f"Motor: {tipo.lower()} (area {cagr_a:+.1f}% / rendimiento {cagr_r:+.1f}%). "
    )
    if elast is not None:
        narrativa += (f"Elasticidad area-produccion ≈ {elast:.2f}: "
                      + ("crecimiento sensible al area (extensivo)."
                         if elast > 0.8
                         else "crecimiento poco dependiente del area (intensivo)."))
    else:
        narrativa += "Elasticidad no estimable con pocos anos."

    return {"prod_total": prod_total, "cagr_prod": cagr_p, "cagr_area": cagr_a,
            "cagr_rend": cagr_r, "tipo": tipo, "elasticidad": elast,
            "top_mun": top_df, "narrativa": narrativa, "agg": agg}


def crop_diagnostic(df: pd.DataFrame, cultivo: str) -> dict:
    d = diagnostic_subset(df[df["cultivo"] == cultivo], df["produccion_t"].sum())
    d["narrativa"] = f"**{cultivo}**: " + d["narrativa"]
    return d


def plot_crop_serie(diag: dict, titulo: str):
    agg = diag["agg"]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=["Produccion (t)", "Rendimiento (t/ha)"],
                        vertical_spacing=0.12)
    fig.add_trace(go.Scatter(x=agg.index, y=agg.p, mode="lines+markers",
                             line=dict(color="#2E8B57", width=3), name="Produccion"), 1, 1)
    fig.add_trace(go.Scatter(x=agg.index, y=agg.p / agg.c, mode="lines+markers",
                             line=dict(color="#5FA8DC", width=2), name="Rendimiento"), 2, 1)
    fig.update_layout(height=480, margin=dict(t=40, b=10), showlegend=False,
                      xaxis_title="Ano")
    return apply_theme(fig, titulo)


def plot_crop_motor(diag: dict):
    vals = [diag["cagr_prod"], diag["cagr_area"], diag["cagr_rend"]]
    labs = ["CAGR produccion", "CAGR area", "CAGR rendimiento"]
    fig = go.Figure()
    for lab, v in zip(labs, vals):
        fig.add_trace(go.Bar(x=[v], y=[lab], orientation="h", name=lab,
                             marker_color="#2E8B57" if v >= 0 else "#D62728",
                             text=[f"{v:+.1f}%"], textposition="outside"))
    fig.add_vline(x=0, line_color="gray")
    fig.update_layout(barmode="group", showlegend=True,
                      legend=dict(orientation="h", y=-0.25),
                      margin=dict(t=40, b=10, l=10), height=320,
                      xaxis_title="CAGR (%)")
    return apply_theme(fig, "Motor del crecimiento (leyenda por componente)")


def plot_top_municipios(sub: pd.DataFrame, cultivo: str):
    top = sub.groupby("municipio")["produccion_t"].sum().sort_values(ascending=False).head(10)
    fig = go.Figure(go.Bar(x=top.values, y=top.index, orientation="h",
                           marker_color="#2E8B57",
                           text=[f"{v:,.0f} t" for v in top.values],
                           textposition="outside"))
    fig.update_layout(margin=dict(t=40, b=10, l=10), height=420,
                      xaxis_title="Produccion acumulada (t)", showlegend=False)
    return apply_theme(fig, f"Top 10 municipios en {cultivo}")
'''

PDFMOD = '''"""PDF de ficha tecnica por cultivo/municipio."""
import io

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from core.reports import meta

VERDE = colors.HexColor("#2E8B57")


def _style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
    ])


def build_ficha_pdf(cultivo: str, ambito: str, agg: pd.DataFrame, diag: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Ficha Tecnica")
    st_ = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=st_["Title"], textColor=VERDE, fontSize=16)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=11, fontSize=9)
    story = [Paragraph(f"Ficha Tecnica: {cultivo}", h1),
             Paragraph(f"Ambito: {ambito} | Periodo: {int(agg.index.min())}-{int(agg.index.max())}", body),
             Spacer(1, 0.4 * cm)]

    kpis = [["Indicador", "Valor"],
            ["Produccion acumulada", f"{diag['prod_total']:,.0f} t"],
            ["CAGR produccion", f"{diag['cagr_prod']:+.1f}%"],
            ["CAGR area sembrada", f"{diag['cagr_area']:+.1f}%"],
            ["CAGR rendimiento", f"{diag['cagr_rend']:+.1f}%"],
            ["Elasticidad area-produccion",
             f"{diag['elasticidad']:.2f}" if diag["elasticidad"] is not None else "n/d"],
            ["Tipo de crecimiento", diag["tipo"]]]
    t = Table(kpis, hAlign="LEFT", colWidths=[8 * cm, 6 * cm])
    t.setStyle(_style())
    story += [t, Spacer(1, 0.5 * cm), Paragraph("<b>Serie anual</b>", body)]

    rows = [["Ano", "Produccion (t)", "Area semb. (ha)", "Area cos. (ha)", "Rend. (t/ha)"]]
    for ano, r in agg.iterrows():
        rows.append([str(int(ano)), f"{r['p']:,.0f}", f"{r['a']:,.0f}", f"{r['c']:,.0f}",
                     f"{r['p'] / r['c']:.1f}" if r["c"] else "-"])
    t2 = Table(rows, hAlign="LEFT")
    t2.setStyle(_style())
    story += [t2, Spacer(1, 0.5 * cm),
              Paragraph("<b>Interpretacion</b>", body),
              Paragraph(diag["narrativa"].replace("**", ""), body),
              Spacer(1, 0.5 * cm),
              Paragraph(f"Fuente: UPRA - EVA 2019-2025. {meta.firma()}.",
                        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8))]
    doc.build(story)
    return buf.getvalue()
'''

PAGE = '''"""Pagina 20: Ficha interactiva cultivo x municipio con exportacion a PDF."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

from config.settings import settings
from ui.charts.crop_card import (diagnostic_subset, plot_crop_motor,
                                 plot_crop_serie, plot_top_municipios)
from core.reports.ficha_pdf import build_ficha_pdf

st.set_page_config(page_title="Ficha Cultivo | EVA Valle", page_icon="🌱", layout="wide")


@st.cache_data(ttl=3600)
def load():
    p = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    return pd.read_csv(p, low_memory=False) if p.exists() else pd.DataFrame()


df = load()
if df.empty:
    st.error("Dataset no encontrado.")
    st.stop()

st.title("🌱 Ficha Tecnica Interactiva: cultivo x municipio")
st.caption("Selecciona cultivo y ambito; consulta CAGR, serie, elasticidad y descarga el PDF.")

c1, c2 = st.columns(2)
with c1:
    cultivos = (df.groupby("cultivo")["produccion_t"].sum()
                .sort_values(ascending=False).index.tolist())
    cultivo = st.selectbox("Cultivo (todos disponibles)", cultivos)
with c2:
    muns = ["Todo el Valle"] + sorted(df["municipio"].unique().tolist())
    ambito = st.selectbox("Municipio", muns)

sub = df[df["cultivo"] == cultivo]
if ambito != "Todo el Valle":
    sub = sub[sub["municipio"] == ambito]

if sub.empty or sub["produccion_t"].sum() <= 0:
    st.warning("Sin datos para esa combinacion cultivo-municipio.")
    st.stop()

total_ref = (df["produccion_t"].sum() if ambito == "Todo el Valle"
             else df[df["cultivo"] == cultivo]["produccion_t"].sum())
diag = diagnostic_subset(sub, total_ref)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Produccion acumulada", f"{diag['prod_total']:,.0f} t")
k2.metric("CAGR produccion", f"{diag['cagr_prod']:+.1f}%")
k3.metric("CAGR area", f"{diag['cagr_area']:+.1f}%")
k4.metric("CAGR rendimiento", f"{diag['cagr_rend']:+.1f}%")
k5.metric("Elasticidad",
          f"{diag['elasticidad']:.2f}" if diag["elasticidad"] is not None else "n/d")
k6.metric("Motor", diag["tipo"])

st.info(f"**{cultivo} — {ambito}:** {diag['narrativa']}")

cA, cB = st.columns([3, 2])
with cA:
    st.plotly_chart(plot_crop_serie(diag, f"Serie historica: {cultivo} ({ambito})"),
                    use_container_width=True)
with cB:
    st.plotly_chart(plot_crop_motor(diag), use_container_width=True)
    if ambito == "Todo el Valle":
        st.plotly_chart(plot_top_municipios(sub, cultivo), use_container_width=True)
    else:
        st.markdown("**Top 5 municipios del cultivo** (referencia departamental)")
        st.dataframe(diag["top_mun"], use_container_width=True, hide_index=True)

# ---------- DESCARGA PDF ----------
pdf = build_ficha_pdf(cultivo, ambito, diag["agg"], diag)
nombre = "".join(ch for ch in f"ficha_{cultivo}_{ambito}" if ch.isalnum() or ch in "_-") + ".pdf"
st.download_button("⬇️ Descargar ficha en PDF", data=pdf, file_name=nombre,
                   mime="application/pdf")

st.markdown("---")
st.caption("Fuente: UPRA - EVA 2019-2025. El PDF incluye KPIs, serie anual e interpretacion.")
'''

Path("ui/charts/crop_card.py").write_text(CARD, encoding="utf-8")
Path("core/reports/ficha_pdf.py").write_text(PDFMOD, encoding="utf-8")
Path("ui/pages/20_Ficha.py").write_text(PAGE, encoding="utf-8")

app = Path("app.py")
lines = app.read_text(encoding="utf-8").splitlines(keepends=True)
if not any("20_Ficha.py" in l for l in lines):
    nueva = '    st.Page("ui/pages/20_Ficha.py", title="Ficha Cultivo", icon="\\U0001F331"),\n'
    for i, l in enumerate(lines):
        if "19_Zonas.py" in l:
            lines.insert(i + 1, nueva)
            break
    app.write_text("".join(lines), encoding="utf-8")
    print("[OK] Pagina Ficha Cultivo registrada en app.py")

print("[OK] crop_card.py (motor con leyenda + top municipios)")
print("[OK] core/reports/ficha_pdf.py (PDF de ficha)")
print("[OK] ui/pages/20_Ficha.py")
print("Reinicia Streamlit y abre la pagina 🌱 Ficha Cultivo")