"""Comparador v2: empates con precision mostrada + grafica de rendimiento en el PDF."""
from pathlib import Path

# ---------- 1) Pagina: ganador con la misma precision que se muestra ----------
p = Path("ui/pages/11_Comparador.py")
c = p.read_text(encoding="utf-8")

old_loop = '''    filas = []
    for k in ["Produccion total (t)", "Area sembrada (ha)", "Rendimiento (t/ha)",
              "Cultivos activos", "% del departamento", "Diversidad (Shannon)",
              "CAGR 2019-2025 (%)"]:
        va, vb = sa[k], sb[k]
        win = "🤝 Empate" if abs(va - vb) < 1e-9 else (f"🅰️ {a}" if va > vb else f"🅱️ {b}")
        filas.append({"Indicador": k, f"A · {a}": f"{va:,.1f}",
                      f"B · {b}": f"{vb:,.1f}", "Gana": win})'''

new_loop = '''    filas = []
    PREC = {"Produccion total (t)": 0, "Area sembrada (ha)": 0,
            "Rendimiento (t/ha)": 1, "Cultivos activos": 0,
            "% del departamento": 1, "Diversidad (Shannon)": 1,
            "CAGR 2019-2025 (%)": 1}
    for k in ["Produccion total (t)", "Area sembrada (ha)", "Rendimiento (t/ha)",
              "Cultivos activos", "% del departamento", "Diversidad (Shannon)",
              "CAGR 2019-2025 (%)"]:
        prec = PREC[k]
        va = round(sa[k], prec)
        vb = round(sb[k], prec)
        win = "🤝 Empate" if va == vb else (f"🅰️ {a}" if va > vb else f"🅱️ {b}")
        filas.append({"Indicador": k, f"A · {a}": f"{va:,.{prec}f}",
                      f"B · {b}": f"{vb:,.{prec}f}", "Gana": win})'''

if old_loop in c:
    c = c.replace(old_loop, new_loop, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Ganador calculado con la precision mostrada (empates reales)")
else:
    print("[AVISO] Bloque de tabla distinto; revisa manualmente")

# ---------- 2) PDF: funcion de rendimiento por ano ----------
pf = Path("core/reports/comparador_pdf.py")
cf = pf.read_text(encoding="utf-8")

REND_FUNC = '''

def _rend_png(df_ab, a, b) -> bytes:
    rend = (df_ab.groupby(["ano", "municipio"])
            .agg(prod=("produccion_t", "sum"), cos=("area_cosechada_ha", "sum"))
            .reset_index())
    rend["rend"] = rend["prod"] / rend["cos"].replace(0, 1)
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    for m, col in ((a, VERDE), (b, NARANJA)):
        d = rend[rend["municipio"] == m].sort_values("ano")
        ax.plot(d["ano"], d["rend"], "o-", color=col, lw=2, label=m)
    ax.set_ylabel("t/ha", fontsize=8)
    ax.set_title("Rendimiento por ano (t/ha)", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _png(fig)


'''

if "_rend_png" not in cf:
    cf = cf.replace("def build_comparador_pdf(", REND_FUNC + "def build_comparador_pdf(", 1)

    old_fuente = '''    story.append(Paragraph(
        f"Fuente: UPRA - EVA 2019-2025. {meta.firma()}.",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8)))'''
    new_fuente = '''    story.append(Paragraph("<b>Rendimiento por ano (t/ha)</b>", body))
    _add_png(story, _rend_png(df_ab, a, b))

    story.append(Paragraph(
        f"Fuente: UPRA - EVA 2019-2025. {meta.firma()}.",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8)))'''
    if old_fuente in cf:
        cf = cf.replace(old_fuente, new_fuente, 1)
        pf.write_text(cf, encoding="utf-8")
        print("[OK] PDF con grafica de rendimiento por ano")
    else:
        pf.write_text(cf, encoding="utf-8")
        print("[AVISO] Ancla de fuente distinta; revisa manualmente")
else:
    print("[INFO] PDF ya tenia grafica de rendimiento")

print("Reinicia Streamlit y vuelve a probar Alcalá vs Andalucía")