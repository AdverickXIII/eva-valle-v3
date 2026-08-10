"""Inspeccion v2: detecta encabezado real del Excel UPRA (filas de portada)."""
import unicodedata
from pathlib import Path

import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 28)

path = Path("data/external/eva_2019_2025_valle_del_cauca.xlsx")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def main():
    print("Leyendo sin encabezado (para ver estructura cruda)...")
    raw = pd.read_excel(path, header=None)

    print("\nPrimeras 12 filas crudas:")
    print(raw.head(12))

    # Detectar fila de encabezado: debe tener municipio + cultivo + produccion
    header_row = None
    for i in range(min(25, len(raw))):
        joined = " ".join(_norm(v) for v in raw.iloc[i].tolist())
        if "municipio" in joined and "cultivo" in joined:
            header_row = i
            break

    print(f"\n>>> Fila de encabezado detectada: {header_row}")
    if header_row is None:
        print("[ERROR] No se detecto el encabezado. Revisa las 12 filas crudas arriba.")
        return

    # Leer con el encabezado correcto
    df = pd.read_excel(path, header=header_row)
    # Eliminar filas vacias o de notas residuales
    df = df.dropna(how="all")

    print(f"\n{'='*60}")
    print(f"COLUMNAS REALES ({len(df.columns)})")
    print(f"{'='*60}")
    for i, c in enumerate(df.columns, 1):
        print(f"{i:2d}. {c}")

    print(f"\nFilas de datos: {len(df):,}")

    cols_norm = {_norm(c): c for c in df.columns}

    # Anios
    anio = cols_norm.get("ano") or cols_norm.get("anio") or \
           next((c for k, c in cols_norm.items() if "ano" in k and "periodo" not in k), None)
    if anio:
        print(f"\n>>> Columna ano: '{anio}'")
        print(f"Anios: {sorted(df[anio].dropna().unique())}")

    # Departamento
    dpto = next((c for k, c in cols_norm.items() if "departamento" in k or k == "dpto"), None)
    if dpto:
        print(f"\n>>> Columna departamento: '{dpto}'")
        deps = sorted(str(d) for d in df[dpto].dropna().unique())
        print(f"Total departamentos: {len(deps)}")
        valle = [d for d in deps if "valle" in _norm(d)]
        print(f"Valor(es) de Valle: {valle}")

    # Municipio
    muni = next((c for k, c in cols_norm.items() if "municipio" in k), None)
    if muni and dpto:
        df_v = df[df[dpto].astype(str).map(lambda x: "valle" in _norm(x))]
        print(f"\n>>> Filas de Valle del Cauca: {len(df_v):,}")
        print(f"Municipios del Valle: {df_v[muni].nunique()}")

    print(f"\n{'='*60}")
    print("MUESTRA (5 filas de Valle si existe)")
    print(f"{'='*60}")
    if dpto:
        print(df[df[dpto].astype(str).map(lambda x: "valle" in _norm(x))].head())
    else:
        print(df.head())


if __name__ == "__main__":
    main()