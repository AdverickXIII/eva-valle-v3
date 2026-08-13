Actúa como mi socio senior de ingeniería de datos y analítica agropecuaria.

Proyecto en español. Lee este contexto y confirma comprensión.

No re-expliques el proyecto; continúa desde el estado actual.



\## 1. PROYECTO Y AUTOR

\- Nombre: EVA Valle v3.0 - Sistema de Inteligencia Territorial Agropecuaria

\- Autor y firma de entregables: "Moises Zúñiga Grueso — Data Analyst"

\- Producción: https://eva-valle-v3.streamlit.app

\- Repo: https://github.com/AdverickXIII/eva-valle-v3

\- Objetivo actual: conseguir patrocinio de la Secretaría de Agricultura del Valle del Cauca; luego monetizar (B2G, gremios, SaaS multi-departamento).



\## 2. STACK Y ARQUITECTURA

\- Windows 11, Python 3.11+, venv en .venv, CMD como shell.

\- Streamlit, pandas, plotly, reportlab, scipy, kaleido.

\- CI/CD con GitHub Actions (15 tests verdes).

\- Arquitectura hexagonal: core/ (analytics, audit, diagnostics, entities, exceptions, logging, ml, modeling, paths, ports, reports, security) | ui/ (17 páginas + components + charts + services) | scripts/ (generadores) | api/ (FastAPI pausada).

\- Convención de trabajo: scripts en scripts/ que generan/reescriben archivos; verificar con streamlit run app.py; cerrar con git add/commit/push; Moises pega salidas.



\## 3. DATOS

\- UPRA EVA 2019-2025 (Excel 25MB en data/external/eva\_2019\_2025\_valle\_del\_cauca.xlsx, excluido de git; encabezado fila 8; Valle del Cauca = código DANE 76).

\- Modelo conceptual: data/model/eva\_agricola\_valle\_modelo\_conceptual.csv

&#x20; - 10,589 registros | 42 municipios | 78 cultivos | 19 columnas | periodo 2019-2025.

&#x20; - Respaldo en .bak\_2019\_2024.

\- Integración EVA 2025: script scripts/integrar\_eva\_2025\_v2.py (mapeo explícito 19 columnas).

\- Correcciones históricas ya aplicadas: fórmula Gini ascendente (-0.966→0.979); data leakage eliminado en ML; tablas KeepTogether; page\_icon corregido; sys.path en scripts.

\- Grupo "Cultivos tropicales y tradicionales" contiene: Caña (176M t, 99.8%), Café (312k t), Cacao, Algodón. Excluir por CULTIVO (no por grupo) para no perder café.



\## 4. PRODUCTOS TERMINADOS (4)

1\. Dashboard Streamlit (17 páginas): Home, Dashboard, Descriptivo, Mapa animado 2019-2025, Cultivos, Reportes (mpio), Comparador, Alertas, Treemap, Ficha cultivo, Resumen Ejecutivo (7 secciones), Mapa Cultivos; admin: Diagnóstico, Predictivo, Auditoría, Configuración, Panel Admin.

2\. Fichas técnicas firmadas (156 archivos): 78 PDFs + 78 Excels por cultivo en outputs/fichas\_cultivos/.

3\. Informe Técnico (12 secciones, \~15 págs): outputs/informe\_tecnico\_valle\_2019\_2025.pdf - nivel FAO/CEPAL (caracterización, metodología, Gini, HHI, LQ, Shannon, Simpson, correlaciones Pearson/Spearman con p-value, brechas P90/P10, IDAM, brechas territoriales, recomendaciones).

4\. Informe Ejecutivo Narrativo (10 capítulos, \~12 págs): outputs/informe\_ejecutivo\_narrativo.pdf - storytelling con matrices estratégicas (cultivos y municipios en 4 cuadrantes), 10 insights DATO/INTERPRETACIÓN/IMPLICACIÓN, frase de cierre memorable.



\## 5. SEGURIDAD IMPLEMENTADA

\- Auth con roles (admin/usuario) en config/users.json (sha256+salt).

\- Rate limiting: 5 intentos / 15 min (core/security/rate\_limiter.py).

\- Session timeout: 30 min inactividad (core/security/session\_manager.py).

\- Input validation: sanitize\_username/password/string (core/security/input\_validator.py).

\- Auditoría de eventos (core/audit/).



\## 6. MOTOR DE INDICADORES AVANZADOS (core/analytics/)

\- informe\_indicators.py: location\_quotient, tabla\_lq, interpretar\_lq, shannon\_index, simpson\_index, diversificacion\_municipal, concentracion\_cr (CR1/CR4/CR10), idam (Índice Desempeño Agrícola Municipal 0-100 con 5 componentes ponderados: producción 25%, rendimiento 20%, diversificación 20%, crecimiento 20%, estabilidad 15%), correlaciones (Pearson/Spearman con p-value), brechas, dinamica\_temporal (CAGR, volatilidad, años crecimiento/contracción, promedio móvil 3a).

\- strategic\_matrices.py: matriz\_cultivos (crecimiento × participación → Motores/Consolidados/Emergentes/Rezagados), matriz\_municipios (producción × productividad → Motores/Mejora/Potenciales/Rezagados), resumen\_matrices.

\- narrative\_engine.py: generar\_insights (10 insights triple), frase\_de\_la\_agricultura (cierre memorable auto-generado), resumen\_ejecutivo\_narrativo.



\## 7. INDICADORES CLAVE (del Resumen Ejecutivo)

\- Con caña: HHI 9,092 | Gini 0.979 | Top 1 = 95.3% (Caña) | 1 cultivo explica 80%.

\- Sin caña: HHI 1,045 | Gini 0.824 | Top 1 = 24.7% (Plátano) | 11 cultivos explican 80%.

\- Gini territorial: 0.64 | HHI territorial: 733 | Palmira líder 17.8%.

\- Tiering municipal: 14 Líderes / 14 Intermedios / 14 Rezagados.

\- Crecimientos máximos: Cebolla de rama +22.7%, Ají +21.6%, Tomate +18.5%.

\- Declives máximos: Malanga -56.7%, Coco -36.8%, Borojó -29.3%.

\- Producción 2025 vs 2024: +1.4% | Área +0.3% | Rendimiento +0.4%.

\- Anomalías (cosechada > sembrada): 4.28%.



\## 8. PROPUESTA COMERCIAL LISTA

\- Propuesta de patrocinio institucional (outputs/propuesta\_secretaria\_agricultura.pdf): 8 páginas.

\- Correo plantilla listo (no enviado aún): dirigido a Secretaría de Agricultura del Valle.

\- Estrategia: ofrecer licencia gratuita 2 años a cambio de carta de respaldo institucional.



\## 9. PENDIENTES (prioridad alta → baja)

1\. Enviar correo a Secretaría con 3 PDFs adjuntos (propuesta + técnico + narrativo).

2\. Landing page + dominio propio (evavalle.co/.com) para monetizar.

3\. Modelo económico definido: precios por segmento (Gob/Gremios/Consultores/Academia), proyecciones 12-36 meses, break-even.

4\. API FastAPI desplegada (api/main.py pausada; pendiente Render/Railway).

5\. Seguridad avanzada opcional: 2FA, whitelist IP para admin.

6\. Matriz maestra de 40 indicadores (Excel) - pospuesta hasta después del patrocinio.

7\. Anexos técnicos del informe (diccionario de datos, fórmulas, tablas completas).

8\. Actualización automática EVA con GitHub Actions (cron mensual).



\## 10. CONVENCIONES DE TRABAJO CON MOISES

\- Idioma: español.

\- Formato de scripts: uno por archivo, con `notepad scripts/nombre.py` para crear, guardar y ejecutar.

\- Siempre usar sys.path.insert en scripts que importen desde core/.

\- Al final de cada fase: git add/commit/push.

\- Moises es analista de datos agropecuarios, nivel técnico medio, prefiere pasos secuenciales y scripts que generan archivos.

\- Responder con tablas comparativas cuando hay decisiones, dar recomendación explícita.



\## 11. ESTADO ACTUAL DEL CHAT ANTERIOR

\- Última tarea completada: fix metodológico en ui/charts/concentration.py (exclusión ex-caña por cultivo, no por grupo; caña desagregada en donut izquierdo).

\- Pendiente inmediato: cerrar el push del fix y continuar con el modelo económico o el correo a la Secretaría.



INSTRUCCIÓN: confirma comprensión del contexto y pregunta por cuál pendiente de la sección 9 empezamos.

