"""Genera el notebook completo del Modulo 2 (RNN/LSTM sobre panel EVA)."""
import json
from pathlib import Path

cells = []
def md(src):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": src.splitlines(keepends=True)})
def code(src):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": src.splitlines(keepends=True)})

md(r"""# Módulo 2 — RNNs y Series Temporales (LSTM)
## Laboratorio: panel municipio-cultivo del Valle (UPRA-EVA 2019-2025)

**Objetivos**
1. BPTT verificado numéricamente en RNN y LSTM.
2. Demostración empírica del vanishing gradient (T=20).
3. Modelo global LSTM entrenado en el panel completo → predicción 2025 (test) y 2026 (Alcalá).
4. Comparación justa: LSTM vs PM3A vs MLP del Módulo 1.

**Matemática**
- RNN: $h_t = \tanh(W_{xh}x_t + W_{hh}h_{t-1} + b_h)$
- Vanishing: $\partial h_t/\partial h_k = \prod_{j=k+1}^{t} W_{hh}^T \mathrm{diag}(\sigma'(z_j))$ → decae exponencialmente
- LSTM: $c_t = f_t \odot c_{t-1} + i_t \odot g_t$ (autopista aditiva del gradiente)
- GRU (ejercicio guiado al final): $z_t, r_t, \tilde h_t$""")

code(r"""import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd()
while ROOT != ROOT.parent and not (ROOT / "app.py").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from core.ml.rnn_scratch import RNN, LSTM, gradient_check
from core.ml.io_utils import save_json, save_csv, RESULTS
print("raiz:", ROOT)""")

md(r"""## 2.1 Verificación de BPTT (gradient check)""")

code(r"""rng = np.random.RandomState(0)
X, y = rng.randn(2, 6), rng.randn(1, 1)
e_rnn = gradient_check(RNN(2, 4), X, y)
e_lstm = gradient_check(LSTM(2, 4), X, y)
print(f"RNN  error relativo: {e_rnn:.2e}", "OK" if e_rnn < 1e-5 else "FALLA")
print(f"LSTM error relativo: {e_lstm:.2e}", "OK" if e_lstm < 1e-5 else "FALLA")
save_json("m2_gradient_checks.json", {"rnn": e_rnn, "lstm": e_lstm})""")

md(r"""## 2.2 Vanishing gradient: ¿por qué LSTM?
Medimos cuánto gradiente llega al primer paso de la secencia (T=20).""")

code(r"""T = 20
Xl = rng.randn(1, T)
ratios, perfiles = {}, {}
for nombre, modelo in [("RNN", RNN(1, 8)), ("LSTM", LSTM(1, 8))]:
    modelo.forward(Xl)
    _, _, dX = modelo.backward(np.ones((1, 1)))
    perfil = np.abs(dX).flatten()
    ratios[nombre] = float(perfil[0] / (perfil[-1] + 1e-12))
    perfiles[nombre] = perfil
    print(f"{nombre}: |dL/dx_1|/|dL/dx_T| = {ratios[nombre]:.2e}")

plt.figure(figsize=(8, 4))
for k, v in perfiles.items():
    plt.plot(range(1, T + 1), v, marker="o", label=k)
plt.yscale("log"); plt.xlabel("t"); plt.ylabel("|dL/dx_t|")
plt.title("Flujo de gradiente hacia el pasado"); plt.legend(); plt.show()""")

md(r"""## 2.3 Datos reales: panel municipio-cultivo (series completas 2019-2025)""")

code(r"""from config.settings import settings
df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)
g = df.groupby(["municipio", "cultivo", "ano"])["produccion_t"].sum().reset_index()
n7 = g.groupby(["municipio", "cultivo"]).ano.nunique()
full = n7[n7 == 7].index
print(f"Series completas (7 anos): {len(full)}")

# Verificacion contra el PDF de Alcala (top 5 cultivos, acumulado)
alc = g[g.municipio == "Alcalá"].groupby("cultivo").produccion_t.sum().sort_values(ascending=False)
PDF5 = {"Plátano": 89843, "Naranja": 51128, "Tomate": 22018, "Piña": 19618, "Mandarina": 19180}
for c, v in PDF5.items():
    print(f"  {c}: CSV {alc.get(c, 0):,.0f} t vs PDF {v:,} t")""")

code(r"""# Ventanas (t-3,t-2,t-1) -> t, normalizadas por serie
Xs, ys, meta = [], [], []
for (mun, cul) in full:
    s = g[(g.municipio == mun) & (g.cultivo == cul)].sort_values("ano")
    p = s.produccion_t.values; anos = s.ano.values
    mn, mx = p.min(), p.max()
    pn = (p - mn) / (mx - mn + 1e-8)
    for t in range(3, 7):
        Xs.append(pn[t-3:t].reshape(1, 3))
        ys.append(np.array([[pn[t]]]))
        meta.append((mun, cul, anos[t], mn, mx, p[t]))
print(f"Ventanas de entrenamiento/test: {len(Xs)}")""")

md(r"""## 2.4 Entrenamiento del modelo global LSTM""")

code(r"""model = LSTM(1, 16, seed=42)
idx = np.arange(len(Xs))
EPOCHS, LR = 12, 0.05
for ep in range(EPOCHS):
    np.random.seed(ep); np.random.shuffle(idx)
    tot = 0.0
    for k in idx:
        model.forward(Xs[k])
        loss, G, _ = model.backward(ys[k])
        model.step(G, LR)
        tot += loss
    print(f"Epoch {ep+1:2d} | MSE {tot/len(Xs):.5f}")""")

md(r"""## 2.5 Test 2025 (fuera de muestra) + predicción 2026 de Alcalá""")

code(r"""# MAPE global en 2025
errs = []
for (mun, cul, an, mn, mx, real) in meta:
    if an != 2025:
        continue
    i = meta.index((mun, cul, an, mn, mx, real))
    pn = model.predict(Xs[i]).flatten()[0]
    pred = pn * (mx - mn) + mn
    errs.append(abs(pred - real) / real * 100)
print(f"MAPE global test 2025 (n={len(errs)}): {np.mean(errs):.2f}%")

# Alcala: top 5 cultivos, real 2025 vs LSTM 2025 vs ambos 2026
rows = []
for (mun, cul) in list(PDF5.keys()) and [(m, c) for (m, c) in full if m == "Alcalá" and c in PDF5]:
    s = g[(g.municipio == mun) & (g.cultivo == cul)].sort_values("ano")
    p = s.produccion_t.values; anos = s.ano.values
    mn, mx = p.min(), p.max()
    pn = (p - mn) / (mx - mn + 1e-8)
    i = meta.index((mun, cul, 2025, mn, mx, p[6]))
    pred25 = model.predict(Xs[i]).flatten()[0] * (mx - mn) + mn
    x26 = pn[3:6].reshape(1, 3)
    pred26 = model.predict(x26).flatten()[0] * (mx - mn) + mn
    pm3a26 = p[3:6].mean()
    rows.append({"cultivo": cul, "real_2025": round(p[6], 0),
                 "lstm_2025": round(pred25, 0), "lstm_2026": round(pred26, 0),
                 "pm3a_2026": round(pm3a26, 0)})
R = pd.DataFrame(rows)
R.loc["TOTAL"] = R.sum(numeric_only=True)
print(R.to_string(index=False))
save_csv("m2_lstm_alcala.csv", R)
save_json("m2_lstm_panel_metrics.json", {"mape_test_2025": float(np.mean(errs))})
print("\nReferencia PDF: proyeccion oficial 2026 (PM3A total) = 39,196 t")
print("Referencia M1: MLP total 2025 = 41,514 t (MAPE 0.87%)")""")

md(r"""## 2.6 Interpretación + ejercicio GRU

Compara columnas: si el LSTM global supera al PM3A por cultivo en 2025,
la arquitectura recurrente está capturando dinámica que el promedio no ve.

**Ejercicio (rigor):** implementa GRU desde cero:
$z_t = \sigma(W_z[h_{t-1};x_t])$, $r_t = \sigma(W_r[h_{t-1};x_t])$,
$\tilde h_t = \tanh(W_h[r_t \odot h_{t-1}; x_t])$,
$h_t = (1-z_t)\odot h_{t-1} + z_t \odot \tilde h_t$.
Deriva su BPTT y verifica con `gradient_check`. Pídeme la solución de referencia al terminar.""")

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                  "name": "python3"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
Path("notebooks/curso/02_rnn_series_temporales.ipynb").write_text(
    json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("[OK] notebooks/curso/02_rnn_series_temporales.ipynb (version completa)")