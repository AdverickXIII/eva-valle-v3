"""Reescribe crop_report.py para que las tablas no se partan entre paginas."""
from pathlib import Path

REPORT = '''"""Reportes Excel y PDF por cultivo (ficha tecnica) con firma."""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from core.reports import meta
from core.reports.crop_data import (crop_concentration, crop_kpis,
                                    crop_top_municipios, crop_yearly,
                                    filter_cultivo, interpretar_gini)

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


def build_crop_excel(df: pd.DataFrame, cultivo: str) -> bytes:
    df_c = filter_cultivo(df, cultivo)
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        k = crop_kpis(df_c, df)
        conc = crop_concentration(df_c)
        k["Gini municipal"] = conc["gini"]
        k["HHI municipal"] = conc["hhi"]
        pd.DataFrame({"Indicador": list(k.keys()), "Valor": list(k.values())}) \
            .to_excel(w, sheet_name="Resumen", index=False)
        meta_df = pd.DataFrame({
            "Campo": ["Elaborado por", "Cargo", "Fecha", "Fuente", "Sistema"],
            "Detalle": [meta.AUTOR, meta.CARGO, date.today().strftime("%Y-%m-%d"),
                        meta.FUENTE, meta.SISTEMA]})
        meta_df.to_excel(w, sheet_name="Resumen", index=False, startrow=len(k) + 2)
        crop_yearly(df_c).to_excel(w, sheet_name="Historico_Anual", index=False)
        crop_top_municipios(df_c).to_excel(w, sheet_name="Top_Municipios", index=False)
    return out.getvalue()


def build_crop_pdf(df: pd.DataFrame, cultivo: str) -> bytes:
    df_c = filter_cultivo(df, cultivo)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title=f"Ficha {cultivo}")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE)
    story = []

    story.append(Paragraph(f"Ficha Tecnica - {cultivo}", title))
    story.append(Paragraph(f"<i>{meta.firma()}</i>", st_["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    # 1. Indicadores
    k = crop_kpis(df_c, df)
    kdata = [["Indicador", "Valor"]] + [[str(a), str(b)] for a, b in k.items()]
    t = Table(kdata, hAlign="LEFT"); t.setStyle(_style())
    story.append(KeepTogether([Paragraph("1. Indicadores del cultivo", st_["Heading2"]),
                               t, Spacer(1, 0.4 * cm)]))

    # 2. Concentracion
    conc = crop_concentration(df_c)
    cdata = [["Indicador", "Valor", "Interpretacion"],
             ["Gini municipal", str(conc["gini"]), interpretar_gini(conc["gini"])],
             ["HHI municipal", str(conc["hhi"]), ""],
             ["Municipio lider (%)", str(conc["top1_pct"]), ""]]
    t2 = Table(cdata, hAlign="LEFT"); t2.setStyle(_style())
    story.append(KeepTogether([
        Paragraph("2. Concentracion territorial (Gini/HHI municipal)", st_["Heading2"]),
        t2, Spacer(1, 0.4 * cm)]))

    # 3. Historico
    ydata = [["Ano", "Produccion (t)", "Area (ha)", "Rendimiento (t/ha)"]]
    for _, r in crop_yearly(df_c).iterrows():
        ydata.append([str(int(r["ano"])), f"{r['produccion']:,.0f}",
                      f"{r['area_sembrada']:,.0f}", f"{r['rendimiento']:.2f}"])
    t3 = Table(ydata, hAlign="LEFT"); t3.setStyle(_style())
    story.append(KeepTogether([Paragraph("3. Historico anual", st_["Heading2"]),
                               t3, Spacer(1, 0.4 * cm)]))

    # 4. Municipios (KeepTogether evita que se parta)
    mdata = [["Municipio", "Produccion (t)", "% del cultivo"]]
    for _, r in crop_top_municipios(df_c).iterrows():
        mdata.append([r["municipio"], f"{r['produccion_t']:,.0f}",
                      f"{r['share_pct']:.1f}%"])
    t4 = Table(mdata, hAlign="LEFT"); t4.setStyle(_style())
    story.append(KeepTogether([Paragraph("4. Principales municipios", st_["Heading2"]),
                               t4]))

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(f"Fuente: {meta.FUENTE}. {meta.firma()}.", st_["Italic"]))
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
'''

Path("core/reports/crop_report.py").write_text(REPORT, encoding="utf-8")
print("[OK] core/reports/crop_report.py (tablas no se parten)")
print("\nRecarga Streamlit (Ctrl+R) y vuelve a descargar la ficha de Platano.")