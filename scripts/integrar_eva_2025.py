"""Integra EVA 2019-2025 al modelo conceptual con respaldo automatico."""
import shutil
import unicodedata
from pathlib import Path

import pandas as pd

import sys
from pathlib import Path as _ROOT
sys.path.insert(0, str(_ROOT(__file__).resolve().parent.parent))

from config.settings import settings

EXCEL = Path("data/external/eva_2019_2025_valle_del_cauca.xlsx")
HEADER_ROW = 8

MAPA = {
    "codigo_dane_municipio": "Código Dane municipio",
    "municipio": "Municipio",
    "cultivo": "Cultivo",
    "grupo_cultivo": "Grupo cultivo",
    "ano": "Año",
    "periodo": "Periodo",
    "area_sembrada_ha": "Área sembrada (ha)",
    "area_cosechada_ha": "Área cosechada (ha)",
    "produccion_t": "Producción (t)",
    "rendimiento_t_ha": "Rendimiento (t/ha)",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def main() -> None:
    model_path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    current = pd.read_csv(model_path, nrows=3)
    print(f"Columnas del modelo actual: {current.columns.tolist()}")
    print(f"Filas actuales: {len(pd.read_csv(model_path)):,}")

    print("\nLeyendo Excel (header=8)...")
    df = pd.read_excel(EXCEL, header=HEADER_ROW).dropna(how="all")
    print(f"Filas leidas: {len(df):,}")

    # Filtrar Valle del Cauca (nombre o codigo 76)
    mask = df["Departamento"].astype(str).str.contains("valle", case=False, na=False)
    if mask.sum() == 0:
        mask = df["Código Dane departamento"].astype(str).str.strip() == "76"
    df_v = df[mask].copy()
    print(f"Filas de Valle del Cauca: {len(df_v):,}")

    # Mapeo por nombre normalizado como respaldo
    cols_norm = {_norm(c): c for c in df_v.columns}

    nuevo = pd.DataFrame()
    for col in current.columns:
        src = MAPA.get(col) or cols_norm.get(_norm(col))
        if src and src in df_v.columns:
            nuevo[col] = df_v[src].values
        else:
            nuevo[col] = None
            print(f"[AVISO] columna '{col}' sin fuente, queda vacia")

    # Tipos
    nuevo["codigo_dane_municipio"] = (
        nuevo["codigo_dane_municipio"].astype(str).str.zfill(5))
    nuevo["ano"] = pd.to_numeric(nuevo["ano"], errors="coerce").astype("Int64")
    for c in ("area_sembrada_ha", "area_cosechada_ha",
              "produccion_t", "rendimiento_t_ha"):
        if c in nuevo.columns:
            nuevo[c] = pd.to_numeric(nuevo[c], errors="coerce")

    # Respaldo + guardado
    bak = model_path.with_name(model_path.name + ".bak_2019_2024")
    if not bak.exists():
        shutil.copy(model_path, bak)
        print(f"\n[OK] Respaldo creado: {bak.name}")
    nuevo.to_csv(model_path, index=False)

    print(f"\n[OK] Modelo actualizado: {len(nuevo):,} filas")
    print(f"Anios: {sorted(nuevo['ano'].dropna().unique())}")
    print(f"Municipios: {nuevo['municipio'].nunique()}")
    print(f"Cultivos: {nuevo['cultivo'].nunique()}")
    print(f"Produccion 2025: {nuevo[nuevo['ano']==2025]['produccion_t'].sum():,.0f} t")

    # .gitignore: excluir el Excel pesado
    gi = Path(".gitignore")
    txt = gi.read_text(encoding="utf-8")
    linea = "data/external/eva_2019_2025_valle_del_cauca.xlsx"
    if linea not in txt:
        gi.write_text(txt.rstrip() + f"\n# Excel pesado EVA 2019-2025\n{linea}\n",
                      encoding="utf-8")
        print("[OK] .gitignore actualizado (Excel excluido)")


if __name__ == "__main__":
    main()