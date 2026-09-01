"""Valida el selector en la serie TOTAL de Alcala (como el PDF)."""
import numpy as np
import pandas as pd
from config.settings import settings
from core.analytics.model_selector import _pred, ARMS

# 1) Serie total de Alcala (agregada por año)
df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)
alc = df[df.municipio == "Alcalá"].groupby("ano")["produccion_t"].sum().sort_index()
print("Serie total Alcala 2019-2025:")
print(alc.to_string())

# 2) MAPE por modelo en el test (2022-2025)
p = alc.values
anos = alc.index.values
results = []
for t in range(3, 7):  # años 2022-2025
    real = p[t]
    for arm in ARMS:
        pred = _pred(arm, p, t)
        mape = abs(pred - real) / real * 100
        results.append({"ano": anos[t], "modelo": arm, "real": real,
                        "pred": pred, "mape": mape})

R = pd.DataFrame(results)
print("\n=== MAPE por año y modelo (serie total) ===")
pivot = R.pivot(index="ano", columns="modelo", values="mape").round(2)
print(pivot.to_string())

print("\n=== MAPE promedio 2022-2025 ===")
avg = R.groupby("modelo").mape.mean().sort_values()
print(avg.round(2).to_string())
print(f"\nCampeon del PDF: PM3A con MAPE 4.2%")
print(f"Campeon del selector: {avg.index[0]} con MAPE {avg.iloc[0]:.2f}%")

if avg.index[0] == "PM3A":
    print("\n✅ VALIDACION PASA: el selector coincide con el PDF en el total municipal")
else:
    print("\n⚠️ DISCREPANCIA: el selector difiere del PDF en el total municipal")
    print("   Investigar: ¿el shrinkage esta sesgando hacia Naive?")