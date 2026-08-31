"""Selector de modelos por bandits con shrinkage empirico (produccion).
Candidatos: PM3A / Naive / Trend / PM5A. Evidencia: rondas 2022-2025 del panel.
Recomendacion = media posterior (evidencia local + prior global), IC 95%.
Exploracion etica: solo si IC se solapan y el cultivo no es critico."""
from functools import lru_cache

import numpy as np
import pandas as pd

try:
    from config import settings
except Exception:
    from config.settings import settings

ARMS = ["PM3A", "Naive", "Trend", "PM5A"]
EPS = 0.05
N0 = 4.0          # fuerza del prior global (equiv. a 4 rondas)
Z95 = 1.96
CRITICOS = {"Arroz", "Maíz", "Yuca", "Papa", "Frijol"}


def _pred(arm, p, t):
    if arm == "PM3A":
        return p[max(0, t - 3):t].mean()
    if arm == "Naive":
        return p[t - 1]
    if arm == "Trend":
        a, b = np.polyfit(np.arange(t), p[:t], 1)
        return a * t + b
    return p[max(0, t - 5):t].mean()


@lru_cache(maxsize=1)
def _panel():
    df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                     low_memory=False)
    return df.groupby(["municipio", "cultivo", "ano"])["produccion_t"].sum().reset_index()


@lru_cache(maxsize=1)
def _evidencia():
    rows = []
    for (mun, cul), s in _panel().groupby(["municipio", "cultivo"]):
        p = s.sort_values("ano").produccion_t.values
        if len(p) < 7:
            continue
        for t in range(3, 7):
            real = p[t]
            if real <= 1e-8:
                continue
            for a in ARMS:
                rows.append((mun, cul, a, abs(_pred(a, p, t) - real) / real * 100))
    r = pd.DataFrame(rows, columns=["municipio", "cultivo", "arm", "ape"])
    mus = r.groupby("arm").ape.mean().to_dict()
    per = r.groupby(["municipio", "cultivo", "arm"]).ape.agg(n="count", media="mean").reset_index()
    return per, mus


def municipios():
    return sorted(_panel().municipio.unique())


def cultivos_de(municipio):
    s = _panel()[(_panel().municipio == municipio) & (_panel().ano == 2025)]
    return list(s.sort_values("produccion_t", ascending=False).cultivo)


def recomendar(municipio, cultivo):
    per, mus = _evidencia()
    sub = per[(per.municipio == municipio) & (per.cultivo == cultivo)]
    out = []
    for a in ARMS:
        row = sub[sub.arm == a]
        n_s = float(row.n.iloc[0]) if len(row) else 0.0
        m_s = float(row.media.iloc[0]) if len(row) else np.nan
        m = (n_s * m_s + N0 * mus[a]) / (n_s + N0) if n_s else mus[a]
        n_eff = n_s + N0
        sd = max(m * 0.5, 5.0)
        out.append({"modelo": a, "ape_est": m, "n": n_eff,
                    "ic_lo": max(0.0, m - Z95 * sd / np.sqrt(n_eff)),
                    "ic_hi": m + Z95 * sd / np.sqrt(n_eff)})
    tab = pd.DataFrame(out).sort_values("ape_est").reset_index(drop=True)
    best, second = tab.iloc[0], tab.iloc[1]
    explorar = (cultivo not in CRITICOS) and (best.ic_hi > second.ic_lo)
    return {"modelo": best.modelo, "ape_est": round(best.ape_est, 1),
            "ic": (round(best.ic_lo, 1), round(best.ic_hi, 1)),
            "explorar": bool(explorar), "alternativa": second.modelo, "tabla": tab}
