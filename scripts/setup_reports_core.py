"""Crea core/reports/ (datos + excel + pdf) y agrega reportlab a requirements."""
from pathlib import Path

INIT = '''"""Generacion de reportes por municipio (Excel y PDF)."""
from core.reports.excel_report import build_municipality_excel
from core.reports.pdf_report import build_municipality_pdf

__all__ = ["build_municipality_excel", "build_municipality_pdf"]
'''

DATA = '''"""Calculos compartidos para los reportes por municipio."""
from __future__ import annotations

import pandas as pd


def filter_municipio(df: pd.DataFrame, municipio: str) -> pd.DataFrame:
    return df[df["municipio"] == municipio].copy()


def kpis(df_m: pd.DataFrame, df_all: pd.DataFrame) -> dict:
    prod = df_m["produccion_t"].sum()
    area = df_m["area_sembrada_ha"].sum()
    cosech = df_m["area_cosechada_ha"].sum()
    rend = prod / cosech if cosech else 0.0
    total_dpto = df_all["produccion_t"].sum()
    share = prod / total_dpto * 100 if total_dpto else 0.0
    return {
        "Produccion total (t)": round(float(prod), 1),
        "Area sembrada (ha)": round(float(area), 1),
        "Rendimiento promedio (t/ha)": round(float(rend), 2),
        "Cultivos activos": int(df_m["cultivo"].nunique()),
        "Periodos con datos": int(df_m["periodo"].nunique()),
        "% de la produccion departamental": round(float(share), 2),
    }


def yearly(df_m: pd.DataFrame) -> pd.DataFrame:
    g = (df_m.groupby("ano")
         .agg(produccion=("produccion_t", "sum"),
              area_sembrada=("area_sembrada_ha", "sum"),
              area_cosechada=("area_cosechada_ha", "sum"))
         .reset_index())
    g["rendimiento"] = (g["produccion"] / g["area_cosechada"].replace(0, 1)).round(2)
    return g


def top_cultivos(df_m: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    g = (df_m.groupby("cultivo")["produccion_t"].sum()
         .sort_values(ascending=False).head(n).reset_index())
    total = g["produccion_t"].sum()
    g["share_pct"] = (g["produccion_t"] / total * 100).round(1) if total else 0.0
    return g


def ranking_posicion(df_all: pd.DataFrame, municipio: str):
    r = (df_all.groupby("municipio")["produccion_t"].sum()
         .sort_values(ascending=False).reset_index())
    hit = r[r["municipio"] == municipio].index
    return (int(hit[0]) + 1, len(r)) if len(hit) else (None, len(r))
'''

EXCEL = '''"""Reporte Excel por municipio (3 hojas)."""
from __future__ import annotations

import io

import pandas as pd

from core.reports.data import filter_municipio, kpis, top_cultivos, yearly


def build_municipality_excel(df: pd.DataFrame, municipio: str) -> bytes:
    df_m = filter_municipio(df, municipio)
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        k = kpis(df_m, df)
        pd.DataFrame({"Indicador": list(k.keys()), "Valor": list(k.values())}) \
            .to_excel(w, sheet_name="Resumen", index=False)
        yearly(df_m).to_excel(w, sheet_name="Historico_Anual", index=False)
        top_cultivos(df_m).to_excel(w, sheet_name="Top_Cultivos", index=False)
    return out.getvalue()
'''

PDF = '''"""Reporte PDF formal por municipio (reportlab)."""
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
    kdata = [["Indicador", "Valor"]] + \
            [[str(a), str(b)] for a, b in kpis(df_m, df).items()]
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
'''

if __name__ == "__main__":
    base = Path("core/reports")
    base.mkdir(parents=True, exist_ok=True)
    for nombre, contenido in {
        "__init__.py": INIT, "data.py": DATA,
        "excel_report.py": EXCEL, "pdf_report.py": PDF,
    }.items():
        (base / nombre).write_text(contenido, encoding="utf-8")
        print(f"[OK] core/reports/{nombre}")

    # Agregar reportlab a requirements.txt si no esta
    req = Path("requirements.txt")
    txt = req.read_text(encoding="utf-8")
    if "reportlab" not in txt:
        req.write_text(txt.rstrip() + "\nreportlab>=4.0\n", encoding="utf-8")
        print("[OK] requirements.txt (+reportlab)")

    print("\nParte 1 lista. Instala y sigue: pip install reportlab")