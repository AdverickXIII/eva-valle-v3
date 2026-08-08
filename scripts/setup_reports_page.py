"""Crea ui/pages/10_Reportes.py y la registra en app.py."""
from pathlib import Path

PAGE = '''"""Pagina 10: Reportes por municipio (Excel y PDF)."""
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

st.set_page_config(page_title="Reportes | EVA Valle", page_icon="\\U0001F4C4", layout="wide")


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
    st.title("\\U0001F4C4 Reportes por Municipio")
    st.caption("Genera y descarga un reporte profesional en Excel o PDF")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    municipios = sorted(df["municipio"].dropna().unique().tolist())
    m = st.selectbox("Selecciona un municipio", municipios)

    df_m = df[df["municipio"] == m]
    k = kpis(df_m, df)

    st.markdown("---")
    render_kpi_row([
        {"label": "Produccion", "value": f"{k['Produccion total (t)']:,.0f} t", "icon": "\\U0001F33E"},
        {"label": "Area", "value": f"{k['Area sembrada (ha)']:,.0f} ha", "icon": "\\U0001F4D0"},
        {"label": "Rendimiento", "value": f"{k['Rendimiento promedio (t/ha)']:.1f} t/ha", "icon": "\\U0001F4C8"},
        {"label": "% del Dpto.", "value": f"{k['% de la produccion departamental']:.1f}%", "icon": "\\U0001F3AF"},
    ], cols=4)

    st.markdown("---")
    safe = m.replace(" ", "_").lower()
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "\\U0001F4CA Descargar Excel",
            data=get_excel(df, m),
            file_name=f"reporte_{safe}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "\\U0001F4C4 Descargar PDF",
            data=get_pdf(df, m),
            file_name=f"reporte_{safe}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.info("\\U0001F4A1 El PDF es un documento formal listo para imprimir o presentar. "
            "El Excel incluye 3 hojas: Resumen, Historico Anual y Top Cultivos.")


main()
'''

if __name__ == "__main__":
    p = Path("ui/pages/10_Reportes.py")
    p.write_text(PAGE, encoding="utf-8")
    print(f"[OK] {p}")

    app = Path("app.py")
    c = app.read_text(encoding="utf-8")
    anchor = 'st.Page("ui/pages/7_Cultivos.py"'
    nueva = '    st.Page("ui/pages/10_Reportes.py", title="Reportes", icon="\\U0001F4C4"),\n'
    if anchor in c and "10_Reportes.py" not in c:
        i = c.find(anchor)
        fin = c.find("\n", i)
        c = c[: fin + 1] + nueva + c[fin + 1 :]
        app.write_text(c, encoding="utf-8")
        print("[OK] app.py (pagina Reportes registrada)")
    else:
        print("[INFO] app.py ya tenia Reportes o no encontro anchor")

    print("\nListo. Ejecuta: streamlit run app.py")