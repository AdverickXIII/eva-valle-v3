"""Fase 7.2: aplica wrappers cacheados a las paginas Descriptivo y Diagnostico."""
from pathlib import Path

MARKER_PATH = "sys.path.insert(0, str(Path(__file__).parent.parent.parent))"
IMPORT_CACHE = (
    "from ui.services.performance import (cached_outliers, cached_time_series, "
    "cached_seasonality, cached_segmentation, cached_root_cause)"
)

# Reemplazos: llamada directa -> version cacheada
REEMPLAZOS = {
    "detect_multivariate_outliers(df_f)": "cached_outliers(df_f)",
    "analyze_time_series(df_f)": "cached_time_series(df_f)",
    "test_seasonality_ab(df_f)": "cached_seasonality(df_f)",
    "segment_municipalities(df_f)": "cached_segmentation(df_f)",
    "find_root_causes(df_f)": "cached_root_cause(df_f)",
}

PAGINAS = [
    "ui/pages/2_Descriptivo.py",
    "ui/pages/3_Diagnostico.py",
]


def aplicar(ruta: str) -> str:
    path = Path(ruta)
    if not path.exists():
        return f"[SKIP] {ruta} no existe"

    content = path.read_text(encoding="utf-8")
    cambios = 0

    # 1. Import de wrappers cacheados
    if MARKER_PATH in content and "cached_outliers" not in content:
        content = content.replace(MARKER_PATH, MARKER_PATH + "\n" + IMPORT_CACHE, 1)
        cambios += 1

    # 2. Reemplazar llamadas directas por cacheadas
    for viejo, nuevo in REEMPLAZOS.items():
        if viejo in content:
            content = content.replace(viejo, nuevo)
            cambios += 1

    if cambios > 0:
        path.write_text(content, encoding="utf-8")
        return f"[OK] {ruta} ({cambios} cambios)"
    return f"[INFO] {ruta} ya estaba optimizada"


if __name__ == "__main__":
    print("Aplicando cache a analisis pesados:")
    for pagina in PAGINAS:
        print("  " + aplicar(pagina))
    print("\nListo. Ejecuta: streamlit run app.py")