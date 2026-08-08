"""Corrige run_step_3_modeling para que guarde el CSV del modelo conceptual."""
from pathlib import Path

filepath = Path("scripts/run_pipeline.py")
content = filepath.read_text(encoding="utf-8")

# Buscar la funcion run_step_3_modeling y reemplazarla
old_func = '''def run_step_3_modeling() -> bool:
    """Ejecuta el Paso 3: Modelado Conceptual."""
    log_section("PASO 3 - MODELADO CONCEPTUAL")
    try:
        from core.modeling import run_conceptual_modeling
        df_modelo, artefactos = run_conceptual_modeling()
        log.info("Paso 3 completado: %d registros", len(df_modelo))
        return True
    except Exception as e:
        log.error("Error en Paso 3: %s", e)
        return False'''

new_func = '''def run_step_3_modeling() -> bool:
    """Ejecuta el Paso 3: Modelado Conceptual."""
    log_section("PASO 3 - MODELADO CONCEPTUAL")
    try:
        from core.modeling import run_conceptual_modeling
        from config.settings import settings
        df_modelo, artefactos = run_conceptual_modeling()
        # Guardar el CSV del modelo conceptual (requerido por Pasos 4, 6, 7)
        ruta = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        df_modelo.to_csv(ruta, index=False, encoding="utf-8-sig")
        log.info("Paso 3 completado: %d registros. Guardado: %s", len(df_modelo), ruta.name)
        return True
    except Exception as e:
        log.error("Error en Paso 3: %s", e)
        return False'''

if old_func in content:
    content = content.replace(old_func, new_func)
    filepath.write_text(content, encoding="utf-8")
    print("[OK] run_step_3_modeling corregida en run_pipeline.py")
else:
    print("[WARN] No se encontro la funcion exacta. Intentando parche alternativo...")
    # Parche alternativo: buscar solo la linea de return True y agregar el guardado antes
    if "df_modelo, artefactos = run_conceptual_modeling()" in content:
        old_line = "        df_modelo, artefactos = run_conceptual_modeling()\n        log.info"
        new_line = """        df_modelo, artefactos = run_conceptual_modeling()
        # Guardar el CSV del modelo conceptual (requerido por Pasos 4, 6, 7)
        from config.settings import settings as _s
        _ruta = _s.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
        _ruta.parent.mkdir(parents=True, exist_ok=True)
        df_modelo.to_csv(_ruta, index=False, encoding="utf-8-sig")
        log.info"""
        content = content.replace(old_line, new_line)
        filepath.write_text(content, encoding="utf-8")
        print("[OK] Parche alternativo aplicado.")
    else:
        print("[ERROR] No se pudo aplicar el parche. Ejecuta la solucion inmediata.")