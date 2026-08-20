"""Desglose exacto del HHI: contribucion de cada cultivo al indice."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from config.settings import settings

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)

print("=" * 70)
print("HHI CON CAÑA")
print("=" * 70)
prod_con = df.groupby("cultivo")["produccion_t"].sum()
total_con = prod_con.sum()
shares_con = (prod_con / total_con * 100).sort_values(ascending=False)
hhi_con = (shares_con ** 2).sum()

print(f"{'Cultivo':<40} {'Share %':>10} {'Contrib HHI':>12}")
print("-" * 70)
acum = 0
for cultivo, share in shares_con.head(15).items():
    contrib = share ** 2
    acum += contrib
    print(f"{cultivo:<40} {share:>10.2f} {contrib:>12.2f}")
otros = shares_con.iloc[15:].sum()
acum += (shares_con.iloc[15:] ** 2).sum()
print(f"{'Otros ' + str(len(shares_con)-15) + ' cultivos':<40} {otros:>10.2f} {(shares_con.iloc[15:]**2).sum():>12.2f}")
print("-" * 70)
print(f"{'HHI TOTAL':<40} {'100.00':>10} {hhi_con:>12.2f}")
print(f"\nLa caña aporta {(shares_con['Caña']**2 / hhi_con * 100):.2f}% del HHI total")

print("\n" + "=" * 70)
print("HHI SIN CAÑA")
print("=" * 70)
df_sin = df[df["cultivo"] != "Caña"]
prod_sin = df_sin.groupby("cultivo")["produccion_t"].sum()
total_sin = prod_sin.sum()
shares_sin = (prod_sin / total_sin * 100).sort_values(ascending=False)
hhi_sin = (shares_sin ** 2).sum()

print(f"{'Cultivo':<40} {'Share %':>10} {'Contrib HHI':>12}")
print("-" * 70)
for cultivo, share in shares_sin.head(15).items():
    contrib = share ** 2
    print(f"{cultivo:<40} {share:>10.2f} {contrib:>12.2f}")
otros = shares_sin.iloc[15:].sum()
print(f"{'Otros ' + str(len(shares_sin)-15) + ' cultivos':<40} {otros:>10.2f} {(shares_sin.iloc[15:]**2).sum():>12.2f}")
print("-" * 70)
print(f"{'HHI TOTAL':<40} {'100.00':>10} {hhi_sin:>12.2f}")

print("\n" + "=" * 70)
print("INTERPRETACION")
print("=" * 70)
print(f"Con caña:  HHI = {hhi_con:,.0f}  → Monocultivo extremo (cana aporta {(shares_con['Caña']**2 / hhi_con * 100):.1f}% del indice)")
print(f"Sin caña:  HHI = {hhi_sin:,.0f}  → Mercado diversificado ({len(shares_sin)} cultivos, ninguno > {shares_sin.iloc[0]:.1f}%)")
print(f"Efecto de quitar la caña: HHI cae {(hhi_con - hhi_sin):,.0f} puntos ({(1 - hhi_sin/hhi_con)*100:.1f}%)")