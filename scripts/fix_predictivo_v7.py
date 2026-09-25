"""AUD-V5-005: reescribir 4_Predictivo.py con mapeo real de columnas,
slug con guion bajo, y filtro municipal real usando forecast_series_level.csv.
Fail-safe: backup, rollback, autotest estatico, sintaxis.
"""
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
import json
import py_compile

RAIZ = Path(__file__).resolve().parent.parent
UI = RAIZ / "ui" / "pages" / "4_Predictivo.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

PREDICTIVO_V7 = r'''"""Pagina Predictivo v7 — portal de artefactos del pipeline v5 (notebook shock-aware).
No ejecuta ningun modelo: lee outputs_v5/ producido por explore_base_agricola_v5_2_fichas (1).ipynb
(47/47 pruebas PASS, naive imbatible, central forzado a pool_A_full, D1 integrado).
AUD-V5-005.
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import re
import unicodedata

st.set_page_config(page_title="Predictivo", page_icon="📈", layout="wide")
OUT = Path("outputs_v5")


def _slug(s: str) -> str:
    """Normaliza a slug de archivo: guion bajo, minusculas, sin acentos.
    Ej: 'Tomate de árbol' -> 'tomate_de_arbol' (coincide con pronostico_tomate_de_arbol.png).
    """
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "cultivo"


def _es_t(v):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "–"
    a = abs(v)
    dec = 0 if a >= 100 else (1 if a >= 10 else 2)
    return f"{v:,.{dec}f}".replace(",", "\0").replace(".", ",").replace("\0", ".")


def _compact(v):
    if v is None or not np.isfinite(v):
        return "–"
    a = abs(v)
    if a >= 1e6:
        return f"{v/1e6:,.2f}".replace(",", "\0").replace(".", ",").replace("\0", ".") + " M"
    if a >= 1e3:
        return f"{v/1e3:,.0f}".replace(",", "\0").replace(".", ",").replace("\0", ".") + " mil"
    return _es_t(v)


def _pct(v):
    if v is None or not np.isfinite(v):
        return "–"
    sgn = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sgn}{abs(v):.1f} %"


# --- verificacion de artefactos ---
NEED = {
    "meta": OUT / "forecasting" / "meta_series.csv",
    "panel": OUT / "temporal" / "panel_anual.csv",
    "fc_series": OUT / "forecasting" / "forecast_series_level.csv",
    "crop_table": OUT / "fichas_cultivos" / "pronostico_por_cultivo.csv",
    "d1": OUT / "scenarios" / "sensitivity_D1_exclude_quiebre.csv",
    "pdf": OUT / "fichas_cultivos" / "fichas_valle_del_cauca.pdf",
}
missing = [k for k, p in NEED.items() if not p.exists()]
if missing:
    st.error(f"🔴 Faltan artefactos del pipeline v5: {missing}. "
             f"Ejecute primero `Kernel > Restart & Run All` en el notebook de trabajo.")
    st.info("Ruta esperada: `outputs_v5/` en la raíz del repo. "
            "En Streamlit Cloud los artefactos deben estar commiteados.")
    st.stop()

# --- carga ---
meta = pd.read_csv(NEED["meta"], encoding="utf-8-sig")
panel = pd.read_csv(NEED["panel"], encoding="utf-8-sig")
fc_series = pd.read_csv(NEED["fc_series"], encoding="utf-8-sig")
crop_table = pd.read_csv(NEED["crop_table"], encoding="utf-8-sig")
d1 = pd.read_csv(NEED["d1"], encoding="utf-8-sig")

# --- encabezado ---
st.title("📈 Proyección agrícola — Valle del Cauca")
st.caption("Motor: pipeline v5 shock-aware (47/47 PASS). Naive imbatible en backtest; "
           "proyección central = `pool_A_full` (decisión del usuario, rotulada). "
           "Escenarios = supuestos condicionales, no predicciones.")

# --- selector de ambito ---
col1, col2 = st.columns([1, 2])
with col1:
    ambito = st.radio("Ámbito", ["🏛️ Departamental", "🏘️ Municipal"], horizontal=False)

if ambito == "🏛️ Departamental":
    scope_muni = None
    scope_code = None
    scope_title = "Valle del Cauca (suma de municipios)"
else:
    munis = sorted(meta.drop_duplicates("muni_code")[["muni_code", "muni"]]
                   .dropna().itertuples(index=False), key=lambda r: r.muni)
    muni_labels = [f"{r.muni} ({r.muni_code})" for r in munis]
    pick = st.selectbox("Municipio", muni_labels, index=0)
    sel = munis[muni_labels.index(pick)]
    scope_muni = sel.muni
    scope_code = sel.muni_code
    scope_title = f"Municipio de {scope_muni}"

# --- selector de cultivo ---
if ambito == "🏛️ Departamental":
    crops = sorted(crop_table["cultivo"].dropna().unique())
    crop_sel = st.selectbox("Cultivo", crops,
                            index=crops.index("Plátano") if "Plátano" in crops else 0)
else:
    # ambito municipal: solo cultivos con serie en ese municipio
    crops_muni = sorted(fc_series[fc_series["muni_code"] == scope_code]["crop"].dropna().unique())
    if not crops_muni:
        st.warning(f"Sin series de pronostico en {scope_muni}.")
        st.stop()
    crop_sel = st.selectbox("Cultivo", crops_muni,
                            index=crops_muni.index("Plátano") if "Plátano" in crops_muni else 0)

st.markdown(f"**Ámbito:** {scope_title}  ·  **Cultivo:** {crop_sel}")

# --- datos del cultivo segun ambito ---
if ambito == "🏛️ Departamental":
    # tabla agregada del notebook (1 fila por cultivo y horizonte)
    crop_row = crop_table[(crop_table["cultivo"] == crop_sel) & (crop_table["h"] == 1)]
    if crop_row.empty:
        st.warning(f"Sin proyección para {crop_sel} (ninguna serie con dato en 2025).")
        st.stop()
    r = crop_row.iloc[0]
    # bandas departamentales simuladas del notebook (ya en la tabla)
    obs_2025 = float(r["observado_2025_t"])
    pron_2026 = float(r["pron_central_t"])
    pi95_lo = float(r["pi95_lo"])
    pi95_hi = float(r["pi95_hi"])
    modelo_central = str(r["modelo_central"])
    band_note = "Bandas: cuantiles empiricos de residuos fuera de muestra (pipeline v5)."
else:
    # ambito municipal: suma de series individuales del municipio
    muni_rows = fc_series[(fc_series["muni_code"] == scope_code) &
                          (fc_series["crop"] == crop_sel) & (fc_series["h"] == 1)]
    if muni_rows.empty:
        st.warning(f"Sin series con dato en 2025 para {crop_sel} en {scope_muni}.")
        st.stop()
    obs_2025 = float(muni_rows["last_obs_t"].sum())
    pron_2026 = float(muni_rows["pron_central_t"].sum())
    # bandas aproximadas (suma de series independientes; declaradas como tal)
    pi95_lo = float(muni_rows["pi95_lo"].sum()) if muni_rows["pi95_lo"].notna().any() else np.nan
    pi95_hi = float(muni_rows["pi95_hi"].sum()) if muni_rows["pi95_hi"].notna().any() else np.nan
    modelos = muni_rows["modelo_central"].dropna().unique()
    modelo_central = "/".join(sorted(modelos)) if len(modelos) else "naive"
    n_series = int(muni_rows["series_id"].nunique())
    band_note = (f"Bandas: suma de intervalos de {n_series} series individuales "
                 f"(aproximacion — las bandas agregadas simuladas solo existen a nivel departamental).")

# --- D1 flag (siempre departamental: sensibilidad del cultivo en todo el dpto) ---
d1_row = d1[d1["cultivo"] == crop_sel]
d1_flag = False
if not d1_row.empty:
    d1r = d1_row.iloc[0]
    delta = float(d1r.get("delta_2026_pct", 0) or 0)
    if bool(d1r.get("afectado", False)) and abs(delta) > 10:
        d1_flag = True
        st.warning(
            f"⚠️ **Sensibilidad D1:** {int(d1r['series_excluidas'])} de {int(d1r['series_total'])} "
            f"series departamentales de {crop_sel} presentan quiebre de definición 2021→2022 no validado con la fuente; "
            f"al excluirlas, la proyección 2026 departamental cae **{abs(delta):.0f}%** "
            f"(de {_compact(d1r['baseline_2026_t'])} a {_compact(d1r['clean_2026_t'])} t). "
            f"Lea el central como cota superior."
        )

# --- KPIs ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("Observado 2025", f"{_compact(obs_2025)} t")
k2.metric("Proyección 2026", f"{_compact(pron_2026)} t",
          _pct(100 * (pron_2026 / obs_2025 - 1)) if obs_2025 else None)
if np.isfinite(pi95_lo) and np.isfinite(pi95_hi):
    k3.metric("Rango 95% (2026)", f"{_compact(pi95_lo)}–{_compact(pi95_hi)} t")
else:
    k3.metric("Rango 95% (2026)", "n.d.")
k4.metric("Modelo central", modelo_central)
st.caption(band_note)

# --- grafica (PNG exacto del notebook, solo a nivel departamental) ---
png = OUT / "fichas_cultivos" / f"pronostico_{_slug(crop_sel)}.png"
if png.exists():
    st.image(str(png), use_container_width=True)
    if ambito == "🏘️ Municipal":
        st.info("ℹ️ La gráfica muestra la serie **departamental**. "
                "La proyección municipal se calcula sumando las series individuales del municipio.")
else:
    st.info("Gráfica PNG no disponible para este cultivo.")

# --- tabla de proyeccion por horizonte ---
st.subheader("Proyección por horizonte")
if ambito == "🏛️ Departamental":
    df_show = crop_table[crop_table["cultivo"] == crop_sel][
        ["h", "anio", "observado_2025_t", "pron_central_t",
         "pi80_lo", "pi80_hi", "pi95_lo", "pi95_hi",
         "esc_normal_t", "esc_historico_t", "esc_estres_t"]
    ].copy()
else:
    # ambito municipal: construye desde fc_series sumando h=1 y h=2
    rows = []
    for h in [1, 2]:
        mh = fc_series[(fc_series["muni_code"] == scope_code) &
                       (fc_series["crop"] == crop_sel) & (fc_series["h"] == h)]
        if mh.empty:
            continue
        rows.append({
            "h": h,
            "anio": int(mh["target_year"].iloc[0]),
            "observado_2025_t": float(mh["last_obs_t"].sum()),
            "pron_central_t": float(mh["pron_central_t"].sum()),
            "pi80_lo": float(mh["pi80_lo"].sum()) if mh["pi80_lo"].notna().any() else np.nan,
            "pi80_hi": float(mh["pi80_hi"].sum()) if mh["pi80_hi"].notna().any() else np.nan,
            "pi95_lo": float(mh["pi95_lo"].sum()) if mh["pi95_lo"].notna().any() else np.nan,
            "pi95_hi": float(mh["pi95_hi"].sum()) if mh["pi95_hi"].notna().any() else np.nan,
            "esc_normal_t": float(mh["esc_normal_t"].sum()),
            "esc_historico_t": float(mh["esc_historico_t"].sum()),
            "esc_estres_t": float(mh["esc_estres_t"].sum()),
        })
    df_show = pd.DataFrame(rows)

df_show = df_show.rename(columns={
    "h": "h", "anio": "Año", "observado_2025_t": "Obs. 2025 (t)",
    "pron_central_t": "Central (t)",
    "pi80_lo": "PI80 lo", "pi80_hi": "PI80 hi",
    "pi95_lo": "PI95 lo", "pi95_hi": "PI95 hi",
    "esc_normal_t": "Normal", "esc_historico_t": "Histórico", "esc_estres_t": "Estrés"
})
for c in df_show.columns[2:]:
    df_show[c] = df_show[c].apply(lambda v: _compact(v))
st.dataframe(df_show, hide_index=True, use_container_width=True)

# --- escenarios (lectura) ---
with st.expander("ℹ️ Cómo leer los escenarios «¿Y si…?»"):
    st.markdown("""
- **Normal:** sigue el ritmo posterior al shock 2020-21 (pesos 0 / 0.5 / 1).
- **Histórico:** dinámica completa 2019-2025 sin intervención (pesos 1 / 1 / 1).
- **Estrés:** se repite una caída como la del shock 2020-21 durante 2 años.
- **Persistencia (naive):** la cifra de 2025 se repite (referencia del backtest).

Son **supuestos condicionales**, no predicciones competidoras.
""")

# --- descargas ---
st.subheader("📥 Descargas")
c1, c2, c3 = st.columns(3)
with c1:
    if png.exists():
        with open(png, "rb") as f:
            st.download_button("📊 PNG del cultivo", f, file_name=png.name, mime="image/png")
with c2:
    if NEED["pdf"].exists():
        with open(NEED["pdf"], "rb") as f:
            st.download_button("📕 Fichas PDF (78 cultivos)", f,
                               file_name="fichas_valle_del_cauca_v5.pdf",
                               mime="application/pdf")
with c3:
    if ambito == "🏛️ Departamental":
        csv = crop_row.to_csv(index=False).encode("utf-8-sig")
    else:
        csv = muni_rows.to_csv(index=False).encode("utf-8-sig")
    scope_tag = "dept" if ambito == "🏛️ Departamental" else _slug(scope_muni)
    st.download_button("📄 CSV del cultivo", csv,
                       file_name=f"proyeccion_{scope_tag}_{_slug(crop_sel)}.csv",
                       mime="text/csv")

# --- nota metodologica ---
with st.expander("📘 Notas metodológicas"):
    st.markdown(f"""
**Fuente:** EVA-UPRA, Base Agrícola 2019-2025. Cifras 2024-2025 provisionales.

**Proyección central:** `{modelo_central}` — crecimiento común a series similares del departamento.
El backtest (walk-forward sin fuga) no halló ningún modelo que supere a naive con IC95% en ninguna vista;
la persistencia es el piso honesto y `pool_A_full` una decisión de planificación rotulada.

**Bandas 80% / 95%:** cuantiles empíricos de residuos fuera de muestra, sin incluir los que cruzan el shock 2020-21.
{band_note}

**Quiebre de definición 2022:** en cultivos transitorios, antes la fuente registra siembras y desde entonces
cosechas efectivas; por eso solo 2022-2025 es comparable en transitorios.
{'**⚠️ Este cultivo tiene series con quiebre D1 no validado.**' if d1_flag else ''}
""")

st.caption("AUD-V5-005 · portal de artefactos v5 · motor legacy archivado")
'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-V5-005", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def main():
    if not UI.exists():
        return fail(f"no existe {UI}")

    # 1) backup
    bak = UI.with_suffix(".py.bak.v6")
    shutil.copy2(UI, bak)

    # 2) escribir portal v7
    UI.write_text(PREDICTIVO_V7, encoding="utf-8")
    print(f"[OK] {UI.name} reescrito (v7: slug _ y filtro municipal) | backup: {bak.name}")

    # 3) autotest estatico
    texto = UI.read_text(encoding="utf-8")
    tokens = ("outputs_v5", "meta_series.csv", "forecast_series_level.csv",
              "sensitivity_D1_exclude_quiebre", "AUD-V5-005", "st.download_button",
              "pronostico_{_slug(crop_sel)}.png",
              "fc_series[\"muni_code\"] == scope_code")
    for token in tokens:
        if token not in texto:
            shutil.copy2(bak, UI)
            return fail(f"autotest: falta {token}")
    print(f"[OK] autotest: {len(tokens)} tokens v7 presentes")

    # 4) sintaxis
    try:
        py_compile.compile(str(UI), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, UI)
        audit("AUD-V5-005", "ROLLBACK", str(e)[:200])
        return fail(f"sintaxis invalida: {e}")
    print("[OK] sintaxis valida")

    audit("AUD-V5-005", "OK", "portal v7 desplegado")
    print("\n[OK] AUD-V5-005 aplicado.")
    print("Siguiente: verificar local con `streamlit run app.py` y luego commitear.")
    return 0


if __name__ == "__main__":
    sys.exit(main())