"""PDF del Indice de Riesgo Territorial (42 municipios)."""
import io

import pandas as pd
from core.reports.branding import pagina_con_logo, build_con_logo
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.reports import meta

VERDE = colors.HexColor("#2E8B57")


def _color_score(score: float):
    """Verde -> amarillo -> rojo, aclarado para fondo de fila."""
    s = max(0.0, min(100.0, float(score)))
    if s <= 50:
        t = s / 50.0
        r = int(154 + (250 - 154) * t)
        g = int(205 + (204 - 205) * t)
        b = int(75 + (21 - 75) * t)
    else:
        t = (s - 50) / 50.0
        r = int(250 + (214 - 250) * t)
        g = int(204 + (39 - 204) * t)
        b = int(21 + (40 - 21) * t)
    r = int(r + (255 - r) * 0.55)
    g = int(g + (255 - g) * 0.55)
    b = int(b + (255 - b) * 0.55)
    return colors.Color(r / 255, g / 255, b / 255)


def build_riesgo_pdf(df_ir: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, onPage=pagina_con_logo, pagesize=letter,
                            title="Indice de Riesgo Territorial")
    st_ = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=st_["Title"], textColor=VERDE, fontSize=15)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=10, fontSize=8.5)

    story = [
        Paragraph("Indice de Riesgo Territorial - Valle del Cauca", h1),
        Paragraph("42 municipios rankeados por riesgo agricola estructural "
                  "(0 = sano, 100 = maximo riesgo)", body),
        Spacer(1, 0.3 * cm),
        Paragraph("Componentes: dependencia de un solo cultivo + baja diversidad "
                  "(Shannon) + declive sostenido (CAGR) + caida reciente. "
                  "Fuente: UPRA - EVA 2019-2025.", body),
        Spacer(1, 0.4 * cm),
    ]

    rows = [["#", "Municipio", "Riesgo", "Depend.", "Divers.", "Declive",
             "Caida", "Produccion (t)"]]
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
    ]
    for i, (_, r) in enumerate(df_ir.iterrows(), start=1):
        rows.append([str(i), str(r["municipio"]), f"{r['score']:.0f}",
                     f"{r['dependencia']:.0f}", f"{r['baja_diversidad']:.0f}",
                     f"{r['declive']:.0f}", f"{r['caida']:.0f}",
                     f"{r['produccion_t']:,.0f}"])
        cmds.append(("BACKGROUND", (0, i), (-1, i), _color_score(r["score"])))
    t = Table(rows, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle(cmds))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        f"Filas coloreadas por nivel de riesgo (verde = sano, rojo = riesgo). "
        f"{meta.firma()}.",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=7.5)))
    build_con_logo(doc, story)
    return buf.getvalue()
