# Arquitectura Hexagonal Modular

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
