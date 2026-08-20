"""Ficha v3: PDF con graficos matplotlib (sin kaleido) + elasticidad coherente."""
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
    story += [t, Spacer(1, 0.5 * cm),
              Paragraph("<b>Serie anual</b>", body)]

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

Path("core/reports/pdf_charts.py").write_text(CHARTS, encoding="utf-8")
Path("core/reports/ficha_pdf.py").write_text(PDFMOD, encoding="utf-8")

# --- Pagina: llamada sin figs (el PDF genera sus propios graficos) ---
p = Path("ui/pages/20_Ficha.py")
c = p.read_text(encoding="utf-8")
old = 'pdf = build_ficha_pdf(cultivo, ambito, diag["agg"], diag, figs=figs_pdf)'
new = 'pdf = build_ficha_pdf(cultivo, ambito, diag["agg"], diag)'
if old in c:
    c = c.replace(old, new, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Pagina ajustada: PDF con graficos matplotlib")
else:
    print("[AVISO] Llamada ya ajustada o distinta; revisa 20_Ficha.py")

# --- crop_card: elasticidad solo si el area varia de verdad ---
pc = Path("ui/charts/crop_card.py")
cc = pc.read_text(encoding="utf-8")
old_e = """    elast = None
    if len(agg) >= 4 and agg.a.nunique() > 1 and (agg.a > 0).all():
        elast = float(np.polyfit(np.log(agg.a.values), np.log(agg.p.values), 1)[0])"""
new_e = """    elast = None
    area_varia = bool(agg.a.max() / agg.a.min() >= 1.15) if (agg.a > 0).all() else False
    if len(agg) >= 4 and agg.a.nunique() > 1 and area_varia:
        elast = float(np.polyfit(np.log(agg.a.values), np.log(agg.p.values), 1)[0])"""
if old_e in cc:
    cc = cc.replace(old_e, new_e, 1)
    cc = cc.replace("Elasticidad no estimable con pocos anos.",
                    "Elasticidad no concluyente (pocos anos o area casi constante); "
                    "el motor se lee por los CAGR de area y rendimiento.")
    pc.write_text(cc, encoding="utf-8")
    print("[OK] Elasticidad ahora solo se estima con variacion real de area")
else:
    print("[AVISO] Bloque de elasticidad distinto; revisa crop_card.py")

print("Reinicia Streamlit y descarga de nuevo el PDF")