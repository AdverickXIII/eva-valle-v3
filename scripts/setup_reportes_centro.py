"""Transforma 10_Reportes en Centro de Reportes con 3 tabs."""
from pathlib import Path

NEW_PAGE = '''"""Pagina 10: Centro de Reportes (ejecutivos + municipales + paquetes de datos)."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.loading_states import render_empty_state
from ui.components.metrics_cards import render_kpi_row
from core.reports import build_municipality_excel, build_municipality_pdf
from core.reports.data import kpis

st.set_page_config(page_title="Reportes | EVA Valle", page_icon="📑", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


@st.cache_data(ttl=3600)
def get_excel(df: pd.DataFrame, municipio: str) -> bytes:
    return build_municipality_excel(df, municipio)


@st.cache_data(ttl=3600)
def get_pdf(df: pd.DataFrame, municipio: str) -> bytes:
    return build_municipality_pdf(df, municipio)


def main() -> None:
    st.title("📑 Centro de Reportes EVA")
    st.caption("Todos los entregables descargables organizados por audiencia")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    tab1, tab2, tab3 = st.tabs([
        "📄 Reportes ejecutivos (PDF)",
        "🏘️ Reportes por municipio",
        "📦 Paquetes de datos (CSV)",
    ])

    # ================================================================
    # TAB 1: REPORTES EJECUTIVOS
    # ================================================================
    with tab1:
        st.subheader("Reportes formales para Secretaría y Dirección")
        st.caption("Documentos PDF listos para imprimir, presentar o archivar.")

        # Resumen Ejecutivo
        st.markdown("#### 📊 Resumen Ejecutivo Departamental")
        st.markdown("""
        **Contenido:** KPIs globales, concentración con/sin caña, tendencias 2019-2025, 
        top cultivos, alertas y recomendaciones estratégicas.
        
        **Audiencia:** Secretaría de Agricultura, Gobernación, prensa.
        """)
        try:
            from core.reports.executive_report import build_executive_pdf
            pdf_ejec = build_executive_pdf(df)
            st.download_button(
                "⬇️ Descargar Resumen Ejecutivo (PDF)",
                data=pdf_ejec,
                file_name="resumen_ejecutivo_valle_2019_2025.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Generador no disponible: {e}")

        st.markdown("---")

        # Zonificación
        st.markdown("#### 🗺️ Zonificación Oficial (Ordenanza 513)")
        st.markdown("""
        **Contenido:** Análisis por subregión (Norte, Centro, Sur, Pacífico) con 
        comparativa dual con/sin caña, Gini territorial y liderazgo productivo.
        
        **Audiencia:** Planeación departamental, Secretarías regionales.
        """)
        try:
            from core.reports.zonification_report import build_zonification_pdf
            pdf_zona = build_zonification_pdf(df)
            st.download_button(
                "⬇️ Descargar Zonificación (PDF)",
                data=pdf_zona,
                file_name="zonificacion_valle_ordenanza_513.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Generador no disponible: {e}")

        st.markdown("---")

        # Validación Satelital
        st.markdown("#### 🛰️ Validación Satelital 100%")
        st.markdown("""
        **Contenido:** Cruzamiento Sentinel-2 (óptico) + Sentinel-1 (radar), 
        cobertura por municipio-año, detección de anomalías.
        
        **Audiencia:** Auditores, revisores técnicos, organismos de control.
        """)
        try:
            from core.reports.satellite_report import build_satellite_pdf
            pdf_sat = build_satellite_pdf(df)
            st.download_button(
                "⬇️ Descargar Validación Satelital (PDF)",
                data=pdf_sat,
                file_name="validacion_satelital_valle_sentinel.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Generador no disponible: {e}")

        st.markdown("---")

        # Modelo Económico (placeholder)
        st.markdown("#### 💼 Modelo Económico EVA")
        st.markdown("""
        **Contenido:** Segmentación de clientes, precios, proyecciones 36 meses, 
        break-even, ROI y escalamiento.
        
        **Estado:** 🚧 Próximamente (mañana lo construimos).
        """)
        st.info("Este reporte se agregará mañana como parte del bloque de modelo económico.")

        st.markdown("---")
        st.caption("💡 Para fichas técnicas interactivas por cultivo, visita 🌱 **Cultivos** → Tab 2.")

    # ================================================================
    # TAB 2: REPORTES POR MUNICIPIO
    # ================================================================
    with tab2:
        st.subheader("Reportes municipales (Excel + PDF)")
        st.caption("Análisis territorial específico por municipio")

        municipios = sorted(df["municipio"].dropna().unique().tolist())
        m = st.selectbox("Selecciona un municipio", municipios, key="reportes_muni")

        df_m = df[df["municipio"] == m]
        k = kpis(df_m, df)

        st.markdown("---")
        render_kpi_row([
            {"label": "Produccion", "value": f"{k['Produccion total (t)']:,.0f} t", "icon": "🌾"},
            {"label": "Area", "value": f"{k['Area sembrada (ha)']:,.0f} ha", "icon": "📐"},
            {"label": "Rendimiento", "value": f"{k['Rendimiento promedio (t/ha)']:.1f} t/ha", "icon": "📈"},
            {"label": "% del Dpto.", "value": f"{k['% de la produccion departamental']:.1f}%", "icon": "🎯"},
        ], cols=4)

        st.markdown("---")
        safe = m.replace(" ", "_").lower()
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "📊 Descargar Excel",
                data=get_excel(df, m),
                file_name=f"reporte_{safe}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                "📄 Descargar PDF",
                data=get_pdf(df, m),
                file_name=f"reporte_{safe}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        st.info("💡 El PDF es un documento formal listo para imprimir o presentar. "
                "El Excel incluye 3 hojas: Resumen, Histórico Anual y Top Cultivos.")

    # ================================================================
    # TAB 3: PAQUETES DE DATOS
    # ================================================================
    with tab3:
        st.subheader("Datasets completos para análisis")
        st.caption("CSVs limpios listos para R, Python, Power BI o Excel avanzado.")

        st.markdown("#### 📊 EVA completo (todos los registros)")
        st.caption(f"Total: {len(df):,} registros | {df['cultivo'].nunique()} cultivos | "
                   f"{df['municipio'].nunique()} municipios | 2019-2025")
        st.download_button(
            "⬇️ Descargar EVA completo (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="eva_valle_completo_2019_2025.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.markdown("---")
        st.markdown("#### 🎯 Datasets analíticos especializados")

        # Outliers
        st.markdown("**Outliers detectados (Isolation Forest)**")
        try:
            from core.analytics.outliers import detect_multivariate_outliers
            df_out = detect_multivariate_outliers(df)
            if not df_out.empty:
                st.caption(f"{len(df_out)} registros anómalos ({len(df_out)/len(df)*100:.1f}%)")
                st.download_button(
                    "⬇️ Outliers (CSV)",
                    data=df_out.to_csv(index=False).encode("utf-8"),
                    file_name="outliers_isolation_forest.csv",
                    mime="text/csv",
                )
            else:
                st.caption("No se detectaron outliers.")
        except Exception as e:
            st.warning(f"Generador no disponible: {e}")

        st.markdown("---")

        # Concentración
        st.markdown("**Índices de concentración (HHI, Gini, Top 1)**")
        try:
            from core.analytics.concentration import calculate_concentration
            conc = calculate_concentration(df)
            if conc:
                conc_df = pd.DataFrame([conc])
                st.download_button(
                    "⬇️ Concentración (CSV)",
                    data=conc_df.to_csv(index=False).encode("utf-8"),
                    file_name="concentracion_hhi_gini.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.warning(f"Generador no disponible: {e}")

        st.markdown("---")

        # CAGR
        st.markdown("**Crecimiento por cultivo (CAGR 2019-2025)**")
        try:
            from core.analytics.growth import calculate_cagr
            cagr = calculate_cagr(df)
            if not cagr.empty:
                st.download_button(
                    "⬇️ CAGR por cultivo (CSV)",
                    data=cagr.to_csv(index=False).encode("utf-8"),
                    file_name="cagr_cultivos_2019_2025.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.warning(f"Generador no disponible: {e}")

        st.markdown("---")
        st.caption("💡 Para análisis interactivos con selectores, visita las páginas "
                   "📊 Descriptivo, 🌱 Cultivos y 🌍 Espacial.")


main()
'''

Path("ui/pages/10_Reportes.py").write_text(NEW_PAGE, encoding="utf-8")
print("[OK] 10_Reportes.py transformado en Centro de Reportes con 3 tabs")
print("Reinicia Streamlit y explora los 3 tabs")