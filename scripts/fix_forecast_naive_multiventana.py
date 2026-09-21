"""AUD-ML-007: forecast.py gana candidato naive + seleccion multi-ventana.
H1: modelo_naive (fitted=lag1 -> residuos de un paso para IC honesto).
H2: ruta de proyeccion constante en _proyectar.
H3: naive entra a los candidatos de backtest.
H4: elegir_mejor elige por MEDIANA de MAPE entre ventanas (1,2) de holdout
    interno (reduce la suerte de colocacion del holdout sobre el choque).
Fail-safe: anclas unicas, backup, py_compile, rollback, autotests, auditoria.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FC = RAIZ / "core" / "analytics" / "forecast.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

ANCLA_HOLT = '''    return {"nombre": "Suavizado exponencial (Holt)", "alpha": alpha, "beta": beta,
            "L": L, "T": T, "fitted": fitted}
'''

NUEVO_NAIVE = '''    return {"nombre": "Suavizado exponencial (Holt)", "alpha": alpha, "beta": beta,
            "L": L, "T": T, "fitted": fitted}


def modelo_naive(t, s):
    """Naive: repite el ultimo valor. fitted = lag 1 (residuos = diferencias de un paso)."""
    if len(s) < 2:
        return None
    fitted = np.empty_like(s, dtype=float)
    fitted[0] = np.nan
    fitted[1:] = s[:-1]
    return {"nombre": "Naive (ultimo valor)", "fitted": fitted, "ultimo": float(s[-1])}
'''

ANCLA_PROY = '''    if nombre == "MLP (3-8-4-1)":
        base = modelo.get("serie_train", serie_original)
        return proyectar_mlp(modelo, n_steps, base)
'''

NUEVO_PROY = '''    if nombre == "MLP (3-8-4-1)":
        base = modelo.get("serie_train", serie_original)
        return proyectar_mlp(modelo, n_steps, base)
    if nombre == "Naive (ultimo valor)":
        return np.full(n_steps, modelo["ultimo"])
'''

ANCLA_CAND = '''        modelo_holt(t_train, s_train, 0.5, 0.2),
        modelo_mlp(pd.Series(s_train)),
    ]'''

NUEVO_CAND = '''        modelo_holt(t_train, s_train, 0.5, 0.2),
        modelo_naive(t_train, s_train),
        modelo_mlp(pd.Series(s_train)),
    ]'''

VIEJO_ELEGIR = '''def elegir_mejor(serie: pd.Series, n_out: int = 2) -> dict:
    """Elige el modelo con menor MAPE y lo reentrena con la serie completa."""
    bt = backtest(serie, n_out)
    if not bt:
        return {"modelo": None, "mape": np.inf, "residuos": np.array([0.0]),
                "ganador": "Datos insuficientes", "ranking": []}
    mejor = min(bt, key=lambda x: x["mape"])
    t_full, s_full = _preparar(serie)
    nombre = mejor["modelo"]["nombre"]
    if nombre == "Tendencia lineal":
        modelo_full = modelo_lineal(t_full, s_full)
    elif nombre.startswith("Promedio movil"):
        modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])
    elif nombre == "MLP (3-8-4-1)":
        modelo_full = modelo_mlp(serie)
    else:
        modelo_full = modelo_holt(t_full, s_full,
                                  mejor["modelo"]["alpha"],
                                  mejor["modelo"]["beta"])
    return {
        "modelo": modelo_full,
        "mape": mejor["mape"],
        "residuos": mejor["residuos"],
        "ganador": nombre,
        "ranking": sorted(bt, key=lambda x: x["mape"]),
        "n_out_efectivo": mejor.get("holdout", n_out),
    }'''

NUEVO_ELEGIR = '''def elegir_mejor(serie: pd.Series, n_out: int = 2,
                 ventanas: tuple = (1, 2)) -> dict:
    """AUD-ML-007: elige por MEDIANA de MAPE entre varias ventanas de holdout
    interno (reduce la suerte de colocacion del holdout sobre el choque) y
    reentrena el ganador con la serie completa."""
    bt_por_ventana = {w: backtest(serie, w) for w in ventanas}
    bt_plana = [r for w in ventanas for r in bt_por_ventana[w]]
    if not bt_plana:
        return {"modelo": None, "mape": np.inf, "residuos": np.array([0.0]),
                "ganador": "Datos insuficientes", "ranking": []}

    agg = {}
    for w in ventanas:
        for r in bt_por_ventana[w]:
            agg.setdefault(r["modelo"]["nombre"], {})[w] = r

    def mediana(nombre):
        return float(np.median([r["mape"] for r in agg[nombre].values()]))

    mejor_nombre = min(agg, key=mediana)
    por_w = agg[mejor_nombre]
    w_rep = n_out if n_out in por_w else max(por_w)
    mejor = por_w[w_rep]

    ranking = []
    for nombre in sorted(agg, key=mediana):
        pw = agg[nombre]
        w2 = n_out if n_out in pw else max(pw)
        rep = dict(pw[w2])
        rep["mape"] = mediana(nombre)
        rep["mapes_por_ventana"] = {w: r["mape"] for w, r in pw.items()}
        ranking.append(rep)

    t_full, s_full = _preparar(serie)
    nombre = mejor_nombre
    if nombre == "Tendencia lineal":
        modelo_full = modelo_lineal(t_full, s_full)
    elif nombre.startswith("Promedio movil"):
        modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])
    elif nombre == "MLP (3-8-4-1)":
        modelo_full = modelo_mlp(serie)
    elif nombre == "Naive (ultimo valor)":
        modelo_full = modelo_naive(t_full, s_full)
    else:
        modelo_full = modelo_holt(t_full, s_full,
                                  mejor["modelo"]["alpha"],
                                  mejor["modelo"]["beta"])
    return {
        "modelo": modelo_full,
        "mape": mediana(mejor_nombre),
        "residuos": mejor["residuos"],
        "ganador": nombre,
        "ranking": ranking,
        "n_out_efectivo": mejor.get("holdout", n_out),
    }'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-ML-007", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def rollback_or_fail(motivo, bak):
    try:
        shutil.copy2(bak, FC)
    except Exception as e:
        audit("AUD-ML-007", "ROLLBACK_FALLIDO", f"{motivo} | rollback: {e}")
        print(f"[ERROR] {motivo} Y el rollback fallo: {e}")
        return 1
    audit("AUD-ML-007", "ROLLBACK", motivo)
    print(f"[ERROR] {motivo}; revirtiendo a {bak.name}")
    return 1


def main():
    try:
        texto = FC.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer forecast.py: {e}")

    if "def modelo_naive" in texto and "ventanas: tuple" in texto:
        print("[SKIP] AUD-ML-007 ya aplicado")
        return 0

    for ancla, nombre in ((ANCLA_HOLT, "fin de modelo_holt"), (ANCLA_PROY, "_proyectar MLP"),
                          (ANCLA_CAND, "candidatos backtest"), (VIEJO_ELEGIR, "elegir_mejor")):
        if texto.count(ancla) != 1:
            return fail(f"ancla {nombre}: {texto.count(ancla)} coincidencias (esperaba 1)")

    texto_nuevo = (texto
                   .replace(ANCLA_HOLT, NUEVO_NAIVE, 1)
                   .replace(ANCLA_PROY, NUEVO_PROY, 1)
                   .replace(ANCLA_CAND, NUEVO_CAND, 1)
                   .replace(VIEJO_ELEGIR, NUEVO_ELEGIR, 1))

    try:
        bak = FC.with_suffix(".py.bak")
        shutil.copy2(FC, bak)
        FC.write_text(texto_nuevo, encoding="utf-8")
    except Exception as e:
        return fail(f"fallo de escritura: {e}")
    print(f"[OK] forecast.py parcheado (4 hunks) | backup: {bak.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(FC)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return rollback_or_fail(f"sintaxis invalida: {r.stderr[:200]}", bak)

    # ---------- Autotests con modulo fresco ----------
    sys.path.insert(0, str(RAIZ))
    for name in list(sys.modules):
        if name == "core" or name.startswith("core."):
            del sys.modules[name]
    import numpy as np
    import pandas as pd
    from core.analytics import forecast

    s7 = pd.Series([100.0, 110.0, 121.0, 133.0, 140.0, 150.0, 160.0])

    # 1) naive presente en backtest con fitted lag-1
    bt = forecast.backtest(s7, 2)
    nombres = [r["modelo"]["nombre"] for r in bt]
    if "Naive (ultimo valor)" not in nombres:
        return rollback_or_fail("autotest: naive no entro a backtest", bak)
    nv = next(r for r in bt if r["modelo"]["nombre"] == "Naive (ultimo valor)")
    f = nv["modelo"]["fitted"]
    if not (np.isnan(f[0]) and np.allclose(f[1:], s7.values[:-1])):
        return rollback_or_fail("autotest: fitted de naive no es lag-1", bak)
    print("[OK] autotest 1: naive en backtest con fitted lag-1")

    # 2) proyeccion naive = constante ultimo valor
    pr = forecast._proyectar(nv["modelo"], 3, s7)
    if not np.allclose(pr, s7.values[-1]):
        return rollback_or_fail("autotest: _proyectar naive no es constante", bak)
    print("[OK] autotest 2: proyeccion naive constante")

    # 3) multi-ventana: ranking con mapes_por_ventana {1, 2}
    res = forecast.elegir_mejor(s7)
    if res["modelo"] is None:
        return rollback_or_fail("autotest: elegir_mejor sin modelo", bak)
    if not all(set(r["mapes_por_ventana"]) == {1, 2} for r in res["ranking"]):
        return rollback_or_fail("autotest: ranking sin mapes por ventana 1 y 2", bak)
    print(f"[OK] autotest 3: multi-ventana activo (ganador '{res['ganador']}', "
          f"MAPE mediano {res['mape']:.1f}%)")

    # 4) serie plana: naive con MAPE 0 en ranking
    plana = pd.Series([100.0] * 7)
    rp = forecast.elegir_mejor(plana)
    mapes = {r["modelo"]["nombre"]: r["mape"] for r in rp["ranking"]}
    if mapes.get("Naive (ultimo valor)") != 0.0:
        return rollback_or_fail("autotest: naive no da MAPE 0 en serie plana", bak)
    print("[OK] autotest 4: naive perfecto en serie plana")

    # 5) end-to-end con IC
    ic = forecast.proyectar_con_ic(s7, n_steps=3)
    if not np.all(np.isfinite(ic["prediccion"])):
        return rollback_or_fail("autotest: proyectar_con_ic no finito", bak)
    print("[OK] autotest 5: proyectar_con_ic end-to-end")

    audit("AUD-ML-007", "OK", "naive candidato + seleccion multi-ventana")
    print("[OK] AUD-ML-007 aplicado, compilado y autotesteado")
    print("Siguiente: Gate 3 -> re-subir forecast.py parcheado a Colab y re-correr celda 6.5")
    return 0


if __name__ == "__main__":
    sys.exit(main())