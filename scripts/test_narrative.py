"""Prueba el motor narrativo con datos reales."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from config.settings import settings
from core.analytics.narrative_engine import (
    generar_insights, frase_de_la_agricultura, resumen_ejecutivo_narrativo,
)

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)

print("=" * 80)
print("INSIGHTS AUTOMATICOS (DATO / INTERPRETACION / IMPLICACION)")
print("=" * 80)
insights = generar_insights(df)
for i, ins in enumerate(insights, 1):
    print(f"\n{i}. DATO:")
    print(f"   {ins['dato']}")
    print(f"   INTERPRETACION:")
    print(f"   {ins['interpretacion']}")
    print(f"   IMPLICACION:")
    print(f"   {ins['implicacion']}")

print("\n" + "=" * 80)
print("FRASE DE LA AGRICULTURA (cierre memorable)")
print("=" * 80)
frase = frase_de_la_agricultura(df)
print(f"\n{frase}\n")

print("=" * 80)
print("RESUMEN COMPLETO")
print("=" * 80)
resumen = resumen_ejecutivo_narrativo(df)
print(f"Total insights generados: {resumen['total_insights']}")
print(f"Frase de cierre: {resumen['frase_cierre'][:100]}...")