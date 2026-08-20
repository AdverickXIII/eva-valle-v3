"""Ficha v2: layout apilado con espacio + PDF con graficos (kaleido)."""
from pathlib import Path

PDFMOD = '''"""PDF de ficha tecnica por cultivo/municipio, con graficos si kaleido esta disponible."""
import io

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image as RLImage, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

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


def _fig_png(fig):
    try:
        return fig.to_image(format="png", width=1000, scale=2)
    except Exception:
        return None


def build_ficha_pdf(cultivo, ambito, agg, diag, figs=None) -> bytes:
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
    story += [t2, Spacer(1, 0.5 * cm)]

    # ---------- GRAFICOS (si kaleido esta disponible) ----------
    if figs:
        incluidos = 0
        for titulo, fig in figs:
            png = _fig_png(fig)
            if png is None:
                continue
            incluidos += 1
            story.append(Paragraph(f"<b>{titulo}</b>", body))
            img = RLImage(io.BytesIO(png))
            w = 16.5 * cm
            h = img.drawHeight * w / img.drawWidth
            img.drawWidth, img.drawHeight = w, h
            story += [img, Spacer(1, 0.4 * cm)]
        if incluidos == 0:
            story.append(Paragraph("(Graficos no incluidos en este equipo: "
                                   "instale kaleido con pip install kaleido.)", body))

    story += [Paragraph("<b>Interpretacion</b>", body),
              Paragraph(diag["narrativa"].replace("**", ""), body),
              Spacer(1, 0.5 * cm),
              Paragraph(f"Fuente: UPRA - EVA 2019-2025. {meta.firma()}.",
                        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8))]
    doc.build(story)
    return buf.getvalue()
'''

PAGE = '''"""Pagina 20: Ficha interactiva cultivo x municipio (layout apilado + PDF con graficos)."""
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
st.caption("Selecciona cultivo y ambito; consulta CAGR, serie, elasticidad y descarga el PDF con graficos.")

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

# KPIs en dos filas de tres (mas aire)
r1a, r1b, r1c = st.columns(3)
r1a.metric("Produccion acumulada", f"{diag['prod_total']:,.0f} t")
r1b.metric("CAGR produccion", f"{diag['cagr_prod']:+.1f}%")
r1c.metric("CAGR area", f"{diag['cagr_area']:+.1f}%")
r2a, r2b, r2c = st.columns(3)
r2a.metric("CAGR rendimiento", f"{diag['cagr_rend']:+.1f}%")
r2b.metric("Elasticidad",
           f"{diag['elasticidad']:.2f}" if diag["elasticidad"] is not None else "n/d")
r2c.metric("Motor", diag["tipo"])

st.info(f"**{cultivo} — {ambito}:** {diag['narrativa']}")

# Graficos APILADOS a ancho completo, con espacio entre ellos
fig_serie = plot_crop_serie(diag, f"Serie historica: {cultivo} ({ambito})")
st.plotly_chart(fig_serie, use_container_width=True)

fig_motor = plot_crop_motor(diag)
st.plotly_chart(fig_motor, use_container_width=True)

figs_pdf = [("Serie historica", fig_serie), ("Motor del crecimiento", fig_motor)]

if ambito == "Todo el Valle":
    fig_top = plot_top_municipios(sub, cultivo)
    st.plotly_chart(fig_top, use_container_width=True)
    figs_pdf.append(("Top 10 municipios", fig_top))
else:
    st.subheader("Top 5 municipios del cultivo (referencia departamental)")
    st.dataframe(diag["top_mun"], use_container_width=True, hide_index=True)

st.markdown("---")
pdf = build_ficha_pdf(cultivo, ambito, diag["agg"], diag, figs=figs_pdf)
nombre = "".join(ch for ch in f"ficha_{cultivo}_{ambito}" if ch.isalnum() or ch in "_-") + ".pdf"
st.download_button("⬇️ Descargar ficha en PDF (con graficos)", data=pdf,
                   file_name=nombre, mime="application/pdf")

st.caption("Fuente: UPRA - EVA 2019-2025.")
'''

Path("core/reports/ficha_pdf.py").write_text(PDFMOD, encoding="utf-8")
Path("ui/pages/20_Ficha.py").write_text(PAGE, encoding="utf-8")

# Mas altura para el motor (leyenda respira)
pc = Path("ui/charts/crop_card.py")
cc = pc.read_text(encoding="utf-8")
if "height=320," in cc:
    cc = cc.replace("height=320,", "height=420,", 1)
    pc.write_text(cc, encoding="utf-8")
    print("[OK] Motor con mas altura")

print("[OK] ficha_pdf.py con graficos embebidos")
print("[OK] 20_Ficha.py con layout apilado")
print("Reinicia Streamlit y prueba la ficha")