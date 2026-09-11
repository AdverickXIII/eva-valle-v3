"""AUD-UI-017: logo del sidebar centrado via CSS y agrandado (width 84 -> 110).
Fail-safe: pre-chequeos, backups, py_compile, rollback, auditoria JSONL.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app.py"
CSS = RAIZ / "ui" / "assets" / "css" / "style.css"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

NUEVO_CSS = '''/* ---------- Logo sidebar centrado (Paso 5) ---------- */
section[data-testid="stSidebar"] [data-testid="stImage"] {
    display: flex;
    justify-content: center;
    margin-bottom: .3rem;
}
'''

VIEJA = 'st.image(str(Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"), width=84)'
NUEVA = 'st.image(str(Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"), width=110)'


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    texto = APP.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    # ---------- app.py: width 84 -> 110 ----------
    if NUEVA in texto:
        print("[INFO] app.py ya tiene width=110")
        texto_nuevo = None
    else:
        n = texto.count(VIEJA)
        if n != 1:
            print(f"[ERROR] linea st.image(...width=84) encontrada {n} veces (esperaba 1)")
            return 1
        texto_nuevo = texto.replace(VIEJA, NUEVA, 1)

    # ---------- style.css: regla de centrado ----------
    if "Logo sidebar centrado" in css:
        print("[INFO] style.css ya tiene la regla de centrado")
        css_nuevo = None
    else:
        css_nuevo = css.rstrip() + "\n\n" + NUEVO_CSS

    if texto_nuevo is None and css_nuevo is None:
        print("[SKIP] AUD-UI-017 ya aplicado por completo")
        return 0

    # Verificaciones en memoria
    if texto_nuevo is not None and NUEVA not in texto_nuevo:
        print("[ERROR] width=110 no quedo en app.py")
        return 1
    if css_nuevo is not None and 'section[data-testid="stSidebar"] [data-testid="stImage"]' not in css_nuevo:
        print("[ERROR] selector de centrado no quedo en style.css")
        return 1

    # Escritura con backups
    if texto_nuevo is not None:
        bak = APP.with_suffix(".py.bak")
        shutil.copy2(APP, bak)
        APP.write_text(texto_nuevo, encoding="utf-8")
        print(f"[OK] app.py: width 84 -> 110 | backup: {bak.name}")
    if css_nuevo is not None:
        bakc = CSS.with_suffix(".css.bak")
        shutil.copy2(CSS, bakc)
        CSS.write_text(css_nuevo, encoding="utf-8")
        print(f"[OK] style.css: regla de centrado agregada | backup: {bakc.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(APP)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        if texto_nuevo is not None:
            shutil.copy2(APP.with_suffix(".py.bak"), APP)
        audit("AUD-UI-017", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-017", "OK", "logo sidebar centrado y agrandado")
    print("[OK] AUD-UI-017 aplicado y compilado")
    return 0


if __name__ == "__main__":
    sys.exit(main())