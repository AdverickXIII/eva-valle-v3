"""AUD-UI-009: elimina el wrapper <div> falso del login (usaba st.columns directo)
y ajusta .eva-login-brand en style.css (min-height + sin .eva-login-wrap).
Fail-safe: pre-chequeos, backups, py_compile, rollback, auditoria JSONL.
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

NUEVO_BLOQUE = '''    col_brand, col_form = st.columns([1.1, 1], gap="small")

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
        st.markdown(
            "<div class='eva-login-form'>"
            "<h2>Acceso a la plataforma</h2>"
            "<p class='eva-login-sub'>Ingresa tus credenciales institucionales.</p>"
            "</div>",
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
'''

NUEVA_BRAND = '''.eva-login-brand {
    flex: 1.1;
    background: linear-gradient(135deg, rgba(15,50,35,0.92) 0%, rgba(15,50,35,0.55) 100%),
        var(--eva-login-bg, none) center / cover no-repeat;
    color: #fff;
    padding: 3rem 2.5rem;
    min-height: 480px;
    border-radius: var(--eva-radius);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    # ---------- app.py ----------
    lineas = APP.read_text(encoding="utf-8").splitlines(keepends=True)
    i = next((idx for idx, l in enumerate(lineas)
              if "eva-login-wrap" in l and "st.markdown" in l), None)
    if i is None:
        if "col_brand, col_form" in "".join(lineas):
            print("[SKIP] app.py ya tiene el login sin wrapper")
            app_ok = True
            texto_app = None
        else:
            print("[ERROR] ancla eva-login-wrap no encontrada y no hay columnas: nada que hacer")
            return 1
    else:
        # Fin de la funcion: primera linea no vacia en columna 0 despues del ancla
        fin = i + 1
        while fin < len(lineas) and (lineas[fin].strip() == "" or lineas[fin][0] in " \t"):
            fin += 1
        nuevas = NUEVO_BLOQUE.splitlines(keepends=True)
        if not nuevas[-1].endswith("\n"):
            nuevas[-1] += "\n"
        lineas[i:fin] = nuevas + ["\n"]
        texto_app = "".join(lineas)
        for token in ("with col_brand:", "with col_form:", 'st.form("login_form")',
                      "<!-- CONTACTO_V2 -->"):
            if token not in texto_app:
                print(f"[ERROR] se perdio '{token}' en el reemplazo")
                return 1
        if "eva-login-wrap" in texto_app:
            print("[ERROR] quedo alguna referencia a eva-login-wrap en app.py")
            return 1
        app_ok = False

    # ---------- style.css ----------
    css = CSS.read_text(encoding="utf-8")
    if "min-height: 480px" in css and ".eva-login-wrap" not in css:
        print("[SKIP] style.css ya ajustado")
        css_nuevo = None
    else:
        css_nuevo = re.sub(r"\.eva-login-wrap\s*\{[^}]*\}\s*\n?", "", css)
        css_nuevo, n = re.subn(r"\.eva-login-brand\s*\{[^}]*\}", NUEVA_BRAND, css_nuevo, count=1)
        if n != 1:
            print("[ERROR] no se encontro la regla .eva-login-brand base para reemplazar")
            return 1
        if ".eva-login-wrap" in css_nuevo or "min-height: 480px" not in css_nuevo:
            print("[ERROR] verificacion CSS fallo (wrap sigue o min-height no quedo)")
            return 1

    # ---------- Escritura con backups ----------
    if texto_app is not None:
        bak = APP.with_suffix(".py.bak")
        shutil.copy2(APP, bak)
        APP.write_text(texto_app, encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "py_compile", str(APP)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            shutil.copy2(bak, APP)
            audit("AUD-UI-009", "ROLLBACK", r.stderr[:300])
            print(f"[ERROR] sintaxis invalida en app.py, revirtiendo: {r.stderr[:300]}")
            return 1
        print(f"[OK] app.py: wrapper eliminado (lineas {i+1}-{fin}) | backup {bak.name}")
    if css_nuevo is not None:
        bakc = CSS.with_suffix(".css.bak")
        shutil.copy2(CSS, bakc)
        CSS.write_text(css_nuevo, encoding="utf-8")
        print(f"[OK] style.css: brand con min-height + .eva-login-wrap eliminada | backup {bakc.name}")

    audit("AUD-UI-009", "OK", "login sin wrapper div + css brand ajustado")
    print("[OK] AUD-UI-009 aplicado")
    print("Siguiente: streamlit run app.py -> ventana privada -> login de 2 paneles")
    return 0


if __name__ == "__main__":
    sys.exit(main())