"""Reescribe zonification_report.py agregando anexo de municipios por zona."""
from pathlib import Path

MOD = '''"""PDF de Zonificacion Oficial (Ordenanza 513 de 2019) con anexo de municipios."""
import io
import unicodedata

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.analytics.zonas import ZONAS, indicadores_por_zona
from core.reports import meta

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
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _limpiar(lista) -> list:
    """Deduplica alias con/sin tilde conservando el nombre oficial."""
    vistos = set()
    out = []
    for m in lista:
        k = _sin_tildes(str(m)).lower()
        if k not in vistos:
            vistos.add(k)
            out.append(str(m))
    return out


def build_zonification_pdf(df: pd.DataFrame) -> bytes:
    if "zona" not in df.columns:
        from core.analytics.zonas import asignar_zona
        df = df.copy()
        df["zona"] = df["municipio"].apply(asignar_zona)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Zonificacion Oficial")
    st_ = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=st_["Title"], textColor=VERDE, fontSize=16)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=11, fontSize=9)

    story = [
        Paragraph("Zonificacion Oficial: Ordenanza 513 de 2019", h1),
        Paragraph("Analisis dual con/sin cana por subregion (Norte, Centro, Sur, Pacifico)", body),
        Spacer(1, 0.5 * cm),
    ]

    ic = indicadores_por_zona(df, excluye_cana=False)
    if not ic.empty:
        story.append(Paragraph("<b>CON CANA</b>", body))
        rows = [["Zona", "Municipios", "Produccion (t)", "Area (ha)", "Rend. (t/ha)",
                 "% del Dpto.", "Gini muni"]]
        for zona, r in ic.iterrows():
            rows.append([zona, str(int(r["municipios"])), f"{r['produccion_t']:,.0f}",
                         f"{r['area_sembrada_ha']:,.0f}", f"{r['rendimiento_t_ha']:.1f}",
                         f"{r['share_dept_pct']:.1f}%", f"{r['gini_municipios']:.2f}"])
        t = Table(rows, hAlign="LEFT")
        t.setStyle(_style())
        story += [t, Spacer(1, 0.5 * cm)]

    isn = indicadores_por_zona(df, excluye_cana=True)
    if not isn.empty:
        story.append(Paragraph("<b>SIN CANA</b>", body))
        rows2 = [["Zona", "Municipios", "Produccion (t)", "Area (ha)", "Rend. (t/ha)",
                  "% del Dpto.", "Gini muni"]]
        for zona, r in isn.iterrows():
            rows2.append([zona, str(int(r["municipios"])), f"{r['produccion_t']:,.0f}",
                          f"{r['area_sembrada_ha']:,.0f}", f"{r['rendimiento_t_ha']:.1f}",
                          f"{r['share_dept_pct']:.1f}%", f"{r['gini_municipios']:.2f}"])
        t2 = Table(rows2, hAlign="LEFT")
        t2.setStyle(_style())
        story += [t2, Spacer(1, 0.5 * cm)]

    if not ic.empty and not isn.empty:
        lider_con = ic["produccion_t"].idxmax()
        lider_sin = isn["produccion_t"].idxmax()
        if lider_con != lider_sin:
            story.append(Paragraph(
                f"<b>Efecto cana:</b> con cana lidera <b>{lider_con}</b>; "
                f"sin cana el liderazgo pasa a <b>{lider_sin}</b>.", body))
        else:
            story.append(Paragraph(
                f"<b>{lider_con}</b> lidera en ambos escenarios; "
                f"sin cana su peso relativo cambia.", body))
        story.append(Spacer(1, 0.5 * cm))

    # ---------- ANEXO: municipios por zona ----------
    story.append(Paragraph("<b>Anexo: municipios por zona</b>", body))
    cell = ParagraphStyle("Cell", parent=body, fontSize=7.5, leading=9.5)
    rows_a = [["Zona", "Municipios"]]
    for zona, lista in ZONAS.items():
        rows_a.append([zona, Paragraph(", ".join(_limpiar(lista)), cell)])
    t4 = Table(rows_a, hAlign="LEFT", colWidths=[2.5 * cm, 14 * cm])
    t4.setStyle(_style())
    story += [t4, Spacer(1, 0.5 * cm)]

    story.append(Paragraph(
        f"Fuente: UPRA - EVA 2019-2025. Zonificacion: POTD Valle del Cauca, "
        f"Ordenanza 513 de 2019. {meta.firma()}.",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8)))

    doc.build(story)
    return buf.getvalue()
'''

Path("core/reports/zonification_report.py").write_text(MOD, encoding="utf-8")
print("[OK] zonification_report.py con anexo de municipios por zona")
print("Reinicia Streamlit y descarga de nuevo el PDF de Zonificacion")