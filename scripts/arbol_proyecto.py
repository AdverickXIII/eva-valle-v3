"""Imprime el arbol del proyecto excluyendo carpetas de ruido. Solo lectura."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXCLUIDAS = {".venv", ".git", "__pycache__", ".ipynb_checkpoints",
             "node_modules", ".streamlit", ".idea", ".vscode"}

def arbol(dirp: Path, prefijo: str = "") -> None:
    entradas = sorted(
        (e for e in dirp.iterdir()
         if e.name not in EXCLUIDAS and not e.name.endswith(".bak")),
        key=lambda e: (e.is_file(), e.name.lower()),
    )
    for i, e in enumerate(entradas):
        ultimo = i == len(entradas) - 1
        conector = "└── " if ultimo else "├── "
        sufijo = "" if e.is_file() else "/"
        print(f"{prefijo}{conector}{e.name}{sufijo}")
        if e.is_dir():
            arbol(e, prefijo + ("    " if ultimo else "│   "))

print(f"{RAIZ.name}/")
arbol(RAIZ)