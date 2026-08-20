"""Reescribe plot_lq_heatmap: eje Y con nombres de municipio + 1 valor por celda."""
from pathlib import Path

NEW_FUNC = '''def plot_lq_heatmap(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Heatmap LQ legible: municipios en Y, grupos en X, un valor por celda."""
    df_sin = df[df["cultivo"] != "Caña"]
    mg = df_sin.groupby(["municipio", "grupo_cultivo"])["produccion_t"].sum()
    m_tot = df_sin.groupby("municipio")["produccion_t"].sum()
    g_tot = df_sin.groupby("grupo_cultivo")["produccion_t"].sum()
    total = float(df_sin["produccion_t"].sum())

    rows = []
    for (m, g), v in mg.items():
        sm = v / m_tot[m] * 100 if m_tot[m] else 0.0
        sd = g_tot[g] / total * 100 if total else 0.0
        if sd > 0 and v > 0:
            rows.append({"municipio": m, "grupo": g, "lq": sm / sd})
    d = pd.DataFrame(rows)

    top_m = m_tot.sort_values(ascending=False).head(top_n).index.tolist()
    piv = (d[d["municipio"].isin(top_m)]
           .pivot_table(index="municipio", columns="grupo", values="lq", fill_value=0)
           .reindex(top_m))

    fig = go.Figure(go.Heatmap(
        z=piv.values,
        x=piv.columns.tolist(),
        y=piv.index.tolist(),
        xgap=2, ygap=2,
        colorscale="YlOrRd", zmin=0, zmax=5,
        colorbar=dict(title="LQ"),
        hovertemplate="%{y} · %{x}<br>LQ = %{z:.2f}<extra></extra>"))

    fig = apply_theme(fig, "Especializacion Territorial (LQ) - Top 15 Municipios")

    # Un solo numero por celda, con contraste segun fondo
    for i, m in enumerate(piv.index):
        for j, g in enumerate(piv.columns):
            v = float(piv.iloc[i, j])
            fig.add_annotation(
                x=g, y=m,
                text=f"{v:.1f}" if v >= 0.05 else "",
                showarrow=False,
                font=dict(size=9, color="white" if v >= 2.5 else "black"))

    fig.update_layout(
        yaxis=dict(type="category", autorange="reversed",
                   tickfont=dict(size=10), title_text=""),
        xaxis=dict(tickangle=-35, type="category"),
        height=560, margin=dict(t=40, b=10, l=10, r=10))
    return fig


'''

p = Path("ui/charts/spatial.py")
c = p.read_text(encoding="utf-8")
i = c.find("def plot_lq_heatmap")
if i == -1:
    print("[ERROR] No encontre plot_lq_heatmap en spatial.py")
    raise SystemExit(1)
j = c.find("\ndef ", i + 10)
if j == -1:
    j = len(c)
c = c[:i] + NEW_FUNC + c[j:]
p.write_text(c, encoding="utf-8")
print("[OK] plot_lq_heatmap reescrito: municipios en Y + 1 valor por celda")
print("Reinicia Streamlit y revisa Descriptivo -> Espacial -> 4.9")