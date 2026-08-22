"""Logo institucional centrado en la pantalla de login."""
from pathlib import Path

p = Path("app.py")
c = p.read_text(encoding="utf-8")

old = '''        st.markdown(
            "<h1 style='text-align:center; color:#2E8B57;'>\\U0001F33E EVA Valle v3.0</h1>",
            unsafe_allow_html=True,
        )'''

new = '''        _logo = Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"
        if _logo.exists():
            st.image(str(_logo), width=150)
        st.markdown(
            "<h1 style='text-align:center; color:#2E8B57;'>EVA Valle v3.0</h1>",
            unsafe_allow_html=True,
        )'''

if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] Logo centrado en el login (y emoji retirado del titulo)")
else:
    print("[AVISO] El bloque del login no coincide; revisa app.py manualmente")