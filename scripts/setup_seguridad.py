"""Agrega archivos sensibles/legacy al .gitignore."""
from pathlib import Path

lineas = [".env", ".vscode/", "config_app.py", "config_base.py", "crear_estructura.py"]
p = Path(".gitignore")
txt = p.read_text(encoding="utf-8") if p.exists() else ""

add = [l for l in lineas if l not in txt]
if add:
    with p.open("a", encoding="utf-8") as f:
        f.write("\n# Archivos locales / legacy (seguridad)\n")
        for l in add:
            f.write(l + "\n")
    print("[OK] .gitignore actualizado:")
    for l in add:
        print("   +", l)
else:
    print("[INFO] .gitignore ya tenia todas las entradas")