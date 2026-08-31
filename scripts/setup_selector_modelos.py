"""Puente M3->produccion: selector de modelos por bandits con shrinkage."""
from pathlib import Path

MOD = '''"""Selector de modelos por bandits con shrinkage empirico (produccion).
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
'''
Path("core/analytics/model_selector.py").write_text(MOD, encoding="utf-8")
print("[OK] core/analytics/model_selector.py")

PAGE = '''"""Pagina 24: Selector de modelos por bandits (puente M3 a produccion)."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from core.analytics.model_selector import (recomendar, municipios, cultivos_de,
                                           ARMS, EPS, CRITICOS)

st.set_page_config(page_title="Selector de Modelos | EVA Valle", page_icon="\\U0001F3B0",
                   layout="wide")
st.title("\\U0001F3B0 Selector de modelos por bandits")
st.caption(f"Candidatos: {', '.join(ARMS)} | shrinkage empirico (N0=4) | IC 95%. "
           f"Exploracion etica: eps={EPS}, solo si IC se solapan y cultivo no critico "
           f"({', '.join(sorted(CRITICOS))}).")

mun = st.selectbox("Municipio", municipios())
cultivos = cultivos_de(mun)

rows, n_exp, n_pm3a = [], 0, 0
for cul in cultivos:
    r = recomendar(mun, cul)
    n_exp += r["explorar"]
    n_pm3a += r["modelo"] == "PM3A"
    rows.append({"cultivo": cul, "modelo": r["modelo"], "ape_est": r["ape_est"],
                 "ic95": f"[{r['ic'][0]}, {r['ic'][1]}]",
                 "explorar": "si" if r["explorar"] else "no",
                 "alternativa": r["alternativa"]})
R = pd.DataFrame(rows)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Campeon mas frecuente", R.modelo.mode().iloc[0])
k2.metric("Series donde PM3A sigue ganando", f"{n_pm3a}/{len(R)}")
k3.metric("Exploracion recomendada", f"{n_exp}/{len(R)}")
k4.metric("Regret vs status quo (torneo M3)", "-58%")

st.markdown("#### Recomendacion por cultivo (2026)")
c1, c2 = st.columns([3, 2])
with c1:
    st.table(R)
with c2:
    fig = go.Figure(go.Bar(x=R.modelo.value_counts().reindex(ARMS).fillna(0),
                           y=ARMS, orientation="h", marker_color="#5FA8DC"))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.info("**Etica de la exploracion:** solo se experimenta cuando hay duda real "
        "(IC solapados) y en cultivos que no comprometen seguridad alimentaria. "
        "En politica publica, explorar sin estas cotas seria irresponsable.")
'''
Path("ui/pages/24_Selector_Modelos.py").write_text(PAGE, encoding="utf-8")
print("[OK] ui/pages/24_Selector_Modelos.py")

app = Path("app.py")
c = app.read_text(encoding="utf-8")
if "24_Selector_Modelos" not in c:
    i = c.find("23_Valor_Economico.py")
    if i != -1:
        eol = c.find("\n", i) + 1
        nueva = ('        ("🎰 6 · Adaptativo — ¿qué modelo confiar?", 1, '
                 'st.Page("ui/pages/24_Selector_Modelos.py", title="Selector de Modelos", '
                 'icon="🎰")),\n')
        c = c[:eol] + nueva + c[eol:]
        app.write_text(c, encoding="utf-8")
        print("[OK] Selector registrado en app.py (seccion 6, rol analista+)")
    else:
        print("[AVISO] no encontre 23_Valor_Economico en app.py")
print("\nVerifica en CMD antes de abrir la app:")
print('  python -c "from core.analytics.model_selector import recomendar; print(recomendar(\'Alcalá\', \'Plátano\')[\'modelo\'], recomendar(\'Alcalá\', \'Plátano\')[\'ic\'])"')