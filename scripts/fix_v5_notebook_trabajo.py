"""AUD-V5-003: aplica al notebook DE TRABAJO '(1)' los dos parches pendientes:
  H-EXP: exports para la app (meta_series.csv, panel_anual.csv) en celda 13b.
  H-D1 : semaforo D1 + nota en fichas (loader, wrapper, llamada, caja, nota) en 13f.
JSON-aware, anclas verificadas contra el contenido real del (1), backup y rollback.
No toca otros archivos: sin archivados ni consolidaciones.
"""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

# ---------- H-EXP (celda 13b) ----------
A_EXP = 'save_table(FC_AGG, "scenarios", "scenarios_aggregate.csv")'
N_EXP = A_EXP + '''
save_table(META.reset_index(), "forecasting", "meta_series.csv")   # AUD-V5-002: metadatos de serie para la app
save_table(PANEL, "temporal", "panel_anual.csv")                   # AUD-V5-002: panel anual P/AC/AS para historicos en la app'''

# ---------- H-D1 (celda 13f) ----------
A1 = "def _confidence(fc, tr, n_munis, frozen, cycle, scope, X):"
N1 = '''def _load_d1_map():
    """AUD-FICHAS-001: sensibilidad D1 por cultivo desde sensitivity_D1_exclude_quiebre.csv."""
    p = Path(CFG.output_dir) / "scenarios" / "sensitivity_D1_exclude_quiebre.csv"
    if not p.exists():
        return {}
    t = pd.read_csv(p, encoding="utf-8-sig")
    if "afectado" in t.columns:
        t = t[t["afectado"].astype(bool)]
    out = {}
    for _, r in t.iterrows():
        out[r["cultivo"]] = {"pct_excluidas": float(r.get("pct_excluidas", 0.0) or 0.0),
                             "delta": float(r.get("delta_2026_pct", 0.0) or 0.0),
                             "n_excl": int(r.get("series_excluidas", 0) or 0),
                             "n_tot": int(r.get("series_total", 0) or 0),
                             "base": float(r.get("baseline_2026_t", np.nan)),
                             "clean": float(r.get("clean_2026_t", np.nan))}
    return out


def _d1_nota(crop, X):
    d = _load_d1_map().get(crop)
    if not d or abs(d["delta"]) <= 10.0:
        return ""
    return (f" <b>Sensibilidad D1</b>: {d['n_excl']} de {d['n_tot']} series de este cultivo "
            f"presentan quiebre de definicion 2021→2022 no validado con la fuente; al excluirlas, "
            f"la proyeccion {X['ORIGIN'] + 1} cae {abs(d['delta']):.0f} % "
            f"(de {es_t(d['base'])} a {es_t(d['clean'])} t). Lea el central como cota superior.")


def _conf_con_d1(fc, tr, n_munis, frozen, cycle, scope, X, crop):
    """Wrapper AUD-FICHAS-001: semaforo original + penalizacion D1 (+2 si >5% de series flaggeadas)."""
    lab, items = _confidence(fc, tr, n_munis, frozen, cycle, scope, X)
    d = _load_d1_map().get(crop)
    if d is not None and d.get("pct_excluidas", 0.0) > 5.0 and lab != "SIN PRONÓSTICO":
        items = list(items) + [(f"Sensibilidad D1: {d['n_excl']} de {d['n_tot']} series con quiebre "
                                f"de definicion 2021→2022 no validado; sin ellas la proyeccion cae "
                                f"{abs(d['delta']):.0f}%. Lea el central como cota superior.", 2)]
        score = sum(s for _, s in items)
        lab = "ALTA" if score == 0 else ("MEDIA" if score <= 2 else "BAJA")
    return lab, items


def _confidence(fc, tr, n_munis, frozen, cycle, scope, X):'''

A2 = "            conf = _confidence(fc, tr, n_munis, frozen, cycle, scope, X)"
N2 = "            conf = _conf_con_d1(fc, tr, n_munis, frozen, cycle, scope, X, crop)"

A3 = "    nh, ny = 52, 30 + 8 + 52"
N3 = "    _d1_txt = _d1_nota(crop, X)\n    nh, ny = 52 + (16 if _d1_txt else 0), 30 + 8 + 52"

A4 = '            + "«Estable» = variación entre −5 % y +5 %. Rendimiento = producción ÷ área cosechada.")'
N4 = ('            + "«Estable» = variación entre −5 % y +5 %. Rendimiento = producción ÷ área cosechada."\n'
      '            + _d1_txt)')

HUNKS = [(A_EXP, N_EXP, "exports app (13b)"), (A1, N1, "loader D1 (13f)"),
         (A2, N2, "llamada conf (13f)"), (A3, N3, "caja nota (13f)"),
         (A4, N4, "cierre nota (13f)")]


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-V5-003", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def main():
    cands = sorted(RAIZ.glob("explore_base_agricola_v5_2_fichas*(1).ipynb"))
    if not cands:
        return fail(f"no se hallo el notebook de trabajo '(1)'. Candidatos en raiz: "
                    f"{[p.name for p in RAIZ.glob('explore_base_agricola_v5_2_fichas*.ipynb')]}")
    nb_path = cands[0]
    print(f"Objetivo: {nb_path.name}")

    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    celdas = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    fuentes = ["".join(c["source"]) for c in celdas]
    todo = "\n".join(fuentes)

    if "meta_series.csv" in todo and "_load_d1_map" in todo:
        print("[SKIP] el notebook (1) ya tiene ambos parches")
        return 0

    for ancla, _, nombre in HUNKS:
        if todo.count(ancla) != 1:
            return fail(f"ancla {nombre}: {todo.count(ancla)} coincidencias (esperaba 1)")

    nuevas, parcheadas = [], 0
    for src in fuentes:
        s = src
        for ancla, nuevo, _ in HUNKS:
            if ancla in s:
                s = s.replace(ancla, nuevo, 1)
        if s != src:
            parcheadas += 1
            try:
                compile(s, "<celda>", "exec")
            except SyntaxError as e:
                return fail(f"sintaxis invalida tras parche: {e}")
        nuevas.append(s)
    if parcheadas != 2:
        return fail(f"los hunks cayeron en {parcheadas} celdas (esperaba 2: 13b y 13f)")

    for c, s in zip(celdas, nuevas):
        c["source"] = s.splitlines(keepends=True)

    bak = nb_path.with_suffix(".ipynb.bak")
    shutil.copy2(nb_path, bak)
    nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    json.loads(nb_path.read_text(encoding="utf-8"))
    print(f"[OK] {nb_path.name} parcheado (5 hunks en 2 celdas) | backup: {bak.name}")

    todo_n = "\n".join(nuevas)
    for token in ("meta_series.csv", "panel_anual.csv", "def _load_d1_map",
                  "def _conf_con_d1", "+ _d1_txt)"):
        if token not in todo_n:
            shutil.copy2(bak, nb_path)
            return fail(f"autotest: falta {token}")
    print("[OK] autotest: exports y semaforo D1 presentes")

    audit("AUD-V5-003", "OK", f"patch completo en {nb_path.name}")
    print("[OK] AUD-V5-003 aplicado. Siguiente: Kernel > Restart & Run All en ese notebook")
    return 0


if __name__ == "__main__":
    sys.exit(main())