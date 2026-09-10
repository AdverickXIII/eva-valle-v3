"""AUD-UI-007: agrega al final de style.css el bloque login institucional (Paso 4).
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

/* ---------- Login institucional (Paso 4) ---------- */
.eva-login-wrap {
    display: flex;
    min-height: 88vh;
    border-radius: var(--eva-radius);
    overflow: hidden;
    box-shadow: var(--eva-shadow-hover);
    margin-top: 1rem;
}
.eva-login-brand {
    flex: 1.1;
    background: linear-gradient(135deg, rgba(15,50,35,0.92) 0%, rgba(15,50,35,0.55) 100%),
        var(--eva-login-bg, none) center / cover no-repeat;
    color: #fff;
    padding: 3rem 2.5rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.eva-login-brand .eva-brand-top h1 {
    font-size: 1.9rem; margin: .8rem 0 .2rem; color: #fff;
}
.eva-login-brand .eva-brand-top p {
    color: #DFF3E7; font-size: .95rem; margin: 0;
}
.eva-login-brand .eva-brand-quote {
    font-size: 1.05rem; font-style: italic; color: #fff;
    border-left: 3px solid var(--eva-primary); padding-left: 1rem;
    margin: 1.5rem 0;
}
.eva-login-brand .eva-brand-stats {
    display: flex; gap: 1.5rem; font-size: .85rem; color: #DFF3E7;
}
.eva-login-brand .eva-brand-version {
    font-size: .75rem; color: #A9D8BE; letter-spacing: .05em;
}
.eva-login-form {
    flex: 1;
    background: var(--eva-card);
    padding: 3rem 2.8rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.eva-login-form h2 { margin: 0 0 .3rem; font-size: 1.3rem; color: var(--eva-text); }
.eva-login-form .eva-login-sub { color: var(--eva-muted); font-size: .88rem; margin-bottom: 1.5rem; }
.eva-login-security {
    display: flex; align-items: center; gap: .4rem;
    color: var(--eva-muted); font-size: .78rem; margin-top: 1.2rem;
}
.eva-login-footer {
    color: var(--eva-muted); font-size: .75rem; text-align: center; margin-top: 1rem;
}
@media (max-width: 900px) {
    .eva-login-wrap { flex-direction: column; min-height: unset; }
    .eva-login-brand { padding: 2rem 1.5rem; }
}
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
    if ".eva-login-wrap" in actual:
        print("[SKIP] bloque login ya presente en style.css (nada que hacer)")
        return 0

    # Dependencias del :root
    for token in ("--eva-radius:", "--eva-shadow-hover:", "--eva-card:", "--eva-primary:"):
        if token not in actual:
            print(f"[ERROR] :root no define {token}; el bloque login quedaria incompleto")
            return 1

    bak = CSS.with_suffix(".css.bak")
    shutil.copy2(CSS, bak)
    CSS.write_text(actual + EXTRA, encoding="utf-8")

    nuevo = CSS.read_text(encoding="utf-8")
    ok = all(t in nuevo for t in (".eva-login-wrap", ".eva-login-brand",
                                  ".eva-login-form", ".eva-login-footer"))
    if not ok:
        shutil.copy2(bak, CSS)
        audit("AUD-UI-007", "ROLLBACK", "verificacion post-escritura fallo")
        print("[ERROR] verificacion fallo, revirtiendo backup")
        return 1

    audit("AUD-UI-007", "OK", "style.css: bloque login institucional (Paso 4)")
    print(f"[OK] AUD-UI-007 aplicado | backup: {bak.name}")
    print("Nota: CSS inerte hoy (el login actual no emite estas clases; Paso 4 lo activara)")
    return 0


if __name__ == "__main__":
    sys.exit(main())