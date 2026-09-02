"""Agrega save_png al helper io_utils.py de forma segura e idempotente.

Estandar de generadores del proyecto: backup .bak, py_compile con rollback,
marcador de idempotencia, chequeo de dependencias y codigos de salida reales.
"""
import py_compile
import shutil
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / "core" / "ml" / "io_utils.py"

FN_TEMPLATE = '''

def save_png(name: str, fig) -> Path:
    """Guarda una figura de matplotlib como PNG dentro de RESULTS.

    Args:
        name: Nombre del archivo (ej. "grafico.png").
        fig: Figura de matplotlib a guardar.

    Returns:
        Ruta completa del archivo guardado.
    """
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS / name
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    print(f"[OK] guardado: {out_path}")
    return out_path
'''


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] no existe el archivo: {TARGET}")
        return 1

    content = TARGET.read_text(encoding="utf-8")

    if "def save_png" in content:
        print("[SKIP] save_png ya existe en io_utils.py")
        return 0

    if "RESULTS" not in content:
        print("[ERROR] io_utils.py no define RESULTS; abortando para no inyectar codigo roto.")
        return 1

    # PEP8: "\n" termina la ultima linea original y el template aporta
    # sus dos "\n" iniciales -> exactamente dos lineas en blanco.
    new_content = content.rstrip("\n") + "\n" + FN_TEMPLATE

    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(new_content, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"[ERROR] sintaxis invalida tras la insercion, revirtiendo: {e}")
        shutil.copy2(backup, TARGET)
        return 1

    print("[OK] save_png agregado a io_utils.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())