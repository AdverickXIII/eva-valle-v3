"""Diagnostico AUD-FICHAS-001: imprime el texto EXACTO (con numeros de linea)
de las 3 regiones a parchear en el notebook v5, leido como JSON parseado."""
import json
from pathlib import Path

NB = Path("explore_base_agricola_v5_2_fichas.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

for i, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") != "code":
        continue
    src = "".join(cell["source"])
    hits = []
    if "def confidence(" in src:
        hits.append("DEF_CONFIDENCE")
    if "confidence(fc," in src and "def confidence(" not in src:
        hits.append("CALL_CONFIDENCE")
    if "Notas metodologicas" in src or "Notas metodológicas" in src:
        hits.append("NOTA_FIJA")
    if not hits:
        continue
    lines = src.splitlines()
    print("=" * 100)
    print(f"CELL #{i} -> {', '.join(hits)}")
    print("=" * 100)
    if "DEF_CONFIDENCE" in hits:
        j = next(k for k, l in enumerate(lines) if l.startswith("def confidence("))
        print("--- def confidence() completo ---")
        print("\n".join(f"{k:4d}| {lines[k]}" for k in range(j, min(len(lines), j + 45))))
    if "CALL_CONFIDENCE" in hits:
        print("--- llamadas a confidence() con contexto ---")
        for k, l in enumerate(lines):
            if "confidence(fc," in l:
                print("\n".join(f"{k2:4d}| {lines[k2]}"
                                for k2 in range(max(0, k - 8), min(len(lines), k + 3))))
                print("-" * 60)
    if "NOTA_FIJA" in hits:
        j = next(k for k, l in enumerate(lines)
                 if ("Notas metodologicas" in l or "Notas metodológicas" in l))
        print("--- region de la nota fija ---")
        print("\n".join(f"{k:4d}| {lines[k]}"
                        for k in range(max(0, j - 16), min(len(lines), j + 8))))