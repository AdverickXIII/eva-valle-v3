"""AUD-UI-006: app.py - retirar CSS inline de contacto + sidebar con jerarquia.
Reemplaza 2 bloques:
1. Contacto: quita <style>...</style>, deja solo <div id="eva-contacto">
2. Sidebar: nueva version con .eva-sidebar-user
Fail-safe: pre-chequeos, backup, py_compile, rollback, auditoria JSONL.
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app.py"
CSS = RAIZ / "ui" / "assets" / "css" / "style.css"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

NUEVO_CONTACTO = '''    # Contacto institucional (v2): correo + telefono + WhatsApp
    st.markdown(
        """
        <!-- CONTACTO_V2 -->
        <div id="eva-contacto">
          📧 <a href="mailto:moises.zuniga.grueso@gmail.com?subject=Acceso%20EVA%20Valle%20v3.0">Escríbenos</a><br>
          📞 <a href="tel:+573167197764">+57 3167197764</a><br>
          💬 <a href="https://wa.me/573167197764" target="_blank">WhatsApp</a>
        </div>
        """,
        unsafe_allow_html=True,
    )'''

NUEVO_SIDEBAR = '''with st.sidebar:
    st.image(str(Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"), width=84)
    st.title("EVA Valle")
    role = current_role()
    role_icon = {"admin": "\\U0001F451", "analista": "\\U0001F9ED", "user": "\\U0001F464"}.get(role, "\\U0001F464")
    role_label = {"admin": "Admin", "analista": "Analista", "user": "Usuario"}.get(role, role)
    st.markdown(
        f'<div class="eva-sidebar-user">{role_icon} <b>{st.session_state.get("username")}</b>'
        f'<br><span style="color:var(--eva-muted);">{role_label}</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("\\U0001F6AA Cerrar sesion", use_container_width=True):
        logout()
        st.rerun()
    st.markdown("---")
    st.caption("UPRA - Unidad de Planificacion Rural y Agropecuaria")
'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    if not APP.is_file():
        print(f"[ERROR] no existe {APP}")
        return 1
    if not CSS.is_file():
        print(f"[ERROR] no existe {CSS}")
        return 1

    texto = APP.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    # Pre-chequeo 1: style.css tiene las reglas necesarias
    if "#eva-contacto" not in css:
        print("[ERROR] style.css no tiene #eva-contacto; el contacto quedaria sin estilo")
        return 1
    if ".eva-sidebar-user" not in css:
        print("[ERROR] style.css no tiene .eva-sidebar-user; el sidebar quedaria sin estilo")
        return 1

    # Pre-chequeo 2: funciones current_role y logout estan definidas
    if "def current_role" not in texto and "current_role" not in texto:
        print("[ERROR] current_role no definida/importada en app.py")
        return 1
    if "def logout" not in texto and "logout" not in texto:
        print("[ERROR] logout no definida/importada en app.py")
        return 1

    # Pre-chequeo 3: idempotencia
    if "eva-sidebar-user" in texto:
        print("[SKIP] app.py ya tiene eva-sidebar-user (cambio ya aplicado)")
        return 0

    # Buscar bloque de contacto (marcadores: <!-- CONTACTO_V2 --> hasta unsafe_allow_html=True)
    match_contacto = re.search(
        r'(    # Contacto institucional \(v2\).*?<!-- CONTACTO_V2 -->.*?</div>\n        """,\n        unsafe_allow_html=True,\n    \))',
        texto,
        re.S
    )
    if not match_contacto:
        print("[ERROR] bloque de contacto no encontrado con la forma esperada")
        return 1

    # Buscar bloque de sidebar (marcadores: with st.sidebar: hasta st.caption("UPRA..."))
    inicio_sidebar = texto.find('with st.sidebar:')
    if inicio_sidebar == -1:
        print("[ERROR] 'with st.sidebar:' no encontrado en app.py")
        return 1
    fin_sidebar = texto.find('st.caption("UPRA - Unidad de Planificacion Rural y Agropecuaria")', inicio_sidebar)
    if fin_sidebar == -1:
        print("[ERROR] st.caption('UPRA...') no encontrado despues de with st.sidebar")
        return 1
    fin_sidebar = texto.find('\n', fin_sidebar) + 1
    bloque_sidebar_viejo = texto[inicio_sidebar:fin_sidebar]

    # Verificar que el bloque viejo del sidebar tiene la forma esperada
    if "st.image" not in bloque_sidebar_viejo or "st.title" not in bloque_sidebar_viejo or "st.button" not in bloque_sidebar_viejo:
        print("[ERROR] bloque de sidebar no tiene la forma esperada (st.image, st.title, st.button)")
        return 1

    # Reemplazos
    texto_nuevo = texto.replace(match_contacto.group(1), NUEVO_CONTACTO, 1)
    texto_nuevo = texto_nuevo.replace(bloque_sidebar_viejo, NUEVO_SIDEBAR, 1)

    # Backup + escritura
    bak = APP.with_suffix(".py.bak")
    shutil.copy2(APP, bak)
    APP.write_text(texto_nuevo, encoding="utf-8")
    print(f"[OK] 2 bloques reemplazados | backup: {bak.name}")

    # py_compile + rollback
    r = subprocess.run([sys.executable, "-m", "py_compile", str(APP)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, APP)
        audit("AUD-UI-006", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-006", "OK", "app.py: contacto sin inline + sidebar con jerarquia")
    print("[OK] AUD-UI-006 aplicado y compilado")
    print("Siguiente: streamlit run app.py -> verificar contacto + sidebar")
    return 0


if __name__ == "__main__":
    sys.exit(main())