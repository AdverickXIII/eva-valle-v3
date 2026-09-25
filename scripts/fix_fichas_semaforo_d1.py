"""AUD-FICHAS-001 v2: sensibilidad D1 en semaforo y nota fija de las fichas.
Lectura/escritura JSON-aware del notebook (las anclas operan sobre codigo real,
no sobre JSON escapado). Anclas verificadas contra dump_fichas_anclas.py:
def _confidence (L468), llamada (L832), caja de notas (L661), cierre nota (L669).
H1: inserta _load_d1_map / _d1_nota / _conf_con_d1 antes de def _confidence.
H2: la llamada pasa por el wrapper (penaliza +2 si >5% de series flaggeadas).
H3: altura dinamica de la caja de notas si hay nota D1.
H4: la nota fija incluye la frase de sensibilidad D1 (|delta 2026| > 10%).
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOTEBOOK = RAIZ / "explore_base_agricola_v5_2_fichas.ipynb"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

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


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-FICHAS-001", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def main():
    if not NOTEBOOK.exists():
        return fail(f"no existe {NOTEBOOK.name} en la raiz del repo")
    try:
        nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    except Exception as e:
        return fail(f"JSON invalido al leer: {e}")

    celdas = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    fuentes = ["".join(c["source"]) for c in celdas]
    todo = "\n".join(fuentes)

    if "_conf_con_d1" in todo and "_load_d1_map" in todo:
        print("[SKIP] AUD-FICHAS-001 ya aplicado")
        return 0

    for ancla, nombre in ((A1, "def _confidence"), (A2, "llamada conf"),
                          (A3, "caja nota fija"), (A4, "cierre nota")):
        if todo.count(ancla) != 1:
            return fail(f"ancla {nombre}: {todo.count(ancla)} coincidencias en todo el notebook (esperaba 1)")

    parcheada = 0
    nuevas = []
    for src in fuentes:
        s = src
        if A1 in s:
            s = s.replace(A1, N1, 1)
        if A2 in s:
            s = s.replace(A2, N2, 1)
        if A3 in s:
            s = s.replace(A3, N3, 1)
        if A4 in s:
            s = s.replace(A4, N4, 1)
        if s != src:
            parcheada += 1
            try:
                compile(s, f"<celda_{parcheada}>", "exec")
            except SyntaxError as e:
                return fail(f"sintaxis invalida en celda parcheada #{parcheada}: {e}")
        nuevas.append(s)
    if parcheada != 1:
        return fail(f"las anclas cayeron en {parcheada} celdas (esperaba 1)")

    for c, s in zip(celdas, nuevas):
        c["source"] = s.splitlines(keepends=True)

    bak = NOTEBOOK.with_suffix(".ipynb.bak")
    try:
        shutil.copy2(NOTEBOOK, bak)
        NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[OK] {NOTEBOOK.name} parcheado (4 hunks en 1 celda) | backup: {bak.name}")
    except Exception as e:
        return fail(f"fallo de escritura: {e}")

    try:
        json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        print("[OK] JSON del notebook valido tras el parche")
    except Exception as e:
        shutil.copy2(bak, NOTEBOOK)
        audit("AUD-FICHAS-001", "ROLLBACK", f"JSON invalido: {e}")
        return fail(f"JSON invalido tras escribir, revirtiendo: {e}")

    todo_n = "\n".join(nuevas)
    for token in ("def _load_d1_map", "def _d1_nota", "def _conf_con_d1",
                  "_conf_con_d1(fc, tr, n_munis, frozen, cycle, scope, X, crop)",
                  "+ _d1_txt)"):
        if token not in todo_n:
            shutil.copy2(bak, NOTEBOOK)
            return fail(f"autotest: falta {token} tras el parche")
    print("[OK] autotest: wrapper, loader, nota y llamada presentes")

    audit("AUD-FICHAS-001", "OK", "v2: semaforo D1 + nota fija con sensibilidad")
    print("[OK] AUD-FICHAS-001 v2 aplicado y validado")
    print("Siguiente: Kernel > Restart & Run All (o re-ejecutar desde modulo 13f)")
    return 0


if __name__ == "__main__":
    sys.exit(main())