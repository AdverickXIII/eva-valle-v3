"""Re-integra EVA 2019-2025 con mapeo EXPLICITO de las 19 columnas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.settings import settings

EXCEL = Path("data/external/eva_2019_2025_valle_del_cauca.xlsx")
HEADER_ROW = 8

# Mapeo completo: columna del modelo -> columna del Excel UPRA
MAPA = {
    "codigo_dane_departamento": "Código Dane departamento",
    "departamento": "Departamento",
    "codigo_dane_municipio": "Código Dane municipio",
    "municipio": "Municipio",
    "desagregacion_cultivo": "Desagregación cultivo",
    "cultivo": "Cultivo",
    "ciclo_del_cultivo": "Ciclo del cultivo",
    "grupo_cultivo": "Grupo cultivo",
    "subgrupo": "Subgrupo",
    "ano": "Año",
    "periodo": "Periodo",
    "area_sembrada_ha": "Área sembrada (ha)",
    "area_cosechada_ha": "Área cosechada (ha)",
    "produccion_t": "Producción (t)",
    "rendimiento_t_ha": "Rendimiento (t/ha)",
    "nombre_cientifico_del_cultivo": "Nombre científico del cultivo",
    "codigo_del_cultivo": "Código del cultivo",
    "estado_fisico_del_cultivo": "Estado físico del cultivo",
}


def main() -> None:
    model_path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    bak = model_path.with_name(model_path.name + ".bak_2019_2024")
    schema = pd.read_csv(bak, nrows=3)
    print(f"Esquema de referencia: {len(schema.columns)} columnas")

    print("Leyendo Excel (header=8)...")
    df = pd.read_excel(EXCEL, header=HEADER_ROW).dropna(how="all")
    mask = df["Departamento"].astype(str).str.contains("valle", case=False, na=False)
    if mask.sum() == 0:
        mask = df["Código Dane departamento"].astype(str).str.strip() == "76"
    df_v = df[mask].copy()
    print(f"Filas Valle del Cauca: {len(df_v):,}")

    nuevo = pd.DataFrame()
    for col in schema.columns:
        if col == "id_registro":
            continue
        src = MAPA.get(col)
        if src and src in df_v.columns:
            nuevo[col] = df_v[src].values
        else:
            nuevo[col] = None
            print(f"[AVISO] '{col}' sin fuente")

    # Tipos
    nuevo["codigo_dane_departamento"] = (
        nuevo["codigo_dane_departamento"].astype(str).str.zfill(2))
    nuevo["codigo_dane_municipio"] = (
        nuevo["codigo_dane_municipio"].astype(str).str.zfill(5))
    nuevo["ano"] = pd.to_numeric(nuevo["ano"], errors="coerce").astype("Int64")
    for c in ("area_sembrada_ha", "area_cosechada_ha",
              "produccion_t", "rendimiento_t_ha"):
        nuevo[c] = pd.to_numeric(nuevo[c], errors="coerce")

    # Regenerar id_registro unico
    nuevo["id_registro"] = [
        f"EVA-{a}-{p}-{m}-{i:05d}"
        for i, (a, p, m) in enumerate(
            zip(nuevo["ano"], nuevo["periodo"], nuevo["codigo_dane_municipio"]), 1)]

    nuevo = nuevo[schema.columns]  # mismo orden de columnas
    nuevo.to_csv(model_path, index=False)

    nulos = nuevo.isna().sum()
    print(f"\n[OK] Modelo re-integrado: {len(nuevo):,} filas")
    print(f"Columnas con nulos: {nulos[nulos > 0].to_dict() or 'NINGUNA'}")
    print(f"Anios: {sorted(nuevo['ano'].dropna().unique())}")
    print(f"Municipios: {nuevo['municipio'].nunique()} | Cultivos: {nuevo['cultivo'].nunique()}")
    print(f"Produccion 2025: {nuevo[nuevo['ano']==2025]['produccion_t'].sum():,.0f} t")
    print(f"\nMuestra id_registro: {nuevo['id_registro'].head(2).tolist()}")


if __name__ == "__main__":
    main()