"""Crea ui/pages/13_Treemap.py y la registra en app.py."""
from pathlib import Path

PAGE = '''"""Pagina 13: Treemap de cultivos (jerarquia grupo -> cultivo)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Treemap | EVA Valle", page_icon="\\U0001F333", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def _cagr(df: pd.DataFrame) -> pd.DataFrame:
    anos = sorted(df["ano"].dropna().unique())
    if len(anos) < 2:
        return pd.DataFrame()
    ini = df[df["ano"] == min(anos)].groupby("cultivo")["produccion_t"].sum()
    fin = df[df["ano"] == max(anos)].groupby("cultivo")["produccion_t"].sum()
    d = pd.DataFrame({"ini": ini, "fin": fin}).dropna()
    d = d[d["ini"] > 0]
    n = int(max(anos)) - int(min(anos))
    d["cagr"] = ((d["fin"] / d["ini"]) ** (1 / n) - 1) * 100
    return d.reset_index()


def main() -> None:
    st.title("\\U0001F333 Treemap de Cultivos")
    st.caption("Jerarquia grupo -> cultivo. Tamano y color configurables. "
               "Haz clic en un grupo para hacer zoom.")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        tam = st.selectbox("Tamano", ["Produccion (t)", "Area sembrada (ha)"], 0)
    with c2:
        col = st.selectbox("Color", ["Produccion (t)", "Rendimiento (t/ha)", "CAGR (%)"], 0)
    with c3:
        anos = sorted(df["ano"].dropna().unique().tolist())
        vista = st.selectbox("Periodo", ["Todo (2019-2024)"] + [str(int(a)) for a in anos], 0)

    df_f = df.copy()
    if vista != "Todo (2019-2024)":
        df_f = df_f[df_f["ano"] == int(vista)]

    agg = (df_f.groupby(["grupo_cultivo", "cultivo"])
           .agg(prod=("produccion_t", "sum"),
                area=("area_sembrada_ha", "sum"),
                cos=("area_cosechada_ha", "sum"))
           .reset_index())
    agg["rend"] = agg["prod"] / agg["cos"].replace(0, 1)

    size_col = "prod" if tam.startswith("Produccion") else "area"
    if col.startswith("Produccion"):
        color_col, cname = "prod", "Produccion (t)"
    elif col.startswith("Rendimiento"):
        color_col, cname = "rend", "Rendimiento (t/ha)"
    else:
        cagr = _cagr(df)
        agg = agg.merge(cagr[["cultivo", "cagr"]], on="cultivo", how="left")
        agg["cagr"] = agg["cagr"].fillna(0)
        color_col, cname = "cagr", "CAGR (%)"

    fig = px.treemap(
        agg,
        path=[px.Constant("Valle"), "grupo_cultivo", "cultivo"],
        values=size_col,
        color=color_col,
        color_continuous_scale="Viridis",
        labels={
            "prod": "Produccion (t)", "area": "Area (ha)",
            "rend": "Rendimiento (t/ha)", "cagr": "CAGR (%)",
            "grupo_cultivo": "Grupo", "cultivo": "Cultivo",
        },
        title=f"Tamano = {tam} | Color = {cname}",
    )
    fig.update_layout(template="plotly_white", height=650,
                      margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.caption("\\U0001F4A1 Consejo: elige Color = CAGR (%) para ver de un vistazo "
               "que cultivos crecen (claro) y cuales declinan (oscuro).")


main()
'''

if __name__ == "__main__":
    Path("ui/pages/13_Treemap.py").write_text(PAGE, encoding="utf-8")
    print("[OK] ui/pages/13_Treemap.py")

    app = Path("app.py")
    c = app.read_text(encoding="utf-8")
    anchor = 'st.Page("ui/pages/12_Alertas.py"'
    nueva = '    st.Page("ui/pages/13_Treemap.py", title="Treemap", icon="\\U0001F333"),\n'
    if anchor in c and "13_Treemap.py" not in c:
        i = c.find(anchor)
        fin = c.find("\n", i)
        c = c[: fin + 1] + nueva + c[fin + 1 :]
        app.write_text(c, encoding="utf-8")
        print("[OK] app.py (pagina Treemap)")
    else:
        print("[INFO] app.py ya tenia Treemap o no encontro anchor")

    print("\nEjecuta: streamlit run app.py")