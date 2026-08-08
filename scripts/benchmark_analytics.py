"""Mide el tiempo de cada analisis pesado con los datos reales."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from config.settings import settings


def medir(nombre: str, func, *args) -> float:
    t0 = time.perf_counter()
    try:
        func(*args)
        ok = "OK "
    except Exception as e:
        ok = "ERR"
        print(f"     {nombre}: {e}")
    t1 = time.perf_counter()
    ms = (t1 - t0) * 1000
    print(f"  [{ok}] {nombre:<38} {ms:>9,.0f} ms")
    return ms


def main() -> None:
    print("\n" + "=" * 60)
    print("  BENCHMARK DE ANALISIS (datos reales)")
    print("=" * 60)

    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        print("Dataset no encontrado. Ejecuta el pipeline primero.")
        return

    t0 = time.perf_counter()
    df = pd.read_csv(path, low_memory=False)
    print(f"  Carga del dataset: {(time.perf_counter()-t0)*1000:,.0f} ms ({len(df)} filas)")
    print("-" * 60)

    from core.analytics.concentration import calculate_concentration
    from core.analytics.descriptive import calculate_descriptive_statistics
    from core.analytics.outliers import detect_multivariate_outliers
    from core.analytics.seasonality import test_seasonality_ab
    from core.analytics.spatial import calculate_location_quotient, calculate_shannon_diversity
    from core.analytics.time_series import analyze_time_series
    from core.diagnostics.root_cause import find_root_causes
    from core.diagnostics.segmentation import segment_municipalities

    resultados = []
    resultados.append(("4.3 Descriptiva", medir("4.3 Descriptiva", calculate_descriptive_statistics, df)))
    resultados.append(("4.6 Concentracion (Gini)", medir("4.6 Concentracion", calculate_concentration, df)))
    resultados.append(("4.5 Outliers (IsolationForest)", medir("4.5 Outliers", detect_multivariate_outliers, df)))
    resultados.append(("4.7 Series tiempo (STL)", medir("4.7 STL", analyze_time_series, df)))
    resultados.append(("4.8 Estacionalidad (Wilcoxon)", medir("4.8 Wilcoxon", test_seasonality_ab, df)))
    resultados.append(("4.9 Location Quotient", medir("4.9 LQ", calculate_location_quotient, df)))
    resultados.append(("4.10 Shannon-Wiener", medir("4.10 Shannon", calculate_shannon_diversity, df)))
    resultados.append(("6.3 K-Means + silueta", medir("6.3 K-Means", segment_municipalities, df)))
    resultados.append(("6.4 Arbol decision", medir("6.4 Arbol", find_root_causes, df)))

    print("-" * 60)
    total = sum(r[1] for r in resultados)
    mas_lento = max(resultados, key=lambda r: r[1])
    print(f"  TOTAL: {total:,.0f} ms")
    print(f"  MAS LENTO: {mas_lento[0]} ({mas_lento[1]:,.0f} ms)")
    print("\n  Los analisis > 500 ms son candidatos a cache en la Sub-fase 7.2.")


if __name__ == "__main__":
    main()