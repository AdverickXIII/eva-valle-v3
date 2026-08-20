"""Tabla de Location Quotient por municipio-grupo."""
from __future__ import annotations

import pandas as pd


def lq_top(df: pd.DataFrame, top_n: int = 20, excluye_cana: bool = False) -> pd.DataFrame:
    if excluye_cana:
        df = df[df["cultivo"] != "Caña"]
    mg = df.groupby(["municipio", "grupo_cultivo"])["produccion_t"].sum()
    m_tot = df.groupby("municipio")["produccion_t"].sum()
    g_tot = df.groupby("grupo_cultivo")["produccion_t"].sum()
    total = float(df["produccion_t"].sum())
    rows = []
    for (m, g), v in mg.items():
        sm = v / m_tot[m] * 100 if m_tot[m] else 0.0
        sd = g_tot[g] / total * 100 if total else 0.0
        if sd > 0 and v > 0:
            rows.append({
                "municipio": m,
                "grupo_cultivo": g,
                "share_municipio_pct": sm,
                "share_valle_pct": sd,
                "lq": sm / sd,
            })
    out = pd.DataFrame(rows).sort_values("lq", ascending=False)
    return out.head(top_n).reset_index(drop=True)
