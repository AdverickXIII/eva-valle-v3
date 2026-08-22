"""Hero banner visible en Inicio con la imagen del agricultor."""
from pathlib import Path

p = Path("ui/pages/0_Home.py")
c = p.read_text(encoding="utf-8")

if "hero_banner" in c:
    print("[INFO] El banner ya estaba aplicado")
    raise SystemExit(0)

i = c.find("st.title(")
if i == -1:
    print("[ERROR] No encontre st.title en 0_Home.py")
    raise SystemExit(1)

BLOQUE = '''# ---------- Hero banner (imagen visible con lema) ----------
import base64 as _b64
from pathlib import Path as _Path

_hero = _Path(__file__).parent.parent / "assets" / "img" / "hero.png"
if _hero.exists():
    _img = _b64.b64encode(_hero.read_bytes()).decode()
    st.markdown(
        f"""<style id="hero_banner">
        .hero-banner {{
            background: linear-gradient(90deg,
                rgba(15,50,35,0.80) 0%, rgba(15,50,35,0.35) 55%, rgba(15,50,35,0.05) 100%),
                url("data:image/png;base64,{{_img}}") center 30% / cover no-repeat;
            border-radius: 16px;
            padding: 46px 40px;
            margin: -8px 0 22px;
        }}
        .hero-banner h2 {{ color: #ffffff; margin: 0; font-size: 1.7rem; }}
        .hero-banner p {{ color: #DFF3E7; margin: 6px 0 0; }}
        </style>
        <div class="hero-banner">
            <h2>El dato oficial, al servicio de quien siembra</h2>
            <p>Inteligencia analitica del agro vallecaucano &middot; UPRA &middot; EVA 2019-2025</p>
        </div>""",
        unsafe_allow_html=True,
    )

'''

c = c[:i] + BLOQUE + c[i:]
p.write_text(c, encoding="utf-8")
print("[OK] Hero banner aplicado en Inicio")
print("Si no has guardado hero.png, hazlo y recarga la pagina")