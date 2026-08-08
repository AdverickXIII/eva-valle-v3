"""
Script de correccion: añade sys.path fix a los scripts CLI.
Ejecutar una sola vez: python scripts/fix_cli_imports.py

Causa del problema:
  Cuando se ejecuta `python scripts/run_pipeline.py`, Python añade
  el directorio `scripts/` al sys.path, pero NO la raíz del proyecto.
  Por eso no encuentra el módulo `config`.

Solucion:
  Insertar al inicio de cada script (despues del docstring):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
"""
from pathlib import Path

# El bloque de codigo a insertar
PATH_FIX = '''import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path para que los imports funcionen
sys.path.insert(0, str(Path(__file__).parent.parent))

'''

SCRIPTS_A_CORREGIR = [
    "scripts/download_data.py",
    "scripts/run_pipeline.py",
    "scripts/run_audit.py",
    "scripts/export_report.py",
]


def fix_script(filepath: Path) -> bool:
    """
    Inserta el sys.path fix al inicio del script, después del docstring.
    Retorna True si se modificó, False si ya tenía el fix.
    """
    if not filepath.exists():
        print(f"[SKIP] {filepath} no existe.")
        return False

    contenido = filepath.read_text(encoding="utf-8")

    # Verificar si ya tiene el fix
    if "sys.path.insert(0, str(Path(__file__).parent.parent))" in contenido:
        print(f"[OK] {filepath} ya tiene el fix. Sin cambios.")
        return False

    lineas = contenido.split("\n")
    nueva_lineas = []
    docstring_cerrado = False
    fix_insertado = False
    en_docstring = False

    for i, linea in enumerate(lineas):
        stripped = linea.strip()

        # Detectar inicio de docstring al inicio del archivo
        if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
            en_docstring = True
            nueva_lineas.append(linea)
            # Verificar si el docstring cierra en la misma línea
            if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                en_docstring = False
                docstring_cerrado = True
            continue

        # Detectar cierre de docstring
        if en_docstring:
            nueva_lineas.append(linea)
            if '"""' in stripped or "'''" in stripped:
                en_docstring = False
                docstring_cerrado = True
            continue

        # Si ya cerró el docstring y no hemos insertado el fix, insertarlo
        if docstring_cerrado and not fix_insertado:
            nueva_lineas.append("")  # Línea en blanco
            nueva_lineas.append(PATH_FIX.rstrip())  # El fix
            fix_insertado = True
            docstring_cerrado = False  # Ya no estamos en docstring

        nueva_lineas.append(linea)

    # Si no había docstring, insertar al inicio
    if not fix_insertado:
        nueva_lineas = [PATH_FIX.rstrip()] + lineas

    nuevo_contenido = "\n".join(nueva_lineas)
    filepath.write_text(nuevo_contenido, encoding="utf-8")
    print(f"[OK] {filepath} corregido")
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