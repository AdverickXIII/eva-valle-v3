"""Registra la pagina 18_Satelite.py en la navegacion manual de app.py."""
from pathlib import Path

p = Path("app.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

marcador = "ui/pages/16_Mapa_Cultivos.py"
nueva = '    st.Page("ui/pages/18_Satelite.py", title="Validacion Satelital", icon="\\U0001F6F0\\uFE0F"),\n'

if any("18_Satelite.py" in l for l in lines):
    print("[INFO] La pagina ya estaba registrada en app.py")
else:
    insertado = False
    for i, l in enumerate(lines):
        if marcador in l:
            lines.insert(i + 1, nueva)
            insertado = True
            break
    if not insertado:
        print("[ERROR] No encontre la linea de Mapa Cultivos en app.py")
        raise SystemExit(1)
    p.write_text("".join(lines), encoding="utf-8")
    print("[OK] Pagina 'Validacion Satelital' registrada despues de 'Mapa Cultivos'")

print("Ahora reinicia Streamlit: Ctrl+C y luego: streamlit run app.py")