"""Login: solo el nombre, sin logo ni emoji."""
from pathlib import Path

p = Path("app.py")
c = p.read_text(encoding="utf-8")

# 1) Por si el logo siguiera presente, eliminarlo
old_logo = '''        _logo = Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"
        if _logo.exists():
            st.image(str(_logo), width=150)
'''
if old_logo in c:
    c = c.replace(old_logo, "", 1)
    print("[OK] Logo eliminado del login")

# 2) Titulo con solo el nombre (sin espiga)
old_t = '            "<h1 style=\'text-align:center; color:#2E8B57;\'>\\U0001F33E EVA Valle v3.0</h1>",'
new_t = '            "<h1 style=\'text-align:center; color:#2E8B57;\'>EVA Valle v3.0</h1>",'
if old_t in c:
    c = c.replace(old_t, new_t, 1)
    print("[OK] Titulo del login: solo el nombre")
elif new_t in c:
    print("[INFO] El titulo ya estaba solo con el nombre")
else:
    print("[AVISO] Revisa el h1 del login manualmente")

p.write_text(c, encoding="utf-8")
print("Recarga con Ctrl+F5 y cierra sesion para ver el login")