"""Logo visible en PDFs: compone sobre blanco + branding usa logo_pdf.png."""
from pathlib import Path
from PIL import Image

img = Path("ui/assets/img")
logo, orig = img / "logo.png", img / "logo_original.png"
pdf_logo = img / "logo_pdf.png"

def stats(p):
    im = Image.open(p).convert("RGBA")
    lo, hi = im.getchannel("A").getextrema()
    px = [v for v in im.getdata() if v[3] > 40]
    if px:
        r = sum(v[0] for v in px) / len(px)
        g = sum(v[1] for v in px) / len(px)
        b = sum(v[2] for v in px) / len(px)
    else:
        r = g = b = -1
    print(f"{p.name}: alpha=({lo},{hi}) color_medio_visible=({r:.0f},{g:.0f},{b:.0f})")

if logo.exists():
    stats(logo)
if orig.exists():
    stats(orig)

src = orig if orig.exists() else logo
base = Image.open(src).convert("RGBA")
bg = Image.new("RGBA", base.size, (255, 255, 255, 255))
bg.paste(base, (0, 0), base)
bg.convert("RGB").save(pdf_logo)
print(f"[OK] {pdf_logo} creado (logo sobre fondo blanco)")

b = Path("core/reports/branding.py")
c = b.read_text(encoding="utf-8")
if "logo_pdf.png" not in c:
    c = c.replace('"logo.png"', '"logo_pdf.png"', 1)
    c = c.replace(
        'LOGO = Path(__file__).resolve().parents[2] / "ui" / "assets" / "img" / "logo_pdf.png"',
        'LOGO = Path(__file__).resolve().parents[2] / "ui" / "assets" / "img" / "logo_pdf.png"\n'
        'if not LOGO.exists():\n'
        '    LOGO = LOGO.with_name("logo.png")')
    b.write_text(c, encoding="utf-8")
    print("[OK] branding.py usa logo_pdf.png con fallback")
else:
    print("[OK] branding.py ya usa logo_pdf.png")