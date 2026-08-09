"""Crea core/reports/executive_report.py: PDF ejecutivo firmado."""
from pathlib import Path

REPORT = '''"""Reporte PDF ejecutivo (una pagina) con firma."""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from core.analytics.alerts import generate_alerts
from core.reports import meta
from core.reports.crop_data import _gini, interpretar_gini

VERDE = colors.HexColor("#2E8B57")
GRIS = colors.HexColor("#4A5568")


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


def _footer(canvas, doc) -> None:
    w, _ = letter
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.line(36, 42, w - 36, 42)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(36, 32,
                      f"{meta.firma()} | {meta.SISTEMA} | Fuente: {meta.FUENTE}")
    canvas.drawRightString(w - 36, 32, f"Pagina {doc.page}")
    canvas.restoreState()


def build_executive_pdf(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Resumen Ejecutivo")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE)
    story = []

    prod = float(df["produccion_t"].sum())
    cos = float(df["area_cosechada_ha"].sum())
    g = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=True)
    shares = g / g.sum() * 100
    hhi = float((shares ** 2).sum())
    gini = _gini(g.values)

    story.append(Paragraph("Resumen Ejecutivo - EVA Valle del Cauca", title))
    story.append(Paragraph(f"<i>{meta.firma()} | UPRA 2019-2024</i>", st_["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("1. Indicadores departamentales", st_["Heading2"]))
    kdata = [["Indicador", "Valor"],
             ["Produccion total (t)", f"{prod:,.0f}"],
             ["Area sembrada (ha)", f"{df['area_sembrada_ha'].sum():,.0f}"],
             ["Rendimiento (t/ha)", f"{prod / cos:.1f}" if cos else "0"],
             ["Municipios", str(df["municipio"].nunique())],
             ["Cultivos", str(df["cultivo"].nunique())]]
    t = Table(kdata, hAlign="LEFT"); t.setStyle(_style()); story.append(t)
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        f"Concentracion: HHI={hhi:,.0f} | Gini={gini:.2f} -> {interpretar_gini(gini)}.",
        st_["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("2. Top cultivos por produccion", st_["Heading2"]))
    tc = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False).head(5)
    cdata = [["Cultivo", "Produccion (t)"]] + \
            [[str(n), f"{v:,.0f}"] for n, v in tc.items()]
    t2 = Table(cdata, hAlign="LEFT"); t2.setStyle(_style()); story.append(t2)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("3. Top municipios por produccion", st_["Heading2"]))
    tm = df.groupby("municipio")["produccion_t"].sum().sort_values(ascending=False).head(5)
    mdata = [["Municipio", "Produccion (t)"]] + \
            [[str(n), f"{v:,.0f}"] for n, v in tm.items()]
    t3 = Table(mdata, hAlign="LEFT"); t3.setStyle(_style()); story.append(t3)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("4. Alertas principales", st_["Heading2"]))
    alerts = generate_alerts(df)[:6]
    adata = [["Severidad", "Alerta"]] + \
            [[a["severidad"], a["titulo"]] for a in alerts]
    t4 = Table(adata, hAlign="LEFT", colWidths=[2.2 * cm, 14 * cm])
    t4.setStyle(_style()); story.append(t4)

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(f"Fuente: {meta.FUENTE}. {meta.firma()}.", st_["Italic"]))
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
'''

Path("core/reports/executive_report.py").write_text(REPORT, encoding="utf-8")
print("[OK] core/reports/executive_report.py")
print("Sigue: python scripts\\setup_executivo_page.py")