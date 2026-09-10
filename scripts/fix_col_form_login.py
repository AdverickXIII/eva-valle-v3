"""AUD-UI-010: reemplaza el bloque with col_form: de render_login() por la version
sin <h2> (evita ancla automatica de Streamlit) con encabezado via <div> estilizado.
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

NUEVO_COL_FORM = '''    with col_form:
        st.markdown(
            "<div style='margin-bottom:1.5rem;'>"
            "<div style='font-size:1.3rem; font-weight:700; color:var(--eva-text); margin-bottom:.3rem;'>"
            "Acceso a la plataforma</div>"
            "<p class='eva-login-sub' style='margin:0;'>Ingresa tus credenciales institucionales.</p>"
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


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    lineas = APP.read_text(encoding="utf-8").splitlines(keepends=True)

    i = next((idx for idx, l in enumerate(lineas)
              if l.strip() == "with col_form:"), None)
    if i is None:
        print("[ERROR] bloque 'with col_form:' no encontrado en app.py")
        return 1

    # Idempotencia: el marcador nuevo es el div estilizado del encabezado
    texto = "".join(lineas)
    if "Acceso a la plataforma</div>" in texto and "<h2>Acceso a la plataforma</h2>" not in texto:
        print("[SKIP] col_form ya tiene la version sin <h2>")
        return 0
    if "<h2>Acceso a la plataforma</h2>" not in texto:
        print("[ERROR] no encuentro el <h2> esperado ni el marcador nuevo; nada tocado")
        return 1

    # Fin de la funcion: primera linea no vacia en columna 0
    fin = i + 1
    while fin < len(lineas) and (lineas[fin].strip() == "" or lineas[fin][0] in " \t"):
        fin += 1

    nuevas = NUEVO_COL_FORM.splitlines(keepends=True)
    if not nuevas[-1].endswith("\n"):
        nuevas[-1] += "\n"
    lineas[i:fin] = nuevas + ["\n"]
    texto_nuevo = "".join(lineas)

    for token in ("with col_brand:", 'st.form("login_form")', "<!-- CONTACTO_V2 -->",
                  "Acceso a la plataforma</div>"):
        if token not in texto_nuevo:
            print(f"[ERROR] se perdio '{token}' en el reemplazo")
            return 1
    if "<h2>Acceso" in texto_nuevo:
        print("[ERROR] sigue habiendo un <h2> de Acceso en app.py")
        return 1

    bak = APP.with_suffix(".py.bak")
    shutil.copy2(APP, bak)
    APP.write_text(texto_nuevo, encoding="utf-8")
    print(f"[OK] col_form reemplazado (lineas {i+1}-{fin}) | backup: {bak.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(APP)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, APP)
        audit("AUD-UI-010", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-010", "OK", "col_form sin <h2>: encabezado via div estilizado")
    print("[OK] AUD-UI-010 aplicado y compilado")
    return 0


if __name__ == "__main__":
    sys.exit(main())