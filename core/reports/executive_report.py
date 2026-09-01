"""Resumen Ejecutivo PDF - Valle del Cauca 2019-2025 (3 paginas, estandar UPRA/CEPAL)."""
from __future__ import annotations

import io

import pandas as pd
from core.reports.branding import pagina_con_logo, build_con_logo
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from core.reports import meta

VERDE = colors.HexColor("#2E8B57")
GRIS = colors.HexColor("#4A5568")


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
    pagina_con_logo(canvas, doc)
    w, _ = letter
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.line(36, 42, w - 36, 42)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(36, 32,
        f"{meta.firma()} | EVA Valle v3.0 | "
        f"Fuente: UPRA - Encuestas de Valuacion Agropecuaria (EVA) 2019-2025")
    canvas.drawRightString(w - 36, 32, f"Pagina {doc.page}")
    canvas.restoreState()


def _pct(new, old):
    return ((new - old) / old) * 100 if old else 0.0


def _gini(values) -> float:
    v = sorted(float(x) for x in values if x > 0)
    n = len(v)
    if n == 0 or sum(v) == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(v))
    return (2 * cum) / (n * sum(v)) - (n + 1) / n


def _hhi(shares_pct) -> float:
    return sum((s / 100.0) ** 2 for s in shares_pct) * 10000


def _metrics_cultivos(sub: pd.DataFrame):
    prod = sub.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    tot = prod.sum()
    shares = prod / tot * 100
    cum = shares.cumsum()
    n80 = int((cum < 80).sum() + 1)
    return prod, shares, _hhi(shares), _gini(prod.values), n80


def _pareto(sub: pd.DataFrame, titulo: str) -> Drawing:
    prod = sub.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    top = prod.head(8)
    otros = prod[8:].sum()
    labels = list(top.index) + (["Otros"] if otros > 0 else [])
    vals = list(top.values) + ([otros] if otros > 0 else [])
    tot = sum(vals)
    pcts = [v / tot * 100 for v in vals]
    d = Drawing(230, 140)
    bc = HorizontalBarChart()
    bc.x = 62
    bc.y = 12
    bc.height = 115
    bc.width = 155
    bc.data = [pcts]
    bc.categoryAxis.categoryNames = labels
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 6
    bc.valueAxis.labels.fontSize = 6
    bc.bars[0].fillColor = VERDE
    bc.barWidth = 8
    d.add(bc)
    return d


def build_executive_pdf(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, onPage=pagina_con_logo, pagesize=letter,
                            title="Resumen Ejecutivo - Valle del Cauca")
    st_ = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=st_["Title"], textColor=VERDE, fontSize=18)
    h2 = ParagraphStyle("H2", parent=st_["Heading2"], textColor=VERDE,
                        spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=11, fontSize=9)
    story = []

    story.append(Paragraph("Resumen Ejecutivo - Valle del Cauca", h1))

    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    ult, ant = anos[-1], anos[-2]
    d_ult = df[df["ano"] == ult]
    d_ant = df[df["ano"] == ant]
    p_ult = d_ult["produccion_t"].sum()
    p_ant = d_ant["produccion_t"].sum()
    a_ult = d_ult["area_sembrada_ha"].sum()
    a_ant = d_ant["area_sembrada_ha"].sum()
    c_ult = d_ult["area_cosechada_ha"].sum()
    c_ant = d_ant["area_cosechada_ha"].sum()
    r_ult = p_ult / c_ult if c_ult else 0
    r_ant = p_ant / c_ant if c_ant else 0

    # --- 1. Panorama general ---
    d1 = [["Indicador", "Valor", "Var. vs ano anterior"],
          ["Produccion", f"{p_ult:,.0f} t", f"{_pct(p_ult, p_ant):+.1f}%"],
          ["Area", f"{a_ult:,.0f} ha", f"{_pct(a_ult, a_ant):+.1f}%"],
          ["Rendimiento", f"{r_ult:.1f} t/ha", f"{_pct(r_ult, r_ant):+.1f}%"],
          ["Municipios", str(df["municipio"].nunique()), "-"],
          ["Cultivos", str(df["cultivo"].nunique()), "-"]]
    t1 = Table(d1, hAlign="LEFT", colWidths=[5*cm, 5*cm, 5*cm])
    t1.setStyle(_style())
    story.append(KeepTogether([
        Paragraph("1. Panorama general", h2), t1, Spacer(1, 0.3*cm)]))

    # --- 2. Concentracion con cana vs sin cana ---
    _, sh_con, hhi_con, gini_con, n80_con = _metrics_cultivos(df)
    df_sin = df[df["cultivo"] != "Caña"]
    _, sh_sin, hhi_sin, gini_sin, n80_sin = _metrics_cultivos(df_sin)
    d2 = [["Indicador", "Con cana", "Sin cana"],
          ["HHI", f"{hhi_con:,.0f}", f"{hhi_sin:,.0f}"],
          ["Gini", f"{gini_con:.3f}", f"{gini_sin:.3f}"],
          ["Top 1 (%)", f"{sh_con.iloc[0]:.1f} ({sh_con.index[0]})",
           f"{sh_sin.iloc[0]:.1f} ({sh_sin.index[0]})"],
          ["Cultivos que explican 80%", str(n80_con), str(n80_sin)]]
    t2 = Table(d2, hAlign="LEFT", colWidths=[6*cm, 4.5*cm, 4.5*cm])
    t2.setStyle(_style())
    p_con = _pareto(df, "con")
    p_sin = _pareto(df_sin, "sin")
    tp = Table([[Paragraph("<b>Pareto CON cana (%)</b>", body),
                 Paragraph("<b>Pareto SIN cana (%)</b>", body)],
                [p_con, p_sin]], colWidths=[8*cm, 8*cm])
    story.append(KeepTogether([
        Paragraph("2. Concentracion productiva: con cana vs sin cana", h2),
        t2, Spacer(1, 0.2*cm), tp, Spacer(1, 0.3*cm)]))

    # --- 3. Distribucion territorial ---
    mun = df.groupby("municipio")["produccion_t"].sum().sort_values(ascending=False)
    sh_m = mun / mun.sum() * 100
    hhi_t = _hhi(sh_m)
    gini_t = _gini(mun.values)
    n = len(mun)
    t3 = n // 3
    d3 = [["Indicador", "Valor"],
          ["Gini territorial", f"{gini_t:.2f}"],
          ["HHI territorial", f"{hhi_t:,.0f}"],
          ["Municipio lider", f"{mun.index[0]} ({sh_m.iloc[0]:.1f}%)"],
          ["Lider / Intermedio / Rezagado", f"{t3} / {t3} / {n - 2*t3}"]]
    t3b = Table(d3, hAlign="LEFT", colWidths=[7*cm, 7*cm])
    t3b.setStyle(_style())
    story.append(KeepTogether([
        Paragraph("3. Distribucion territorial", h2), t3b, Spacer(1, 0.3*cm)]))

    # --- 4. Tendencias y dinamica (3 columnas por tabla, sin duplicados) ---
    tend = (df.groupby("ano")
            .agg(prod=("produccion_t", "sum"), cos=("area_cosechada_ha", "sum"))
            .reset_index())
    d4 = [["Ano", "Produccion (t)", "Rendimiento (t/ha)"]]
    for _, r in tend.iterrows():
        rend = r["prod"] / r["cos"] if r["cos"] else 0
        d4.append([str(int(r["ano"])), f"{r['prod']:,.0f}", f"{rend:.2f}"])
    t4 = Table(d4, hAlign="LEFT", colWidths=[3*cm, 5*cm, 5*cm])
    t4.setStyle(_style())
    story.append(KeepTogether([
        Paragraph(f"4. Tendencias y dinamica ({anos[0]}-{ult})", h2),
        t4, Spacer(1, 0.2*cm)]))

    p_ini = df[df["ano"] == anos[0]].groupby("cultivo")["produccion_t"].sum()
    p_fin = df[df["ano"] == ult].groupby("cultivo")["produccion_t"].sum()
    base = pd.DataFrame({"ini": p_ini, "fin": p_fin}).dropna()
    base = base[base["ini"] >= 1000]
    base["cagr"] = ((base["fin"] / base["ini"]) ** (1 / (ult - anos[0])) - 1) * 100
    crecen = base.sort_values("cagr", ascending=False).head(3)
    declinan = base.sort_values("cagr").head(3)
    d4b = [["Dinamica", "Cultivo", "CAGR"]]
    for c, r in crecen.iterrows():
        d4b.append(["Crecen", str(c), f"+{r['cagr']:.1f}%"])
    for c, r in declinan.iterrows():
        d4b.append(["Declinan", str(c), f"{r['cagr']:.1f}%"])
    t4b = Table(d4b, hAlign="LEFT", colWidths=[3*cm, 9*cm, 3*cm])
    t4b.setStyle(_style())
    story.append(KeepTogether([t4b, Spacer(1, 0.3*cm)]))

    # --- 5. Calidad y confiabilidad del dato ---
    total_reg = len(df)
    anom = (df["area_cosechada_ha"] > df["area_sembrada_ha"]).sum()
    vac = df[["produccion_t", "area_sembrada_ha", "area_cosechada_ha"]].isna().any(axis=1).sum()
    d5 = [["Aspecto", "Detalle"],
          ["Fuente", "UPRA - EVA (autodeclaracion municipal)"],
          ["Cobertura", f"{df['municipio'].nunique()} municipios, {anos[0]}-{ult}"],
          ["Registros", f"{total_reg:,}"],
          ["Anomalias (cosechada > sembrada)", f"{anom/total_reg*100:.2f}%"],
          ["Vacios", f"{vac/total_reg*100:.1f}%"]]
    t5 = Table(d5, hAlign="LEFT", colWidths=[6*cm, 9*cm])
    t5.setStyle(_style())
    story.append(KeepTogether([
        Paragraph("5. Calidad y confiabilidad del dato", h2), t5, Spacer(1, 0.3*cm)]))

    # --- 6. Hallazgos clave ---
    hall = [
        f"Cana concentra {sh_con.iloc[0]:.1f}% de la produccion departamental.",
        f"Concentracion productiva: Gini={gini_con:.2f} (por cultivo).",
        f"{crecen.index[0]} es el motor de crecimiento (CAGR +{crecen['cagr'].iloc[0]:.1f}%).",
        f"{declinan.index[0]} muestra el mayor declive (CAGR {declinan['cagr'].iloc[0]:.1f}%).",
        f"Produccion {ult} vs {ant}: {_pct(p_ult, p_ant):+.1f}%.",
    ]
    story.append(Paragraph("6. Hallazgos clave", h2))
    for h in hall:
        story.append(Paragraph(f"- {h}", body))

    # --- 7. Recomendaciones ---
    story.append(Paragraph("7. Recomendaciones", h2))
    recs = [
        ("Diversificacion productiva.", f"Con cana, HHI={hhi_con:,.0f} (monocultivo). "
         f"Sin cana, HHI={hhi_sin:,.0f}: hay base para diversificar hacia cultivos de mayor valor."),
        ("Priorizacion territorial.", f"Gini territorial={gini_t:.2f}: la produccion se "
         f"concentra en pocos municipios ({mun.index[0]} lidera con {sh_m.iloc[0]:.1f}%). "
         f"Focalizar inversion en municipios intermedios/rezagados."),
        ("Separar lectura cana vs resto.", "Reportar siempre ambos escenarios: la cana domina "
         "el tonelaje, pero la economia agricola no-canera tiene dinamica propia (frutas, exportacion)."),
        ("Mejora de calidad del dato.", "Declarar anomalias (area cosechada > sembrada) y vacios; "
         "validar con teledeteccion o aforos en proximos ciclos."),
    ]
    for titulo, det in recs:
        story.append(Paragraph(f"<b>{titulo}</b> {det}", body))
        story.append(Spacer(1, 0.2*cm))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        f"Fuente: UPRA - Encuestas de Valuacion Agropecuaria (EVA) {anos[0]}-{ult}. "
        f"Recomendaciones generadas automaticamente, sujetas a validacion de experto. "
        f"Elaborado por {meta.AUTOR} - {meta.CARGO}.",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8, textColor=GRIS)))

    build_con_logo(doc, story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
