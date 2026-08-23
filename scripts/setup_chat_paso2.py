"""Paso 2: pagina del Asistente + registro en el menu + parches de robustez."""
from pathlib import Path

if not Path("core/chat/engine.py").exists():
    print("[AVISO] Falta el motor: ejecuta primero  python scripts\\setup_chat_paso1.py")
    raise SystemExit(1)

# --- Parche 1: import de settings a prueba de variantes ---
e = Path("core/chat/engine.py")
ec = e.read_text(encoding="utf-8")
old_imp = "from config.settings import settings"
new_imp = ("try:\n    from config import settings\n"
           "except Exception:\n    from config.settings import settings")
if old_imp in ec:
    ec = ec.replace(old_imp, new_imp, 1)
    print("[OK] Import de settings robusto")

# --- Parche 2: reconocer '#1' como intencion de ranking ---
old_k = '("ranking", ["ranking", "posicion", "lider", "primer", "top", "quien produce mas"]),'
new_k = '("ranking", ["ranking", "posicion", "lider", "primer", "top", "quien produce mas", "#1", "numero 1"]),'
if old_k in ec:
    ec = ec.replace(old_k, new_k, 1)
    print("[OK] '#1' reconocido como ranking")
e.write_text(ec, encoding="utf-8")

# --- Pagina del chat ---
PAGE = '''"""Pagina 21: Asistente conversacional determinista (dato oficial, cero alucinacion)."""
import streamlit as st

from core.chat.engine import ask

st.set_page_config(page_title="Asistente | EVA Valle", icon="\\U0001F4AC", layout="wide")

st.title("\\U0001F4AC Asistente del Agro Vallecaucano")
st.caption("Preguntas en lenguaje natural; respuestas con el dato oficial UPRA-EVA 2019-2025. "
           "Sin invencion: cada cifra sale del dataset.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending" not in st.session_state:
    st.session_state.pending = None

SUG = [
    "Cuanto platano produjo Sevilla en 2025?",
    "Quien es el #1 en naranja?",
    "Por que crecio el platano en Sevilla?",
    "Hay municipios en declive?",
]
cols = st.columns(len(SUG))
for c, s in zip(cols, SUG):
    if c.button(s, use_container_width=True):
        st.session_state.pending = s

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("pagina"):
            st.caption(f"\\U0001F517 Profundiza en la pagina: {msg['pagina']}")

prompt = st.chat_input("Ej: cuanto platano produjo Sevilla en 2025?")
prompt = prompt or st.session_state.pending
if prompt:
    st.session_state.pending = None
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    r = ask(prompt)
    st.session_state.chat_history.append({"role": "assistant", "content": r["texto"],
                                          "pagina": r.get("pagina")})
    with st.chat_message("assistant"):
        st.markdown(r["texto"])
        if r.get("pagina"):
            st.caption(f"\\U0001F517 Profundiza en la pagina: {r['pagina']}")
'''
Path("ui/pages/21_Asistente.py").write_text(PAGE, encoding="utf-8")
print("[OK] ui/pages/21_Asistente.py creada")

# --- Registro en el menu (seccion propia, todos los roles) ---
app = Path("app.py")
c = app.read_text(encoding="utf-8")
old = '("📦 Entregables", 0, st.Page("ui/pages/10_Reportes.py", title="Reportes", icon="📄")),'
new = ('("💬 Asistente", 0, st.Page("ui/pages/21_Asistente.py", title="Asistente", icon="💬")),\n'
       '        ' + old)
if "21_Asistente" not in c:
    if old in c:
        app.write_text(c.replace(old, new, 1), encoding="utf-8")
        print("[OK] Asistente registrado en el menu (visible para los 3 roles)")
    else:
        print("[AVISO] No encontre la linea de Entregables; registra la pagina a mano")
else:
    print("[INFO] El Asistente ya estaba registrado")

print("\nReinicia Streamlit y entra a la pagina Asistente")