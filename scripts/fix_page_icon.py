"""Corrige icon= -> page_icon= en las paginas nuevas."""
from pathlib import Path

for f in ["ui/pages/11_Comparador.py", "ui/pages/12_Alertas.py"]:
    p = Path(f)
    if not p.exists():
        print(f"[SKIP] {f} no existe")
        continue
    c = p.read_text(encoding="utf-8")
    if ", icon=" in c:
        c = c.replace(", icon=", ", page_icon=")
        p.write_text(c, encoding="utf-8")
        print(f"[OK] {f} corregido")
    else:
        print(f"[INFO] {f} ya estaba bien")

print("\nRecarga Streamlit (Ctrl+R en el navegador).")