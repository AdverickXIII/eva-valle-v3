"""Diagnostico: variantes de MAPE + protocolo del modulo forecast + correccion M1."""
import re
from pathlib import Path
import numpy as np
import pandas as pd

from config.settings import settings

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)
alc = df[df.municipio == "Alcalá"].groupby("ano")["produccion_t"].sum().sort_index()
p = alc.values
anos = alc.index.values

pm3a, pm5a, reals, yrs = [], [], [], []
for t in range(3, 7):
    reals.append(p[t]); yrs.append(int(anos[t]))
    pm3a.append(p[t-3:t].mean())
    pm5a.append(p[max(0, t-5):t].mean())

def mape(preds):
    return float(np.mean(np.abs(np.array(preds) - np.array(reals)) / np.abs(reals)) * 100)

print("=== Variantes de MAPE para PM3A (total Alcala) ===")
print(f"  media 2022-2025:    {mape(pm3a):.2f}")
print(f"  agregado 2022-2025: {abs(sum(pm3a)-sum(reals))/sum(reals)*100:.2f}")
print(f"  agregado 2023-2025: {abs(sum(pm3a[1:])-sum(reals[1:]))/sum(reals[1:])*100:.2f}")
print(f"  mediana 2022-2025:  {float(np.median(np.abs(np.array(pm3a)-reals)/reals)*100):.2f}")

print("\n=== Lineas del modulo forecast que definen el protocolo ===")
src = Path("core/analytics/forecast.py").read_text(encoding="utf-8")
hits = 0
for i, line in enumerate(src.splitlines(), 1):
    if re.search(r"mape|backtest|movil|promedio|window|horizonte", line, re.I):
        print(f"{i:4d}: {line.rstrip()}")
        hits += 1
if not hits:
    print("  (sin coincidencias; pegar forecast.py completo)")

print("\n=== Correccion del baseline M1 (sin lookahead) ===")
m1 = pd.read_csv(Path("core/ml/results/m1_alcala_predicciones.csv")).dropna(subset=["real_t"])
m1["ano"] = m1.ano.astype(int)
m1["pm3a_ok"] = m1.ano.map(dict(zip(yrs, pm3a)))
m1["pm5a_ok"] = m1.ano.map(dict(zip(yrs, pm5a)))
for c in ["mlp_t", "pm3a_ok", "pm5a_ok"]:
    m = float(np.mean(np.abs(m1[c] - m1.real_t) / m1.real_t) * 100)
    print(f"  {c:8s} MAPE: {m:.2f}")
m1.to_csv("core/ml/results/m1_alcala_predicciones_corregido.csv", index=False)
print("[OK] guardado: core/ml/results/m1_alcala_predicciones_corregido.csv")