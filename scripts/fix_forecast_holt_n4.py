"""AUD-ML-004 v3: fix de 2 bugs + visibilidad de holdout en forecast.py.
Bug 1: Holt fitted de un paso adelante (fitted[0]=NaN, convencion unica).
Bug 2: holdout adaptativo n_out=1 para series de n=4 (docstring n>=4).
Diff 3: backtest expone 'holdout' y elegir_mejor retorna 'n_out_efectivo'.
v3: purga sys.modules antes del autotest, helper rollback_or_fail,
autotest numerico contra referencia manual independiente.
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

VIEJO_HOLT = '''    fitted = np.empty_like(s, dtype=float)
    fitted[0] = L
    for i in range(1, len(s)):
        L_new = alpha * s[i] + (1 - alpha) * (L + T)
        T_new = beta * (L_new - L) + (1 - beta) * T
        L, T = L_new, T_new
        fitted[i] = L + T if i < len(s) - 1 else L
'''

NUEVO_HOLT = '''    fitted = np.empty_like(s, dtype=float)
    fitted[0] = np.nan  # no hay pronostico de un paso para el primer punto
    for i in range(1, len(s)):
        fitted[i] = L + T  # pronostico de un paso: L_{i-1} + T_{i-1} (pre-update)
        L_new = alpha * s[i] + (1 - alpha) * (L + T)
        T_new = beta * (L_new - L) + (1 - beta) * T
        L, T = L_new, T_new
'''

VIEJO_GUARD = '''    t, s = _preparar(serie)
    if len(s) - n_out < 3:
        return []
    t_train, s_train = t[:-n_out], s[:-n_out]
'''

NUEVO_GUARD = '''    t, s = _preparar(serie)
    if len(s) < 4:
        return []
    if len(s) - n_out < 3:
        n_out = max(1, len(s) - 3)  # series de 4 anos: holdout de 1 (docstring n>=4)
    t_train, s_train = t[:-n_out], s[:-n_out]
'''

VIEJO_RES = '''        resultados.append({
            "modelo": m, "mape": mape,
            "residuos": residuos if len(residuos) > 0 else np.array([0.0]),
        })'''

NUEVO_RES = '''        resultados.append({
            "modelo": m, "mape": mape,
            "residuos": residuos if len(residuos) > 0 else np.array([0.0]),
            "holdout": n_out,
        })'''

VIEJO_RET = '''    return {
        "modelo": modelo_full,
        "mape": mejor["mape"],
        "residuos": mejor["residuos"],
        "ganador": nombre,
        "ranking": sorted(bt, key=lambda x: x["mape"]),
    }'''

NUEVO_RET = '''    return {
        "modelo": modelo_full,
        "mape": mejor["mape"],
        "residuos": mejor["residuos"],
        "ganador": nombre,
        "ranking": sorted(bt, key=lambda x: x["mape"]),
        "n_out_efectivo": mejor.get("holdout", n_out),
    }'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-ML-004", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def rollback_or_fail(motivo, bak):
    try:
        shutil.copy2(bak, FC)
    except Exception as e:
        audit("AUD-ML-004", "ROLLBACK_FALLIDO", f"{motivo} | rollback: {e}")
        print(f"[ERROR] {motivo} Y el rollback fallo: {e}")
        return 1
    audit("AUD-ML-004", "ROLLBACK", motivo)
    print(f"[ERROR] {motivo}; revirtiendo a {bak.name}")
    return 1


def main():
    try:
        texto = FC.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer forecast.py: {e}")

    if ("pronostico de un paso: L_{i-1}" in texto and "holdout de 1" in texto
            and '"holdout": n_out' in texto):
        print("[SKIP] AUD-ML-004 v3 ya aplicado")
        return 0

    for ancla, nombre in ((VIEJO_HOLT, "bloque Holt"), (VIEJO_GUARD, "guard backtest"),
                          (VIEJO_RES, "dict resultados"), (VIEJO_RET, "return elegir_mejor")):
        if texto.count(ancla) != 1:
            return fail(f"ancla de {nombre}: {texto.count(ancla)} coincidencias (esperaba 1)")

    texto_nuevo = (texto
                   .replace(VIEJO_HOLT, NUEVO_HOLT, 1)
                   .replace(VIEJO_GUARD, NUEVO_GUARD, 1)
                   .replace(VIEJO_RES, NUEVO_RES, 1)
                   .replace(VIEJO_RET, NUEVO_RET, 1))

    try:
        bak = FC.with_suffix(".py.bak")
        shutil.copy2(FC, bak)
        FC.write_text(texto_nuevo, encoding="utf-8")
    except Exception as e:
        return fail(f"fallo de escritura: {e}")
    print(f"[OK] forecast.py parcheado (4 diffs) | backup: {bak.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(FC)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return rollback_or_fail(f"sintaxis invalida: {r.stderr[:200]}", bak)

    # ---------- Autotest con modulo fresco ----------
    sys.path.insert(0, str(RAIZ))
    for name in list(sys.modules):           # evita validar codigo viejo en memoria
        if name == "core" or name.startswith("core."):
            del sys.modules[name]
    import numpy as np
    import pandas as pd
    from core.analytics import forecast

    # Bug 2 + Diff 3: n=4 proyecta y reporta holdout efectivo 1
    s4 = pd.Series([100.0, 110.0, 121.0, 133.0])
    r4 = forecast.elegir_mejor(s4)
    if r4["modelo"] is None:
        return rollback_or_fail("autotest: n=4 sigue en 'Datos insuficientes'", bak)
    if r4.get("n_out_efectivo") != 1:
        return rollback_or_fail(f"autotest: n_out_efectivo={r4.get('n_out_efectivo')} en n=4 (esperaba 1)", bak)
    print(f"[OK] autotest Bug 2: n=4 elige '{r4['ganador']}' con holdout 1")

    s7 = pd.Series([100.0, 110.0, 121.0, 133.0, 140.0, 150.0, 160.0])
    r7 = forecast.elegir_mejor(s7)
    if r7.get("n_out_efectivo") != 2:
        return rollback_or_fail(f"autotest: n_out_efectivo={r7.get('n_out_efectivo')} en n=7 (esperaba 2)", bak)

    # Bug 1: fitted de Holt vs referencia manual independiente
    sv = s7.values
    m = forecast.modelo_holt(np.arange(7), sv)
    f = m["fitted"]
    L, T = float(sv[0]), float(sv[1] - sv[0])
    ref = [np.nan]
    for i in range(1, len(sv)):
        ref.append(L + T)
        Ln = 0.3 * sv[i] + 0.7 * (L + T)
        Tn = 0.1 * (Ln - L) + 0.9 * T
        L, T = Ln, Tn
    ref = np.array(ref)
    if not (np.isnan(f[0]) and np.allclose(f[1:], ref[1:])):
        return rollback_or_fail("autotest: fitted de Holt no coincide con la referencia manual", bak)
    print("[OK] autotest Bug 1: Holt coincide con referencia de un paso adelante")

    audit("AUD-ML-004", "OK", "v3: Holt un paso + holdout adaptativo + holdout visible")
    print("[OK] AUD-ML-004 v3 aplicado, compilado y autotesteado")
    return 0


if __name__ == "__main__":
    sys.exit(main())