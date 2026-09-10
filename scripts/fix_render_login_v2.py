"""AUD-UI-008 v2: reemplaza SOLO la funcion render_login() usando escaneo por
indentacion: el cuerpo termina en la primera linea no vacia en columna 0.
Asi NO se traga el flujo principal (gate de auth + sidebar) que vive entre defs.
Fail-safe: pre-chequeos, backup, py_compile, rollback, auditoria JSONL.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

NUEVO = '''def render_login() -> None:
    """Pantalla de login institucional con rate limiting y validacion."""
    st.markdown(
        "<style>section[data-testid='stSidebar']{display:none;}"
        "[data-testid='stSidebarCollapsedControl']{display:none;}</style>",
        unsafe_allow_html=True,
    )
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
    )

    # Fondo del panel de marca: reutiliza hero.png si existe (mismo asset del Home)
    import base64 as _b64
    _hero = Path(__file__).parent / "ui" / "assets" / "img" / "hero.png"
    if _hero.exists():
        _img = _b64.b64encode(_hero.read_bytes()).decode()
        st.markdown(
            f"<style>:root{{--eva-login-bg: url('data:image/png;base64,{_img}');}}</style>",
            unsafe_allow_html=True,
        )

    logo_path = Path(__file__).parent / "ui" / "assets" / "img" / "logo.png"
    logo_b64 = ""
    if logo_path.exists():
        import base64 as _b64_logo
        logo_b64 = _b64_logo.b64encode(logo_path.read_bytes()).decode()

    st.markdown('<div class="eva-login-wrap">', unsafe_allow_html=True)
    col_brand, col_form = st.columns([1.1, 1], gap="small")

    with col_brand:
        logo_html = (
            f'<img src="data:image/png;base64,{logo_b64}" width="56" />'
            if logo_b64 else ""
        )
        st.markdown(
            f"""
            <div class="eva-login-brand">
                <div class="eva-brand-top">
                    {logo_html}
                    <h1>EVA Valle</h1>
                    <p>Inteligencia Agrícola Territorial</p>
                </div>
                <div class="eva-brand-quote">
                    "El dato oficial, al servicio de quien siembra"
                </div>
                <div>
                    <div class="eva-brand-stats">
                        <span>42 municipios</span>
                        <span>78 cultivos</span>
                        <span>2019–2025</span>
                    </div>
                    <div class="eva-brand-version" style="margin-top:.8rem;">
                        Plataforma analítica · UPRA · EVA 2019-2025 &nbsp;·&nbsp; v3.0
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_form:
        st.markdown('<div class="eva-login-form">', unsafe_allow_html=True)
        st.markdown(
            "<h2>Acceso a la plataforma</h2>"
            "<p class='eva-login-sub'>Ingresa tus credenciales institucionales.</p>",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            entrar = st.form_submit_button("Ingresar", use_container_width=True)
        if entrar:
            u = sanitize_username(usuario)
            p = sanitize_password(password)
            if not u or not p:
                st.error("⚠️ Usuario o contraseña invalidos.")
            elif not login_limiter.is_allowed(u):
                st.error("⚠️ Demasiados intentos fallidos. Espera 15 minutos.")
            elif verify(u, p):
                login_limiter.reset(u)
                login(u)
                st.rerun()
            else:
                st.error("⛔ Usuario o contraseña incorrectos.")
        st.markdown(
            "<div class='eva-login-security'>🔒 Conexión protegida · datos oficiales UPRA</div>"
            "<div class='eva-login-footer'>EVA Valle v3.0 · Valle del Cauca, Colombia</div>",
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
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

    lineas = APP.read_text(encoding="utf-8").splitlines(keepends=True)

    # Localizar inicio de la funcion
    inicio = next((i for i, l in enumerate(lineas)
                   if l.startswith("def render_login(")), None)
    if inicio is None:
        print("[ERROR] def render_login no encontrada")
        return 1

    # Escaneo por indentacion: el cuerpo = lineas vacias o indentadas
    fin = inicio + 1
    while fin < len(lineas) and (lineas[fin].strip() == "" or lineas[fin][0] in " \t"):
        fin += 1

    cuerpo = "".join(lineas[inicio:fin])
    if "eva-login-wrap" in cuerpo:
        print("[SKIP] render_login ya tiene el diseno institucional")
        return 0

    # Pre-chequeo CRITICO: el flujo principal debe vivir DESPUES de la funcion
    resto = "".join(lineas[fin:])
    for token in ("st.stop()", "with st.sidebar", "current_role()",
                  "st.navigation(_build_navigation(role))"):
        if token not in resto:
            print(f"[ERROR] flujo principal incompleto despues de render_login: falta '{token}'")
            print("        NO reemplazo: primero restaura el gate de auth (rollback .bak)")
            return 1

    # Reemplazo quirurgico: solo [inicio:fin)
    nuevas = NUEVO.splitlines(keepends=True)
    if not nuevas[-1].endswith("\n"):
        nuevas[-1] += "\n"
    lineas[inicio:fin] = nuevas + ["\n"]
    texto_nuevo = "".join(lineas)

    # Verificaciones estructurales post-reemplazo (en memoria, antes de escribir)
    if texto_nuevo.count("def render_login(") != 1:
        print("[ERROR] quedo mas de un def render_login")
        return 1
    for token in ("st.stop()", "with st.sidebar", "current_role()"):
        if token not in texto_nuevo:
            print(f"[ERROR] se perdio '{token}' en el reemplazo")
            return 1

    bak = APP.with_suffix(".py.bak")
    shutil.copy2(APP, bak)
    APP.write_text(texto_nuevo, encoding="utf-8")
    print(f"[OK] render_login reemplazado (lineas {inicio+1}-{fin}) | backup: {bak.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(APP)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, APP)
        audit("AUD-UI-008", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-008", "OK", "render_login institucional v2 (escaneo por indentacion)")
    print("[OK] AUD-UI-008 v2 aplicado y compilado")
    return 0


if __name__ == "__main__":
    sys.exit(main())