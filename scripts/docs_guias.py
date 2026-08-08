"""Genera docs/ (4 guias)."""
from pathlib import Path

ARQ = '''# Arquitectura Hexagonal Modular

UI (Streamlit) invoca -> PUERTOS ENTRADA (core/ports/inbound)
-> NUCLEO (core/: audit, modeling, analytics, diagnostics, ml)
-> PUERTOS SALIDA (core/ports/outbound) <- implementados por ADAPTADORES
(adapters/: storage, downloader, ml_registry).

## Reglas de Dependencia
1. core/ NO importa de adapters/ ni ui/.
2. adapters/ implementa puertos outbound.
3. ui/ importa de core/ y de ui/charts, ui/components.
4. config/ es leido por todos, no importa de nadie.

## Capas
- core/: logica pura (calculate_concentration, fit_target_encoding)
- core/ports/: contratos (AnalyticsPort, StoragePort)
- adapters/: I/O real (CsvStorage, UpraDownloader, JoblibModelRegistry)
- ui/: presentacion (paginas, Plotly, componentes)
- config/: settings.py, constants.py

## Flujo de Datos
Excel -> adapters/storage -> core/audit (1+2) -> CSV limpio
-> core/modeling (3) -> CSV modelo -> analytics (4) + diagnostics (6) + ml (7)
-> artefactos CSV + joblib -> ui/ renderiza.
'''

USO = '''# Guia de Uso del Dashboard

Abre streamlit run app.py y ve a http://localhost:8501.
Navega con la barra lateral (8 paginas).

- Inicio: hub de acceso rapido.
- Dashboard: KPIs, evolucion historica, Pareto.
- Descriptivo: 12 analisis en 6 tabs.
- Diagnostico: 5 analisis causales.
- Predictivo: R2/MAE/ROC-AUC, importancia, real vs predicho, Holt-Winters.
- Auditoria: 14 hallazgos por severidad.
- Configuracion: estado del pipeline, descarga UPRA, parametros.
- Cultivos: Tabla A (historico municipal), B (comparativa vs dpto),
  C (ranking 42 municipios).

## Filtros
Panel lateral: municipio, grupo, ciclo, rango de anos.
Boton "Limpiar Filtros" para restablecer.

## Descargas
Cada tabla tiene boton de descarga CSV.
'''

PIPE = '''# Pipeline de Datos (Pasos 0-7)

Ejecucion: python scripts\\run_pipeline.py [--skip-download]

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
'''

TEST = '''# Pruebas Automatizadas

Ejecutar: python -m pytest tests/unit -v  (esperado: 15 passed)
Cobertura: python -m pytest tests/unit --cov=core --cov-report=term-missing

| Test | Previene |
|---|---|
| test_gini_en_rango_valido | Gini negativo |
| test_fit_calcula_medias_de_train | Data leakage |
| test_apply_..._rellena_no_vistos | Fuga de categorias |
| test_ids_unicos | Llaves duplicadas |
| test_nulls_* | Auditorias sin deteccion |

Anadir test: crear tests/unit/test_modulo.py con datos sinteticos
deterministas y aserciones claras; ejecutar pytest.
'''

if __name__ == "__main__":
    Path("docs").mkdir(parents=True, exist_ok=True)
    for nombre, contenido in {
        "ARQUITECTURA.md": ARQ, "USO_DASHBOARD.md": USO,
        "PIPELINE.md": PIPE, "TESTS.md": TEST,
    }.items():
        Path(f"docs/{nombre}").write_text(contenido, encoding="utf-8")
        print(f"[OK] docs/{nombre}")
    print("Fase 9 completa: 7 documentos.")