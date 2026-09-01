"""Hotfix AUD-BRAND v2: el callback de pagina se pasa a build(), no al constructor.

AUD-BRAND-005: SimpleDocTemplate(onPage=...) guarda un atributo muerto;
reportlab solo ejecuta callbacks via build(onFirstPage/onLaterPages).
Se agrega build_con_logo() en branding.py y se rewiring doc.build(...) en
todos los generadores de core/reports/*.py.
AUD-BRAND-021: la prueba de humo ahora inspecciona el artefacto:
el PDF debe contener un XObject /Subtype /Image (el sello incrustado).
Estandar: backups .bak, manifiesto JSONL, logging, idempotencia.
"""
import importlib
import json
import logging
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("hotfix_logo")

AUDIT_LOG_PATH = ROOT / "logs" / "audit_hotfix.json"
audit_events: list[dict] = []

HELPER = '''

def build_con_logo(doc, flowables, **kw):
    """AUD-BRAND-005: build() con callbacks de pagina donde reportlab los ejecuta.

    Respeta un callback custom si el generador lo dejo en el constructor
    (atributo doc.onPage); si no, usa pagina_con_logo.
    """
    cb = getattr(doc, "onPage", None) or pagina_con_logo
    kw.setdefault("onFirstPage", cb)
    kw.setdefault("onLaterPages", cb)
    doc.build(flowables, **kw)
'''


def audit(code: str, message: str, **extra) -> None:
    audit_events.append({"code": code, "message": message,
                         "timestamp": datetime.now(timezone.utc).isoformat(),
                         **extra})
    log.info("[%s] %s", code, message)


def backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy(path, bak)


def main() -> None:
    # ---------- 1) branding.py: agregar helper (sin tocar el codigo del usuario)
    bp = ROOT / "core" / "reports" / "branding.py"
    b = bp.read_text(encoding="utf-8")
    if "def build_con_logo" not in b:
        backup(bp)
        bp.write_text(b.rstrip() + "\n" + HELPER, encoding="utf-8")
        audit("AUD-BRAND-005", "build_con_logo agregado a branding.py")
    else:
        audit("AUD-BRAND-000", "branding.py ya tiene build_con_logo")

    # ---------- 2) Rewiring de generadores en core/reports ----------
    parcheados, advertidos = [], []
    for fp in sorted((ROOT / "core" / "reports").glob("*.py")):
        c = fp.read_text(encoding="utf-8")
        if "onPage=" not in c or "build_con_logo" in c:
            continue
        c2 = re.sub(
            r"from core\.reports\.branding import ([^\n]+)",
            lambda m: m.group(0) if "build_con_logo" in m.group(1)
            else f"from core.reports.branding import {m.group(1).rstrip()}, build_con_logo",
            c, count=1)
        n_build = c2.count("doc.build(")
        if n_build == 0:
            advertidos.append(fp.name)
            audit("AUD-BRAND-997", f"{fp.name}: tiene onPage= pero sin doc.build(; "
                  "revisar manualmente", level="error")
            continue
        c2 = c2.replace("doc.build(", "build_con_logo(doc, ")
        backup(fp)
        fp.write_text(c2, encoding="utf-8")
        parcheados.append(fp.name)
        audit("AUD-BRAND-006", f"{fp.name}: doc.build -> build_con_logo "
              f"({n_build} llamada(s))")
    if advertidos:
        audit("AUD-BRAND-996", f"Archivos sin rewiring automatico: {advertidos}",
              level="error")

    # ---------- 3) Prueba de humo QUE INSPECCIONA EL ARTEFACTO ----------
    import core.reports.branding as brand
    importlib.reload(brand)
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate

    out = ROOT / "test_logo.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=letter)
    brand.build_con_logo(doc, [Paragraph("Prueba de sello institucional EVA Valle",
                                         getSampleStyleSheet()["Normal"])])
    raw = out.read_bytes()
    has_img = b"/Subtype /Image" in raw
    audit("AUD-BRAND-021", f"test_logo.pdf: {len(raw):,} bytes, "
          f"imagen incrustada={has_img}")
    if not has_img:
        audit("AUD-BRAND-998", "El PDF de prueba NO contiene el sello: "
              "revisar logo_pdf.png", level="error")

    # ---------- 4) Tracking en git ----------
    r = subprocess.run(["git", "ls-files", "ui/assets/img/logo_pdf.png"],
                       capture_output=True, text=True, cwd=str(ROOT))
    tracked = bool(r.stdout.strip())
    audit("AUD-BRAND-030", "logo_pdf.png trackeado" if tracked
          else "logo_pdf.png NO trackeado: el Cloud no lo tiene", tracked=tracked)

    # ---------- 5) Manifiesto ----------
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"run": datetime.now(timezone.utc).isoformat(),
                             "events": audit_events}) + "\n")
    log.info("Parcheados: %s", parcheados)
    log.info("✅ Hotfix AUD-BRAND v2 completo. Abre test_logo.pdf: el sello debe verse.")
    if not tracked:
        log.info("OBLIGATORIO: git add ui/assets/img/logo_pdf.png")


if __name__ == "__main__":
    main()