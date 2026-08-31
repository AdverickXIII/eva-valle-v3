"""Agrega la iteracion v2 (regularizacion) al notebook 02."""
import json
from pathlib import Path

p = Path("notebooks/curso/02_rnn_series_temporales.ipynb")
nb = json.loads(p.read_text(encoding="utf-8"))
cells = nb["cells"]

def md(src):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": src.splitlines(keepends=True)})
def code(src):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": src.splitlines(keepends=True)})

md(r"""## 2.7 Iteracion v2 — regularizacion completa
Dropout 0.2 + L2 1e-4 + lr decay + early stopping (val=2024, test=2025 intocable).
Features d=3: produccion, area y rendimiento normalizados por serie.""")

code(r"""g2 = df.groupby(["municipio", "cultivo", "ano"]).agg(
    prod=("produccion_t", "sum"), area=("area_cosechada_ha", "sum")).reset_index()
g2["rend"] = g2.prod / g2.area.clip(lower=1e-6)
n7b = g2.groupby(["municipio", "cultivo"]).ano.nunique()
fullb = n7b[n7b == 7].index

X2, y2, meta2 = [], [], []
for (mun, cul) in fullb:
    s = g2[(g2.municipio == mun) & (g2.cultivo == cul)].sort_values("ano")
    P = s[["prod", "area", "rend"]].values
    mins, maxs = P.min(0), P.max(0)
    Pn = (P - mins) / (maxs - mins + 1e-8)
    anos = s.ano.values
    for t in range(3, 7):
        X2.append(Pn[t-3:t].T)
        y2.append(np.array([[Pn[t, 0]]]))
        meta2.append((mun, cul, anos[t], mins[0], maxs[0], P[t, 0]))

tr_idx = [k for k, m in enumerate(meta2) if m[2] <= 2023]
va_idx = [k for k, m in enumerate(meta2) if m[2] == 2024]
te_idx = [k for k, m in enumerate(meta2) if m[2] == 2025]
print(f"train {len(tr_idx)} | val {len(va_idx)} | test {len(te_idx)}")""")

code(r"""from core.ml.lstm_v2 import LSTMv2
m2 = LSTMv2(3, 16, p_drop=0.2, l2=1e-4, seed=42)

def mse_set(model, idxs):
    return float(np.mean([np.mean((model.forward(X2[k]) - y2[k]) ** 2) for k in idxs]))

best_val, best_snap, wait = 1e9, None, 0
for ep in range(150):
    lr = 0.05 * (0.995 ** ep)
    np.random.seed(ep); order = tr_idx[:]; np.random.shuffle(order)
    for k in order:
        m2.forward(X2[k], train=True)
        m2.step(m2.backward(y2[k]), lr)
    if ep % 5 == 0:
        vv = mse_set(m2, va_idx)
        tag = ""
        if vv < best_val:
            best_val, best_snap, wait = vv, m2.snapshot(), 0
            tag = " *best"
        else:
            wait += 5
        print(f"Epoch {ep:3d} | lr {lr:.4f} | train {mse_set(m2, tr_idx):.4f} | val {vv:.4f}{tag}")
        if wait >= 25:
            print("early stopping en epoch", ep); break
m2.restore(best_snap)
print(f"mejor val MSE: {best_val:.4f}")""")

code(r"""errs = []
for k in te_idx:
    mun, cul, an, mn, mx, real = meta2[k]
    if real <= 1e-8:
        continue
    pred = m2.forward(X2[k]).flatten()[0] * (mx - mn) + mn
    errs.append(abs(pred - real) / real * 100)
mape_v2 = float(np.mean(errs))
print(f"MAPE global test 2025 (LSTM v2, n={len(errs)}): {mape_v2:.2f}%")
print("Referencias: LSTM v1 = 50.38% | PM3A PDF = 4.2% | MLP M1 (Alcala) = 2.82%")

rows = []
for cul in PDF5:
    s = g2[(g2.municipio == "Alcalá") & (g2.cultivo == cul)].sort_values("ano")
    if len(s) < 4 or s.ano.iloc[-1] != 2025:
        continue
    P = s[["prod", "area", "rend"]].values
    mins, maxs = P.min(0), P.max(0)
    Pn = (P - mins) / (maxs - mins + 1e-8)
    anos = s.ano.values
    i25 = list(anos).index(2025)
    p25 = (m2.forward(Pn[i25-3:i25].T).flatten()[0] * (maxs[0] - mins[0]) + mins[0]) if i25 >= 3 else np.nan
    p26 = m2.forward(Pn[-3:].T).flatten()[0] * (maxs[0] - mins[0]) + mins[0]
    rows.append({"cultivo": cul, "real_2025": round(P[i25, 0], 0),
                 "v2_2025": round(p25, 0), "v2_2026": round(p26, 0),
                 "pm3a_2026": round(P[-3:, 0].mean(), 0)})
R2 = pd.DataFrame(rows)
R2.loc["TOTAL"] = R2.sum(numeric_only=True)
print(R2.to_string(index=False))
save_csv("m2_lstm_alcala_v2.csv", R2)
save_json("m2_lstm_v2_metrics.json", {"mape_test_2025": mape_v2, "best_val_mse": best_val})""")

md(r"""## 2.8 Interpretacion v1 vs v2
Si el MAPE v2 baja fuerte: la regularizacion funciono (el v1 memorizaba ruido).
Si sigue alto en el panel global pero bien en Alcala: la leccion es otra —
**un modelo global no siempre gana a modelos locales**, y elegir entre ellos
es exactamente el tema del Modulo 3 (bandits y seleccion de modelos).""")

p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("[OK] celdas 2.7-2.8 agregadas al notebook 02")