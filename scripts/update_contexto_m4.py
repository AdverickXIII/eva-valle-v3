"""Registra el Modulo 4 en CONTEXTO.md."""
from pathlib import Path

p = Path("CONTEXTO.md")
c = p.read_text(encoding="utf-8")
bloque = """- Modulo 4 (CNN): clasificacion de vocacion productiva (imagenes 12x7)
  - CNN acc test 91.67% vs baseline 83.33% (+8.33%), n=42 municipios
  - Hallazgo: Filtro 1 es detector especializado de vocacion bananera (activa 2.77 vs 0.3-0.5)
  - Limitacion: desbalance de clases (Banano 1 train / 0 test) infla el accuracy
  - Artefactos: core/ml/cnn_scratch.py, notebooks/curso/04_cnn_patrones_espaciales.ipynb,
    core/ml/results/m4_*.json/csv/png
"""
if "Modulo 4 (CNN)" not in c:
    c = c.replace("- Modulo 3 (Bandits)", bloque + "- Modulo 3 (Bandits)")
    p.write_text(c, encoding="utf-8")
    print("[OK] CONTEXTO.md actualizado con Modulo 4")