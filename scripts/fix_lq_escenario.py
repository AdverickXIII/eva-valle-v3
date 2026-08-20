"""Unifica la base de calculo LQ: checkbox con/sin cana para heatmap Y tabla."""
from pathlib import Path

# --- 1) lq_table.py: aceptar excluye_cana ---
p1 = Path("core/analytics/lq_table.py")
c1 = p1.read_text(encoding="utf-8")
old1 = "def lq_top(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:\n    mg ="
new1 = ("def lq_top(df: pd.DataFrame, top_n: int = 20, excluye_cana: bool = False) -> pd.DataFrame:\n"
        "    if excluye_cana:\n"
        "        df = df[df[\"cultivo\"] != \"Caña\"]\n"
        "    mg =")
if old1 in c1:
    p1.write_text(c1.replace(old1, new1, 1), encoding="utf-8")
    print("[OK] lq_top con parametro excluye_cana")
else:
    print("[AVISO] lq_top ya ajustado o formato distinto")

# --- 2) spatial.py: heatmap con parametro ---
p2 = Path("ui/charts/spatial.py")
c2 = p2.read_text(encoding="utf-8")
old2 = 'def plot_lq_heatmap(df: pd.DataFrame, top_n: int = 15) -> go.Figure:'
new2 = 'def plot_lq_heatmap(df: pd.DataFrame, top_n: int = 15, excluye_cana: bool = True) -> go.Figure:'
old2b = '    df_sin = df[df["cultivo"] != "Caña"]'
new2b = '    df_sin = df[df["cultivo"] != "Caña"] if excluye_cana else df'
if old2 in c2 and old2b in c2:
    c2 = c2.replace(old2, new2, 1).replace(old2b, new2b, 1)
    p2.write_text(c2, encoding="utf-8")
    print("[OK] plot_lq_heatmap con parametro excluye_cana")
else:
    print("[AVISO] heatmap ya ajustado o formato distinto")

# --- 3) Pagina: checkbox que gobierna ambas piezas ---
p3 = Path("ui/pages/2_Descriptivo.py")
c3 = p3.read_text(encoding="utf-8")
old3 = "        st.plotly_chart(plot_lq_heatmap(df_f, top_n=15), use_container_width=True)"
new3 = ("        sin_cana = st.checkbox(\"Analizar sin cana (economia agricola real)\", value=True,\n"
        "                               help=\"Con cana, los LQ se inflan: la cana aplasta los porcentajes departamentales.\")\n"
        "        st.plotly_chart(plot_lq_heatmap(df_f, top_n=15, excluye_cana=sin_cana), use_container_width=True)")
old3b = "        df_lq = lq_top(df_f, 200)"
new3b = "        df_lq = lq_top(df_f, 200, excluye_cana=sin_cana)"
if old3 in c3 and old3b in c3:
    c3 = c3.replace(old3, new3, 1).replace(old3b, new3b, 1)
    p3.write_text(c3, encoding="utf-8")
    print("[OK] Checkbox de escenario conectado a heatmap y tabla")
else:
    print("[AVISO] Revisa manualmente tab5")

print("\nReinicia Streamlit: heatmap y tabla ahora usan la MISMA base")