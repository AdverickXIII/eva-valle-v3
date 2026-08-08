"""Reporte Excel por municipio (3 hojas)."""
from __future__ import annotations

import io

import pandas as pd

from core.reports.data import filter_municipio, kpis, top_cultivos, yearly


def build_municipality_excel(df: pd.DataFrame, municipio: str) -> bytes:
    df_m = filter_municipio(df, municipio)
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        k = kpis(df_m, df)
        pd.DataFrame({"Indicador": list(k.keys()), "Valor": list(k.values())})             .to_excel(w, sheet_name="Resumen", index=False)
        yearly(df_m).to_excel(w, sheet_name="Historico_Anual", index=False)
        top_cultivos(df_m).to_excel(w, sheet_name="Top_Cultivos", index=False)
    return out.getvalue()
