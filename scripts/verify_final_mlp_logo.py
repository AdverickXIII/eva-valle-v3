"""Verificacion final: ranking con MLP + PDF local + logo en git."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from config.settings import settings
from core.analytics.forecast import proyectar_con_ic

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)
serie = (df[(df.municipio == "Alcalá") & (df.cultivo == "Plátano")]
         .groupby("ano")["produccion_t"].sum().sort_index())
res = proyectar_con_ic(serie, n_steps=3)
print(f"Ganador: {res['ganador']} | MAPE {res['mape']:.2f}%")
for r in res["ranking"]:
    print(f"  {r['modelo']['nombre']:30s} MAPE {r['mape']:.2f}")

from core.reports.predictivo_pdf import build_predictivo_pdf
pdf = build_predictivo_pdf("Plátano", "Alcalá", serie, res, 3)
out = ROOT / "test_proyeccion_mlp.pdf"
out.write_bytes(pdf)
print(f"[OK] PDF local: {out}")

r = subprocess.run(["git", "ls-files", "ui/assets/img/"],
                   capture_output=True, text=True, cwd=str(ROOT))
print("\nImg trackeados en git:", r.stdout.strip() or "(NINGUNO)")