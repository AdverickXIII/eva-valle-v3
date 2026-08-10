"""Genera fichas tecnicas (PDF + Excel) para todos los cultivos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.settings import settings
from core.reports.crop_report import build_crop_excel, build_crop_pdf


def main() -> None:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    df = pd.read_csv(path, low_memory=False)

    out_dir = Path("outputs/fichas_cultivos")
    out_dir.mkdir(parents=True, exist_ok=True)

    cultivos = sorted(df["cultivo"].dropna().unique())
    print(f"Generando fichas para {len(cultivos)} cultivos (2019-2025)...")

    for i, cultivo in enumerate(cultivos, 1):
        safe = cultivo.replace(" ", "_").replace("/", "-").lower()
        (out_dir / f"ficha_{safe}.pdf").write_bytes(build_crop_pdf(df, cultivo))
        (out_dir / f"ficha_{safe}.xlsx").write_bytes(build_crop_excel(df, cultivo))
        print(f"[{i}/{len(cultivos)}] {cultivo}")

    # Excluir del repo (son entregables locales)
    gi = Path(".gitignore")
    txt = gi.read_text(encoding="utf-8")
    if "outputs/fichas_cultivos/" not in txt:
        gi.write_text(txt.rstrip() + "\noutputs/fichas_cultivos/\n", encoding="utf-8")
        print("[OK] .gitignore actualizado")

    print(f"\n[OK] {len(cultivos)} PDFs + {len(cultivos)} Excels en {out_dir}")


if __name__ == "__main__":
    main()