"""Radiografia de la seccion 4.4: datos, trazos y tema."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from config.settings import settings
from ui.charts.distributions import plot_distribuciones_log

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)

print("=== 1. COLUMNAS DEL CSV (las que interesan) ===")
print([c for c in df.columns if any(k in c.lower() for k in ["area", "prod", "rend"])])

print("\n=== 2. VALORES POSITIVOS POR METRICA ===")
for col in ["area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha"]:
    if col in df.columns:
        s = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        print(f"{col}: dtype={df[col].dtype}, positivos={(s > 0).sum()}")
    else:
        print(f"{col}: *** NO EXISTE EN EL CSV ***")

print("\n=== 3. TRAZOS DE LA FIGURA ===")
fig = plot_distribuciones_log(df)
print(f"Numero de trazos: {len(fig.data)}")
for i, tr in enumerate(fig.data):
    n = len(tr.x) if getattr(tr, "x", None) is not None else 0
    print(f"trazo {i}: tipo={tr.type}, puntos={n}")

print("\n=== 4. CONFIG DEL EJE X ===")
print("type:", fig.layout.xaxis.type)
print("range:", fig.layout.xaxis.range)
print("tickvals:", fig.layout.xaxis.tickvals)