"""Ficha PDF final: + tabla comparativa vs departamento + graficos garantizados."""
from pathlib import Path

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

PDFMOD = '''"""PDF de ficha tecnica: KPIs + serie + comparativa vs dpto + graficos + interpretacion."""
import io

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image as RLImage, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from core.reports import meta
from core.reports.pdf_charts import indice_png, serie_png

VERDE = colors.HexColor("#2E8B57")


def _style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
    ])


def _add_png(story, png):
    img = RLImage(io.BytesIO(png))
    w = 16.5 * cm
    h = img.drawHeight * w / img.drawWidth
    img.drawWidth, img.drawHeight = w, h
    story += [img, Spacer(1, 0.4 * cm)]


def build_ficha_pdf(cultivo, ambito, agg, diag, comp=None) -> bytes:
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

    # ---------- COMPARATIVA VS DEPARTAMENTO (solo si hay municipio) ----------
    if comp is not None and not comp.empty:
        story.append(Paragraph("<b>Comparativa vs Departamento (por ano)</b>", body))
        rows_c = [["Ano", "Prod. municipio (t)", "Prod. dpto (t)", "% Part.",
                   "Rend. muni (t/ha)", "Rend. dpto (t/ha)"]]
        for _, r in comp.iterrows():
            rows_c.append([str(int(r["ano"])), f"{r['prod_muni']:,.0f}",
                           f"{r['prod_dpto']:,.0f}", f"{r['participacion_pct']:.1f}%",
                           f"{r['rend_muni']:.1f}", f"{r['rend_dpto']:.1f}"])
        t3 = Table(rows_c, hAlign="LEFT")
        t3.setStyle(_style())
        story += [t3, Spacer(1, 0.5 * cm)]

    # ---------- GRAFICOS ----------
    try:
        story.append(Paragraph("<b>Serie historica</b>", body))
        _add_png(story, serie_png(agg))
        story.append(Paragraph("<b>Motor del crecimiento (indice 2019=100)</b>", body))
        _add_png(story, indice_png(agg))
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
print("[OK] pdf_charts.py y ficha_pdf.py reescritos (con comparativa vs dpto)")

# ---------- Elasticidad coherente (por si quedo pendiente) ----------
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
    print("[OK] Elasticidad ahora solo con variacion real de area")
else:
    print("[INFO] Elasticidad ya estaba corregida")

# ---------- Pagina: calcular comp y pasarla al PDF ----------
p = Path("ui/pages/7_Cultivos.py")
c = p.read_text(encoding="utf-8")
old_b = """        ambito_pdf = muni_sel if muni_sel != "Todo el departamento" else "Todo el Valle"
        sub_pdf = df_c if muni_sel == "Todo el departamento" else df_c[df_c["municipio"] == muni_sel]
        if not sub_pdf.empty and diag["prod_total"] > 0:
            pdf = build_ficha_pdf(cultivo_sel, ambito_pdf, diag["agg"], diag)"""
new_b = """        ambito_pdf = muni_sel if muni_sel != "Todo el departamento" else "Todo el Valle"
        sub_pdf = df_c if muni_sel == "Todo el departamento" else df_c[df_c["municipio"] == muni_sel]

        comp_pdf = None
        if muni_sel != "Todo el departamento" and not sub_pdf.empty:
            muni_ano = sub_pdf.groupby("ano").agg(
                prod_muni=("produccion_t", "sum"),
                cosech_muni=("area_cosechada_ha", "sum")).reset_index()
            dpto_ano = df_c.groupby("ano").agg(
                prod_dpto=("produccion_t", "sum"),
                cosech_dpto=("area_cosechada_ha", "sum")).reset_index()
            comp_pdf = muni_ano.merge(dpto_ano, on="ano")
            comp_pdf["rend_muni"] = comp_pdf["prod_muni"] / comp_pdf["cosech_muni"].replace(0, 1)
            comp_pdf["rend_dpto"] = comp_pdf["prod_dpto"] / comp_pdf["cosech_dpto"].replace(0, 1)
            comp_pdf["participacion_pct"] = (comp_pdf["prod_muni"] /
                                             comp_pdf["prod_dpto"].replace(0, 1) * 100)

        if not sub_pdf.empty and diag["prod_total"] > 0:
            pdf = build_ficha_pdf(cultivo_sel, ambito_pdf, diag["agg"], diag,
                                  comp=comp_pdf)"""
if old_b in c:
    c = c.replace(old_b, new_b, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Tab 3: PDF con tabla comparativa vs departamento")
else:
    print("[AVISO] Bloque de PDF distinto; revisa manualmente")

print("Reinicia Streamlit y descarga la ficha de Platanos-Sevilla de nuevo")