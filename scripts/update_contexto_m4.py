"""Registra el Módulo 4 en CONTEXTO.md, insertándolo después del bloque del Módulo 3.

Estándar de generadores del proyecto: ruta absoluta desde __file__,
backup con shutil.copy2, ancla con fallo seguro, verificación post-replace,
inserción tras el bloque completo (no en medio) y códigos de salida reales.
"""
import shutil
import sys
from pathlib import Path

CONTEXTO_PATH = Path(__file__).resolve().parent.parent / "CONTEXTO.md"
ANCLA = "- Modulo 3 (Bandits)"

BLOQUE_MODULO_4 = """- Modulo 4 (CNN): clasificacion de vocacion productiva (imagenes 12x7)
  - CNN acc test 91.67% vs baseline 83.33% (+8.33%), n=42 municipios
  - Hallazgo: Filtro 1 es detector especializado de vocacion bananera (activa 2.77 vs 0.3-0.5)
  - Limitacion: desbalance de clases (Banano 1 train / 0 test) infla el accuracy
  - Artefactos: core/ml/cnn_scratch.py, notebooks/curso/04_cnn_patrones_espaciales.ipynb,
    core/ml/results/m4_*.json/csv/png
"""


def insertar_despues_del_bloque(contenido: str, ancla: str, bloque: str) -> str:
    """Inserta `bloque` después del bloque completo que empieza con `ancla`
    (tras sus sub-lineas indentadas), no en medio de él.

    Si no hay otro bloque después, anexa al final del documento.
    """
    idx = contenido.find(ancla)
    if idx == -1:
        return contenido
    sig = contenido.find("\n- ", idx + len(ancla))
    pos = sig if sig != -1 else len(contenido)
    return contenido[:pos] + "\n" + bloque + contenido[pos:]


def main() -> int:
    if not CONTEXTO_PATH.exists():
        print(f"[ERROR] no existe el archivo: {CONTEXTO_PATH}")
        return 1

    contenido = CONTEXTO_PATH.read_text(encoding="utf-8")

    if "Modulo 4 (CNN)" in contenido:
        print("[SKIP] Modulo 4 ya está registrado en CONTEXTO.md")
        return 0

    if ANCLA not in contenido:
        print(f"[ERROR] no se encontró el ancla {ANCLA!r}; no se modificó el archivo")
        return 1

    # Backup por seguridad antes de escribir
    backup_path = CONTEXTO_PATH.with_suffix(".md.bak")
    shutil.copy2(CONTEXTO_PATH, backup_path)

    # Inserción DESPUÉS del bloque completo de Módulo 3 (orden cronológico)
    nuevo_contenido = insertar_despues_del_bloque(contenido, ANCLA, BLOQUE_MODULO_4)

    if nuevo_contenido == contenido:
        print("[ERROR] el reemplazo no tuvo efecto; no se modificó el archivo")
        return 1

    CONTEXTO_PATH.write_text(nuevo_contenido, encoding="utf-8")
    print("[OK] CONTEXTO.md actualizado: Modulo 4 insertado tras el bloque de Modulo 3")
    print(f"[INFO] backup guardado en: {backup_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())