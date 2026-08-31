"""Tierra rural Valle del Cauca (v6: diagnostico de columnas reales)."""
import pandas as pd
import requests
from io import StringIO

URL = "https://www.datos.gov.co/resource/rttb-pk7n.csv"

print("=== 1) Descarga (ya tienes 1.8GB, esto reutiliza si es posible) ===")
print("Descargando dataset completo...")
r = requests.get(URL, timeout=600)
print(f"HTTP {r.status_code} | {len(r.content) / 1e6:.1f} MB")

print("\n=== 2) Lectura CSV (omitiendo the_geom por peso) ===")
peek = pd.read_csv(StringIO(r.text), nrows=2)
print(f"Columnas completas: {peek.columns.tolist()}")
use_cols = [c for c in peek.columns if c != "the_geom"]
df = pd.read_csv(StringIO(r.text), usecols=use_cols, low_memory=False)
print(f"Total filas: {len(df):,}")

print("\n=== 3) Filtrado al Valle del Cauca ===")
print("Valores únicos de cod_depart (primeros 10):")
print(df["cod_depart"].value_counts().head(10))
valle = df[df["cod_depart"].astype(str).str.strip() == "76"]
print(f"Filas del Valle: {len(valle):,}")

print("\n=== 4) Columnas disponibles en Valle ===")
print(valle.columns.tolist())

print("\n=== 5) Tipos de datos ===")
print(valle.dtypes)

print("\n=== 6) Muestra de 5 filas ===")
print(valle.head().to_string())

print("\n=== 7) Municipios del Valle en el dataset ===")
munis = sorted(valle["municipio"].dropna().unique())
print(f"Municipios ({len(munis)}): {munis}")

print("\n=== 8) Rangos de precios ===")
rango_col = [c for c in valle.columns if "rango" in c.lower() or "precio" in c.lower()]
print(f"Columnas candidatas: {rango_col}")
for col in rango_col:
    print(f"\n{col}:")
    print(valle[col].value_counts())

print("\n=== 9) Area (ha) ===")
area_col = [c for c in valle.columns if "area" in c.lower() or "ha" in c.lower()]
print(f"Columnas candidatas: {area_col}")
if area_col:
    valle[area_col[0]] = pd.to_numeric(valle[area_col[0]], errors="coerce")
    print(valle[area_col[0]].describe())
    print(f"Area total (ha): {valle[area_col[0]].sum():,.0f}")