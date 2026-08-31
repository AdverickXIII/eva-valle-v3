"""Cierre definitivo del Modulo 3: proyecciones propias + baselines corregidos."""
from pathlib import Path

p = Path("CONTEXTO.md")
c = p.read_text(encoding="utf-8")

bloque = """- Modulo 3 (Bandits): torneo de seleccion + selector de produccion
  - Torneo: eps-greedy reduce regret 58% vs status quo fijo
  - Selector: shrinkage empirico (N0=4) + IC 95% + exploracion etica acotada
  - Hallazgo: PM5A supera PM3A en total municipal Alcala (MAPE 3.48% vs 7.62%)
  - Nota: el "4.2%" del PDF viene de MAPE agregado (no medio), protocolo backtest n_out=2
  - Las proyecciones del PDF son nuestras (forecast.py), no oficiales del Estado
  - Baselines M1 corregidos (sin lookahead): MLP 2.82% < PM5A 3.48% < PM3A 7.62%
  - Pagina 24: Selector de Modelos por bandits en produccion
  - Artefactos: core/ml/bandits.py, core/analytics/model_selector.py, ui/pages/24_Selector_Modelos.py
"""

# Reemplazar el bloque anterior del Modulo 3
c = c.replace(
    "- Modulo 3 (Bandits): torneo de seleccion + selector de produccion\n"
    "  - Torneo: eps-greedy reduce regret 58% vs status quo fijo\n"
    "  - Selector: shrinkage empirico (N0=4) + IC 95% + exploracion etica acotada\n"
    "  - Hallazgo: PM5A supera PM3A (nuestro baseline inicial) en total municipal Alcala\n"
    "    (MAPE 3.48% vs 7.62%). Nota: las proyecciones del PDF son nuestras (forecast.py), no oficiales del Estado\n"
    "  - Pagina 24: Selector de Modelos por bandits en produccion\n"
    "  - Artefactos: core/ml/bandits.py, core/analytics/model_selector.py, ui/pages/24_Selector_Modelos.py",
    bloque.rstrip()
)

p.write_text(c, encoding="utf-8")
print("[OK] CONTEXTO.md cerrado con metodologia alineada")