"""Marca institucional: logo en cada pagina de todos los PDF."""
from pathlib import Path

from reportlab.lib.units import cm

_IMG = Path(__file__).resolve().parents[2] / "ui" / "assets" / "img"
LOGO = _IMG / "logo_pdf.png"
if not LOGO.exists():
    LOGO = _IMG / "logo.png"


def pagina_con_logo(canvas, doc):
    if not LOGO.exists():
        return
    canvas.drawImage(str(LOGO), 18.4 * cm, 24.6 * cm,
                     width=2.4 * cm, height=2.4 * cm,
                     preserveAspectRatio=True, mask="auto")
