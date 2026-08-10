"""Crea ui/pages/16_Mapa_Cultivos.py y la registra."""
from pathlib import Path

PAGE = '''"""Pagina 16: Mapa coropletico por cultivo."""
from __future__ import annotations

import pandas as pd
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.charts.spatial_map import plot_choropleth_municipios
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Mapa Cultivos | EVA Valle", page_icon="\\U0001F5FA\\uFE0F", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def main() -> None:
    st.title("\\U0001F5FA\\uFE0F Mapa Coropletico por Cultivo")
    st.caption("Distribucion territorial de cada cultivo (2019-2025)")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    c1, c2 = st.columns(2)
    with c1:
        cultivo = st.selectbox("Cultivo", sorted(df["cultivo"].dropna().unique().tolist()))
    with c2:
        metrica = st.selectbox("Metrica",
            ["produccion_t", "area_sembrada_ha", "area_cosechada_ha"],
            format_func=lambda x: {"produccion_t": "Produccion (t)",
                                   "area_sembrada_ha": "Area sembrada (ha)",
                                   "area_cosechada_ha": "Area cosechada (ha)"}[x])

    df_c = df[df["cultivo"] == cultivo]
    fig = plot_choropleth_municipios(df_c, metrica, f"{cultivo} por municipio")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Municipios", df_c["municipio"].nunique())
    k2.metric("Produccion", f"{df_c['produccion_t'].sum():,.0f} t")
    k3.metric("Area", f"{df_c['area_sembrada_ha'].sum():,.0f} ha")
    cos = df_c["area_cosechada_ha"].sum()
    k4.metric("Rendimiento", f"{df_c['produccion_t'].sum()/cos:.2f} t/ha" if cos else "-")


main()
'''

if __name__ == "__main__":
    Path("ui/pages/16_Mapa_Cultivos.py").write_text(PAGE, encoding="utf-8")
    print("[OK] ui/pages/16_Mapa_Cultivos.py")

    app = Path("app.py")
    c = app.read_text(encoding="utf-8")
    anchor = 'st.Page("ui/pages/15_Ejecutivo.py"'
    nueva = '    st.Page("ui/pages/16_Mapa_Cultivos.py", title="Mapa Cultivos", icon="\\U0001F5FA\\uFE0F"),\n'
    if anchor in c and "16_Mapa_Cultivos.py" not in c:
        i = c.find(anchor)
        fin = c.find("\n", i)
        c = c[: fin + 1] + nueva + c[fin + 1 :]
        app.write_text(c, encoding="utf-8")
        print("[OK] app.py (pagina Mapa Cultivos)")
    print("\nEjecuta: streamlit run app.py")