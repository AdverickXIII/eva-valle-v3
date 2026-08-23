"""Elimina los botones de preguntas sugeridas de la pagina del Asistente."""
from pathlib import Path

p = Path("ui/pages/21_Asistente.py")
c = p.read_text(encoding="utf-8")

old = '''SUG = [
    "Cuanto platano produjo Sevilla en 2025?",
    "Quien es el #1 en naranja?",
    "Por que crecio el platano en Sevilla?",
    "Hay municipios en declive?",
]
cols = st.columns(len(SUG))
for c, s in zip(cols, SUG):
    if c.button(s, use_container_width=True):
        st.session_state.pending = s

'''

if old in c:
    p.write_text(c.replace(old, "", 1), encoding="utf-8")
    print("[OK] Botones sugeridos eliminados; chat limpio")
else:
    print("[AVISO] Bloque no encontrado; revisa 21_Asistente.py")