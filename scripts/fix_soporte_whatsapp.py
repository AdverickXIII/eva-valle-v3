"""AUD-UI-013: agrega el enlace de WhatsApp a la linea .eva-login-support.
Insercion quirurgica dentro del st.markdown existente (sin reescribir el bloque).
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

VIEJO = '''" · <a href='tel:+573167197764'>+57 316 719 7764</a>"
        "</div>",'''

NUEVO = '''" · <a href='tel:+573167197764'>+57 316 719 7764</a>"
        " · <a href='https://wa.me/573167197764' target='_blank'>WhatsApp</a>"
        "</div>",'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    texto = APP.read_text(encoding="utf-8")

    # Idempotencia
    if "wa.me/573167197764" in texto:
        print("[SKIP] enlace de WhatsApp ya presente en app.py")
        return 0

    # Pre-chequeo: ancla exacta, una sola vez
    n = texto.count(VIEJO)
    if n != 1:
        print(f"[ERROR] ancla del bloque de soporte encontrada {n} veces (esperaba 1)")
        return 1

    texto_nuevo = texto.replace(VIEJO, NUEVO, 1)

    # Verificaciones en memoria
    if "wa.me/573167197764" not in texto_nuevo:
        print("[ERROR] el enlace de WhatsApp no quedo insertado")
        return 1
    if texto_nuevo.count("eva-login-support") != 1:
        print("[ERROR] hay mas de un bloque eva-login-support")
        return 1
    for token in ("with col_brand:", 'st.form("login_form")', "Contacta a soporte"):
        if token not in texto_nuevo:
            print(f"[ERROR] se perdio '{token}'")
            return 1

    bak = APP.with_suffix(".py.bak")
    shutil.copy2(APP, bak)
    APP.write_text(texto_nuevo, encoding="utf-8")
    print(f"[OK] enlace WhatsApp agregado | backup: {bak.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(APP)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, APP)
        audit("AUD-UI-013", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-013", "OK", "linea de soporte con tercer enlace WhatsApp")
    print("[OK] AUD-UI-013 aplicado y compilado")
    return 0


if __name__ == "__main__":
    sys.exit(main())