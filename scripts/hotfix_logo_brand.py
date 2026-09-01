"""Hotfix AUD-BRAND: logo institucional visible en todos los PDF.

Trabaja con el branding.py del usuario (AUD-BRAND-001..004): solo lo escribe
si no esta presente aun. Estandar del proyecto: backups .bak, manifiesto
JSONL (logs/audit_hotfix.json), logging estructurado, diagnostico PIL del
asset, prueba de humo con PDF real y chequeo de tracking en git.
"""
import importlib
import json
import logging
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

MIN_PIX_VISIBLES = 50  # umbral: un logo real tiene al menos unos cientos


def audit(code: str, message: str, **extra) -> None:
    audit_events.append({"code": code, "message": message,
                         "timestamp": datetime.now(timezone.utc).isoformat(),
                         **extra})
    log.info("[%s] %s", code, message)


def backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy(path, bak)
    log.info("Backup creado: %s", bak)


def stats_logo(p: Path) -> dict:
    from PIL import Image
    im = Image.open(p).convert("RGBA")
    lo, hi = im.getchannel("A").getextrema()
    px = [v for v in im.getdata() if v[3] > 40]
    if px:
        r = sum(v[0] for v in px) / len(px)
        g = sum(v[1] for v in px) / len(px)
        b = sum(v[2] for v in px) / len(px)
    else:
        r = g = b = -1.0
    no_blancos = sum(1 for v in px if min(v[0], v[1], v[2]) < 235)
    return {"alpha": (lo, hi), "rgb_visible": (round(r), round(g), round(b)),
            "pix_no_blancos": no_blancos}


# ---------------------------------------------------------------------------
# branding.py del usuario (AUD-BRAND-001..004) - verbatim
# ---------------------------------------------------------------------------
BRANDING_USUARIO = '''"""Marca institucional: logo en cada pagina de todos los PDF.

AUD-BRAND-001: logo con tamano explicito (2.4 x 2.4 cm) arriba a la derecha;
sin width/height reportlab usa pixeles nativos y el logo sale de pagina.
AUD-BRAND-002: prefiere logo_pdf.png (compuesto sobre blanco, visible en papel);
cae a logo.png solo si aquel no existe.
AUD-BRAND-003: posicion calculada desde doc.pagesize (no coordenadas fijas),
para que el sello quede correcto sin importar tamano de pagina u orientacion.
AUD-BRAND-004: fallas al estampar el logo se registran y no interrumpen
la generacion del PDF (mejor un reporte sin logo que un reporte que no sale).
"""

import logging
from pathlib import Path

from reportlab.lib.units import cm

log = logging.getLogger("eva.branding")

_IMG = Path(__file__).resolve().parents[2] / "ui" / "assets" / "img"
LOGO_PDF = _IMG / "logo_pdf.png"
LOGO_UI = _IMG / "logo.png"
LOGO = LOGO_PDF if LOGO_PDF.exists() else LOGO_UI

# Tamano del logo (fijo, independiente del tamano de pagina)
_LOGO_W = 2.4 * cm
_LOGO_H = 2.4 * cm

# Margenes respecto al borde superior derecho de la pagina
_LOGO_MARGIN_TOP = 1.2 * cm
_LOGO_MARGIN_RIGHT = 1.4 * cm


def pagina_con_logo(canvas, doc):
    """Callback onPage: estampa el logo institucional en cada pagina.

    La posicion se calcula a partir de doc.pagesize en vez de coordenadas
    absolutas, para que el sello quede correctamente anclado a la esquina
    superior derecha sin importar si la pagina es A4, Carta, u orientacion
    horizontal/vertical.
    """
    if not LOGO.exists():
        log.warning("AUD-BRAND-004: no se encontro archivo de logo (%s ni %s)", LOGO_PDF, LOGO_UI)
        return

    page_w, page_h = doc.pagesize
    x = page_w - _LOGO_MARGIN_RIGHT - _LOGO_W
    y = page_h - _LOGO_MARGIN_TOP - _LOGO_H

    canvas.saveState()
    try:
        canvas.drawImage(
            str(LOGO), x, y,
            width=_LOGO_W, height=_LOGO_H,
            preserveAspectRatio=True, mask="auto",
        )
    except Exception as e:
        log.warning("AUD-BRAND-004: no se pudo estampar el logo (%s)", e)
    finally:
        canvas.restoreState()
'''


def main() -> None:
    from PIL import Image

    img = ROOT / "ui" / "assets" / "img"
    logo, orig, pdf_logo = img / "logo.png", img / "logo_original.png", img / "logo_pdf.png"

    # ---------- 1) Diagnostico del asset ----------
    for p in (logo, orig):
        if p.exists():
            audit("AUD-BRAND-010", f"Diagnostico {p.name}", **stats_logo(p))

    src = logo
    if orig.exists():
        rgb = stats_logo(logo).get("rgb_visible", (0, 0, 0)) if logo.exists() else (255, 255, 255)
        if all(c > 240 for c in rgb):
            src = orig
            audit("AUD-BRAND-011", "logo.png blanco/invisible; fuente = logo_original.png")
        else:
            audit("AUD-BRAND-011", "logo.png con color visible; fuente = logo.png")

    # ---------- 2) Compuesto sobre blanco ----------
    base = Image.open(src).convert("RGBA")
    bg = Image.new("RGBA", base.size, (255, 255, 255, 255))
    bg.paste(base, (0, 0), base)
    bg.convert("RGB").save(pdf_logo)
    nw = stats_logo(pdf_logo)["pix_no_blancos"]
    audit("AUD-BRAND-002", f"logo_pdf.png compuesto desde {src.name}", pix_no_blancos=nw)
    if nw < MIN_PIX_VISIBLES:
        audit("AUD-BRAND-999", "logo_pdf.png sin contenido visible; revisar fuente",
              level="error")

    # ---------- 3) branding.py = version del usuario (si falta) ----------
    bp = ROOT / "core" / "reports" / "branding.py"
    if "AUD-BRAND-003" in bp.read_text(encoding="utf-8"):
        audit("AUD-BRAND-000", "branding.py ya es la version del usuario (001..004)")
    else:
        backup(bp)
        bp.write_text(BRANDING_USUARIO, encoding="utf-8")
        audit("AUD-BRAND-001", "branding.py escrito con la version del usuario")

    # ---------- 4) Prueba de humo: PDF real con el sello ----------
    import core.reports.branding as brand
    importlib.reload(brand)
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate

    out = ROOT / "test_logo.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=letter, onPage=brand.pagina_con_logo)
    doc.build([Paragraph("Prueba de sello institucional EVA Valle",
                         getSampleStyleSheet()["Normal"])])
    size = out.stat().st_size
    audit("AUD-BRAND-020", f"test_logo.pdf generado ({size:,} bytes)")
    if size < 5000:
        audit("AUD-BRAND-998", "test_logo.pdf muy pequeno; el logo podria no estar "
              "incrustado", level="error")

    # ---------- 5) Tracking en git (causa raiz historica del Cloud) ----------
    r = subprocess.run(["git", "ls-files", "ui/assets/img/logo_pdf.png"],
                       capture_output=True, text=True, cwd=str(ROOT))
    tracked = bool(r.stdout.strip())
    audit("AUD-BRAND-030",
          "logo_pdf.png trackeado en git" if tracked
          else "logo_pdf.png NO trackeado: el Cloud no lo tiene",
          tracked=tracked)

    # ---------- 6) Manifiesto ----------
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"run": datetime.now(timezone.utc).isoformat(),
                             "events": audit_events}) + "\n")
    log.info("✅ Hotfix AUD-BRAND completo. Abre test_logo.pdf y confirma el sello.")
    if not tracked:
        log.info("OBLIGATORIO antes del push: git add ui/assets/img/logo_pdf.png")


if __name__ == "__main__":
    main()