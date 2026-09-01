"""PDF de ficha tecnica con graficos matplotlib embebidos."""
import io

import pandas as pd
from core.reports.branding import pagina_con_logo, build_con_logo
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


def build_ficha_pdf(cultivo, ambito, agg, diag, figs=None, comp=None, **kwargs) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, onPage=pagina_con_logo, pagesize=letter, title="Ficha Tecnica")
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

    if comp is not None:
        try:
            story.append(Paragraph("<b>Comparativa vs Departamento</b>", body))
            cols = list(comp.columns)[:8]
            rows = [cols]
            for _, r in comp.head(12).iterrows():
                fila = []
                for col in cols:
                    v = r[col]
                    fila.append(f"{v:,.1f}" if isinstance(v, float) else str(v))
                rows.append(fila)
            t3 = Table(rows, hAlign="LEFT")
            t3.setStyle(_style())
            story += [t3, Spacer(1, 0.4 * cm)]
        except Exception:
            pass

    story += [Paragraph("<b>Interpretacion</b>", body),
              Paragraph(diag["narrativa"].replace("**", ""), body),
              Spacer(1, 0.5 * cm),
              Paragraph(f"Fuente: UPRA - EVA 2019-2025. {meta.firma()}.",
                        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8))]
    build_con_logo(doc, story)
    return buf.getvalue()
