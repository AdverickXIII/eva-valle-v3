"""AUD-ML-005 v2: cache de proyectar_con_ic() por (anos, valores, horizonte, index_name).
Corrige 6 puntos de revision: valida imports, audita todo fallo, try/except en I/O,
preserva index.name real, inserta antes de def main (nivel modulo), indentacion dinamica.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PRED = RAIZ / "ui" / "pages" / "4_Predictivo.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

VIEJA_LLAMADA = 'res = proyectar_con_ic(serie, n_steps=horizonte)'

FUNCION_CACHEADA = '''
@st.cache_data(ttl=3600, show_spinner="Calculando proyección predictiva...")
def proyectar_cached(anos: tuple, valores: tuple, horizonte: int,
                     index_name: str) -> dict:
    """Wrapper cacheado de proyectar_con_ic (hash estable via tuples)."""
    serie_cache = pd.Series(valores, index=pd.Index(anos, name=index_name), dtype=float)
    return proyectar_con_ic(serie_cache, n_steps=horizonte)


'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-ML-005", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def main():
    try:
        texto = PRED.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer {PRED.name}: {e}")

    if "def proyectar_cached" in texto:
        print("[SKIP] AUD-ML-005 ya aplicado")
        return 0

    # (1) validar imports del destino
    for tok in ("import streamlit as st", "import pandas as pd"):
        if tok not in texto:
            return fail(f"falta import en destino: {tok}")

    if texto.count(VIEJA_LLAMADA) != 1:
        return fail(f"llamada encontrada {texto.count(VIEJA_LLAMADA)} veces (esperaba 1)")

    lineas = texto.splitlines(keepends=True)

    # (5) ancla de nivel modulo
    i_main = next((i for i, l in enumerate(lineas) if l.startswith("def main(")), None)
    if i_main is None:
        return fail("ancla 'def main(' no encontrada en columna 0")

    # (6) indentacion real de la llamada
    i_llam = next((i for i, l in enumerate(lineas) if VIEJA_LLAMADA in l), None)
    if i_llam is None:
        return fail("llamada no encontrada por linea")
    indent = len(lineas[i_llam]) - len(lineas[i_llam].lstrip())
    pad, pad2 = " " * indent, " " * (indent + 4)
    nueva_llamada = (
        f"{pad}res = proyectar_cached(\n"
        f"{pad2}tuple(int(x) for x in serie.index),\n"
        f"{pad2}tuple(float(x) for x in serie.values),\n"
        f"{pad2}int(horizonte),\n"
        f"{pad2}serie.index.name or 'ano',\n"
        f"{pad})"
    )

    # (5) insertar funcion antes de def main
    lineas[i_main:i_main] = FUNCION_CACHEADA.splitlines(keepends=True)
    texto_nuevo = "".join(lineas).replace(VIEJA_LLAMADA, nueva_llamada, 1)

    for tok in ("def proyectar_cached", "proyectar_cached(", "index_name",
                "serie.index.name", "def load_dataset", "run_safe(main)"):
        if tok not in texto_nuevo:
            return fail(f"falta '{tok}' tras el cambio")
    if VIEJA_LLAMADA in texto_nuevo:
        return fail("la llamada vieja sigue presente")

    try:
        bak = PRED.with_suffix(".py.bak")
        shutil.copy2(PRED, bak)
        PRED.write_text(texto_nuevo, encoding="utf-8")
    except Exception as e:
        return fail(f"fallo de escritura: {e}")
    print(f"[OK] 4_Predictivo.py cacheado | backup: {bak.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(PRED)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        try:
            shutil.copy2(bak, PRED)
        except Exception as e:
            audit("AUD-ML-005", "ROLLBACK_FALLIDO", str(e))
            return fail(f"sintaxis invalida Y rollback fallo: {e}")
        audit("AUD-ML-005", "ROLLBACK", r.stderr[:300])
        return fail(f"sintaxis invalida, revirtiendo: {r.stderr[:300]}")

    audit("AUD-ML-005", "OK", "cache de proyectar_con_ic (v2 con 6 fixes)")
    print("[OK] AUD-ML-005 v2 aplicado y compilado")
    return 0


if __name__ == "__main__":
    sys.exit(main())