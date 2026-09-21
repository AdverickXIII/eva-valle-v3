"""Motor de forecasting robusto para series agricolas cortas (n>=4).

Seis modelos compiten por serie (lineal, PM2A, PM3A, Holt x2, MLP 3-8-4-1);
el backtesting elige el mejor (menor MAPE).
Devuelve proyeccion con intervalos de confianza por percentiles de residuos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.analytics.mlp_forecast import modelo_mlp, proyectar_mlp


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
    return {"nombre": f"Promedio movil {ventana}A", "ventana": ventana,
            "fitted": fitted, "last_mean": float(s[-ventana:].mean())}


def modelo_holt(t, s, alpha: float = 0.3, beta: float = 0.1):
    if len(t) < 3:
        return None
    L = float(s[0])
    T = float(s[1] - s[0]) if len(s) > 1 else 0.0
    fitted = np.empty_like(s, dtype=float)
    fitted[0] = np.nan  # no hay pronostico de un paso para el primer punto
    for i in range(1, len(s)):
        fitted[i] = L + T  # pronostico de un paso: L_{i-1} + T_{i-1} (pre-update)
        L_new = alpha * s[i] + (1 - alpha) * (L + T)
        T_new = beta * (L_new - L) + (1 - beta) * T
        L, T = L_new, T_new
    return {"nombre": "Suavizado exponencial (Holt)", "alpha": alpha, "beta": beta,
            "L": L, "T": T, "fitted": fitted}


def modelo_naive(t, s):
    """Naive: repite el ultimo valor. fitted = lag 1 (residuos = diferencias de un paso)."""
    if len(s) < 2:
        return None
    fitted = np.empty_like(s, dtype=float)
    fitted[0] = np.nan
    fitted[1:] = s[:-1]
    return {"nombre": "Naive (ultimo valor)", "fitted": fitted, "ultimo": float(s[-1])}


def _mape(real: np.ndarray, pred: np.ndarray) -> float:
    real = np.asarray(real, dtype=float)
    pred = np.asarray(pred, dtype=float)
    mask = np.abs(real) > 1e-8
    if not mask.any():
        return np.inf
    return float(np.mean(np.abs((real[mask] - pred[mask]) / real[mask])) * 100)


def _proyectar(modelo: dict, n_steps: int, serie_original=None) -> np.ndarray:
    nombre = modelo["nombre"]
    if nombre == "Tendencia lineal":
        t_future = np.arange(len(modelo["fitted"]), len(modelo["fitted"]) + n_steps)
        return modelo["a"] + modelo["b"] * t_future
    if nombre.startswith("Promedio movil"):
        return np.full(n_steps, modelo["last_mean"])
    if nombre == "MLP (3-8-4-1)":
        base = modelo.get("serie_train", serie_original)
        return proyectar_mlp(modelo, n_steps, base)
    if nombre == "Naive (ultimo valor)":
        return np.full(n_steps, modelo["ultimo"])
    # Holt
    L, T = modelo["L"], modelo["T"]
    return np.array([L + (i + 1) * T for i in range(n_steps)])


def backtest(serie: pd.Series, n_out: int = 2) -> list[dict]:
    """Oculta los ultimos n_out valores, entrena y mide MAPE por modelo."""
    t, s = _preparar(serie)
    if len(s) < 4:
        return []
    if len(s) - n_out < 3:
        n_out = max(1, len(s) - 3)  # series de 4 anos: holdout de 1 (docstring n>=4)
    t_train, s_train = t[:-n_out], s[:-n_out]
    s_real = s[-n_out:]
    candidatos = [
        modelo_lineal(t_train, s_train),
        modelo_promedio(t_train, s_train, 2),
        modelo_promedio(t_train, s_train, 3),
        modelo_holt(t_train, s_train, 0.3, 0.1),
        modelo_holt(t_train, s_train, 0.5, 0.2),
        modelo_naive(t_train, s_train),
        modelo_mlp(pd.Series(s_train)),
    ]
    resultados = []
    for m in candidatos:
        if m is None:
            continue
        fitted = m["fitted"]
        if np.all(np.isnan(fitted)):
            continue
        pred = _proyectar(m, n_out, serie)
        if np.any(np.isnan(pred)):
            continue
        mape = _mape(s_real, pred)
        residuos = s_train[~np.isnan(fitted)] - fitted[~np.isnan(fitted)]
        resultados.append({
            "modelo": m, "mape": mape,
            "residuos": residuos if len(residuos) > 0 else np.array([0.0]),
            "holdout": n_out,
        })
    return resultados


def elegir_mejor(serie: pd.Series, n_out: int = 2,
                 ventanas: tuple = (1, 2)) -> dict:
    """AUD-ML-007: elige por MEDIANA de MAPE entre varias ventanas de holdout
    interno (reduce la suerte de colocacion del holdout sobre el choque) y
    reentrena el ganador con la serie completa."""
    bt_por_ventana = {w: backtest(serie, w) for w in ventanas}
    bt_plana = [r for w in ventanas for r in bt_por_ventana[w]]
    if not bt_plana:
        return {"modelo": None, "mape": np.inf, "residuos": np.array([0.0]),
                "ganador": "Datos insuficientes", "ranking": []}

    agg = {}
    for w in ventanas:
        for r in bt_por_ventana[w]:
            agg.setdefault(r["modelo"]["nombre"], {})[w] = r

    def mediana(nombre):
        return float(np.median([r["mape"] for r in agg[nombre].values()]))

    mejor_nombre = min(agg, key=mediana)
    por_w = agg[mejor_nombre]
    w_rep = n_out if n_out in por_w else max(por_w)
    mejor = por_w[w_rep]

    ranking = []
    for nombre in sorted(agg, key=mediana):
        pw = agg[nombre]
        w2 = n_out if n_out in pw else max(pw)
        rep = dict(pw[w2])
        rep["mape"] = mediana(nombre)
        rep["mapes_por_ventana"] = {w: r["mape"] for w, r in pw.items()}
        ranking.append(rep)

    t_full, s_full = _preparar(serie)
    nombre = mejor_nombre
    if nombre == "Tendencia lineal":
        modelo_full = modelo_lineal(t_full, s_full)
    elif nombre.startswith("Promedio movil"):
        modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])
    elif nombre == "MLP (3-8-4-1)":
        modelo_full = modelo_mlp(serie)
    elif nombre == "Naive (ultimo valor)":
        modelo_full = modelo_naive(t_full, s_full)
    else:
        modelo_full = modelo_holt(t_full, s_full,
                                  mejor["modelo"]["alpha"],
                                  mejor["modelo"]["beta"])
    return {
        "modelo": modelo_full,
        "mape": mediana(mejor_nombre),
        "residuos": mejor["residuos"],
        "ganador": nombre,
        "ranking": ranking,
        "n_out_efectivo": mejor.get("holdout", n_out),
    }


def proyectar_con_ic(serie: pd.Series, n_steps: int = 3,
                     niveles: tuple = (0.10, 0.25, 0.75, 0.90)) -> dict:
    res = elegir_mejor(serie)
    if res["modelo"] is None:
        return res
    pred = _proyectar(res["modelo"], n_steps, serie)
    residuos = np.asarray(res["residuos"], dtype=float)
    residuos = residuos[np.isfinite(residuos)]
    if len(residuos):
        med = float(np.median(np.abs(residuos)))
        if med > 1e-8:
            residuos = residuos[np.abs(residuos) <= 10.0 * med]
    if not len(residuos):
        residuos = np.array([0.0])
    if len(residuos) and float(np.std(residuos)) > 0:
        residuos = residuos - float(np.mean(residuos))
    cuantiles = {f"P{int(p*100)}": float(np.quantile(residuos, p)) for p in niveles}
    escenarios = {
        "conservador": np.maximum(0.0, pred + cuantiles["P10"]),
        "tendencial": np.maximum(0.0, pred),
        "optimista": np.maximum(0.0, pred + cuantiles["P90"]),
        "ic_bajo": np.maximum(0.0, pred + cuantiles["P25"]),
        "ic_alto": np.maximum(0.0, pred + cuantiles["P75"]),
    }
    return {**res, "prediccion": pred, "escenarios": escenarios, "cuantiles": cuantiles}