"""PDF ejecutivo de alto nivel (7 secciones) con firma y analisis dual."""
from __future__ import annotations

import io

import pandas as pd
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from core.analytics.executive import executive_summary
from core.analytics.pareto import (conc_metrics, pareto, quality,
                                   recomendaciones, territorial, tiering)
from core.reports import meta

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


def _tabla(data) -> Table:
    t = Table(data, hAlign="LEFT")
    t.setStyle(_style())
    return t


def _pareto(df: pd.DataFrame, exclude_cana: bool, color=VERDE,
            width: float = 230, height: float = 140) -> Drawing:
    """Pareto horizontal compacto (con o sin cana)."""
    p = pareto(df, exclude_cana, 8)
    d = Drawing(width, height)
    bc = HorizontalBarChart()
    bc.x = 80
    bc.y = 6
    bc.height = height - 16
    bc.width = width - 88
    bc.data = [list(p["share"])]
    bc.categoryAxis.categoryNames = list(p["cultivo"])
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 6
    bc.valueAxis.valueMin = 0
    bc.valueAxis.labels.fontSize = 6
    bc.bars[0].fillColor = color
    bc.barWidth = 9
    d.add(bc)
    return d


def build_executive_pdf(df: pd.DataFrame) -> bytes:
    s = executive_summary(df)
    cc = conc_metrics(df, False)
    sc = conc_metrics(df, True)
    ter = territorial(df)
    q = quality(df)
    tier = tiering(df)["tier"].value_counts()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Resumen Ejecutivo")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE)
    story = []

    story.append(Paragraph("Resumen Ejecutivo - Valle del Cauca", title))
    story.append(Paragraph(f"<i>{meta.firma()} | UPRA 2019-2025 | "
                           "Estandar profesional (UPRA/CEPAL)</i>", st_["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    # 1. Panorama
    d1 = [["Indicador", "Valor", "Var. vs ano anterior"]] +          [[x["label"], x["value"], x["delta"] or "-"] for x in s["kpis"]]
    b = [Paragraph("1. Panorama general", st_["Heading2"]),
         _tabla(d1), Spacer(1, 0.4 * cm)]
    story.append(KeepTogether(b))

    # 2. Concentracion dual
    d2 = [["Indicador", "Con cana", "Sin cana"],
          ["HHI", f"{cc['hhi']:,.0f}", f"{sc['hhi']:,.0f}"],
          ["Gini", str(cc["gini"]), str(sc["gini"])],
          ["Top 1 (%)", f"{cc['top1_pct']:.1f} ({cc['top1']})",
           f"{sc['top1_pct']:.1f} ({sc['top1']})"],
          ["Cultivos que explican 80%", str(cc["n80"]), str(sc["n80"])]]
    graf_cana = _pareto(df, False, color=VERDE)
    graf_sin = _pareto(df, True, color=colors.HexColor("#DD6B20"))
    tabla_grafs = Table(
        [[Paragraph("<b>Pareto CON cana (%)</b>", st_["Normal"]),
          Paragraph("<b>Pareto SIN cana (%)</b>", st_["Normal"])],
         [graf_cana, graf_sin]],
        colWidths=[234, 234])
    tabla_grafs.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    b = [Paragraph("2. Concentracion productiva: con cana vs sin cana",
                   st_["Heading2"]),
         _tabla(d2), Spacer(1, 0.2 * cm), tabla_grafs, Spacer(1, 0.4 * cm)]
    story.append(KeepTogether(b))
    # 3. Territorial
    d3 = [["Indicador", "Valor"],
          ["Gini territorial", f"{ter['gini']:.2f}"],
          ["HHI territorial", f"{ter['hhi']:,.0f}"],
          ["Municipio lider", f"{ter['top']} ({ter['top_pct']:.1f}%)"],
          ["Lider / Intermedio / Rezagado",
           f"{tier.get('Lider',0)} / {tier.get('Intermedio',0)} / {tier.get('Rezagado',0)}"]]
    b = [Paragraph("3. Distribucion territorial", st_["Heading2"]),
         _tabla(d3), Spacer(1, 0.4 * cm)]
    story.append(KeepTogether(b))

    # 4. Tendencias y dinamica
    d4 = [["Ano", "Produccion (t)", "Rendimiento (t/ha)"]]
    for _, r in s["tendencia"].iterrows():
        d4.append([str(int(r["ano"])), f"{r['produccion']:,.0f}",
                   f"{r['rendimiento']:.2f}"])
    t4 = Table(d4, hAlign="LEFT", colWidths=[3*cm, 5*cm, 5*cm])
    t4.setStyle(_style())
    story.append(KeepTogether([
        Paragraph("4. Tendencias y dinamica (2019-2025)", st_["Heading2"]),
        t4, Spacer(1, 0.2*cm)]))

    # Tabla de dinamica de cultivos
    d4b = [["Dinamica", "Cultivo", "CAGR"]]
    for _, r in s["crecen"].iterrows():
        d4b.append(["Crecen", r["cultivo"], f"+{r['cagr']:.1f}%"])
    for _, r in s["declinan"].iterrows():
        d4b.append(["Declinan", r["cultivo"], f"{r['cagr']:.1f}%"])
    t4b = Table(d4b, hAlign="LEFT", colWidths=[3*cm, 7*cm, 3*cm])
    t4b.setStyle(_style())
    story.append(KeepTogether([t4b, Spacer(1, 0.4*cm)]))
    # 5. Calidad del dato
    d5 = [["Aspecto", "Detalle"],
          ["Fuente", q["fuente"]],
          ["Cobertura", q["cobertura"]],
          ["Registros", f"{q['registros']:,}"],
          ["Anomalias (cosechada > sembrada)", f"{q['pct_anomalia']}%"],
          ["Vacios", f"{q['pct_nulos']}%"]]
    b = [Paragraph("5. Calidad y confiabilidad del dato", st_["Heading2"]),
         _tabla(d5), Spacer(1, 0.4 * cm)]
    story.append(KeepTogether(b))

    # 6. Hallazgos
    h = [Paragraph(f"- {m}", st_["Normal"]) for m in s["mensajes"]]
    b = [Paragraph("6. Hallazgos clave", st_["Heading2"])] + h + [Spacer(1, 0.4 * cm)]
    story.append(KeepTogether(b))

    # 7. Recomendaciones
    r = [Paragraph(f"<b>{t}.</b> {d}", st_["Normal"])
         for t, d in recomendaciones(df)]
    b = [Paragraph("7. Recomendaciones", st_["Heading2"])] + r + [Spacer(1, 0.5 * cm)]
    story.append(KeepTogether(b))

    story.append(Paragraph(
        f"Fuente: {meta.FUENTE}. Recomendaciones generadas automaticamente, "
        f"sujetas a validacion de experto. {meta.firma()}.", st_["Italic"]))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
