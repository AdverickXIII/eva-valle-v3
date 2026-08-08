"""
Script de correccion v2: mueve el sys.path fix DESPUES del from __future__.
Ejecutar una sola vez: python scripts/fix_cli_imports_v2.py

Causa del problema:
  El fix anterior inserto sys.path ANTES del from __future__ import,
  violando la regla de Python que exige __future__ al inicio del archivo.

Solucion:
  1. Eliminar el fix anterior (si existe)
  2. Insertar el fix DESPUES del from __future__ import
  3. Si no hay __future__, insertar despues del docstring
"""
from pathlib import Path
import re

SCRIPTS_A_CORREGIR = [
    "scripts/download_data.py",
    "scripts/run_pipeline.py",
    "scripts/run_audit.py",
    "scripts/export_report.py",
]

# El bloque de codigo a insertar (sin la linea de __future__)
PATH_FIX_LINES = [
    "import sys",
    "from pathlib import Path",
    "",
    "# Añadir la raíz del proyecto al sys.path para que los imports funcionen",
    "sys.path.insert(0, str(Path(__file__).parent.parent))",
    "",
]


def fix_script(filepath: Path) -> bool:
    """
    Corrige un script CLI:
    1. Elimina el fix anterior si existe
    2. Inserta el fix DESPUES del from __future__ import
    """
    if not filepath.exists():
        print(f"[SKIP] {filepath} no existe.")
        return False

    contenido = filepath.read_text(encoding="utf-8")
    lineas = contenido.split("\n")

    # Paso 1: Eliminar el fix anterior si existe
    lineas_limpias = []
    skip_next_empty = False
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        stripped = linea.strip()

        # Detectar el inicio del fix anterior
        if stripped == "import sys" and i + 1 < len(lineas):
            # Verificar si las siguientes líneas son parte del fix
            next_stripped = lineas[i + 1].strip() if i + 1 < len(lineas) else ""
            if next_stripped == "from pathlib import Path":
                # Saltar el bloque del fix (hasta la línea de sys.path.insert)
                j = i
                while j < len(lineas):
                    if "sys.path.insert" in lineas[j]:
                        j += 1
                        # Saltar líneas vacías después del fix
                        while j < len(lineas) and lineas[j].strip() == "":
                            j += 1
                        break
                    j += 1
                i = j
                continue

        lineas_limpias.append(linea)
        i += 1

    # Paso 2: Encontrar la posición correcta para insertar el fix
    insert_pos = None

    # Buscar from __future__ import
    for idx, linea in enumerate(lineas_limpias):
        if linea.strip().startswith("from __future__ import"):
            insert_pos = idx + 1
            break

    # Si no hay __future__, buscar el final del docstring
    if insert_pos is None:
        en_docstring = False
        for idx, linea in enumerate(lineas_limpias):
            stripped = linea.strip()
            if idx == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
                en_docstring = True
                if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                    insert_pos = idx + 1
                    break
                continue
            if en_docstring:
                if '"""' in stripped or "'''" in stripped:
                    insert_pos = idx + 1
                    break

    # Si no se encontró docstring ni __future__, insertar al inicio
    if insert_pos is None:
        insert_pos = 0

    # Paso 3: Insertar el fix en la posición correcta
    lineas_finales = lineas_limpias[:insert_pos] + PATH_FIX_LINES + lineas_limpias[insert_pos:]

    # Escribir el archivo corregido
    nuevo_contenido = "\n".join(lineas_finales)
    filepath.write_text(nuevo_contenido, encoding="utf-8")
    print(f"[OK] {filepath} corregido (fix movido después de __future__)")
    return True


def main() -> int:
    """Punto de entrada principal."""
    corregidos = 0
    for script_path in SCRIPTS_A_CORREGIR:
        filepath = Path(script_path)
        if fix_script(filepath):
            corregidos += 1

    print(f"\n{corregidos} scripts CLI corregidos.")
    print("Ejecuta: python scripts\\run_pipeline.py --help")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())