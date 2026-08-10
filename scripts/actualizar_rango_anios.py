"""Actualiza 2019-2024 -> 2019-2025 en core/, ui/ y app.py."""
from pathlib import Path

raices = [Path("core"), Path("ui"), Path("app.py")]
total = 0
for raiz in raices:
    archivos = [raiz] if raiz.is_file() else list(raiz.rglob("*.py"))
    for p in archivos:
        if not p.exists():
            continue
        c = p.read_text(encoding="utf-8")
        if "2019-2024" in c:
            n = c.count("2019-2024")
            c = c.replace("2019-2024", "2019-2025")
            p.write_text(c, encoding="utf-8")
            total += n
            print(f"[OK] {p} ({n} reemplazos)")

print(f"\nTotal reemplazos: {total}")
print("Ahora los reportes diran 2019-2025.")