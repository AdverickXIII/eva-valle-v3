"""AUD-UI-012 v3: Alternativa A de soporte en login (linea contextual centrada).
Tokens de verificacion: 'eva-login-support' SIN punto para app.py (atributo class),
'.eva-login-support {' CON punto solo para style.css (selector).
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

NUEVO_MARKDOWN = (
    '    st.markdown(\n'
    '        "<div class=\'eva-login-support\'>"\n'
    '        "¿Problemas para ingresar? "\n'
    '        "<a href=\'mailto:moises.zuniga.grueso@gmail.com?subject=Acceso%20EVA%20Valle%20v3.0\'>Contacta a soporte</a>"\n'
    '        " · <a href=\'tel:+573167197764\'>+57 316 719 7764</a>"\n'
    '        "</div>",\n'
    '        unsafe_allow_html=True,\n'
    '    )\n'
)

NUEVO_CSS = '''/* ---------- Soporte institucional en login (Paso 23) ---------- */
.eva-login-support {
    text-align: center;
    font-size: .78rem;
    color: var(--eva-muted);
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--eva-border);
}
.eva-login-support a { color: var(--eva-info); text-decoration: none; font-weight: 500; }
.eva-login-support a:hover { text-decoration: underline; }
'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    # Auto-chequeo con token SIN punto (como aparece en el atributo class)
    for token in ("eva-login-support", "st.markdown(", "unsafe_allow_html"):
        if token not in NUEVO_MARKDOWN:
            print(f"[ERROR] NUEVO_MARKDOWN corrupto en este script: falta '{token}'")
            return 1

    texto = APP.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    if "eva-login-support" in texto and ".eva-login-support {" in css and "CONTACTO_V2" not in texto:
        print("[SKIP] Alternativa A ya aplicada")
        return 0

    # 1. Limpiar artefactos de B y el widget flotante
    n_b = len(re.findall(r'<div class="eva-brand-contact">', texto))
    texto = re.sub(r'[ \t]*<div class="eva-brand-contact">.*?</div>\n?', '', texto, flags=re.S)
    n_f = len(re.findall(r'<!-- CONTACTO_V2 -->', texto))
    texto = re.sub(
        r'\s*st\.markdown\(\s*"""\s*<!-- CONTACTO_V2 -->\s*<div id="eva-contacto">.*?"""'
        r'\s*,\s*unsafe_allow_html=True,\s*\)',
        '\n', texto, flags=re.S)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    print(f"[INFO] artefactos Alt B eliminados: {n_b} | widgets flotantes eliminados: {n_f}")

    for fantasma in ("eva-brand-contact", "CONTACTO_V2", 'id="eva-contacto"'):
        if fantasma in texto:
            print(f"[ERROR] quedo '{fantasma}' en app.py tras limpiar")
            return 1

    # 2. Insertar linea de soporte al final de render_login
    if "eva-login-support" not in texto:
        lineas = texto.splitlines(keepends=True)
        i = next((k for k, l in enumerate(lineas)
                  if l.strip().startswith("col_brand, col_form = st.columns(")), None)
        if i is None:
            print("[ERROR] ancla de columnas no encontrada")
            return 1
        fin = i + 1
        while fin < len(lineas) and (lineas[fin].strip() == "" or lineas[fin][0] in " \t"):
            fin += 1
        while fin > i and lineas[fin - 1].strip() == "":
            fin -= 1
        print(f"[INFO] ancla en linea {i+1} | fin de funcion en linea {fin}")
        lineas[fin:fin] = ["\n"] + NUEVO_MARKDOWN.splitlines(keepends=True)
        texto = "".join(lineas)

    for token in ("with col_brand:", "with col_form:", 'st.form("login_form")',
                  "eva-login-support"):
        if token not in texto:
            print(f"[ERROR] falta '{token}' en app.py tras el cambio")
            return 1

    # 3. CSS: retirar reglas muertas y agregar .eva-login-support
    css = re.sub(r'\.eva-brand-contact(?:\s+a(?::hover)?)?\s*\{[^}]*\}\s*\n?', '', css, flags=re.S)
    css = re.sub(r'#eva-contacto(?:\s+a(?::hover)?)?\s*\{[^}]*\}\s*\n?', '', css, flags=re.S)
    if ".eva-login-support {" not in css:
        css = css.rstrip() + "\n\n" + NUEVO_CSS
    if "#eva-contacto" in css or ".eva-brand-contact" in css or ".eva-login-support {" not in css:
        print("[ERROR] verificacion de style.css fallo")
        return 1

    # 4. Escritura con backups
    bak_app = APP.with_suffix(".py.bak")
    bak_css = CSS.with_suffix(".css.bak")
    shutil.copy2(APP, bak_app)
    shutil.copy2(CSS, bak_css)
    APP.write_text(texto, encoding="utf-8")
    CSS.write_text(css, encoding="utf-8")
    print(f"[OK] app.py y style.css escritos | backups: {bak_app.name}, {bak_css.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(APP)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak_app, APP)
        shutil.copy2(bak_css, CSS)
        audit("AUD-UI-012", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-012", "OK", "Alternativa A aplicada (v3 tokens corregidos)")
    print("[OK] AUD-UI-012 v3 aplicado y compilado")
    return 0


if __name__ == "__main__":
    sys.exit(main())