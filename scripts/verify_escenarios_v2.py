"""Verificacion estricta: el IC debe tener ANCHO (P10 < tendencial < P90)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from config.settings import settings
from core.analytics.forecast import proyectar_con_ic

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)
serie = (df[(df.municipio == "Alcalá") & (df.cultivo == "Plátano")]
         .groupby("ano")["produccion_t"].sum().sort_index())
res = proyectar_con_ic(serie, n_steps=3)
esc = res["escenarios"]
c, t, o = esc["conservador"], esc["tendencial"], esc["optimista"]

print(f"Ganador: {res['ganador']} | MAPE {res['mape']:.2f}%")
print(f"Conservador: {c.round(0).tolist()}")
print(f"Tendencial:  {t.round(0).tolist()}")
print(f"Optimista:   {o.round(0).tolist()}")
print(f"IC 50% 2026: {esc['ic_bajo'][0]:,.0f} - {esc['ic_alto'][0]:,.0f}")

checks = {
    "c <= t siempre": bool(np.all(c <= t + 1e-6)),
    "t <= o siempre": bool(np.all(t <= o + 1e-6)),
    "IC con ancho (>0)": bool(esc["ic_alto"][0] > esc["ic_bajo"][0] + 1.0),
    "o > t en algun ano": bool(np.any(o > t + 1.0)),
    "c < t en algun ano": bool(np.any(c < t - 1.0)),
    "max < 30k t": bool(float(np.max(o)) < 30000),
}
for k, v in checks.items():
    print(f"  {'✅' if v else '❌'} {k}")
print("\n✅ ESCENARIOS REALMENTE CUERDOS" if all(checks.values())
      else "\n❌ IC sigue degenerado: NO publicar")