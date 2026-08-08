"""Crea core/reports/meta.py y reescribe excel_report.py con firma profesional."""
from pathlib import Path

META = '''"""Metadatos de autoria y branding de los reportes."""
from __future__ import annotations

AUTOR = "Moises Zúñiga Grueso"
CARGO = "Data Analyst"
SISTEMA = "EVA Valle v3.0"
FUENTE = "UPRA - Encuestas de Valuacion Agropecuaria (EVA) 2019-2024"


def firma() -> str:
    """Linea de autoria estandar para todos los informes."""
    return f"Elaborado por {AUTOR} - {CARGO}"
'''

EXCEL = '''"""Reporte Excel por municipio (3 hojas) con firma profesional."""
from __future__ import annotations

import io
from datetime import date

import pandas as pd

from core.reports import meta
from core.reports.data import filter_municipio, kpis, top_cultivos, yearly


def build_municipality_excel(df: pd.DataFrame, municipio: str) -> bytes:
    df_m = filter_municipio(df, municipio)
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        # Hoja Resumen: KPIs + bloque de autoria
        k = kpis(df_m, df)
        kdf = pd.DataFrame({"Indicador": list(k.keys()), "Valor": list(k.values())})
        kdf.to_excel(w, sheet_name="Resumen", index=False)

        meta_df = pd.DataFrame({
            "Campo": ["Elaborado por", "Cargo", "Fecha de generacion",
                      "Fuente", "Sistema"],
            "Detalle": [meta.AUTOR, meta.CARGO,
                        date.today().strftime("%Y-%m-%d"),
                        meta.FUENTE, meta.SISTEMA],
        })
        meta_df.to_excel(w, sheet_name="Resumen", index=False,
                         startrow=len(kdf) + 2)

        yearly(df_m).to_excel(w, sheet_name="Historico_Anual", index=False)
        top_cultivos(df_m).to_excel(w, sheet_name="Top_Cultivos", index=False)
    return out.getvalue()
'''

if __name__ == "__main__":
    Path("core/reports/meta.py").write_text(META, encoding="utf-8")
    print("[OK] core/reports/meta.py")
    Path("core/reports/excel_report.py").write_text(EXCEL, encoding="utf-8")
    print("[OK] core/reports/excel_report.py (con firma)")
    print("\nSigue: python scripts\\setup_reports_pdf_brand.py")