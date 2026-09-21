"""AUD-UI-019: centra el logo del sidebar centrando la <img> directamente
(margin auto), porque el contenedor stImage es shrink-to-fit y justify-content
no tiene espacio extra que repartir. Solo CSS.
"""
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSS = RAIZ / "ui" / "assets" / "css" / "style.css"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

VIEJO = '''section[data-testid="stSidebar"] [data-testid="stImage"] {
    display: flex;
    justify-content: center;
    margin-bottom: .3rem;
}'''

NUEVO = '''section[data-testid="stSidebar"] [data-testid="stImage"] {
    display: flex;
    justify-content: center;
    width: 100%;
    margin-bottom: .3rem;
}
section[data-testid="stSidebar"] [data-testid="stImage"] img {
    display: block;
    margin: 0 auto;
}'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    css = CSS.read_text(encoding="utf-8")
    if "stImage\"] img" in css:
        print("[SKIP] centrado robusto ya presente")
        return 0
    if VIEJO not in css:
        print("[ERROR] regla original de centrado no encontrada tal cual")
        return 1
    css_nuevo = css.replace(VIEJO, NUEVO, 1)
    bak = CSS.with_suffix(".css.bak")
    shutil.copy2(CSS, bak)
    CSS.write_text(css_nuevo, encoding="utf-8")
    audit("AUD-UI-019", "OK", "logo sidebar centrado via margin auto en img")
    print(f"[OK] AUD-UI-019 aplicado | backup: {bak.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())