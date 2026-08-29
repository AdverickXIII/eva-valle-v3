"""El historial del Asistente se reinicia al cambiar de usuario/rol."""
from pathlib import Path

p = Path("ui/pages/21_Asistente.py")
c = p.read_text(encoding="utf-8")

old = '''if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending" not in st.session_state:
    st.session_state.pending = None'''

new = '''_ident = "|".join(str(st.session_state.get(k)) for k in
                 ("usuario", "user", "role", "logged_in"))
if st.session_state.get("chat_owner") != _ident:
    st.session_state.chat_history = []
    st.session_state.chat_ctx = {}
    st.session_state.pending = None
    st.session_state.chat_owner = _ident
elif "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending" not in st.session_state:
    st.session_state.pending = None'''

if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] Historial aislado por identidad de sesion")
else:
    print("[AVISO] Bloque no encontrado")