"""Predictivo v2: forecast robusto (numpy puro) + ML existente."""
from pathlib import Path

# ---------- 1) MOTOR DE FORECASTING (numpy puro, sin statsmodels) ----------
FORECAST = '''"""Motor de forecasting robusto para series agricolas cortas (n>=4).

Tres modelos compiten por serie; el backtesting elige el mejor (menor MAPE).
Devuelve proyeccion con intervalos de confianza por percentiles de residuos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _preparar(serie: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    s = serie.dropna().astype(float).values
    t = np.arange(len(s))
    return t, s


def modelo_lineal(t, s):
    if len(t) < 2 or s.std() == 0:
        return None
    b, a = np.polyfit(t, s, 1)
    fitted = a + b * t
    return {"nombre": "Tendencia lineal", "a": a, "b": b, "fitted": fitted}


def modelo_promedio(t, s, ventana: int = 3):
    if len(s) < ventana:
        return None
    fitted = np.full_like(s, np.nan, dtype=float)
    for i in range(ventana, len(s)):
        fitted[i] = s[i - ventana:i].mean()
    # El pronostico fuera de muestra es el promedio de los ultimos <ventana> valores
    return {"nombre": f"Promedio movil {ventana}A", "ventana": ventana,
            "fitted": fitted, "last_mean": float(s[-ventana:].mean())}


def modelo_holt(t, s, alpha: float = 0.3, beta: float = 0.1):
    if len(t) < 3:
        return None
    L = float(s[0])
    T = float(s[1] - s[0]) if len(s) > 1 else 0.0
    fitted = np.empty_like(s, dtype=float)
    fitted[0] = L
    for i in range(1, len(s)):
        L_new = alpha * s[i] + (1 - alpha) * (L + T)
        T_new = beta * (L_new - L) + (1 - beta) * T
        L, T = L_new, T_new
        fitted[i] = L + T if i < len(s) - 1 else L
    return {"nombre": "Suavizado exponencial (Holt)", "alpha": alpha, "beta": beta,
            "L": L, "T": T, "fitted": fitted}


def _proyectar(modelo, n_steps: int) -> np.ndarray:
    if modelo is None:
        return np.full(n_steps, np.nan)
    if modelo["nombre"] == "Tendencia lineal":
        t0 = int(modelo["fitted"].shape[0] if hasattr(modelo["fitted"], "shape")
                 else len(modelo["fitted"]))
        t_future = np.arange(t0, t0 + n_steps)
        return modelo["a"] + modelo["b"] * t_future
    if modelo["nombre"].startswith("Promedio movil"):
        return np.full(n_steps, modelo["last_mean"])
    # Holt
    out = np.empty(n_steps)
    L, T = modelo["L"], modelo["T"]
    for i in range(n_steps):
        L = L + T
        out[i] = L
    return out


def _mape(real: np.ndarray, pred: np.ndarray) -> float:
    mask = real > 0
    if mask.sum() == 0:
        return np.inf
    return float(np.mean(np.abs((real[mask] - pred[mask]) / real[mask])) * 100)


def backtest(serie: pd.Series, n_out: int = 2) -> list[dict]:
    """Oculta los ultimos n_out valores, entrena y mide MAPE por modelo."""
    t, s = _preparar(serie)
    if len(s) - n_out < 3:
        return []
    t_train, s_train = t[:-n_out], s[:-n_out]
    s_real = s[-n_out:]
    candidatos = [
        modelo_lineal(t_train, s_train),
        modelo_promedio(t_train, s_train, 2),
        modelo_promedio(t_train, s_train, 3),
        modelo_holt(t_train, s_train, 0.3, 0.1),
        modelo_holt(t_train, s_train, 0.5, 0.2),
    ]
    resultados = []
    for m in candidatos:
        if m is None:
            continue
        fitted = m["fitted"]
        if np.all(np.isnan(fitted)):
            continue
        # Para comparar, necesitamos el pronostico de los n_out pasos fuera
        # Usamos el valor proyectado desde el final del entrenamiento
        # Lineal y Holt proyectan; Promedio usa last_mean
        pred = _proyectar(m, n_out)
        if np.any(np.isnan(pred)):
            continue
        mape = _mape(s_real, pred)
        residuos = s_train[~np.isnan(fitted)] - fitted[~np.isnan(fitted)]
        resultados.append({
            "modelo": m, "mape": mape,
            "residuos": residuos if len(residuos) > 0 else np.array([0.0]),
        })
    return resultados


def elegir_mejor(serie: pd.Series, n_out: int = 2) -> dict:
    """Elige el modelo con menor MAPE y lo reentrena con la serie completa."""
    bt = backtest(serie, n_out)
    if not bt:
        return {"modelo": None, "mape": np.inf, "residuos": np.array([0.0]),
                "ganador": "Datos insuficientes"}
    mejor = min(bt, key=lambda x: x["mape"])
    t_full, s_full = _preparar(serie)
    nombre = mejor["modelo"]["nombre"]
    # Reentrenar con toda la serie
    if nombre == "Tendencia lineal":
        modelo_full = modelo_lineal(t_full, s_full)
    elif nombre.startswith("Promedio movil"):
        modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])
    else:
        modelo_full = modelo_holt(t_full, s_full,
                                  mejor["modelo"]["alpha"],
                                  mejor["modelo"]["beta"])
    return {
        "modelo": modelo_full,
        "mape": mejor["mape"],
        "residuos": mejor["residuos"],
        "ganador": nombre,
        "ranking": sorted(bt, key=lambda x: x["mape"]),
    }


def proyectar_con_ic(serie: pd.Series, n_steps: int = 3,
                     niveles: tuple = (0.10, 0.25, 0.75, 0.90)) -> dict:
    res = elegir_mejor(serie)
    if res["modelo"] is None:
        return res
    pred = _proyectar(res["modelo"], n_steps)
    residuos = res["residuos"]
    cuantiles = {f"P{int(p*100)}": float(np.quantile(residuos, p)) for p in niveles}
    escenarios = {
        "conservador": pred + cuantiles["P10"],
        "tendencial": pred,
        "optimista": pred + cuantiles["P90"],
        "ic_bajo": pred + cuantiles["P25"],
        "ic_alto": pred + cuantiles["P75"],
    }
    return {**res, "prediccion": pred, "escenarios": escenarios, "cuantiles": cuantiles}
'''

Path("core/analytics/forecast.py").write_text(FORECAST, encoding="utf-8")
print("[OK] core/analytics/forecast.py creado (motor numpy puro)")

# ---------- 2) PAGINA: Predictivo v2 ----------
PAGE = '''"""Pagina 4: Predictivo v2 (forecast robusto + ML)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.analytics.forecast import elegir_mejor, proyectar_con_ic
from core.reports.predictivo_pdf import build_predictivo_pdf
from ui.components.loading_states import render_empty_state
from ui.services.error_handler import run_safe

st.set_page_config(page_title="Predictivo | EVA Valle", page_icon="\\U0001F916", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def main() -> None:
    st.title("\\U0001F916 Analisis Predictivo")
    st.caption("Proyeccion 2026-2028 con seleccion automatica de modelo y backtesting")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    # ---------- SELECTORES ----------
    c1, c2, c3 = st.columns(3)
    with c1:
        cultivos = (df.groupby("cultivo")["produccion_t"].sum()
                    .sort_values(ascending=False).index.tolist())
        cultivo = st.selectbox("Cultivo", cultivos)
    with c2:
        munis = ["Todo el departamento"] + sorted(df["municipio"].unique().tolist())
        muni = st.selectbox("Municipio", munis)
    with c3:
        horizonte = st.slider("Horizonte (anos)", 1, 5, 3)

    df_c = df[df["cultivo"] == cultivo].copy()
    if muni != "Todo el departamento":
        df_c = df_c[df_c["municipio"] == muni]
    if df_c.empty:
        st.warning("Sin datos para esa combinacion.")
        return

    # Serie anual
    serie = df_c.groupby("ano")["produccion_t"].sum().sort_index()
    if len(serie) < 4:
        st.error("Serie demasiado corta (se necesitan al menos 4 anos).")
        return

    # ---------- PROYECCION ----------
    res = proyectar_con_ic(serie, n_steps=horizonte)
    modelo = res["modelo"]
    if modelo is None:
        st.error("No se pudo ajustar ningun modelo.")
        return

    # KPIs
    ultimo = int(serie.index[-1])
    ultimo_v = float(serie.iloc[-1])
    proy_base = float(res["prediccion"][-1])
    var_pct = (proy_base / ultimo_v - 1) * 100
    mape = res["mape"]

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(f"Ultimo ano ({ultimo})", f"{ultimo_v:,.0f} t")
    k2.metric(f"Proyeccion {ultimo + horizonte}", f"{proy_base:,.0f} t",
              delta=f"{var_pct:+.1f}%")
    k3.metric("MAPE backtest", f"{mape:.1f}%",
              help="Error medio al predecir los ultimos 2 anos desde el resto")
    k4.metric("Modelo ganador", res["ganador"].replace("Suavizado exponencial ", ""))
    k5.metric("Conservador", f"{float(res['escenarios']['conservador'][-1]):,.0f} t")

    # ---------- GRAFICO ----------
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie.index, y=serie.values, mode="lines+markers",
                             name="Historico", line=dict(color="#2E8B57", width=3)))
    anos_fut = np.arange(ultimo + 1, ultimo + 1 + horizonte)
    # IC
    fig.add_trace(go.Scatter(
        x=np.concatenate([anos_fut, anos_fut[::-1]]),
        y=np.concatenate([res["escenarios"]["ic_alto"],
                          res["escenarios"]["ic_bajo"][::-1]]),
        fill="toself", fillcolor="rgba(94,168,220,0.25)",
        line=dict(color="rgba(0,0,0,0)"), name="IC 50%", showlegend=True))
    # Escenarios
    fig.add_trace(go.Scatter(x=anos_fut, y=res["escenarios"]["conservador"],
                             mode="lines", name="Conservador (P10)",
                             line=dict(color="#DD6B20", dash="dot", width=1.5)))
    fig.add_trace(go.Scatter(x=anos_fut, y=res["escenarios"]["tendencial"],
                             mode="lines+markers", name="Tendencial",
                             line=dict(color="#DD6B20", width=3)))
    fig.add_trace(go.Scatter(x=anos_fut, y=res["escenarios"]["optimista"],
                             mode="lines", name="Optimista (P90)",
                             line=dict(color="#2E8B57", dash="dot", width=1.5)))
    # Union historico-proyeccion
    fig.add_trace(go.Scatter(
        x=[ultimo, anos_fut[0]],
        y=[ultimo_v, res["escenarios"]["tendencial"][0]],
        mode="lines", line=dict(color="#DD6B20", width=3, dash="dash"),
        showlegend=False))
    fig.update_layout(template="plotly_white", height=480,
                      title=f"{cultivo} en {muni} - Proyeccion con IC",
                      yaxis_title="Produccion (t)")
    st.plotly_chart(fig, use_container_width=True)

    # ---------- TABLA DE ESCENARIOS ----------
    rows = []
    for i, an in enumerate(anos_fut):
        rows.append({
            "Ano": int(an),
            "Conservador (P10)": f"{res['escenarios']['conservador'][i]:,.0f}",
            "Tendencial": f"{res['escenarios']['tendencial'][i]:,.0f}",
            "Optimista (P90)": f"{res['escenarios']['optimista'][i]:,.0f}",
            "IC 50%": f"{res['escenarios']['ic_bajo'][i]:,.0f} - "
                      f"{res['escenarios']['ic_alto'][i]:,.0f}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Interpretacion automatica
    if mape < 10:
        nivel = "alta"
    elif mape < 20:
        nivel = "moderada"
    else:
        nivel = "baja"
    st.info(f"**Interpretacion:** El modelo **{res['ganador']}** fue seleccionado "
            f"automaticamente por tener el menor MAPE ({mape:.1f}%) al predecir "
            f"los ultimos 2 anos. Credibilidad del forecast: **{nivel}**. "
            f"Escenario tendencial: {proy_base:,.0f} t en {int(anos_fut[-1])} "
            f"({var_pct:+.1f}% vs {ultimo}).")

    # ---------- RANKING DE MODELOS (backtest) ----------
    with st.expander("🔬 Comparativa de modelos (backtest)"):
        st.caption("Se ocultan los ultimos 2 anos, se entrena cada modelo con "
                   "el resto y se mide el error al predecirlos. "
                   "El que menos se equivoca, gana.")
        filas = []
        for r in res["ranking"]:
            filas.append({
                "Modelo": r["modelo"]["nombre"],
                "MAPE (%)": f"{r['mape']:.1f}",
                "Ganador": "✅" if r is res["ranking"][0] else "",
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    # ---------- EXPORTACION ----------
    st.markdown("---")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "⬇️ Descargar proyeccion (CSV)",
            data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
            file_name=f"proyeccion_{cultivo}_{muni}.csv".lower().replace(" ", "_"),
            mime="text/csv", use_container_width=True)
    with d2:
        st.download_button(
            "⬇️ Descargar proyeccion (PDF)",
            data=build_predictivo_pdf(cultivo, muni, serie, res, horizonte),
            file_name=f"proyeccion_{cultivo}_{muni}.pdf".lower().replace(" ", "_"),
            mime="application/pdf", use_container_width=True)


run_safe(main)
'''

Path("ui/pages/4_Predictivo.py").write_text(PAGE, encoding="utf-8")
print("[OK] ui/pages/4_Predictivo.py reescrita (v2)")

# ---------- 3) PDF DE PROYECCION ----------
PDFMOD = '''"""PDF de proyeccion con escenarios e IC."""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image as RLImage, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from core.reports import meta

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
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Proyeccion Agricola")
    st_ = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=st_["Title"], textColor=VERDE_RL, fontSize=15)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=11, fontSize=9)

    story = [
        Paragraph(f"Proyeccion Agricola: {cultivo}", h1),
        Paragraph(f"Ambito: {muni} | Periodo historico: "
                  f"{int(serie.index.min())}-{int(serie.index.max())} | "
                  f"Horizonte: {horizonte} anos", body),
        Spacer(1, 0.4 * cm),
        Paragraph("<b>Resultado del modelo</b>", body),
    ]

    mape = res["mape"]
    ultimo = int(serie.index[-1])
    ultimo_v = float(serie.iloc[-1])
    proy_final = float(res["prediccion"][-1])
    var_pct = (proy_final / ultimo_v - 1) * 100 if ultimo_v else 0
    nivel = "alta" if mape < 10 else ("moderada" if mape < 20 else "baja")

    rows = [
        ["Indicador", "Valor"],
        ["Modelo seleccionado (menor MAPE)", res["ganador"]],
        ["MAPE del backtest", f"{mape:.1f}%"],
        ["Credibilidad del forecast", nivel.capitalize()],
        [f"Ultimo ano registrado ({ultimo})", f"{ultimo_v:,.0f} t"],
        [f"Proyeccion tendencial ({ultimo + horizonte})", f"{proy_final:,.0f} t"],
        ["Variacion proyectada", f"{var_pct:+.1f}%"],
        [f"Escenario conservador (P10) {ultimo + horizonte}",
         f"{float(res['escenarios']['conservador'][-1]):,.0f} t"],
        [f"Escenario optimista (P90) {ultimo + horizonte}",
         f"{float(res['escenarios']['optimista'][-1]):,.0f} t"],
    ]
    t = Table(rows, hAlign="LEFT", colWidths=[9 * cm, 7 * cm])
    t.setStyle(_style())
    story += [t, Spacer(1, 0.4 * cm)]

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
        "<b>Metodologia:</b> Se prueban 5 candidatos (tendencia lineal, "
        "promedio movil 2 y 3 anos, Holt con dos sets de hiperparametros). "
        "Se ocultan los ultimos 2 anos, se entrena con el resto y se mide "
        "MAPE. El de menor error gana y se reentrena con toda la serie para "
        "proyectar. Los intervalos son percentiles de los residuos del "
        "entrenamiento (P10/P25/P75/P90).", body))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        f"Fuente: UPRA - EVA 2019-2025. {meta.firma()}.",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8)))
    doc.build(story)
    return buf.getvalue()
'''

Path("core/reports/predictivo_pdf.py").write_text(PDFMOD, encoding="utf-8")
print("[OK] core/reports/predictivo_pdf.py creado")

print()
print("=" * 70)
print("Predictivo v2 listo. Reinicia Streamlit y prueba:")
print("  - Cana en Todo el departamento (debe dar ~572k t en 2026)")
print("  - Platano en Sevilla (debe dar ~82k t en 2026, crecimiento moderado)")
print("  - Mira el expander 'Comparativa de modelos' para ver el backtest")
print("  - Descarga el PDF con escenarios e IC")
print("=" * 70)