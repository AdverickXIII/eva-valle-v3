"""Genera informe tecnico 2024-2025 con tablas y graficas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import io
from datetime import date

import pandas as pd
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from config.settings import settings
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
    canvas.drawString(36, 32, f"{meta.firma()} | EVA Valle v3.0 | Informe 2024-2025")
    canvas.drawRightString(w - 36, 32, f"Pagina {doc.page}")
    canvas.restoreState()


def _pct_change(new, old):
    """Calcula variacion porcentual."""
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100


def build_informe(df: pd.DataFrame) -> bytes:
    # Filtrar 2024-2025
    df_24 = df[df["ano"] == 2024]
    df_25 = df[df["ano"] == 2025]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Informe Tecnico 2024-2025")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE, fontSize=20)
    h1 = ParagraphStyle("H1", parent=st_["Heading1"], textColor=VERDE)
    h2 = ParagraphStyle("H2", parent=st_["Heading2"], textColor=VERDE)
    
    story = []

    # --- PORTADA ---
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Informe Tecnico", title))
    story.append(Paragraph("Valle del Cauca 2024-2025", ParagraphStyle("Sub",
                           parent=st_["Heading2"], textColor=GRIS, fontSize=16)))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Area, produccion y rendimiento por tipo de cultivo y municipios",
                           st_["Heading3"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"Elaborado por: <b>{meta.AUTOR}</b><br/>"
                           f"{meta.CARGO}<br/>"
                           f"Fecha: {date.today().strftime('%Y-%m-%d')}<br/>"
                           f"Fuente: UPRA EVA 2024-2025", st_["Normal"]))

    # --- SECCION 1: AREA CULTIVADA POR TIPO DE CULTIVO ---
    story.append(Paragraph("1. Area cultivada y variacion segun el tipo de cultivo", h1))
    story.append(Spacer(1, 0.3 * cm))

    # Agrupar por grupo_cultivo
    area_24 = df_24.groupby("grupo_cultivo")["area_sembrada_ha"].sum().reset_index()
    area_24.columns = ["grupo_cultivo", "area_2024"]
    
    area_25 = df_25.groupby("grupo_cultivo")["area_sembrada_ha"].sum().reset_index()
    area_25.columns = ["grupo_cultivo", "area_2025"]
    
    area_merged = area_24.merge(area_25, on="grupo_cultivo", how="outer").fillna(0)
    area_merged["variacion_pct"] = area_merged.apply(
        lambda row: _pct_change(row["area_2025"], row["area_2024"]), axis=1)
    area_merged = area_merged.sort_values("area_2025", ascending=False)

    # Tabla
    tabla_data = [["Grupo de Cultivo", "Area 2024 (ha)", "Area 2025 (ha)", "Variacion (%)"]]
    for _, row in area_merged.iterrows():
        tabla_data.append([
            row["grupo_cultivo"],
            f"{row['area_2024']:,.0f}",
            f"{row['area_2025']:,.0f}",
            f"{row['variacion_pct']:+.1f}%"
        ])
    
    t = Table(tabla_data, hAlign="LEFT", colWidths=[6 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
    t.setStyle(_style())
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))

    # Grafica de area por grupo
    fig1 = px.bar(area_merged, x="grupo_cultivo", y=["area_2024", "area_2025"],
                  barmode="group", title="Area cultivada por grupo de cultivo (2024 vs 2025)",
                  labels={"value": "Area (ha)", "variable": "Año"})
    fig1.update_layout(template="plotly_white", height=400,
                      legend=dict(orientation="h", y=1.15))
    
    # Guardar grafica temporal
    img_path = Path("outputs/temp_fig1.png")
    fig1.write_image(img_path, width=800, height=400, scale=2)
    story.append(Image(img_path, width=17 * cm, height=8.5 * cm))
    story.append(Spacer(1, 0.5 * cm))

    # --- SECCION 2: PRODUCCION Y RENDIMIENTO POR GRUPO Y MUNICIPIO ---
    story.append(Paragraph("2. Produccion, rendimiento y variacion por grupo y municipios", h1))
    story.append(Spacer(1, 0.3 * cm))

    # Por grupo de cultivo
    story.append(Paragraph("2.1 Por grupo de cultivo", h2))
    
    prod_24 = df_24.groupby("grupo_cultivo").agg(
        prod_2024=("produccion_t", "sum"),
        area_cos_2024=("area_cosechada_ha", "sum")
    ).reset_index()
    prod_24["rend_2024"] = prod_24["prod_2024"] / prod_24["area_cos_2024"].replace(0, 1)

    prod_25 = df_25.groupby("grupo_cultivo").agg(
        prod_2025=("produccion_t", "sum"),
        area_cos_2025=("area_cosechada_ha", "sum")
    ).reset_index()
    prod_25["rend_2025"] = prod_25["prod_2025"] / prod_25["area_cos_2025"].replace(0, 1)

    prod_merged = prod_24.merge(prod_25, on="grupo_cultivo", how="outer").fillna(0)
    prod_merged["var_prod_pct"] = prod_merged.apply(
        lambda row: _pct_change(row["prod_2025"], row["prod_2024"]), axis=1)
    prod_merged["var_rend_pct"] = prod_merged.apply(
        lambda row: _pct_change(row["rend_2025"], row["rend_2024"]), axis=1)
    prod_merged = prod_merged.sort_values("prod_2025", ascending=False)

    # Tabla de produccion
    tabla_prod = [["Grupo", "Prod 2024 (t)", "Prod 2025 (t)", "Var %",
                   "Rend 2024 (t/ha)", "Rend 2025 (t/ha)", "Var %"]]
    for _, row in prod_merged.iterrows():
        tabla_prod.append([
            row["grupo_cultivo"],
            f"{row['prod_2024']:,.0f}",
            f"{row['prod_2025']:,.0f}",
            f"{row['var_prod_pct']:+.1f}%",
            f"{row['rend_2024']:.2f}",
            f"{row['rend_2025']:.2f}",
            f"{row['var_rend_pct']:+.1f}%"
        ])
    
    t2 = Table(tabla_prod, hAlign="LEFT", 
               colWidths=[3.5 * cm, 2.3 * cm, 2.3 * cm, 2 * cm, 2.3 * cm, 2.3 * cm, 2 * cm])
    t2.setStyle(_style())
    story.append(t2)
    story.append(Spacer(1, 0.5 * cm))

    # Por municipios (top 10)
    story.append(Paragraph("2.2 Top 10 municipios por produccion", h2))
    
    mun_24 = df_24.groupby("municipio").agg(
        prod_2024=("produccion_t", "sum"),
        area_cos_2024=("area_cosechada_ha", "sum")
    ).reset_index()
    mun_24["rend_2024"] = mun_24["prod_2024"] / mun_24["area_cos_2024"].replace(0, 1)

    mun_25 = df_25.groupby("municipio").agg(
        prod_2025=("produccion_t", "sum"),
        area_cos_2025=("area_cosechada_ha", "sum")
    ).reset_index()
    mun_25["rend_2025"] = mun_25["prod_2025"] / mun_25["area_cos_2025"].replace(0, 1)

    mun_merged = mun_24.merge(mun_25, on="municipio", how="outer").fillna(0)
    mun_merged["var_prod_pct"] = mun_merged.apply(
        lambda row: _pct_change(row["prod_2025"], row["prod_2024"]), axis=1)
    mun_merged = mun_merged.sort_values("prod_2025", ascending=False).head(10)

    # Tabla de municipios
    tabla_mun = [["Municipio", "Prod 2024 (t)", "Prod 2025 (t)", "Var %", "Rend 2025 (t/ha)"]]
    for _, row in mun_merged.iterrows():
        tabla_mun.append([
            row["municipio"],
            f"{row['prod_2024']:,.0f}",
            f"{row['prod_2025']:,.0f}",
            f"{row['var_prod_pct']:+.1f}%",
            f"{row['rend_2025']:.2f}"
        ])
    
    t3 = Table(tabla_mun, hAlign="LEFT",
               colWidths=[4 * cm, 3 * cm, 3 * cm, 3 * cm, 3.5 * cm])
    t3.setStyle(_style())
    story.append(t3)
    story.append(Spacer(1, 0.5 * cm))

    # --- FIGURA 1: AREA DE ALIMENTOS POR MUNICIPIOS ---
    story.append(Paragraph("3. Lista de figuras", h1))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Figura 1. Area cultivada de alimentos por municipios (2025)</b>",
                           st_["Normal"]))
    story.append(Spacer(1, 0.3 * cm))

    # Filtrar grupos de alimentos (frutales, hortalizas, cereales, tuberculos)
    alimentos_keywords = ["frutales", "hortalizas", "cereales", "tuberculos", "granos"]
    df_alimentos = df_25[df_25["grupo_cultivo"].str.lower().str.contains("|".join(alimentos_keywords), na=False)]
    
    area_alimentos = df_alimentos.groupby("municipio")["area_sembrada_ha"].sum().reset_index()
    area_alimentos = area_alimentos.sort_values("area_sembrada_ha", ascending=False).head(15)

    fig2 = px.bar(area_alimentos, x="municipio", y="area_sembrada_ha",
                  title="Top 15 municipios - Area de alimentos (2025)",
                  labels={"area_sembrada_ha": "Area (ha)", "municipio": "Municipio"},
                  color_discrete_sequence=["#2E8B57"])
    fig2.update_layout(template="plotly_white", height=400, xaxis_tickangle=-45)
    
    img_path2 = Path("outputs/temp_fig2.png")
    fig2.write_image(img_path2, width=800, height=400, scale=2)
    story.append(Image(img_path2, width=17 * cm, height=8.5 * cm))
    story.append(Spacer(1, 0.5 * cm))

    # Tabla de area de alimentos
    tabla_alim = [["Municipio", "Area 2025 (ha)"]]
    for _, row in area_alimentos.iterrows():
        tabla_alim.append([row["municipio"], f"{row['area_sembrada_ha']:,.0f}"])
    
    t4 = Table(tabla_alim, hAlign="LEFT", colWidths=[6 * cm, 4 * cm])
    t4.setStyle(_style())
    story.append(t4)
    story.append(Spacer(1, 0.5 * cm))

    # --- CIERRE ---
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"Fuente: UPRA - Encuestas de Valuacion Agropecuaria (EVA) 2024-2025. "
        f"Elaborado por {meta.AUTOR} - {meta.CARGO}.",
        ParagraphStyle("Footer", parent=st_["Italic"], fontSize=8, textColor=GRIS)))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    
    # Limpiar imagenes temporales
    img_path.unlink(missing_ok=True)
    img_path2.unlink(missing_ok=True)
    
    return buf.getvalue()


def main() -> None:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    df = pd.read_csv(path, low_memory=False)

    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "informe_tecnico_2024_2025.pdf"

    pdf_bytes = build_informe(df)
    out_path.write_bytes(pdf_bytes)

    print(f"[OK] Informe tecnico generado: {out_path}")
    print(f"     Tamano: {out_path.stat().st_size / 1024:.1f} KB")
    print(f"\nContenido:")
    print(f"  1. Area cultivada por tipo de cultivo (2024-2025)")
    print(f"  2. Produccion y rendimiento por grupo y municipios")
    print(f"  3. Figura 1: Area de alimentos por municipios")


if __name__ == "__main__":
    main()