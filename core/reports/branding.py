"""Marca institucional: logo en cada pagina de todos los PDF.

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


def build_con_logo(doc, flowables, **kw):
    """AUD-BRAND-005: build() con callbacks de pagina donde reportlab los ejecuta.

    Respeta un callback custom si el generador lo dejo en el constructor
    (atributo doc.onPage); si no, usa pagina_con_logo.
    """
    cb = getattr(doc, "onPage", None) or pagina_con_logo
    kw.setdefault("onFirstPage", cb)
    kw.setdefault("onLaterPages", cb)
    doc.build(flowables, **kw)
