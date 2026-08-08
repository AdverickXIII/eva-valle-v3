"""Reporte PDF formal por municipio (reportlab)."""
from __future__ import annotations

import io

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from core.reports.data import (filter_municipio, kpis, ranking_posicion,
                               top_cultivos, yearly)

VERDE = colors.HexColor("#2E8B57")


def _style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F8F9FA")]),
    ])


def build_municipality_pdf(df: pd.DataFrame, municipio: str) -> bytes:
    df_m = filter_municipio(df, municipio)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            title=f"Reporte {municipio}")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE)
    story = []

    story.append(Paragraph("EVA Valle v3.0 - Reporte Agricola Municipal", title))
    story.append(Paragraph(f"<b>Municipio:</b> {municipio} | UPRA 2019-2024",
                           st_["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("1. Indicadores principales", st_["Heading2"]))
    kdata = [["Indicador", "Valor"]] +             [[str(a), str(b)] for a, b in kpis(df_m, df).items()]
    t = Table(kdata, hAlign="LEFT")
    t.setStyle(_style())
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    pos, total = ranking_posicion(df, municipio)
    if pos:
        story.append(Paragraph(
            f"Posicion departamental por produccion: <b>#{pos}</b> de {total}.",
            st_["Normal"]))
        story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("2. Historico anual", st_["Heading2"]))
    ydata = [["Ano", "Produccion (t)", "Area sembrada (ha)", "Rendimiento (t/ha)"]]
    for _, r in yearly(df_m).iterrows():
        ydata.append([str(int(r["ano"])), f"{r['produccion']:,.0f}",
                      f"{r['area_sembrada']:,.0f}", f"{r['rendimiento']:.2f}"])
    t2 = Table(ydata, hAlign="LEFT")
    t2.setStyle(_style())
    story.append(t2)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("3. Principales cultivos", st_["Heading2"]))
    cdata = [["Cultivo", "Produccion (t)", "% del municipio"]]
    for _, r in top_cultivos(df_m).iterrows():
        cdata.append([r["cultivo"], f"{r['produccion_t']:,.0f}",
                      f"{r['share_pct']:.1f}%"])
    t3 = Table(cdata, hAlign="LEFT")
    t3.setStyle(_style())
    story.append(t3)

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "Fuente: UPRA - Encuestas de Valuacion Agropecuaria (EVA) 2019-2024. "
        "Generado automaticamente por EVA Valle v3.0.", st_["Italic"]))

    doc.build(story)
    return buf.getvalue()
