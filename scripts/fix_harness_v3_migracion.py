"""AUD-HAR-001 v5: migracion de eva_baseline_v3.py a harness de registro.
H1: Config.n_final 1->2 via regex anclado a inicio de linea.
H2: flag serie_con_huecos en panel semestral; seasonal-naive se enmascara (NaN)
    en series con huecos (shift(2) no es el mismo semestre).
H3: ejecutar() exporta cobertura_quiebre.csv y casos_mezclados.csv.
Autotest 2 corregido: usa .iloc[0] para extraer valor escalar del flag
(el panel semestral tiene multiples filas por serie, una por periodo).
"""
import inspect
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HAR = RAIZ / "eva_baseline_v3.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

# ---------- H1: regex de linea completa, inicio anclado ----------
PAT_NFINAL = re.compile(
    r"^    n_final: int = 1 +# folds finales reservados \(recomendado probar 2\)$",
    re.M)
NUEVO_NFINAL = ("    n_final: int = 2          "
                "# folds finales reservados (alineado con Gates: ultimos 2 anos)")

# ---------- H2 ----------
ANCLA_PANELES = '    ps = ps.sort_values(K + ["periodo"]).reset_index(drop=True)'
NUEVO_PANELES = '''    ps = ps.sort_values(K + ["periodo"]).reset_index(drop=True)
    # AUD-HAR-001: huecos semestrales por serie. Si faltan semestres, shift(2)
    # NO es el mismo semestre del ano anterior: se marca para enmascarar el
    # candidato estacional en esas series.
    span = (ps.groupby(K)["ano"].transform("max")
            - ps.groupby(K)["ano"].transform("min") + 1) * 2
    obs = ps.groupby(K)["periodo"].transform("nunique")
    ps["serie_con_huecos"] = (span - obs) > 0'''

ANCLA_RAMA = '    folds = generar_folds(panel, col_tiempo, lag_estacional=lag_estacional)'
NUEVO_RAMA = '''    folds = generar_folds(panel, col_tiempo, lag_estacional=lag_estacional)
    if lag_estacional and "serie_con_huecos" in panel.columns:
        flag = panel[K + ["serie_con_huecos"]].drop_duplicates()
        folds = folds.merge(flag, on=K, how="left")
        folds.loc[folds["serie_con_huecos"].fillna(False),
                  "pred_seasonal_naive_1a"] = np.nan
        folds = folds.drop(columns=["serie_con_huecos"])'''

# ---------- H3 ----------
ANCLA_EXPORT = '    quiebres.to_csv("flags_quiebre.csv", index=False, encoding="utf-8-sig")'
NUEVO_EXPORT = '''    quiebres.to_csv("flags_quiebre.csv", index=False, encoding="utf-8-sig")
    res["cobertura"].to_csv("cobertura_quiebre.csv", index=False, encoding="utf-8-sig")
    res["casos_mezclados"].to_csv("casos_mezclados.csv", index=False, encoding="utf-8-sig")'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-HAR-001", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def main():
    if not HAR.exists():
        return fail(f"no existe {HAR.name} en la raiz del repo")
    try:
        t = HAR.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer {HAR.name}: {e}")

    if "serie_con_huecos" in t and "n_final: int = 2" in t:
        print("[SKIP] AUD-HAR-001 ya aplicado")
        return 0

    n_nf = len(PAT_NFINAL.findall(t))
    if n_nf != 1:
        return fail(f"ancla n_final (regex linea): {n_nf} coincidencias (esperaba 1)")
    for ancla, nombre in ((ANCLA_PANELES, "construir_paneles"),
                          (ANCLA_RAMA, "correr_rama"),
                          (ANCLA_EXPORT, "export ejecutar")):
        if t.count(ancla) != 1:
            return fail(f"ancla {nombre}: {t.count(ancla)} coincidencias (esperaba 1)")

    t_n = (PAT_NFINAL.sub(NUEVO_NFINAL, t, count=1)
           .replace(ANCLA_PANELES, NUEVO_PANELES, 1)
           .replace(ANCLA_RAMA, NUEVO_RAMA, 1)
           .replace(ANCLA_EXPORT, NUEVO_EXPORT, 1))

    bak = HAR.with_suffix(".py.bak")
    try:
        shutil.copy2(HAR, bak)
        HAR.write_text(t_n, encoding="utf-8")
        print(f"[OK] {HAR.name} parcheado (3 hunks) | backup: {bak.name}")
    except Exception as e:
        return fail(f"fallo de escritura: {e}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(HAR)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, HAR)
        audit("AUD-HAR-001", "ROLLBACK", r.stderr[:200])
        return fail(f"sintaxis invalida, revirtiendo: {r.stderr[:200]}")

    # ---------- Autotests con modulo fresco ----------
    sys.path.insert(0, str(RAIZ))
    for name in list(sys.modules):
        if name.startswith("eva_baseline"):
            del sys.modules[name]
    import numpy as np
    import pandas as pd
    import eva_baseline_v3 as ev

    # 1) Config=2 y firmas de funcion con default intacto (via parametros, no strings)
    if ev.Config().n_final != 2:
        shutil.copy2(bak, HAR)
        return fail("autotest: Config.n_final no quedo en 2")
    d_rama = inspect.signature(ev.correr_rama).parameters["n_final"].default
    d_div = inspect.signature(ev.dividir_seleccion_final).parameters["n_final"].default
    if d_rama != 1 or d_div != 1:
        shutil.copy2(bak, HAR)
        return fail(f"autotest: defaults de firmas alterados (rama={d_rama}, div={d_div})")
    print("[OK] autotest 1: Config.n_final=2; defaults de correr_rama/dividir intactos")

    # 2) Huecos detectados en panel semestral sintetico
    filas = []
    for muni, cult, periodos in [
        ("Sevilla", "Lulo", ["2019A", "2019B", "2020A", "2020B"]),
        ("Sevilla", "Maiz", ["2019A", "2020B", "2021A", "2021B"]),
    ]:
        for per in periodos:
            filas.append({"municipio": muni, "cultivo": cult,
                          "ano": int(per[:4]), "periodo": per,
                          "tipo_periodo": "semestral", "ciclo": "Transitorio",
                          "produccion": 100.0, "area": 10.0})
    pa, ps, meta = ev.construir_paneles(pd.DataFrame(filas))
    huecos = ps.set_index(ev.K)["serie_con_huecos"]
    
    # CORRECCION: usar .iloc[0] para extraer valor escalar (el panel tiene multiples
    # filas por serie, una por periodo; el flag es el mismo para todas)
    maiz_huecos = huecos.loc[("Sevilla", "Maiz")].iloc[0]
    lulo_huecos = huecos.loc[("Sevilla", "Lulo")].iloc[0]
    
    if not bool(maiz_huecos):
        shutil.copy2(bak, HAR)
        return fail("autotest: serie con huecos no detectada")
    if bool(lulo_huecos):
        shutil.copy2(bak, HAR)
        return fail("autotest: serie completa marcada con huecos")
    print("[OK] autotest 2: huecos semestrales detectados correctamente")

    # 3) Candidato estacional enmascarado solo donde hay huecos
    out = ev.correr_rama(ps, "periodo", meta, lag_estacional=2,
                         n_final=1, con_regresion=False)
    f = out["folds"]
    if not f[f["cultivo"] == "Maiz"]["pred_seasonal_naive_1a"].isna().all():
        shutil.copy2(bak, HAR)
        return fail("autotest: seasonal-naive no enmascarado en serie con huecos")
    if f[f["cultivo"] == "Lulo"]["pred_seasonal_naive_1a"].isna().all():
        shutil.copy2(bak, HAR)
        return fail("autotest: seasonal-naive perdido en serie completa")
    print("[OK] autotest 3: seasonal-naive enmascarado solo en series con huecos")

    # 4) Exports presentes
    for token in ("cobertura_quiebre.csv", "casos_mezclados.csv"):
        if token not in t_n:
            shutil.copy2(bak, HAR)
            return fail(f"autotest: falta export de {token}")
    print("[OK] autotest 4: exports de cobertura y casos mezclados presentes")

    audit("AUD-HAR-001", "OK", "v5: autotest 2 con .iloc[0] para valor escalar")
    print("[OK] AUD-HAR-001 v5 aplicado, compilado y autotesteado")
    print("Siguiente: commit + corrida real con EVA_XLSX + chequeo de regresion")
    return 0


if __name__ == "__main__":
    sys.exit(main())