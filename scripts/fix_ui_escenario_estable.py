"""AUD-UI-022 v3: UI dual oficial=estable(naive) / referencia=ensemble(tendencial).

v3: el bloque de ranking se ancla con regex entre bordes sin emojis (el ancla
v2 contenia mojibake del codepage de cmd y no matcheaba el UTF-8 real).
v2: funcion nueva AGREGADA al final de forecast.py (no inyectada en medio de
proyectar_con_ic), IC ensanchado con sqrt(t), mape=NaN, imports al tope,
autotest de regresion sobre proyectar_con_ic.
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FC = RAIZ / "core" / "analytics" / "forecast.py"
UI = RAIZ / "ui" / "pages" / "4_Predictivo.py"
PDF = RAIZ / "core" / "reports" / "predictivo_pdf.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

# ========== Hunk 1: forecast.py - agregar funcion al final ==========
NUEVA_FUNCION_ESTABLE = '''

def proyectar_estable_con_ic(serie: pd.Series, n_steps: int = 3) -> dict:
    """AUD-UI-022: proyeccion oficial = naive (ultimo valor) con IC de residuos.

    La regla pre-registrada del Gate 3 activa este escenario como oficial.
    El ensemble local queda como referencia tendencial.
    El IC se ensancha con sqrt(t) (propiedad de random walks).
    """
    s = serie.dropna().astype(float).values
    if len(s) < 3:
        return {"modelo": None, "mape": np.nan, "ganador": "Datos insuficientes",
                "prediccion": np.full(n_steps, np.nan),
                "escenarios": {"conservador": np.full(n_steps, np.nan),
                               "tendencial": np.full(n_steps, np.nan),
                               "optimista": np.full(n_steps, np.nan),
                               "ic_bajo": np.full(n_steps, np.nan),
                               "ic_alto": np.full(n_steps, np.nan)}}

    ultimo = float(s[-1])
    residuos = np.diff(s)
    p10, p25, p75, p90 = np.percentile(residuos, [10, 25, 75, 90])

    # Ensanchamiento de incertidumbre (random walk: desviacion crece con sqrt(t))
    factores = np.sqrt(np.arange(1, n_steps + 1))

    prediccion = np.full(n_steps, ultimo)
    return {
        "modelo": {"nombre": "Naive (ultimo valor)", "ultimo": ultimo},
        "mape": np.nan,  # No aplica para naive por construccion
        "ganador": "Escenario estable (naive)",
        "prediccion": prediccion,
        "escenarios": {
            "conservador": prediccion + p10 * factores,
            "tendencial": prediccion,
            "optimista": prediccion + p90 * factores,
            "ic_bajo": prediccion + p25 * factores,
            "ic_alto": prediccion + p75 * factores,
        },
        "residuos": residuos,
    }
'''

# ========== Hunk 2: 4_Predictivo.py - UI dual ==========
VIEJO_IMPORT_FC = 'from core.analytics.forecast import elegir_mejor, proyectar_con_ic'
NUEVO_IMPORT_FC = ('from core.analytics.forecast import (elegir_mejor, proyectar_con_ic,\n'
                   '                                      proyectar_estable_con_ic)')

VIEJO_CACHE = '''@st.cache_data(ttl=3600, show_spinner="Calculando proyeccion (ensemble + MLP)...")
def _proyectar_cacheado(serie: pd.Series, horizonte: int) -> dict:
    return proyectar_con_ic(serie, n_steps=horizonte)'''

NUEVO_CACHE = '''@st.cache_data(ttl=3600, show_spinner="Calculando proyeccion (estable + tendencial)...")
def _proyectar_cacheado(serie: pd.Series, horizonte: int) -> tuple:
    """AUD-UI-022: devuelve (oficial=estable, referencia=ensemble)."""
    return (
        proyectar_estable_con_ic(serie, n_steps=horizonte),
        proyectar_con_ic(serie, n_steps=horizonte),
    )'''

VIEJO_PROYECCION = '''    # ---------- PROYECCION ----------
    res = _proyectar_cacheado(serie, horizonte)
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
    k5.metric("Conservador", f"{float(res['escenarios']['conservador'][-1]):,.0f} t")'''

NUEVO_PROYECCION = '''    # ---------- PROYECCION DUAL (AUD-UI-022) ----------
    res_estable, res_ensemble = _proyectar_cacheado(serie, horizonte)
    if res_estable["modelo"] is None or res_ensemble["modelo"] is None:
        st.error("No se pudo calcular la proyeccion.")
        return

    # KPIs - oficial = estable (naive), referencia = ensemble
    ultimo = int(serie.index[-1])
    ultimo_v = float(serie.iloc[-1])
    proy_oficial = float(res_estable["prediccion"][-1])
    proy_ref = float(res_ensemble["prediccion"][-1])
    var_pct_oficial = (proy_oficial / ultimo_v - 1) * 100
    var_pct_ref = (proy_ref / ultimo_v - 1) * 100
    mape_ensemble = res_ensemble["mape"]

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(f"Ultimo ano ({ultimo})", f"{ultimo_v:,.0f} t")
    k2.metric(f"Oficial {ultimo + horizonte}", f"{proy_oficial:,.0f} t",
              delta=f"{var_pct_oficial:+.1f}%",
              help="Escenario estable (naive) - proyeccion oficial")
    k3.metric("Referencia tendencial", f"{proy_ref:,.0f} t",
              delta=f"{var_pct_ref:+.1f}%",
              help="Ensemble local (Holt/lineal/PM/MLP) - referencia")
    k4.metric("MAPE ensemble", f"{mape_ensemble:.1f}%",
              help="Error del ensemble en backtest (ultimos 2 anos)")
    k5.metric("Modelo ensemble", res_ensemble["ganador"].replace("Suavizado exponencial ", ""))'''

VIEJO_GRAFICO = '''    # ---------- GRAFICO ----------
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
    st.plotly_chart(fig, use_container_width=True)'''

NUEVO_GRAFICO = '''    # ---------- GRAFICO DUAL (AUD-UI-022) ----------
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie.index, y=serie.values, mode="lines+markers",
                             name="Historico", line=dict(color="#2E8B57", width=3)))
    anos_fut = np.arange(ultimo + 1, ultimo + 1 + horizonte)
    # IC del escenario oficial (estable/naive) - ensanchado con sqrt(t)
    fig.add_trace(go.Scatter(
        x=np.concatenate([anos_fut, anos_fut[::-1]]),
        y=np.concatenate([res_estable["escenarios"]["ic_alto"],
                          res_estable["escenarios"]["ic_bajo"][::-1]]),
        fill="toself", fillcolor="rgba(94,168,220,0.25)",
        line=dict(color="rgba(0,0,0,0)"), name="IC 50% (oficial)", showlegend=True))
    # Escenario oficial: estable (naive) - linea solida
    fig.add_trace(go.Scatter(x=anos_fut, y=res_estable["escenarios"]["tendencial"],
                             mode="lines+markers", name="Oficial (estable)",
                             line=dict(color="#2E8B57", width=4)))
    # Escenario de referencia: ensemble - linea punteada
    fig.add_trace(go.Scatter(x=anos_fut, y=res_ensemble["escenarios"]["tendencial"],
                             mode="lines+markers", name="Referencia (tendencial)",
                             line=dict(color="#DD6B20", width=2.5, dash="dash")))
    # Union historico-proyeccion oficial
    fig.add_trace(go.Scatter(
        x=[ultimo, anos_fut[0]],
        y=[ultimo_v, res_estable["escenarios"]["tendencial"][0]],
        mode="lines", line=dict(color="#2E8B57", width=4, dash="dash"),
        showlegend=False))
    fig.update_layout(template="plotly_white", height=480,
                      title=f"{cultivo} en {muni} - Proyeccion oficial vs referencia",
                      yaxis_title="Produccion (t)")
    st.plotly_chart(fig, use_container_width=True)'''

VIEJO_TABLA = '''    # ---------- TABLA DE ESCENARIOS ----------
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
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)'''

NUEVO_TABLA = '''    # ---------- TABLA DE ESCENARIOS DUAL (AUD-UI-022) ----------
    rows = []
    for i, an in enumerate(anos_fut):
        rows.append({
            "Ano": int(an),
            "Oficial (estable)": f"{res_estable['escenarios']['tendencial'][i]:,.0f}",
            "IC 50% (oficial)": f"{res_estable['escenarios']['ic_bajo'][i]:,.0f} - "
                                f"{res_estable['escenarios']['ic_alto'][i]:,.0f}",
            "Referencia (tendencial)": f"{res_ensemble['escenarios']['tendencial'][i]:,.0f}",
            "Diferencia": f"{res_ensemble['escenarios']['tendencial'][i] - res_estable['escenarios']['tendencial'][i]:+.0f}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)'''

VIEJO_INTERPRETACION = '''    # Interpretacion automatica
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
            f"({var_pct:+.1f}% vs {ultimo}).")'''

NUEVO_INTERPRETACION = '''    # Interpretacion automatica (AUD-UI-022)
    st.info(
        f"**Proyeccion oficial:** escenario estable (naive) = {proy_oficial:,.0f} t "
        f"en {int(anos_fut[-1])} ({var_pct_oficial:+.1f}% vs {ultimo}). "
        f"El intervalo de confianza se ensancha con el tiempo (propiedad de random walks). "
        f"**Referencia tendencial:** ensemble ({res_ensemble['ganador']}) = {proy_ref:,.0f} t "
        f"({var_pct_ref:+.1f}% vs {ultimo}, MAPE backtest {mape_ensemble:.1f}%). "
        f"La proyeccion oficial usa el ultimo valor observado porque el ensemble "
        f"no supera al naive en el holdout 2024-2025 (Gate 3)."
    )'''

# Ancla del ranking: regex entre bordes SIN emojis (inmune a mojibake/codepage)
PAT_RANKING = re.compile(
    r"    # ---------- RANKING DE MODELOS \(backtest\) ----------\n"
    r".*?"
    r"        st\.dataframe\(pd\.DataFrame\(filas\), use_container_width=True, hide_index=True\)\n",
    re.DOTALL)

NUEVO_RANKING = '''    # ---------- RANKING DE MODELOS (backtest del ensemble) ----------
    with st.expander("🔬 Comparativa de modelos (backtest del ensemble)"):
        st.caption("Ranking interno del ensemble (referencia tendencial). "
                   "Se ocultan los ultimos 2 anos, se entrena cada modelo con "
                   "el resto y se mide el error al predecirlos.")
        filas = []
        for r in res_ensemble["ranking"]:
            filas.append({
                "Modelo": r["modelo"]["nombre"],
                "MAPE (%)": f"{r['mape']:.1f}",
                "Ganador": "✅" if r is res_ensemble["ranking"][0] else "",
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
'''

# ========== Hunk 3: predictivo_pdf.py - PDF dual ==========
VIEJO_IMPORT_PDF = 'from core.reports import meta'
NUEVO_IMPORT_PDF = ('from core.reports import meta\n'
                    'from core.analytics.forecast import proyectar_estable_con_ic')

VIEJO_PDF_RESULTADO = '''    story = [
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
    story += [t, Spacer(1, 0.4 * cm)]'''

NUEVO_PDF_RESULTADO = '''    story = [
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
    story.append(Spacer(1, 0.3 * cm))'''

VIEJO_PDF_METODOLOGIA = '''    story.append(Paragraph(
        "<b>Metodologia:</b> Se prueban 6 candidatos (tendencia lineal, "
        "promedio movil 2 y 3 anos, Holt con dos sets de hiperparametros, y un MLP 3-8-4-1 entrenado desde cero). "
        "Se ocultan los ultimos 2 anos, se entrena con el resto y se mide "
        "MAPE. El de menor error gana y se reentrena con toda la serie para "
        "proyectar. Los intervalos son percentiles de los residuos del "
        "entrenamiento (P10/P25/P75/P90).", body))'''

NUEVO_PDF_METODOLOGIA = '''    story.append(Paragraph(
        "<b>Metodologia:</b> Se prueban 7 candidatos (tendencia lineal, "
        "promedio movil 2 y 3 anos, Holt con dos sets de hiperparametros, "
        "naive ultimo valor, y un MLP 3-8-4-1 entrenado desde cero). "
        "Se ocultan los ultimos 2 anos, se entrena con el resto y se mide "
        "MAPE. El de menor error gana el ensemble. La proyeccion oficial "
        "usa naive (ultimo valor) con IC ensanchado con sqrt(t); el ensemble "
        "se muestra como referencia tendencial (AUD-UI-022, Gate 3).", body))'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-UI-022", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def rollback_or_fail(motivo, backups):
    for ruta, bak in backups.items():
        try:
            shutil.copy2(bak, ruta)
        except Exception as e:
            audit("AUD-UI-022", "ROLLBACK_FALLIDO", f"{motivo} | {ruta.name}: {e}")
            print(f"[ERROR] {motivo} Y el rollback de {ruta.name} fallo: {e}")
            return 1
    audit("AUD-UI-022", "ROLLBACK", motivo)
    print(f"[ERROR] {motivo}; revirtiendo {len(backups)} archivos")
    return 1


def main():
    try:
        t_fc = FC.read_text(encoding="utf-8")
        t_ui = UI.read_text(encoding="utf-8")
        t_pdf = PDF.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer archivos: {e}")

    if "def modelo_naive" not in t_fc:
        return fail("forecast.py sin AUD-ML-007 (modelo_naive); ejecutar primero")

    if "def proyectar_estable_con_ic" in t_fc:
        print("[SKIP] AUD-UI-022 ya aplicado")
        return 0

    anclas = [
        (t_ui, VIEJO_IMPORT_FC, "4_Predictivo.py: import forecast"),
        (t_ui, VIEJO_CACHE, "4_Predictivo.py: cache"),
        (t_ui, VIEJO_PROYECCION, "4_Predictivo.py: proyeccion"),
        (t_ui, VIEJO_GRAFICO, "4_Predictivo.py: grafico"),
        (t_ui, VIEJO_TABLA, "4_Predictivo.py: tabla"),
        (t_ui, VIEJO_INTERPRETACION, "4_Predictivo.py: interpretacion"),
        (t_pdf, VIEJO_IMPORT_PDF, "predictivo_pdf.py: import meta"),
        (t_pdf, VIEJO_PDF_RESULTADO, "predictivo_pdf.py: resultado"),
        (t_pdf, VIEJO_PDF_METODOLOGIA, "predictivo_pdf.py: metodologia"),
    ]
    for texto, ancla, nombre in anclas:
        if texto.count(ancla) != 1:
            return fail(f"ancla {nombre}: {texto.count(ancla)} coincidencias (esperaba 1)")

    n_rank = len(PAT_RANKING.findall(t_ui))
    if n_rank != 1:
        return fail(f"ancla ranking (regex): {n_rank} coincidencias (esperaba 1)")

    # Aplicar cambios
    t_fc_n = t_fc + NUEVA_FUNCION_ESTABLE
    t_ui_n = (t_ui.replace(VIEJO_IMPORT_FC, NUEVO_IMPORT_FC, 1)
                  .replace(VIEJO_CACHE, NUEVO_CACHE, 1)
                  .replace(VIEJO_PROYECCION, NUEVO_PROYECCION, 1)
                  .replace(VIEJO_GRAFICO, NUEVO_GRAFICO, 1)
                  .replace(VIEJO_TABLA, NUEVO_TABLA, 1)
                  .replace(VIEJO_INTERPRETACION, NUEVO_INTERPRETACION, 1))
    t_ui_n = PAT_RANKING.sub(lambda m: NUEVO_RANKING, t_ui_n, count=1)
    t_pdf_n = (t_pdf.replace(VIEJO_IMPORT_PDF, NUEVO_IMPORT_PDF, 1)
                    .replace(VIEJO_PDF_RESULTADO, NUEVO_PDF_RESULTADO, 1)
                    .replace(VIEJO_PDF_METODOLOGIA, NUEVO_PDF_METODOLOGIA, 1))

    backups = {}
    try:
        for ruta, nuevo in ((FC, t_fc_n), (UI, t_ui_n), (PDF, t_pdf_n)):
            bak = ruta.with_suffix(ruta.suffix + ".bak")
            shutil.copy2(ruta, bak)
            backups[ruta] = bak
            ruta.write_text(nuevo, encoding="utf-8")
            print(f"[OK] {ruta.name} actualizado | backup: {bak.name}")
    except Exception as e:
        return rollback_or_fail(f"fallo de escritura: {e}", backups)

    for ruta in backups:
        r = subprocess.run([sys.executable, "-m", "py_compile", str(ruta)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return rollback_or_fail(f"sintaxis invalida en {ruta.name}: {r.stderr[:200]}", backups)

    # ---------- Autotests con modulo fresco ----------
    sys.path.insert(0, str(RAIZ))
    for name in list(sys.modules):
        if name == "core" or name.startswith("core."):
            del sys.modules[name]
    import numpy as np
    import pandas as pd
    from core.analytics.forecast import proyectar_estable_con_ic, proyectar_con_ic

    s = pd.Series([100.0, 110.0, 121.0, 133.0, 140.0, 150.0, 160.0])

    # Regresion: proyectar_con_ic sigue viva (atrapa cuerpo huerfano)
    res_orig = proyectar_con_ic(s, n_steps=3)
    if res_orig["modelo"] is None:
        return rollback_or_fail("autotest regresion: proyectar_con_ic devolvio None", backups)
    print("[OK] autotest regresion: proyectar_con_ic sigue viva")

    res = proyectar_estable_con_ic(s, n_steps=3)
    if not np.allclose(res["prediccion"], 160.0):
        return rollback_or_fail("autotest: proyeccion no es ultimo valor", backups)
    print("[OK] autotest: proyeccion estable = ultimo valor")

    ancho = res["escenarios"]["ic_alto"] - res["escenarios"]["ic_bajo"]
    if not (np.all(ancho > 0) and np.all(np.diff(ancho) > 0)):
        return rollback_or_fail("autotest: IC no se ensancha con sqrt(t)", backups)
    print("[OK] autotest: IC ensanchado con sqrt(t)")

    if not np.isnan(res["mape"]):
        return rollback_or_fail("autotest: mape del naive deberia ser NaN", backups)
    print("[OK] autotest: mape del naive es NaN")

    audit("AUD-UI-022", "OK", "v3: UI dual + ancla ranking inmune a mojibake")
    print("[OK] AUD-UI-022 v3 aplicado, compilado y autotesteado")
    print("Siguiente: commit + reboot en Cloud")
    return 0


if __name__ == "__main__":
    sys.exit(main())