"""AUD-UI-020: elimina st.title("EVA Valle") del sidebar.
Queda solo el logo centrado + tarjeta de usuario + boton + caption.
No toca el titulo del login ni del Home (son bloques distintos).
Fail-safe: pre-chequeos, backup, py_compile, rollback, auditoria JSONL.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

VIEJA = '    st.title("EVA Valle")\n'


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    texto = APP.read_text(encoding="utf-8")

    # Idempotencia
    if VIEJA not in texto:
        print("[SKIP] el sidebar ya no tiene st.title('EVA Valle')")
        return 0

    n = texto.count(VIEJA)
    if n != 1:
        print(f"[ERROR] linea st.title('EVA Valle') encontrada {n} veces (esperaba 1)")
        return 1

    texto_nuevo = texto.replace(VIEJA, "", 1)

    # Verificaciones en memoria
    if 'st.title("EVA Valle")' in texto_nuevo:
        print("[ERROR] el titulo sigue presente tras el reemplazo")
        return 1
    for token in ("with st.sidebar:", "st.image(", "eva-sidebar-user",
                  "Cerrar sesion", "UPRA - Unidad de Planificacion Rural y Agropecuaria"):
        if token not in texto_nuevo:
            print(f"[ERROR] se perdio '{token}' del sidebar")
            return 1

    bak = APP.with_suffix(".py.bak")
    shutil.copy2(APP, bak)
    APP.write_text(texto_nuevo, encoding="utf-8")
    print(f"[OK] titulo del sidebar eliminado | backup: {bak.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(APP)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, APP)
        audit("AUD-UI-020", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-020", "OK", "sidebar sin titulo: solo logo centrado")
    print("[OK] AUD-UI-020 aplicado y compilado")
    return 0


if __name__ == "__main__":
    sys.exit(main())