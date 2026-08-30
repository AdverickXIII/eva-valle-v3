# CONTEXTO.md - EVA Valle v3.0 (memoria del proyecto)

## Que es
Plataforma analitica del agro del Valle del Cauca sobre dato oficial UPRA-EVA 2019-2025.
4 niveles analiticos (descriptivo, diagnostico, predictivo, prescriptivo) + gobernanza.
Stack: Streamlit + Plotly + reportlab. 3 roles (usuario/analista/admin).

## Estructura clave
- app.py: login y navegacion por roles
- core/analytics/: suite analitica (descriptive, concentration, ex_cana, lq_table,
  forecast, growth, inferential, narrative_engine, outliers, pareto, pipeline,
  seasonality, spatial, strategic_matrices, time_series, zonas, alerts, elasticity,
  executive, informe_indicators, irs)
- core/chat/engine.py: Asistente determinista (fuzzy, contexto, horizonte 2019-2028)
- core/reports/: 11 generadores de PDF firmados + branding (logo) +
  presentacion_oficial (Ficha BID + presentacion 10 laminas)
- ui/pages/: 22 paginas organizadas por nivel analitico
- scripts/: metodologia de parches minimos (setup_*/fix_*)

## Cifras ancla (verificacion rapida)
42 municipios | 78 cultivos | 2019-2025 | 0 anomalias satelitales
Sevilla #1 platano (81,630 t en 2025) | Alcala #34 (276,012 t)
Cana = 95.3% | 4 zonas Ord. 513 | Proyeccion Alcala 2026: 39,196 t (MAPE 4.2%)

## Modelo economico (2026-08-30)
- Pagina 23 Valor Economico: PIB agro 5.93 billones COP (2025)
- Precios v1 oficiales: tabla PRECIO_OFICIAL_V1 calibrada con Boletines UPRA Primer Mercado 2025, trazabilidad por cultivo
- Fuentes SIPSA_P (DANE mayoristas) y Primer Mercado UPRA no tienen descarga programatica; se calibra manualmente desde boletines PDF

## Estado (2026-08-27)
- Cloud: eva-valle-v3.streamlit.app (cuenta usuario/usuario123 verificada)
- Secretario (Don Hector) retoma esta semana; mensaje-guia enviado; demo 15 min propuesta.

## Temas pausados
1. Logo en PDF municipal (diagnostico: type core\reports\branding.py)
2. Revision pestana a pestana (Dashboard, Mapa, Predictivo...)
3. Modelo economico (precios, segmentacion, 36 meses)
4. Postulacion BID / code@iadb.org + cita IDEAtlas (ODS 11)
5. Modulo periurbano v2

## Protocolo de trabajo
- Paso a paso con confirmacion "estamos?"
- Parches via scripts con anclas exactas, sin reescrituras masivas
