"""Marca institucional: logo en cada pagina de todos los PDF."""
from pathlib import Path

from reportlab.lib.units import cm

LOGO = Path(__file__).resolve().parents[2] / "ui" / "assets" / "img" / "logo_pdf.png"
if not LOGO.exists():
    LOGO = LOGO.with_name("logo.png")


def pagina_con_logo(canvas, doc):
    if not LOGO.exists():
        return
    canvas.saveState()
    canvas.drawImage(str(LOGO), 18.4 * cm, 24.4 * cm,
                     width=2.2 * cm, height=2.2 * cm,
                     preserveAspectRatio=True, mask="auto")
    canvas.restoreState()
