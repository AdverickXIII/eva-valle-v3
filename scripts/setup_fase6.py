"""Fase 6: crea ui/services/ y aplica manejo de errores global a las paginas."""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ui/services/__init__.py
# ═══════════════════════════════════════════════════════════
SERVICES_INIT = '''"""Servicios de UI: carga de datos, logging y manejo de errores."""
from ui.services.data_service import load_model_dataset, validate_dataset
from ui.services.error_handler import run_safe, safe_page
from ui.services.ui_logger import log_action

__all__ = ["load_model_dataset", "validate_dataset", "run_safe", "safe_page", "log_action"]
'''

# ═══════════════════════════════════════════════════════════
# ui/services/data_service.py
# ═══════════════════════════════════════════════════════════
DATA_SERVICE = '''"""Servicio centralizado de carga y validacion de datos para la UI."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import settings

COLUMNAS_REQUERIDAS = [
    "municipio", "cultivo", "grupo_cultivo", "ano", "periodo",
    "area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha",
]


@st.cache_data(ttl=3600)
def load_model_dataset() -> pd.DataFrame:
    """Carga el dataset del modelo conceptual con cache de 1 hora."""
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def validate_dataset(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Verifica que el dataset tenga las columnas requeridas y datos.

    Returns:
        Tupla (es_valido, lista_de_problemas).
    """
    problemas = []
    if df is None or df.empty:
        return False, ["El dataset esta vacio o no existe. Ejecuta el pipeline."]
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        problemas.append(f"Columnas faltantes: {faltantes}")
    return (len(problemas) == 0), problemas
'''

# ═══════════════════════════════════════════════════════════
# ui/services/ui_logger.py
# ═══════════════════════════════════════════════════════════
UI_LOGGER = '''"""Logging de acciones del usuario en la UI."""
from __future__ import annotations

from core.logging import get_logger

log = get_logger("ui.actions")


def log_action(action: str, detalle: str = "") -> None:
    """Registra una accion del usuario en el log del sistema."""
    log.info("UI | %s %s", action, detalle)
'''

# ═══════════════════════════════════════════════════════════
# ui/services/error_handler.py
# ═══════════════════════════════════════════════════════════
ERROR_HANDLER = '''"""Manejo de errores global para paginas Streamlit."""
from __future__ import annotations

import functools

import streamlit as st

from core.logging import get_logger

log = get_logger("ui.errors")


def run_safe(main_func) -> None:
    """Ejecuta el main de una pagina con manejo de errores global."""
    try:
        main_func()
    except Exception as e:
        log.error("Error en pagina: %s", e)
        st.error(f"Ocurrio un error inesperado: {e}")
        st.info(
            "Intenta recargar la pagina, o verifica que el pipeline "
            "se haya ejecutado: python scripts/run_pipeline.py --skip-download"
        )


def safe_page(func):
    """Decorador que envuelve una pagina con manejo de errores."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.error("Error en pagina: %s", e)
            st.error(f"Ocurrio un error inesperado: {e}")
    return wrapper
'''

# ═══════════════════════════════════════════════════════════
# APLICAR run_safe A LAS 7 PAGINAS
# ═══════════════════════════════════════════════════════════
PAGINAS = [
    "ui/pages/1_Dashboard.py",
    "ui/pages/2_Descriptivo.py",
    "ui/pages/3_Diagnostico.py",
    "ui/pages/4_Predictivo.py",
    "ui/pages/5_Auditoria.py",
    "ui/pages/6_Configuracion.py",
    "ui/pages/7_Cultivos.py",
]

MARKER_PATH = "sys.path.insert(0, str(Path(__file__).parent.parent.parent))"
IMPORT_RUNSAFE = "from ui.services.error_handler import run_safe"


def aplicar_a_pagina(ruta: str) -> str:
    path = Path(ruta)
    if not path.exists():
        return f"[SKIP] {ruta} no existe"

    content = path.read_text(encoding="utf-8")
    cambios = 0

    # 1. Añadir import de run_safe despues del sys.path.insert
    if MARKER_PATH in content and IMPORT_RUNSAFE not in content:
        content = content.replace(MARKER_PATH, MARKER_PATH + "\n" + IMPORT_RUNSAFE, 1)
        cambios += 1

    # 2. Reemplazar la llamada final main() por run_safe(main)
    idx = content.rfind("main()")
    if idx != -1 and "run_safe(main)" not in content:
        content = content[:idx] + "run_safe(main)" + content[idx + len("main()"):]
        cambios += 1

    if cambios > 0:
        path.write_text(content, encoding="utf-8")
        return f"[OK] {ruta} ({cambios} cambios)"
    return f"[INFO] {ruta} ya estaba actualizada"


if __name__ == "__main__":
    # 1. Crear servicios
    servicios = {
        "ui/services/__init__.py": SERVICES_INIT,
        "ui/services/data_service.py": DATA_SERVICE,
        "ui/services/ui_logger.py": UI_LOGGER,
        "ui/services/error_handler.py": ERROR_HANDLER,
    }
    for ruta, contenido in servicios.items():
        p = Path(ruta)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")

    # 2. Aplicar manejo de errores a las paginas
    print("\nAplicando manejo de errores global:")
    for pagina in PAGINAS:
        print("  " + aplicar_a_pagina(pagina))

    print("\nFase 6 aplicada. Ejecuta: streamlit run app.py")