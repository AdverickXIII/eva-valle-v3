"""Registra el hito del Modulo 1 en CONTEXTO.md."""
from pathlib import Path

p = Path("CONTEXTO.md")
c = p.read_text(encoding="utf-8")

bloque = """## Curso de Deep Learning (2026-09-01)
- Modulo 1 (MLPs): MLP desde cero supera Promedio Movil 3A en Alcala
  - MAPE MLP: 2.82% vs MAPE PM3A: 9.92% (reduccion 72%)
  - 4 folds leave-one-out (2022-2025), MLP gana 3 de 4
  - Artefactos: core/ml/results/m1_alcala_*.json, m1_alcala_predicciones.csv
  - Notebook: notebooks/curso/01_mlp_backprop.ipynb
"""

if "Modulo 1 (MLPs)" not in c:
    c = c.replace("## Temas pausados", bloque + "\n## Temas pausados")
    p.write_text(c, encoding="utf-8")
    print("[OK] CONTEXTO.md actualizado con hito del Modulo 1")