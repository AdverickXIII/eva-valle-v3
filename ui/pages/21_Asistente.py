"""Pagina 21: Asistente conversacional determinista (dato oficial, cero alucinacion)."""
import streamlit as st

import plotly.graph_objects as go

from core.chat.engine import ask

st.set_page_config(page_title="Asistente | EVA Valle", page_icon="\U0001F4AC", layout="wide")

st.title("\U0001F4AC Asistente del Agro Vallecaucano")
st.caption("Preguntas en lenguaje natural; respuestas con el dato oficial UPRA-EVA 2019-2025. "
           "Sin invencion: cada cifra sale del dataset.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending" not in st.session_state:
    st.session_state.pending = None

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("pagina"):
            st.caption(f"\U0001F517 Profundiza en la pagina: {msg['pagina']}")

prompt = st.chat_input("Ej: cuanto platano produjo Sevilla en 2025?")
prompt = prompt or st.session_state.pending
if prompt:
    st.session_state.pending = None
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    ctx = st.session_state.get('chat_ctx', {})
    r = ask(prompt, ctx=ctx)
    st.session_state.chat_ctx = r.get('ctx', {})
    st.session_state.chat_history.append({"role": "assistant", "content": r["texto"],
                                          "pagina": r.get("pagina")})
    with st.chat_message("assistant"):
        st.markdown(r["texto"])
        if r.get("serie"):
            _fig = go.Figure(go.Scatter(x=r["serie"]["x"], y=r["serie"]["y"],
                                        mode="lines+markers"))
            _fig.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=20),
                               title=r["serie"].get("titulo", ""))
            st.plotly_chart(_fig, use_container_width=True)
        if r.get("pagina"):
            st.caption(f"\U0001F517 Profundiza en la pagina: {r['pagina']}")
