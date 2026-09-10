"""AUD-UI-005: agrega al final de style.css el bloque sidebar-jerarquia + contacto.
Fail-safe: idempotencia, backup, verificacion post-escritura, auditoria JSONL.
"""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSS = RAIZ / "ui" / "assets" / "css" / "style.css"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

EXTRA = '''

/* ---------- Sidebar: jerarquía de secciones (Paso 5) ---------- */
.eva-sidebar-user {
    background: var(--eva-card);
    border: 1px solid var(--eva-border);
    border-radius: var(--eva-radius-sm);
    padding: .6rem .8rem;
    margin-bottom: .5rem;
    font-size: .85rem;
}
.eva-sidebar-section {
    color: var(--eva-muted);
    font-size: .72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    margin: 1.1rem 0 .2rem;
    padding: 0 .2rem;
}

/* ---------- Widget de contacto (movido desde app.py inline) ---------- */
#eva-contacto {
    position: fixed; bottom: 14px; left: 14px; z-index: 999;
    font-size: 0.85rem; line-height: 1.6; background: rgba(255,255,255,0.95);
    padding: 8px 12px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
#eva-contacto a { color: var(--eva-info); text-decoration: none; font-weight: 600; }
#eva-contacto a:hover { text-decoration: underline; }
'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    if not CSS.is_file():
        print(f"[ERROR] no existe {CSS}")
        return 1

    actual = CSS.read_text(encoding="utf-8")

    # Idempotencia
    if ".eva-sidebar-user" in actual:
        print("[SKIP] bloque ya presente en style.css (nada que hacer)")
        return 0

    # Dependencia: --eva-info debe existir en :root
    if "--eva-info:" not in actual:
        print("[ERROR] :root no define --eva-info; el color de enlaces quedaria invalido")
        return 1

    bak = CSS.with_suffix(".css.bak")
    shutil.copy2(CSS, bak)
    CSS.write_text(actual + EXTRA, encoding="utf-8")

    # Verificacion post-escritura
    nuevo = CSS.read_text(encoding="utf-8")
    ok = all(t in nuevo for t in (".eva-sidebar-user", ".eva-sidebar-section", "#eva-contacto"))
    if not ok:
        shutil.copy2(bak, CSS)
        audit("AUD-UI-005", "ROLLBACK", "verificacion post-escritura fallo")
        print("[ERROR] verificacion fallo, revirtiendo backup")
        return 1

    audit("AUD-UI-005", "OK", "style.css: sidebar jerarquia + contacto centralizado")
    print(f"[OK] AUD-UI-005 aplicado | backup: {bak.name}")
    print("Nota: el inline de #eva-contacto en app.py sigue activo (fase 2: retirarlo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())