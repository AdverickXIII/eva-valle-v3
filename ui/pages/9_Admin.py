"""Pagina 9: Panel de Administracion (solo admin)."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.services.auth import add_user, current_role, list_users, remove_user

st.set_page_config(page_title="Admin | EVA Valle", page_icon="\U0001F510", layout="wide")

if current_role() != "admin":
    st.error("\u26D4 Acceso restringido a administradores.")
    st.stop()

st.title("\U0001F510 Panel de Administracion")
st.caption("Gestion de usuarios y estado del sistema")
st.markdown("---")

tab1, tab2 = st.tabs(["\U0001F465 Usuarios", "\u2699\uFE0F Sistema"])

with tab1:
    st.subheader("Usuarios registrados")
    usuarios = list_users()
    df_users = pd.DataFrame(
        [{"usuario": u, "rol": r} for u, r in usuarios.items()]
    )
    st.dataframe(df_users, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("\u2795 Agregar usuario")
    with st.form("add_user"):
        c1, c2, c3 = st.columns(3)
        with c1:
            nuevo_u = st.text_input("Usuario")
        with c2:
            nuevo_p = st.text_input("Contrase\u00f1a", type="password")
        with c3:
            nuevo_r = st.selectbox("Rol", ["usuario", "admin"])
        crear = st.form_submit_button("Crear usuario")
    if crear:
        if nuevo_u and nuevo_p:
            add_user(nuevo_u, nuevo_p, nuevo_r)
            st.success(f"\u2705 Usuario '{nuevo_u}' creado con rol '{nuevo_r}'.")
            st.rerun()
        else:
            st.warning("Completa usuario y contrase\u00f1a.")

    st.markdown("---")
    st.subheader("\U0001F5D1 Eliminar usuario")
    eliminar_de = [u for u in usuarios if u != "admin"]
    if eliminar_de:
        sel = st.selectbox("Usuario a eliminar", eliminar_de)
        if st.button("\U0001F5D1 Eliminar"):
            remove_user(sel)
            st.success(f"\u2705 Usuario '{sel}' eliminado.")
            st.rerun()
    else:
        st.info("No hay usuarios eliminables (solo existe el admin).")

with tab2:
    st.subheader("Estado del sistema")
    st.markdown(f"**Proyecto:** {settings.PROJECT_NAME}")
    st.markdown(f"**Entorno:** {settings.ENV}")
    st.markdown(f"**Ruta raiz:** `{settings.PROJECT_ROOT}`")
    st.markdown("---")
    st.markdown("**Datos:**")
    st.code(
        f"Modelo conceptual: {settings.DATA_MODEL_PATH}\n"
        f"Tablas de salida: {settings.OUTPUTS_TABLES_PATH}",
        language=None,
    )
