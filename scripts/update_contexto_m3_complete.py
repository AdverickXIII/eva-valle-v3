"""Registra el Modulo 3 completo con DM en CONTEXTO.md."""
from pathlib import Path

p = Path("CONTEXTO.md")
c = p.read_text(encoding="utf-8")
bloque = """- Modulo 3 (Bandits): torneo de seleccion de modelos (3,170 rondas, 10 semillas)
  - Regret final: fijo PM3A 121,106 | eps-greedy 50,389 (-58.4%) | UCB1 54,071 | Thompson 70,763
  - APE medio: Naive 54.1 < PM3A 61.3 < Trend 82.1 ≈ PM5A 82.4
  - Diebold-Mariano: PM3A mejor que Trend (DM=-2.03, p=0.042) al 95% confianza
  - Leccion: explorar (eps=0.1) reduce regret 58% vs status quo; colas pesadas favorecen eps-greedy
  - Artefactos: core/ml/results/m3_*.json/csv; core/ml/bandits.py
"""
if "Modulo 3 (Bandits)" in c:
    c = c.replace("- Modulo 3 (Bandits): torneo de seleccion de modelos", bloque.rstrip())
else:
    c = c.replace("- Modulo 2 (RNN/LSTM)", bloque + "- Modulo 2 (RNN/LSTM)")
p.write_text(c, encoding="utf-8")
print("[OK] CONTEXTO.md actualizado con Modulo 3 completo")