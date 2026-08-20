"""Agrega tabla Top-LQ + ejemplo real + matriz de combinaciones a la pestana Espacial."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MOD = '''"""Tabla de Location Quotient por municipio-grupo."""
from __future__ import annotations

import pandas as pd


def lq_top(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    mg = df.groupby(["municipio", "grupo_cultivo"])["produccion_t"].sum()
    m_tot = df.groupby("municipio")["produccion_t"].sum()
    g_tot = df.groupby("grupo_cultivo")["produccion_t"].sum()
    total = float(df["produccion_t"].sum())
    rows = []
    for (m, g), v in mg.items():
        sm = v / m_tot[m] * 100 if m_tot[m] else 0.0
        sd = g_tot[g] / total * 100 if total else 0.0
        if sd > 0 and v > 0:
            rows.append({
                "municipio": m,
                "grupo_cultivo": g,
                "share_municipio_pct": sm,
                "share_valle_pct": sd,
                "lq": sm / sd,
            })
    out = pd.DataFrame(rows).sort_values("lq", ascending=False)
    return out.head(top_n).reset_index(drop=True)
'''

Path("core/analytics/lq_table.py").write_text(MOD, encoding="utf-8")

# --- Parche de la pagina ---
p = Path("ui/pages/2_Descriptivo.py")
c = p.read_text(encoding="utf-8")

if "lq_top" not in c:
    imp = "from core.analytics.spatial import calculate_location_quotient, calculate_shannon_diversity"
    c = c.replace(imp, imp + "\nfrom core.analytics.lq_table import lq_top")

i5 = c.find("    with tab5:")
i6 = c.find("    with tab6:")
if i5 == -1 or i6 == -1:
    print("[ERROR] No encontre tab5/tab6")
    raise SystemExit(1)

NEW_TAB5 = '''    with tab5:
        st.subheader("4.9 Location Quotient")
        st.plotly_chart(plot_lq_heatmap(df_f, top_n=15), use_container_width=True)
        st.markdown("**Top 20 especializaciones (LQ)** — municipios vs grupos de cultivo:")
        df_lq = lq_top(df_f, 20)
        st.dataframe(df_lq.round(2), use_container_width=True, hide_index=True)
        st.caption("LQ = (% del grupo en el municipio) / (% del grupo en el Valle). "
                   "LQ > 1 = especializacion; LQ >= 4 = vocacion fuerte.")

        st.subheader("4.10 Shannon-Wiener")
        st.plotly_chart(plot_shannon_barras(df_f, min_area=1000), use_container_width=True)
        st.markdown("""
**Matriz de decision (LQ x Shannon):**
| Combinacion | Lectura | Accion sugerida |
|---|---|---|
| LQ alto + Shannon bajo | Especializado y dependiente | Proteger la cadena + diversificar marginalmente |
| LQ alto + Shannon alto | Especializado con colchon | Fortalecer la vocacion |
| LQ bajo + Shannon alto | Diversificado sin vocacion clara | Detectar cadenas emergentes |
| LQ bajo + Shannon bajo | Sin vocacion y concentrado | Prioridad de inversion publica |
""")

'''

c = c[:i5] + NEW_TAB5 + c[i6:]
p.write_text(c, encoding="utf-8")
print("[OK] core/analytics/lq_table.py creado")
print("[OK] tab5 con tabla Top-LQ + matriz de combinaciones")

# --- Ejemplo REAL de calculo LQ con tus datos ---
import pandas as pd
from config.settings import settings
from core.analytics.lq_table import lq_top

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)
t = lq_top(df, 3)
print("\n=== EJEMPLO REAL DE CALCULO LQ ===")
for _, r in t.iterrows():
    print(f"{r['municipio']} / {r['grupo_cultivo']}:")
    print(f"  share municipio = {r['share_municipio_pct']:.2f}%  |  share Valle = {r['share_valle_pct']:.2f}%")
    print(f"  LQ = {r['share_municipio_pct']:.2f} / {r['share_valle_pct']:.2f} = {r['lq']:.2f}\n")
print("Reinicia Streamlit y revisa Descriptivo -> Espacial")