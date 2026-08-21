"""Ficha v3 auto-reparable: detecta o recrea la pagina, PDF con graficos matplotlib."""
import glob
from pathlib import Path

CHARTS = '''"""Graficos matplotlib para el PDF (deterministas, sin kaleido)."""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VERDE = "#2E8B57"
AZUL = "#5FA8DC"
ROJO = "#D62728"


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


def motor_png(diag) -> bytes:
    vals = [diag["cagr_prod"], diag["cagr_area"], diag["cagr_rend"]]
    labs = ["CAGR produccion", "CAGR area", "CAGR rendimiento"]
    cols = [VERDE if v >= 0 else ROJO for v in vals]
    fig, ax = plt.subplots(figsize=(8.5, 2.6))
    ax.barh(labs, vals, color=cols)
    for i, v in enumerate(vals):
        ax.text(v + (0.3 if v >= 0 else -0.3), i, f"{v:+.1f}%",
                va="center", ha="left" if v >= 0 else "right", fontsize=9)
    ax.axvline(0, color="gray", lw=0.8)
    ax.set_title("Motor del crecimiento (%)")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()
'''

PDFMOD = '''"""PDF de ficha tecnica con graficos matplotlib embebidos."""
import io

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image as RLImage, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from core.reports import meta
from core.reports.pdf_charts import motor_png, serie_png

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


def _add_png(story, png):
    img = RLImage(io.BytesIO(png))
    w = 16.5 * cm
    h = img.drawHeight * w / img.drawWidth
    img.drawWidth, img.drawHeight = w, h
    story += [img, Spacer(1, 0.4 * cm)]


def build_ficha_pdf(cultivo, ambito, agg, diag) -> bytes:
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

    try:
        story.append(Paragraph("<b>Serie historica</b>", body))
        _add_png(story, serie_png(agg))
        story.append(Paragraph("<b>Motor del crecimiento</b>", body))
        _add_png(story, motor_png(diag))
    except Exception as e:
        story.append(Paragraph(f"(Graficos no disponibles: {e})", body))

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

st.plotly_chart(plot_crop_serie(diag, f"Serie historica: {cultivo} ({ambito})"),
                use_container_width=True)
st.plotly_chart(plot_crop_motor(diag), use_container_width=True)

if ambito == "Todo el Valle":
    st.plotly_chart(plot_top_municipios(sub, cultivo), use_container_width=True)
else:
    st.subheader("Top 5 municipios del cultivo (referencia departamental)")
    st.dataframe(diag["top_mun"], use_container_width=True, hide_index=True)

st.markdown("---")
pdf = build_ficha_pdf(cultivo, ambito, diag["agg"], diag)
nombre = "".join(ch for ch in f"ficha_{cultivo}_{ambito}" if ch.isalnum() or ch in "_-") + ".pdf"
st.download_button("⬇️ Descargar ficha en PDF (con graficos)", data=pdf,
                   file_name=nombre, mime="application/pdf")

st.caption("Fuente: UPRA - EVA 2019-2025.")
'''

Path("core/reports/pdf_charts.py").write_text(CHARTS, encoding="utf-8")
Path("core/reports/ficha_pdf.py").write_text(PDFMOD, encoding="utf-8")
print("[OK] pdf_charts.py + ficha_pdf.py (graficos matplotlib)")

# --- Detectar o recrear la pagina de la Ficha ---
cands = sorted(glob.glob("ui/pages/20_*.py"))
if cands:
    page_path = Path(cands[0])
    page_path.write_text(PAGE, encoding="utf-8")
    print(f"[OK] Pagina detectada y actualizada: {page_path}")
else:
    page_path = Path("ui/pages/20_Ficha_Cultivo.py")
    page_path.write_text(PAGE, encoding="utf-8")
    print("[OK] Pagina recreada como 20_Ficha_Cultivo.py")

# --- Asegurar registro unico en app.py ---
app = Path("app.py")
at = app.read_text(encoding="utf-8")
fname = page_path.as_posix().replace("ui/pages/", "")
if fname not in at:
    at = at.replace("20_Ficha.py", f"ui/pages/{fname}").replace("ui/pages/ui/pages/", "ui/pages/")
    if fname not in at:
        linea = f'    st.Page("ui/pages/{fname}", title="Ficha Cultivo", icon="\\U0001F331", url_path="ficha-cultivo"),\n'
        idx = at.find("19_Zonas.py")
        if idx != -1:
            eol = at.find("\n", idx)
            at = at[:eol + 1] + linea + at[eol + 1:]
        else:
            at += linea
    app.write_text(at, encoding="utf-8")
    print("[OK] app.py actualizado con la pagina de Ficha")
else:
    print("[OK] app.py ya referencia la pagina")

# --- Elasticidad coherente en crop_card ---
pc = Path("ui/charts/crop_card.py")
cc = pc.read_text(encoding="utf-8")
old_e = "    if len(agg) >= 4 and agg.a.nunique() > 1 and (agg.a > 0).all():"
new_e = ("    area_varia = bool(agg.a.max() / agg.a.min() >= 1.15) if (agg.a > 0).all() else False\n"
         "    if len(agg) >= 4 and agg.a.nunique() > 1 and area_varia:")
if old_e in cc:
    cc = cc.replace(old_e, new_e, 1)
    cc = cc.replace("Elasticidad no estimable con pocos anos.",
                    "Elasticidad no concluyente (pocos anos o area casi constante); "
                    "el motor se lee por los CAGR de area y rendimiento.")
    pc.write_text(cc, encoding="utf-8")
    print("[OK] Elasticidad solo con variacion real de area")
else:
    print("[INFO] Elasticidad ya ajustada")

print("\nReinicia Streamlit y descarga la ficha de Platano + Sevilla")