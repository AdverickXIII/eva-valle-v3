"""Asigna url_path unico a la pagina Ficha Cultivo para evitar colision de URLs."""
from pathlib import Path

p = Path("app.py")
c = p.read_text(encoding="utf-8")

if 'url_path="ficha-cultivo"' in c:
    print("[INFO] El url_path ya estaba asignado.")
    raise SystemExit(0)

old = '20_Ficha.py", title="Ficha Cultivo"'
if old not in c:
    print("[ERROR] No encontre la linea de 20_Ficha.py en app.py")
    raise SystemExit(1)

c = c.replace(old, old + ', url_path="ficha-cultivo"', 1)
p.write_text(c, encoding="utf-8")
print("[OK] url_path='ficha-cultivo' agregado a app.py")
print("Reinicia Streamlit: la pagina quedara en /ficha-cultivo")