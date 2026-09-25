"""AUD-UI-026 v2: boton de fichas v5 como entregable oficial en Predictivo.
v2: cadena de anclas de respaldo + diagnostico incorporado (si ninguna ancla
existe, imprime la region real de exportacion con repr() para calibrar).
El bloque se inserta dentro de main() y no depende del contexto de la pagina:
lee el PDF de fichas desde entregables/ (commiteado) o outputs_v5/ (local).
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
UI = RAIZ / "ui" / "pages" / "4_Predictivo.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

BLOQUE = '''
    # AUD-UI-026: fichas v5 como entregable oficial (pipeline auditado)
    from pathlib import Path as _Path
    _fichas_v5 = None
    for _p in ("entregables/fichas_valle_del_cauca_v5.pdf",
               "outputs_v5/fichas_cultivos/fichas_valle_del_cauca.pdf"):
        if _Path(_p).exists():
            _fichas_v5 = _Path(_p)
            break
    if _fichas_v5:
        st.download_button(
            "📊 Descargar FICHAS OFICIALES v5 (pipeline auditado, 47/47 PASS)",
            data=_fichas_v5.read_bytes(),
            file_name="fichas_valle_del_cauca_v5.pdf",
            mime="application/pdf",
        )
        st.caption(
            "**Entregable oficial:** las fichas v5 salen del pipeline auditado "
            "(47/47 pruebas PASS; ningun modelo supera a naive con IC95%; central "
            "forzado a pool_A_full como decision rotulada; bandas calibradas y "
            "semaforo con sensibilidad D1). Esta pagina conserva el motor historico "
            "(naive + IC sqrt(t)) como referencia operativa."
        )
    else:
        st.info(
            "📊 **Fichas oficiales v5 no disponibles en este entorno.** Generelas "
            "con el notebook explore_base_agricola_v5_2_fichas.ipynb (Kernel > "
            "Restart & Run All). Incluyen portada, indice, 78 fichas con bandas "
            "80/95%, escenarios y semaforo de confianza con nota D1."
        )
'''

ANCLAS = [
    ("cabecera EXPORTACION + separador",
     '    # ---------- EXPORTACION ----------\n    st.markdown("---")'),
    ("cabecera EXPORTACION",
     "    # ---------- EXPORTACION ----------"),
    ("columnas de botones",
     "    d1, d2 = st.columns(2)"),
]


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-UI-026", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def diagnostico(t):
    lines = t.splitlines()
    i = next((k for k, l in enumerate(lines)
              if "EXPORTACION" in l or "download_button" in l), None)
    if i is None:
        print("[DIAG] no se hallo ni 'EXPORTACION' ni 'download_button' en el archivo")
        return
    print(f"[DIAG] region real de exportacion (lineas {i}..{min(len(lines), i+26)}):")
    for k in range(max(0, i - 2), min(len(lines), i + 26)):
        print(f"{k:4d}| {lines[k]!r}")


def main():
    if not UI.exists():
        return fail(f"no existe {UI.name}")
    try:
        t = UI.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer {UI.name}: {e}")

    if "fichas_valle_del_cauca" in t:
        print("[SKIP] AUD-UI-026 ya aplicado")
        return 0

    elegida = None
    for nombre, ancla in ANCLAS:
        n = t.count(ancla)
        if n == 1:
            elegida = (nombre, ancla)
            break
        print(f"[..] ancla {nombre}: {n} coincidencias (se requiere 1)")
    if elegida is None:
        diagnostico(t)
        return fail("ninguna ancla de respaldo existe; ver [DIAG] arriba")

    nombre, ancla = elegida
    t_n = t.replace(ancla, ancla + BLOQUE, 1)

    bak = UI.with_suffix(".py.bak")
    try:
        shutil.copy2(UI, bak)
        UI.write_text(t_n, encoding="utf-8")
        print(f"[OK] {UI.name} parcheado (ancla: {nombre}) | backup: {bak.name}")
    except Exception as e:
        return fail(f"fallo de escritura: {e}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(UI)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, UI)
        audit("AUD-UI-026", "ROLLBACK", r.stderr[:200])
        return fail(f"sintaxis invalida, revirtiendo: {r.stderr[:200]}")

    for token in ("fichas_valle_del_cauca", "AUD-UI-026", "entregables/"):
        if token not in t_n:
            shutil.copy2(bak, UI)
            return fail(f"autotest: falta {token} tras el parche")
    print("[OK] autotest: boton v5, caption y rutas presentes")

    audit("AUD-UI-026", "OK", f"bloque fichas v5 insertado (ancla: {nombre})")
    print("[OK] AUD-UI-026 v2 aplicado y validado")
    return 0


if __name__ == "__main__":
    sys.exit(main())