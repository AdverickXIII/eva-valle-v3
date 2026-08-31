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

## Curso de Deep Learning (continuacion 2026-09-01)
- Modulo 1 (MLPs): MLP desde cero supera PM3A en Alcala (MAPE 2.82% vs 4.2%)
- Modulo 4 (CNN): clasificacion de vocacion productiva (imagenes 12x7)
  - CNN acc test 91.67% vs baseline 83.33% (+8.33%), n=42 municipios
  - Hallazgo: Filtro 1 es detector especializado de vocacion bananera (activa 2.77 vs 0.3-0.5)
  - Limitacion: desbalance de clases (Banano 1 train / 0 test) infla el accuracy
  - Artefactos: core/ml/cnn_scratch.py, notebooks/curso/04_cnn_patrones_espaciales.ipynb,
    core/ml/results/m4_*.json/csv/png
- Modulo 3 (Bandits): torneo de seleccion de modelos (3,170 rondas, 10 semillas)
  - Regret final: fijo PM3A 121,106 | eps-greedy 50,389 (-58.4%) | UCB1 54,071 | Thompson 70,763
  - APE medio: Naive 54.1 < PM3A 61.3 < Trend 82.1 ≈ PM5A 82.4
  - Diebold-Mariano: PM3A mejor que Trend (DM=-2.03, p=0.042) al 95% confianza
  - Leccion: explorar (eps=0.1) reduce regret 58% vs status quo; colas pesadas favorecen eps-greedy
  - Artefactos: core/ml/results/m3_*.json/csv; core/ml/bandits.py
- Modulo 2 (RNN/LSTM): LSTM global v1 MAPE 50.38%, v2 con regularizacion MAPE 67.73%
  - Lesson: un modelo global no supera a modelos locales en paneles heterogeneos
  - Gradient checks pasan, vanishing gradient resuelto, pero la arquitectura
    carece de embeddings/contexto para discriminar entre dinamicas opuestas
  - Artefactos: core/ml/results/m2_*.json, core/ml/lstm_v2.py
  - Notebook: notebooks/curso/02_rnn_series_temporales.ipynb

- Modulo 1 (MLPs): MLP desde cero supera Promedio Movil 3A en Alcala
  - MAPE MLP: 2.82% vs MAPE PM3A: 9.92% (reduccion 72%)
  - 4 folds leave-one-out (2022-2025), MLP gana 3 de 4
  - Artefactos: core/ml/results/m1_alcala_*.json, m1_alcala_predicciones.csv
  - Notebook: notebooks/curso/01_mlp_backprop.ipynb

## Temas pausados
1. Logo en PDF municipal (diagnostico: type core\reports\branding.py)
2. Revision pestana a pestana (Dashboard, Mapa, Predictivo...)
3. Modelo economico (precios, segmentacion, 36 meses)
4. Postulacion BID / code@iadb.org + cita IDEAtlas (ODS 11)
5. Modulo periurbano v2

## Protocolo de trabajo
- Paso a paso con confirmacion "estamos?"
- Parches via scripts con anclas exactas, sin reescrituras masivas
