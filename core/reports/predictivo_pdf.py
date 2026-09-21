"""PDF de proyeccion con escenarios e IC."""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from core.reports.branding import pagina_con_logo, build_con_logo
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image as RLImage, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from core.reports import meta
from core.analytics.forecast import proyectar_estable_con_ic

VERDE = "#2E8B57"
NARANJA = "#DD6B20"
VERDE_RL = colors.HexColor("#2E8B57")


def _style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_RL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
    ])


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()


def _add_png(story, png):
    img = RLImage(io.BytesIO(png))
    w = 16.5 * cm
    h = img.drawHeight * w / img.drawWidth
    img.drawWidth, img.drawHeight = w, h
    story += [img, Spacer(1, 0.4 * cm)]


def _forecast_png(serie, res) -> bytes:
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.plot(serie.index, serie.values, "o-", color=VERDE, lw=2.5, label="Historico")
    anos = serie.index.values
    ultimo = int(anos[-1])
    n_steps = len(res["prediccion"])
    fut = np.arange(ultimo + 1, ultimo + 1 + n_steps)
    ic_bajo = res["escenarios"]["ic_bajo"]
    ic_alto = res["escenarios"]["ic_alto"]
    ax.fill_between(fut, ic_bajo, ic_alto, alpha=0.25, color="#5FA8DC", label="IC 50%")
    ax.plot(fut, res["escenarios"]["tendencial"], "o-", color=NARANJA, lw=2.5,
            label="Tendencial")
    ax.plot(fut, res["escenarios"]["conservador"], "--", color=NARANJA, lw=1.2,
            label="Conservador (P10)")
    ax.plot(fut, res["escenarios"]["optimista"], "--", color=VERDE, lw=1.2,
            label="Optimista (P90)")
    ax.set_ylabel("Produccion (t)", fontsize=9)
    ax.set_title("Proyeccion con intervalos de confianza", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _png(fig)


def build_predictivo_pdf(cultivo, muni, serie, res, horizonte) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, onPage=pagina_con_logo, pagesize=letter, title="Proyeccion Agricola")
    st_ = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=st_["Title"], textColor=VERDE_RL, fontSize=15)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=11, fontSize=9)

    story = [
        Paragraph(f"Proyeccion Agricola: {cultivo}", h1),
        Paragraph(f"Ambito: {muni} | Periodo historico: "
                  f"{int(serie.index.min())}-{int(serie.index.max())} | "
                  f"Horizonte: {horizonte} anos", body),
        Spacer(1, 0.4 * cm),
        Paragraph("<b>Proyeccion oficial (escenario estable)</b>", body),
    ]

    res_estable = proyectar_estable_con_ic(serie, n_steps=horizonte)
    res_ensemble = res

    ultimo = int(serie.index[-1])
    ultimo_v = float(serie.iloc[-1])
    proy_oficial = float(res_estable["prediccion"][-1])
    proy_ref = float(res_ensemble["prediccion"][-1])
    var_pct_oficial = (proy_oficial / ultimo_v - 1) * 100 if ultimo_v else 0
    var_pct_ref = (proy_ref / ultimo_v - 1) * 100 if ultimo_v else 0

    rows = [
        ["Indicador", "Oficial (estable)", "Referencia (ensemble)"],
        ["Modelo", res_estable["ganador"], res_ensemble["ganador"]],
        ["MAPE backtest", "N/A (naive)", f"{res_ensemble['mape']:.1f}%"],
        [f"Proyeccion {ultimo + horizonte}", f"{proy_oficial:,.0f} t", f"{proy_ref:,.0f} t"],
        ["Variacion vs ultimo ano", f"{var_pct_oficial:+.1f}%", f"{var_pct_ref:+.1f}%"],
        [f"IC 50% bajo ({ultimo + horizonte})",
         f"{float(res_estable['escenarios']['ic_bajo'][-1]):,.0f} t",
         f"{float(res_ensemble['escenarios']['ic_bajo'][-1]):,.0f} t"],
        [f"IC 50% alto ({ultimo + horizonte})",
         f"{float(res_estable['escenarios']['ic_alto'][-1]):,.0f} t",
         f"{float(res_ensemble['escenarios']['ic_alto'][-1]):,.0f} t"],
    ]
    t = Table(rows, hAlign="LEFT", colWidths=[5 * cm, 5.5 * cm, 5.5 * cm])
    t.setStyle(_style())
    story += [t, Spacer(1, 0.4 * cm)]

    story.append(Paragraph(
        "<b>Nota metodologica (Gate 3):</b> La proyeccion oficial usa el escenario "
        "estable (naive = ultimo valor) porque el ensemble local no supera al naive "
        "en el holdout 2024-2025 (WAPE mediano 16.5% vs 11.1%). El intervalo de "
        "confianza oficial se ensancha con sqrt(t) (propiedad de random walks). "
        "El ensemble se mantiene como referencia tendencial para series con tendencia real.", body))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("<b>Proyeccion con intervalos</b>", body))
    _add_png(story, _forecast_png(serie, res))

    story.append(Paragraph("<b>Tabla de escenarios</b>", body))
    rows2 = [["Ano", "Conservador (P10)", "Tendencial", "Optimista (P90)",
              "IC 50%"]]
    anos_fut = np.arange(ultimo + 1, ultimo + 1 + horizonte)
    for i, an in enumerate(anos_fut):
        rows2.append([
            str(int(an)),
            f"{res['escenarios']['conservador'][i]:,.0f}",
            f"{res['escenarios']['tendencial'][i]:,.0f}",
            f"{res['escenarios']['optimista'][i]:,.0f}",
            f"{res['escenarios']['ic_bajo'][i]:,.0f} - "
            f"{res['escenarios']['ic_alto'][i]:,.0f}",
        ])
    t2 = Table(rows2, hAlign="LEFT")
    t2.setStyle(_style())
    story += [t2, Spacer(1, 0.4 * cm)]

    story.append(Paragraph("<b>Ranking de modelos (backtest)</b>", body))
    rows3 = [["Modelo", "MAPE (%)"]]
    for r in res["ranking"]:
        marca = "✅" if r is res["ranking"][0] else ""
        rows3.append([r["modelo"]["nombre"] + marca, f"{r['mape']:.1f}"])
    t3 = Table(rows3, hAlign="LEFT")
    t3.setStyle(_style())
    story += [t3, Spacer(1, 0.4 * cm)]

    story.append(Paragraph(
        "<b>Metodologia:</b> Se prueban 7 candidatos (tendencia lineal, "
        "promedio movil 2 y 3 anos, Holt con dos sets de hiperparametros, "
        "naive ultimo valor, y un MLP 3-8-4-1 entrenado desde cero). "
        "Se ocultan los ultimos 2 anos, se entrena con el resto y se mide "
        "MAPE. El de menor error gana el ensemble. La proyeccion oficial "
        "usa naive (ultimo valor) con IC ensanchado con sqrt(t); el ensemble "
        "se muestra como referencia tendencial (AUD-UI-022, Gate 3).", body))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        f"Fuente: UPRA - EVA 2019-2025. {meta.firma()}.",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8)))
    build_con_logo(doc, story)
    return buf.getvalue()
