"""
Analisis 7.4: Proyeccion tendencial (Holt-Winters).
Suavizamiento exponencial de la produccion total semestral.

Mejoras respecto al notebook:
- Sin matplotlib (separacion calculo / visualizacion).
- Manejo robusto de series cortas.
"""
from __future__ import annotations

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from core.logging import get_logger

log = get_logger("core.ml.forecasting")

MIN_SERIE_LENGTH = 8
FORECAST_PERIODS = 2
FORECAST_LABELS = ["2025A", "2025B"]


def forecast_time_series(
    df: pd.DataFrame,
    forecast_periods: int = FORECAST_PERIODS,
) -> dict[str, pd.DataFrame | str]:
    """
    Proyeccion tendencial con Holt-Winters (sin estacionalidad).

    Args:
        df: DataFrame con columnas ano, periodo, produccion_t.
        forecast_periods: Numero de periodos a proyectar (default 2).

    Returns:
        Diccionario con: df_proyeccion (historico + pronostico),
        metodo ("holt_winters" o "insuficiente").
    """
    required_cols = ["ano", "periodo", "produccion_t"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    df_time = (
        df.groupby(["ano", "periodo"])["produccion_t"]
        .sum()
        .reset_index()
        .sort_values(["ano", "periodo"])
        .reset_index(drop=True)
    )

    serie = df_time["produccion_t"]
    if len(serie) < MIN_SERIE_LENGTH:
        log.warning(
            "Serie muy corta (%d < %d) para Holt-Winters. "
            "Retornando solo datos historicos.",
            len(serie), MIN_SERIE_LENGTH,
        )
        df_time["tipo"] = "Historico"
        return {"df_proyeccion": df_time, "metodo": "insuficiente"}

    try:
        modelo_hw = ExponentialSmoothing(
            serie,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        )
        fit_hw = modelo_hw.fit()
        pronostico = fit_hw.forecast(forecast_periods)

        df_forecast = pd.DataFrame({
            "periodo": FORECAST_LABELS[:forecast_periods],
            "produccion_predicha": pronostico,
            "tipo": "Pronostico",
        })

        df_hist = df_time.copy()
        df_hist["tipo"] = "Historico"
        df_hist = df_hist.rename(columns={"produccion_t": "produccion_predicha"})

        df_final = pd.concat([df_hist, df_forecast], ignore_index=True)

        log.info(
            "Holt-Winters completado: %d periodos historicos + %d pronosticados.",
            len(df_hist), forecast_periods,
        )
        return {"df_proyeccion": df_final, "metodo": "holt_winters"}

    except Exception as e:
        log.error("Error en Holt-Winters: %s", e)
        df_time["tipo"] = "Historico"
        return {"df_proyeccion": df_time, "metodo": f"error: {e}"}
