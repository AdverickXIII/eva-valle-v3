"""PARTE 1: Base del informe tecnico (portada + secciones 1-4)."""
from pathlib import Path

PARTE1 = r'''"""Generador del informe tecnico EVA Valle 2019-2025 (nivel FAO/CEPAL)."""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from config.settings import settings
from core.analytics.informe_indicators import (
    brechas, concentracion_cr, correlaciones, diversificacion_municipal,
    dinamica_temporal, idam, tabla_lq,
)
from core.reports import meta

VERDE = colors.HexColor("#2E8B57")
GRIS = colors.HexColor("#4A5568")
NARANJA = colors.HexColor("#DD6B20")


def _style():
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


def _footer(canvas, doc):
    w, _ = letter
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.line(36, 42, w - 36, 42)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(36, 32, f"{meta.firma()} | Informe Tecnico 2019-2025")
    canvas.drawRightString(w - 36, 32, f"Pagina {doc.page}")
    canvas.restoreState()


def _tabla(data, col_widths=None):
    t = Table(data, hAlign="LEFT", colWidths=col_widths)
    t.setStyle(_style())
    return t


def _barras(labels, valores, titulo, color=VERDE, width=460, height=180):
    d = Drawing(width, height)
    bc = HorizontalBarChart()
    bc.x = 120
    bc.y = 10
    bc.height = height - 30
    bc.width = width - 130
    bc.data = [valores]
    bc.categoryAxis.categoryNames = labels
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 7
    bc.valueAxis.labels.fontSize = 7
    bc.bars[0].fillColor = color
    bc.barWidth = 10
    d.add(bc)
    return d


def _pct(new, old):
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100


# =====================================================================
# BUILDER PRINCIPAL (se llena por partes)
# =====================================================================
def build_informe(df: pd.DataFrame) -> bytes:
    """Genera el informe tecnico completo."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            title="Informe Tecnico EVA Valle 2019-2025")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE, fontSize=22)
    h1 = ParagraphStyle("H1", parent=st_["Heading1"], textColor=VERDE,
                        spaceBefore=14, spaceAfter=6)
    h2 = ParagraphStyle("H2", parent=st_["Heading2"], textColor=VERDE,
                        spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=12)
    story = []

    # --- PORTADA ---
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Informe Tecnico", title))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Dinamica y Estructura Agricola<br/>Valle del Cauca 2019-2025",
        ParagraphStyle("Sub", parent=st_["Heading2"],
                       textColor=GRIS, fontSize=16, leading=20)))
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        "<b>Analisis estadistico, territorial y productivo</b><br/>"
        "con indicadores de concentracion, especializacion y desempeno",
        ParagraphStyle("Desc", parent=st_["Normal"], alignment=1)))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        f"<b>Elaborado por:</b> {meta.AUTOR}<br/>"
        f"{meta.CARGO}<br/><br/>"
        f"<b>Fecha:</b> {date.today().strftime('%Y-%m-%d')}<br/>"
        f"<b>Fuente oficial:</b> UPRA - Encuestas de Valoracion Agropecuaria (EVA)",
        body))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("<i>Documento tecnico de referencia</i>",
                           ParagraphStyle("Italic", parent=st_["Italic"], alignment=1)))

    # --- RESUMEN EJECUTIVO (seccion 1) ---
    story.append(Paragraph("1. Resumen Ejecutivo", h1))
    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    ultimo, anterior = anos[-1], anos[-2]
    p_ult = df[df["ano"] == ultimo]["produccion_t"].sum()
    p_ant = df[df["ano"] == anterior]["produccion_t"].sum()
    a_ult = df[df["ano"] == ultimo]["area_sembrada_ha"].sum()
    c_ult = df[df["ano"] == ultimo]["area_cosechada_ha"].sum()
    rend = p_ult / c_ult if c_ult else 0

    story.append(Paragraph(
        f"El sector agricola del Valle del Cauca registro en {ultimo} una produccion de "
        f"<b>{p_ult:,.0f} toneladas</b> ({_pct(p_ult, p_ant):+.1f}% vs {anterior}), en "
        f"<b>{a_ult:,.0f} hectareas</b> de area sembrada y un rendimiento promedio de "
        f"<b>{rend:.1f} t/ha</b>, distribuidas entre <b>{df['cultivo'].nunique()} cultivos</b> "
        f"y <b>{df['municipio'].nunique()} municipios</b>.", body))
    story.append(Spacer(1, 0.3 * cm))

    hallazgos = [
        "La cana de azucar concentra 95% del tonelaje departamental; "
        "al excluirla emergen 11 cultivos relevantes (platano, pina, maiz, citricos).",
        "Gini productivo = 0.98 (extrema concentracion por cultivo).",
        "Gini territorial = 0.64 (alta concentracion por municipio; Palmira lidera).",
        "Top 4 municipios concentran ~45% de la produccion departamental.",
        "Cebolla de rama y aji presentan los mayores CAGR (22-27%).",
        "Malanga, coco y borojo muestran declives sostenidos.",
    ]
    for h in hallazgos:
        story.append(Paragraph(f"&bull; {h}", body))

    # Placeholder para el resto del contenido (secciones 2-15)
    # SECCION_2_15_PLACEHOLDER

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


def main():
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    df = pd.read_csv(path, low_memory=False)
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "informe_tecnico_valle_2019_2025.pdf"
    pdf_bytes = build_informe(df)
    out_path.write_bytes(pdf_bytes)
    print(f"[OK] Informe tecnico: {out_path}")
    print(f"     Tamano: {out_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
'''

Path("core/reports/informe_tecnico.py").write_text(PARTE1, encoding="utf-8")
print("[OK] Parte 1 creada (portada + seccion 1)")
print("Sigue: python scripts\\setup_informe_parte2.py")