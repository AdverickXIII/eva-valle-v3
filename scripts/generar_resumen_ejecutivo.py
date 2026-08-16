"""Genera el Resumen Ejecutivo PDF (standalone)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from config.settings import settings
from core.reports.executive_report import build_executive_pdf

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)
out = Path("outputs/resumen_ejecutivo.pdf")
out.write_bytes(build_executive_pdf(df))
print(f"[OK] Resumen Ejecutivo generado: {out}")
print(f"     Tamano: {out.stat().st_size / 1024:.1f} KB")
