# Pipeline de Datos (Pasos 0-7)

Ejecucion: python scripts\run_pipeline.py [--skip-download]

| Paso | Modulo | Salida |
|---|---|---|
| 0 | adapters/downloader | data/raw/upra/*.xlsx |
| 1 | core/audit/loader | 01_clean/...estandarizado.csv |
| 2 | core/audit | auditoria_...csv (14 hallazgos) |
| 3 | core/modeling | 02_modelo/...conceptual.csv |
| 4 | core/analytics | 12 CSVs 4_*.csv |
| 6 | core/diagnostics | 8 CSVs 6_*.csv |
| 7 | core/ml | 5 CSVs 7_*.csv + 2 .joblib |

Scripts individuales: download_data.py, run_audit.py, export_report.py.
Artefactos en outputs/tables/, modelos en models/, logs en logs/.
