"""Registra el Modulo 2 con honestidad cientifica."""
from pathlib import Path

p = Path("CONTEXTO.md")
c = p.read_text(encoding="utf-8")

bloque = """## Curso de Deep Learning (continuacion 2026-09-01)
- Modulo 1 (MLPs): MLP desde cero supera PM3A en Alcala (MAPE 2.82% vs 4.2%)
- Modulo 2 (RNN/LSTM): LSTM global v1 MAPE 50.38%, v2 con regularizacion MAPE 67.73%
  - Lesson: un modelo global no supera a modelos locales en paneles heterogeneos
  - Gradient checks pasan, vanishing gradient resuelto, pero la arquitectura
    carece de embeddings/contexto para discriminar entre dinamicas opuestas
  - Artefactos: core/ml/results/m2_*.json, core/ml/lstm_v2.py
  - Notebook: notebooks/curso/02_rnn_series_temporales.ipynb
"""

c = c.replace("## Curso de Deep Learning (2026-09-01)", bloque)
p.write_text(c, encoding="utf-8")
print("[OK] CONTEXTO.md actualizado con Modulo 2")