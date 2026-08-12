"""Prueba las matrices estrategicas con datos reales."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from config.settings import settings
from core.analytics.strategic_matrices import (
    matriz_cultivos, matriz_municipios, resumen_matrices,
)

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)

print("=" * 65)
print("MATRIZ 1: CULTIVOS (crecimiento x participacion)")
print("=" * 65)
mc = matriz_cultivos(df)
print(mc[["cultivo", "participacion_pct", "cagr", "cuadrante"]].head(12).to_string(index=False))
print(f"\nTotal cultivos analizados: {len(mc)}")

print("\n" + "=" * 65)
print("MATRIZ 2: MUNICIPIOS (produccion x productividad)")
print("=" * 65)
mm = matriz_municipios(df)
print(mm[["municipio", "produccion", "rendimiento", "productividad_relativa", "cuadrante"]].head(12).to_string(index=False))
print(f"\nTotal municipios analizados: {len(mm)}")

print("\n" + "=" * 65)
print("RESUMEN NARRATIVO")
print("=" * 65)
r = resumen_matrices(df)
print("\nCULTIVOS:")
print(f"  Motores ({r['cultivos']['n_motores']}): {r['cultivos']['motores']}")
print(f"  Consolidados ({r['cultivos']['n_consolidados']}): {r['cultivos']['consolidados']}")
print(f"  Emergentes ({r['cultivos']['n_emergentes']}): {r['cultivos']['emergentes']}")
print(f"  Rezagados ({r['cultivos']['n_rezagados']}): {r['cultivos']['rezagados']}")
print("\nMUNICIPIOS:")
print(f"  Motores ({r['municipios']['n_motores']}): {r['municipios']['motores']}")
print(f"  Mejora ({r['municipios']['n_mejora']}): {r['municipios']['mejora']}")
print(f"  Potenciales ({r['municipios']['n_potenciales']}): {r['municipios']['potenciales']}")
print(f"  Rezagados ({r['municipios']['n_rezagados']}): {r['municipios']['rezagados']}")