"""Banner v2: HTML sin indentacion para que Markdown lo interprete."""
from pathlib import Path

p = Path("ui/pages/0_Home.py")
c = p.read_text(encoding="utf-8")
i = c.find("# ---------- Hero banner")
j = c.find("st.title(", i)
if i == -1 or j == -1:
    print("[ERROR] Bloque hero no encontrado")
    raise SystemExit(1)

NEW = '''# ---------- Hero banner (visible aun sin imagen) ----------
import base64 as _b64
from pathlib import Path as _Path

_hero = _Path(__file__).parent.parent / "assets" / "img" / "hero.png"
if _hero.exists():
    _img = _b64.b64encode(_hero.read_bytes()).decode()
    _capa = f'url("data:image/png;base64,{_img}") center 30% / cover no-repeat'
else:
    _capa = "none"

st.markdown(
    f"""<style id="hero_banner">
.hero-banner {{
    background: linear-gradient(90deg,
        rgba(15,50,35,0.85) 0%, rgba(15,50,35,0.45) 55%, rgba(15,50,35,0.10) 100%),
        {_capa};
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
c = c[:i] + NEW + c[j:]
p.write_text(c, encoding="utf-8")
print("[OK] Banner v2: <style> y <div> en columna 0 (Markdown los interpretara)")