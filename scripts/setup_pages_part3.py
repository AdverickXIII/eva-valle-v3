"""Setup pages part 3: Auditoria + Configuracion."""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# PAGINA 5: AUDITORIA
# ═══════════════════════════════════════════════════════════
PAGE_AUDITORIA = '''"""Pagina 5: Auditoria - Calidad de datos."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.metrics_cards import render_kpi_row
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
import plotly.express as px

st.set_page_config(page_title="Auditoria | EVA Valle", page_icon="\\U0001F50D", layout="wide")


@st.cache_data(ttl=3600)
def load_audit_report() -> pd.DataFrame:
    path = settings.OUTPUTS_TABLES_PATH / "auditoria_agricola_valle_2019_2024.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def main() -> None:
    st.title("\\U0001F50D Auditoria de Calidad de Datos")
    st.caption("Paso 2 - Reporte de auditoria tecnica profunda")

    df_audit = load_audit_report()
    if df_audit.empty:
        render_empty_state(
            "Reporte de auditoria no encontrado",
            hint="Ejecuta: python scripts/run_audit.py",
        )
        return

    st.markdown("---")

    # ── KPIs por severidad ───────────────────────────────────
    n_errors = len(df_audit[df_audit["severidad"] == "ERROR"])
    n_warnings = len(df_audit[df_audit["severidad"] == "ADVERTENCIA"])
    n_info = len(df_audit[df_audit["severidad"] == "INFO"])
    n_total = len(df_audit)

    render_kpi_row([
        {"label": "Errores", "value": f"{n_errors}", "icon": "\\u274C",
         "delta_type": "negative" if n_errors > 0 else "positive"},
        {"label": "Advertencias", "value": f"{n_warnings}", "icon": "\\u26A0\\uFE0F",
         "delta_type": "negative" if n_warnings > 3 else "neutral"},
        {"label": "Info", "value": f"{n_info}", "icon": "\\u2139\\uFE0F",
         "delta_type": "neutral"},
        {"label": "Total Hallazgos", "value": f"{n_total}", "icon": "\\U0001F4CB",
         "delta_type": "neutral"},
    ])

    st.markdown("---")

    # ── Grafico de distribucion por severidad ────────────────
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Distribucion por Severidad")
        sev_counts = df_audit["severidad"].value_counts()
        fig_sev = px.pie(
            values=sev_counts.values,
            names=sev_counts.index,
            color=sev_counts.index,
            color_discrete_map={
                "ERROR": "#F56565",
                "ADVERTENCIA": "#ECC94B",
                "INFO": "#4299E1",
            },
            hole=0.4,
        )
        fig_sev.update_layout(template="plotly_dark", showlegend=True)
        st.plotly_chart(fig_sev, use_container_width=True)

    with col2:
        st.subheader("Detalle de Hallazgos")
        # Filtro por severidad
        selected_sev = st.multiselect(
            "Filtrar por severidad",
            options=["ERROR", "ADVERTENCIA", "INFO"],
            default=["ERROR", "ADVERTENCIA", "INFO"],
        )
        df_filtered = df_audit[df_audit["severidad"].isin(selected_sev)]

        st.dataframe(
            df_filtered[["codigo", "severidad", "descripcion", "detalle"]],
            use_container_width=True,
            height=350,
        )
        render_download_button(df_filtered, "reporte_auditoria_filtrado.csv")

    st.markdown("---")

    # ── Tabs para auditorias especificas ─────────────────────
    st.subheader("Detalle por Auditoria")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "\\U0001F4D0 Estructura y Nulos",
        "\\U0001F501 Duplicados y Territorial",
        "\\U0001F4C5 Temporal y Rangos",
        "\\U0001F527 Consistencia Logica",
        "\\U0001F4CA Dataset",
    ])

    with tab1:
        st.markdown("**Auditoria 2.1: Estructura** y **2.2: Nulos**")
        df_estr = df_audit[df_audit["codigo"].str.contains("AUD-00|AUD-NUL", na=False)]
        if not df_estr.empty:
            st.dataframe(df_estr, use_container_width=True)
        else:
            st.info("Sin hallazgos de estructura o nulos.")

    with tab2:
        st.markdown("**Auditoria 2.3: Duplicados** y **2.4: Integridad Territorial**")
        df_dup_terr = df_audit[df_audit["codigo"].str.contains("AUD-DUP|AUD-TER", na=False)]
        if not df_dup_terr.empty:
            st.dataframe(df_dup_terr, use_container_width=True)
        else:
            st.info("Sin hallazgos de duplicados o integridad territorial.")

    with tab3:
        st.markdown("**Auditoria 2.5: Coherencia Temporal** y **2.6: Rangos Numericos**")
        df_temp_rang = df_audit[df_audit["codigo"].str.contains("AUD-TEM|AUD-RNG|AUD-ZERO|AUD-OUT", na=False)]
        if not df_temp_rang.empty:
            st.dataframe(df_temp_rang, use_container_width=True)
        else:
            st.info("Sin hallazgos temporales o de rangos.")

    with tab4:
        st.markdown("**Auditoria 2.7: Consistencia Logica**")
        df_log = df_audit[df_audit["codigo"].str.contains("AUD-LOG", na=False)]
        if not df_log.empty:
            st.dataframe(df_log, use_container_width=True)
            # Mostrar detalles del error mas critico
            errors_log = df_log[df_log["severidad"] == "ERROR"]
            if not errors_log.empty:
                st.warning(f"**{len(errors_log)} error(es) critico(s) de consistencia logica:**")
                for _, row in errors_log.iterrows():
                    st.error(f"[{row['codigo']}] {row['descripcion']}")
                    if row.get("detalle"):
                        st.caption(f"Detalle: {row['detalle']}")
        else:
            st.info("Sin hallazgos de consistencia logica.")

    with tab5:
        st.markdown("**Vista rapida del dataset auditado**")
        df_data = load_dataset()
        if not df_data.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Registros", f"{len(df_data):,}")
            with col2:
                st.metric("Columnas", f"{len(df_data.columns)}")
            with col3:
                st.metric("Municipios", f"{df_data['municipio'].nunique()}")

            st.markdown("---")
            st.subheader("Primeras filas del dataset")
            st.dataframe(df_data.head(20), use_container_width=True)

            st.markdown("---")
            st.subheader("Tipos de datos")
            df_dtypes = df_data.dtypes.reset_index()
            df_dtypes.columns = ["Columna", "Tipo"]
            st.dataframe(df_dtypes, use_container_width=True)
        else:
            render_empty_state("Dataset no encontrado")

    # ── Descarga del reporte completo ────────────────────────
    st.markdown("---")
    st.subheader("\\U0001F4E5 Exportar Reporte Completo")
    render_download_button(
        df_audit,
        "auditoria_agricola_valle_2019_2024.csv",
        label="\\U0001F4E5 Descargar Reporte Completo de Auditoria",
    )


main()
'''

# ═══════════════════════════════════════════════════════════
# PAGINA 6: CONFIGURACION
# ═══════════════════════════════════════════════════════════
PAGE_CONFIGURACION = '''"""Pagina 6: Configuracion - Estado del sistema y acciones."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings

st.set_page_config(page_title="Configuracion | EVA Valle", page_icon="\\u2699\\uFE0F", layout="wide")


def check_pipeline_status() -> dict[str, dict]:
    """Verifica que archivos existen en cada paso del pipeline."""
    status = {
        "Paso 0: Descarga UPRA": {
            "ruta": settings.DATA_RAW_PATH,
            "archivos": list(settings.DATA_RAW_PATH.glob("*.xlsx")) if settings.DATA_RAW_PATH.exists() else [],
        },
        "Paso 1: Dataset Estandarizado": {
            "ruta": settings.DATA_PROCESSED_PATH / "01_clean",
            "archivos": list((settings.DATA_PROCESSED_PATH / "01_clean").glob("*.csv")) if (settings.DATA_PROCESSED_PATH / "01_clean").exists() else [],
        },
        "Paso 3: Modelo Conceptual": {
            "ruta": settings.DATA_MODEL_PATH,
            "archivos": list(settings.DATA_MODEL_PATH.glob("*.csv")) if settings.DATA_MODEL_PATH.exists() else [],
        },
        "Paso 4: Analisis Descriptivo": {
            "ruta": settings.OUTPUTS_TABLES_PATH,
            "archivos": list(settings.OUTPUTS_TABLES_PATH.glob("4_*.csv")) if settings.OUTPUTS_TABLES_PATH.exists() else [],
        },
        "Paso 6: Diagnostico": {
            "ruta": settings.OUTPUTS_TABLES_PATH,
            "archivos": list(settings.OUTPUTS_TABLES_PATH.glob("6_*.csv")) if settings.OUTPUTS_TABLES_PATH.exists() else [],
        },
        "Paso 7: Predictivo": {
            "ruta": settings.OUTPUTS_TABLES_PATH,
            "archivos": list(settings.OUTPUTS_TABLES_PATH.glob("7_*.csv")) if settings.OUTPUTS_TABLES_PATH.exists() else [],
        },
        "Modelos ML": {
            "ruta": settings.MODELS_PATH,
            "archivos": list(settings.MODELS_PATH.glob("*.joblib")) if settings.MODELS_PATH.exists() else [],
        },
        "Auditoria": {
            "ruta": settings.OUTPUTS_TABLES_PATH,
            "archivos": list(settings.OUTPUTS_TABLES_PATH.glob("auditoria_*.csv")) if settings.OUTPUTS_TABLES_PATH.exists() else [],
        },
    }
    return status


def main() -> None:
    st.title("\\u2699\\uFE0F Configuracion del Sistema")
    st.caption("Estado del pipeline, descargas y parametros")

    st.markdown("---")

    # ── Seccion 1: Estado del Pipeline ───────────────────────
    st.subheader("\\U0001F4CA Estado del Pipeline")
    st.caption("Archivos generados por cada paso")

    status = check_pipeline_status()

    for paso, info in status.items():
        archivos = info["archivos"]
        ruta = info["ruta"]

        col1, col2, col3 = st.columns([3, 1, 3])
        with col1:
            st.markdown(f"**{paso}**")
            st.caption(f"Ruta: `{ruta}`")
        with col2:
            if archivos:
                st.success(f"\\u2705 {len(archivos)} archivo(s)")
            else:
                st.warning("\\u274C Sin archivos")
        with col3:
            if archivos:
                for arch in archivos[:3]:
                    size_mb = arch.stat().st_size / (1024 * 1024)
                    st.caption(f"\\U0001F4C4 `{arch.name}` ({size_mb:.2f} MB)")
                if len(archivos) > 3:
                    st.caption(f"... y {len(archivos) - 3} mas")

        st.markdown("---")

    # ── Seccion 2: Descarga UPRA ─────────────────────────────
    st.subheader("\\u2B07\\uFE0F Descarga de Datos UPRA")
    st.caption("Descarga las bases Agricola y Pecuaria del portal EVA de la UPRA")

    if st.button("\\U0001F680 Iniciar Descarga UPRA", type="primary"):
        with st.spinner("Iniciando WebDriver y descargando datos..."):
            try:
                from adapters.downloader.upra_downloader import UpraDownloader
                downloader = UpraDownloader()
                with st.spinner("Descargando base Agricola..."):
                    filepath_agr = downloader.download("agricola")
                    st.success(f"\\u2705 Descargado: `{filepath_agr.name}`")
                with st.spinner("Descargando base Pecuaria..."):
                    filepath_pec = downloader.download("pecuario")
                    st.success(f"\\u2705 Descargado: `{filepath_pec.name}`")
                st.balloons()
            except Exception as e:
                st.error(f"\\u274C Error en la descarga: {e}")
                st.info("Asegurate de tener Chrome instalado y conexion a internet.")

    st.markdown("---")

    # ── Seccion 3: Ejecutar Pasos del Pipeline ───────────────
    st.subheader("\\u25B6\\uFE0F Ejecutar Pasos del Pipeline")
    st.caption("Ejecuta pasos individuales del pipeline desde la interfaz")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("\\U0001F504 Paso 1: Carga y Estandarizacion"):
            with st.spinner("Ejecutando Paso 1..."):
                try:
                    from core.audit.loader import load_and_standardize
                    df_valle, mapeo = load_and_standardize()
                    st.success(f"\\u2705 Paso 1 completado: {len(df_valle):,} registros")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")

        if st.button("\\U0001F50D Paso 2: Auditoria"):
            with st.spinner("Ejecutando Paso 2..."):
                try:
                    from core.audit.loader import load_and_standardize
                    from core.audit import run_all_audits
                    from core.audit.report import generate_audit_report
                    df_valle, _ = load_and_standardize()
                    findings = run_all_audits(df_valle)
                    df_report = generate_audit_report(findings)
                    st.success(f"\\u2705 Paso 2 completado: {len(findings)} hallazgos")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")

        if st.button("\\U0001F3D7\\uFE0F Paso 3: Modelado Conceptual"):
            with st.spinner("Ejecutando Paso 3..."):
                try:
                    from core.modeling import run_conceptual_modeling
                    df_modelo, artefactos = run_conceptual_modeling()
                    st.success(f"\\u2705 Paso 3 completado: {len(df_modelo):,} registros")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")

    with col2:
        if st.button("\\U0001F4C8 Paso 4: Analisis Descriptivo"):
            with st.spinner("Ejecutando Paso 4 (12 analisis)..."):
                try:
                    from core.analytics import run_all_analytics
                    artefactos = run_all_analytics()
                    st.success(f"\\u2705 Paso 4 completado: {len(artefactos)} artefactos")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")

        if st.button("\\U0001F52C Paso 6: Diagnostico"):
            with st.spinner("Ejecutando Paso 6 (5 analisis)..."):
                try:
                    from core.diagnostics import run_all_diagnostics
                    artefactos = run_all_diagnostics()
                    st.success(f"\\u2705 Paso 6 completado: {len(artefactos)} artefactos")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")

        if st.button("\\U0001F916 Paso 7: Predictivo"):
            with st.spinner("Ejecutando Paso 7 (modelos ML)..."):
                try:
                    from core.ml import run_all_ml
                    artefactos = run_all_ml(persist_models=True)
                    st.success(f"\\u2705 Paso 7 completado: {len(artefactos)} artefactos")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")

    st.markdown("---")

    # ── Seccion 4: Parametros del Sistema ────────────────────
    st.subheader("\\u2699\\uFE0F Parametros del Sistema")
    st.caption("Configuracion cargada desde `.env`")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Proyecto:**")
        st.code(f"""PROJECT_NAME: {settings.PROJECT_NAME}
ENV: {settings.ENV}
PROJECT_ROOT: {settings.PROJECT_ROOT}""", language=None)

        st.markdown("**Datos:**")
        st.code(f"""DATA_RAW_PATH: {settings.DATA_RAW_PATH}
DATA_PROCESSED_PATH: {settings.DATA_PROCESSED_PATH}
DATA_MODEL_PATH: {settings.DATA_MODEL_PATH}""", language=None)

    with col2:
        st.markdown("**Descarga UPRA:**")
        st.code(f"""UPRA_BASE_URL: {settings.UPRA_BASE_URL}
DOWNLOAD_TIMEOUT: {settings.DOWNLOAD_TIMEOUT}s
DOWNLOAD_RETRIES: {settings.DOWNLOAD_RETRIES}
HEADLESS: {settings.HEADLESS}""", language=None)

        st.markdown("**Machine Learning:**")
        st.code(f"""ML_RANDOM_STATE: {settings.ML_RANDOM_STATE}
ML_TEST_SIZE: {settings.ML_TEST_SIZE}
ML_MODELS_PATH: {settings.MODELS_PATH}""", language=None)

    st.markdown("---")

    # ── Seccion 5: Informacion del Proyecto ──────────────────
    st.subheader("\\u2139\\uFE0F Acerca del Proyecto")

    st.markdown(
        """
**EVA Valle v3.0** — Dashboard Analitico de Produccion Agricola

- **Fuente de datos:** UPRA (Unidad de Planificacion Rural y Agropecuaria)
- **Periodo:** 2019-2024 (6 anos)
- **Alcance:** 42 municipios del Valle del Cauca
- **Registros:** ~9,032
- **Arquitectura:** Hexagonal Modular (Ports & Adapters)
- **Stack:** Python 3.14 + Streamlit + Plotly + Pandas + scikit-learn
        """
    )

    st.markdown(
        '<div class="eva-footer">'
        "EVA Valle v3.0 | UPRA | Arquitectura Hexagonal Modular"
        "</div>",
        unsafe_allow_html=True,
    )


main()
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "ui/pages/5_\\U0001F50D_Auditoria.py": PAGE_AUDITORIA,
        "ui/pages/6_\\u2699\\uFE0F_Configuracion.py": PAGE_CONFIGURACION,
    }

    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")

    print(f"\n{len(archivos)} paginas creadas.")
    print("Ejecuta: streamlit run app.py")