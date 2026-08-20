"""Reporte PDF formal por municipio con firma profesional."""
from __future__ import annotations

import io

import pandas as pd
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from core.analytics.forecast import proyectar_con_ic
from core.reports import meta
from core.reports.data import (cagr_municipality, filter_municipio,
                               forecast_municipality, kpis, ranking_posicion,
                               top_cultivos, yearly)

VERDE = colors.HexColor("#2E8B57")
NARANJA = colors.HexColor("#DD6B20")
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
    """Pie de pagina profesional en cada hoja."""
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


def _production_chart(f: dict) -> Drawing:
    years = f["years"]
    cats = [str(y) for y in years] + [str(y) for y in f["forecast_years"]]
    hist = list(f["values"]) + [0] * len(f["forecast_years"])
    fore = [0] * len(years) + list(f["forecast_values"])
    d = Drawing(460, 200)
    bc = VerticalBarChart()
    bc.x = 45
    bc.y = 25
    bc.height = 140
    bc.width = 390
    bc.data = [hist, fore]
    bc.categoryAxis.categoryNames = cats
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 7
    bc.valueAxis.valueMin = 0
    bc.valueAxis.labels.fontSize = 7
    bc.barWidth = 14
    bc.bars[0].fillColor = VERDE
    bc.bars[1].fillColor = NARANJA
    d.add(bc)
    return d


def build_municipality_pdf(df: pd.DataFrame, municipio: str) -> bytes:
    df_m = filter_municipio(df, municipio)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title=f"Reporte {municipio}")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE)
    story = []

    story.append(Paragraph("EVA Valle v3.0 - Reporte Agricola Municipal", title))
    story.append(Paragraph(f"<b>Municipio:</b> {municipio} | UPRA 2019-2025",
                           st_["Normal"]))
    story.append(Paragraph(f"<i>{meta.firma()}</i>", st_["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # 1. Indicadores
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

    # 2. Historico anual
    story.append(Paragraph("2. Historico anual", st_["Heading2"]))
    ydata = [["Ano", "Produccion (t)", "Area sembrada (ha)", "Rendimiento (t/ha)"]]
    for _, r in yearly(df_m).iterrows():
        ydata.append([str(int(r["ano"])), f"{r['produccion']:,.0f}",
                      f"{r['area_sembrada']:,.0f}", f"{r['rendimiento']:.2f}"])
    t2 = Table(ydata, hAlign="LEFT")
    t2.setStyle(_style())
    story.append(t2)
    story.append(Spacer(1, 0.4 * cm))

    # 3. Principales cultivos
    story.append(Paragraph("3. Principales cultivos", st_["Heading2"]))
    cdata = [["Cultivo", "Produccion (t)", "% del municipio"]]
    for _, r in top_cultivos(df_m).iterrows():
        cdata.append([r["cultivo"], f"{r['produccion_t']:,.0f}",
                      f"{r['share_pct']:.1f}%"])
    t3 = Table(cdata, hAlign="LEFT")
    t3.setStyle(_style())
    story.append(t3)
    story.append(Spacer(1, 0.5 * cm))

    # 4. Proyeccion con seleccion automatica de modelo (motor v2)
    nota_proy = "Proyeccion basada en tendencia lineal historica."
    serie = pd.Series({int(r["ano"]): float(r["produccion"])
                       for _, r in yearly(df_m).iterrows()}).sort_index()
    res_fc = proyectar_con_ic(serie, n_steps=3) if len(serie) >= 4 else {}
    if res_fc.get("modelo") is not None:
        ultimo = int(serie.index[-1])
        ultimo_v = float(serie.iloc[-1])
        anos_fut = list(range(ultimo + 1, ultimo + 4))
        f = {"years": [int(y) for y in serie.index],
             "values": [float(v) for v in serie.values],
             "forecast_years": anos_fut,
             "forecast_values": [float(v)
                                 for v in res_fc["escenarios"]["tendencial"]]}
        fy = anos_fut[0]
        fv = float(res_fc["escenarios"]["tendencial"][0])
        var = (fv / ultimo_v - 1) * 100 if ultimo_v else 0.0
        mape = float(res_fc["mape"])
        nivel = "alta" if mape < 10 else ("moderada" if mape < 20 else "baja")
        nota_proy = ("Proyeccion con seleccion automatica de modelo por "
                     "backtesting (MAPE).")
        story.append(Paragraph(f"4. Proyeccion de produccion {fy}-{anos_fut[-1]}",
                               st_["Heading2"]))
        story.append(_production_chart(f))
        story.append(Paragraph(
            "<font color='#2E8B57'>Verde</font> = historico | "
            "<font color='#DD6B20'>Naranja</font> = proyeccion (modelo ganador)",
            st_["Italic"]))
        story.append(Spacer(1, 0.2 * cm))
        signo = "+" if var >= 0 else ""
        story.append(Paragraph(
            f"Produccion proyectada {fy}: <b>{fv:,.0f} t</b> "
            f"({signo}{var:.1f}% vs {ultimo}). Modelo: <b>{res_fc['ganador']}</b> | "
            f"MAPE backtest: <b>{mape:.1f}%</b> | Credibilidad: <b>{nivel}</b>.",
            st_["Normal"]))
        rows = [["Ano", "Conservador (P10)", "Tendencial", "Optimista (P90)"]]
        for i, an in enumerate(anos_fut):
            rows.append([str(an),
                         f"{float(res_fc['escenarios']['conservador'][i]):,.0f}",
                         f"{float(res_fc['escenarios']['tendencial'][i]):,.0f}",
                         f"{float(res_fc['escenarios']['optimista'][i]):,.0f}"])
        t4 = Table(rows, hAlign="LEFT")
        t4.setStyle(_style())
        story += [Spacer(1, 0.2 * cm), t4, Spacer(1, 0.4 * cm)]
    else:
        f = forecast_municipality(df_m)
        if f:
            fy = f["forecast_years"][0]
            fv = f["forecast_values"][0]
            last_v = f["values"][-1]
            var = (fv / last_v - 1) * 100 if last_v else 0.0
            story.append(Paragraph(f"4. Proyeccion de produccion {fy}",
                                   st_["Heading2"]))
            story.append(_production_chart(f))
            story.append(Paragraph(
                "<font color='#2E8B57'>Verde</font> = historico | "
                "<font color='#DD6B20'>Naranja</font> = proyeccion tendencial",
                st_["Italic"]))
            story.append(Spacer(1, 0.2 * cm))
            signo = "+" if var >= 0 else ""
            story.append(Paragraph(
                f"Produccion proyectada {fy}: <b>{fv:,.0f} t</b> "
                f"({signo}{var:.1f}% vs {f['years'][-1]}).", st_["Normal"]))
            story.append(Spacer(1, 0.4 * cm))

    # 5. CAGR por cultivo
    story.append(Paragraph("5. Crecimiento anual compuesto (CAGR) por cultivo",
                           st_["Heading2"]))
    cagr = cagr_municipality(df_m)
    if not cagr.empty:
        gdata = [["Cultivo", "Prod. inicio (t)", "Prod. final (t)", "CAGR %"]]
        for _, r in cagr.head(8).iterrows():
            gdata.append([r["cultivo"], f"{r['prod_inicio']:,.0f}",
                          f"{r['prod_fin']:,.0f}", f"{r['cagr_pct']:.1f}%"])
        t5 = Table(gdata, hAlign="LEFT")
        t5.setStyle(_style())
        story.append(t5)
    else:
        story.append(Paragraph(
            "Datos insuficientes para calcular CAGR por cultivo.", st_["Italic"]))

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        f"Fuente: {meta.FUENTE}. {nota_proy} {meta.firma()}.", st_["Italic"]))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
