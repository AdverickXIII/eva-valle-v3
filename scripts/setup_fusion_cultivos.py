"""Fusion: deja una unica pagina 'Cultivos'; elimina la duplicada Ficha Cultivo."""
from pathlib import Path

# 1) Quitar el registro de la pagina duplicada en app.py
app = Path("app.py")
lines = app.read_text(encoding="utf-8").splitlines(keepends=True)
n0 = len(lines)
lines = [l for l in lines if "20_Ficha_Cultivo.py" not in l and "20_Ficha.py" not in l]
if len(lines) != n0:
    app.write_text("".join(lines), encoding="utf-8")
    print(f"[OK] {n0 - len(lines)} entrada(s) de 'Ficha Cultivo' eliminada(s) de app.py")
else:
    print("[INFO] app.py no registraba la pagina duplicada")

# 2) Borrar el archivo duplicado
for nombre in ["20_Ficha_Cultivo.py", "20_Ficha.py"]:
    p = Path("ui/pages") / nombre
    if p.exists():
        p.unlink()
        print(f"[OK] {nombre} eliminado del repositorio")

# 3) Verificar que 7_Cultivos tiene los elementos clave de la ficha
c7 = Path("ui/pages/7_Cultivos.py").read_text(encoding="utf-8").lower()
print("\n=== Contenido de la pagina Cultivos (7) ===")
for clave in ["elasticidad", "narrativa", "cagr", "build_ficha_pdf",
              "tabla b", "tabla c", "ranking"]:
    print(f"  contiene '{clave}': {clave in c7}")

print("\nReinicia Streamlit: el menu quedara con una unica entrada 'Cultivos'")