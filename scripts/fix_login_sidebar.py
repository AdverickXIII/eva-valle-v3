"""AUD-UI-002: contacto v2 (correo + telefono + WhatsApp) en la pantalla de login.

Correcciones definitivas:
- mailto HORNEADO: {CONTACTO_EMAIL} con una sola llave en el f-string del hotfix,
  para que se sustituya aqui y quede como texto estatico en app.py.
- re.sub del telefono: string plano (no raw) para que las comillas no queden escapadas.
- Deteccion del bloque viejo con {CONTACTO_EMAIL} literal como aguja de respaldo.
- Datos reales del usuario fijados.

Estandar: backup .bak, py_compile con rollback, marcador, fallo seguro, exit codes,
log JSONL en logs/audit_hotfix.jsonl.
"""
import json
import py_compile
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

MARCADOR = "<!-- CONTACTO_V2 -->"

CONTACTO_EMAIL = "moises.zuniga.grueso@gmail.com"
CONTACTO_TELEFONO = "+57 3167197764"
DIGITOS_MINIMOS = 12


def _resolver_app_path() -> Path:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from eva_config import EVA_PROJECT_ROOT  # type: ignore
        return Path(EVA_PROJECT_ROOT) / "app.py"
    except Exception:
        return Path(__file__).resolve().parent.parent / "app.py"


APP = _resolver_app_path()
LOG_PATH = APP.parent / "logs" / "audit_hotfix.jsonl"


def _audit(evento: str, estado: str, detalle: str = "") -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        registro = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "evento": evento, "estado": estado, "detalle": detalle,
            "archivo": str(APP), "script": "fix_login_sidebar.py",
        }
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[WARN] no se pudo escribir el log: {e}")


def _fin_llamada(c: str, start: int) -> int:
    depth, i, n = 0, start, len(c)
    while i < n:
        if c.startswith('"""', i) or c.startswith("'''", i):
            q = c[i:i + 3]
            j = c.find(q, i + 3)
            if j == -1:
                return -1
            i = j + 3
            continue
        if c[i] == '"':
            j = i + 1
            while j < n:
                if c[j] == "\\":
                    j += 2
                    continue
                if c[j] == '"':
                    break
                j += 1
            if j >= n:
                return -1
            i = j + 1
            continue
        if c[i] == "'":
            j = i + 1
            while j < n:
                if c[j] == "\\":
                    j += 2
                    continue
                if c[j] == "'":
                    break
                j += 1
            if j >= n:
                return -1
            i = j + 1
            continue
        if c[i] == "(":
            depth += 1
        elif c[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def localizar_bloque(c: str):
    """Busca el bloque de contacto a reemplazar con multiples estrategias."""
    # Estrategia A: comentario de cabecera (incluye el comentario en el reemplazo)
    for comentario in ("# Contacto institucional discreto", "# Contacto institucional"):
        pos = c.find(comentario)
        if pos != -1:
            start = c.find("st.markdown(", pos)
            if start != -1:
                fin = _fin_llamada(c, start)
                if fin != -1:
                    return pos, fin
    # Estrategia B: agujas de texto dentro del st.markdown
    for aguja in ("Cont&#225;ctenos", "Contáctenos", "Contactenos",
                  "Problemas de acceso", "eva-contacto",
                  "mailto:{CONTACTO_EMAIL}", CONTACTO_EMAIL):
        pos = c.find(aguja)
        while pos != -1:
            start = c.rfind("st.markdown(", 0, pos)
            if start != -1:
                fin = _fin_llamada(c, start)
                if fin != -1 and pos < fin:
                    return start, fin
            pos = c.find(aguja, pos + 1)
    return -1, -1


def snippet_contacto_v2(indent: int) -> str:
    """Bloque a inyectar. Correo y telefono HORNEADOS (una sola llave en f-string)."""
    digits = re.sub(r"\D", "", CONTACTO_TELEFONO)
    pad = " " * indent
    cuerpo = f'''# Contacto institucional (v2): correo + telefono + WhatsApp
st.markdown(
    """
    {MARCADOR}
    <style>
    #eva-contacto {{
        position: fixed; bottom: 14px; left: 14px; z-index: 999;
        font-size: 0.85rem; line-height: 1.6; background: rgba(255,255,255,0.95);
        padding: 8px 12px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    #eva-contacto a {{ color: #0f6cbd; text-decoration: none; font-weight: 600; }}
    #eva-contacto a:hover {{ text-decoration: underline; }}
    </style>
    <div id="eva-contacto">
      📧 <a href="mailto:{CONTACTO_EMAIL}?subject=Acceso%20EVA%20Valle%20v3.0">Escríbenos</a><br>
      📞 <a href="tel:+{digits}">{CONTACTO_TELEFONO}</a><br>
      💬 <a href="https://wa.me/{digits}" target="_blank">WhatsApp</a>
    </div>
    """,
    unsafe_allow_html=True,
)'''
    return "\n".join(pad + ln if ln else ln for ln in cuerpo.splitlines())


def sincronizar_constantes(c: str) -> str:
    """Actualiza/inserta CONTACTO_EMAIL y CONTACTO_TELEFONO en app.py.
    Usa string plano (no raw) para evitar comillas escapadas."""
    c = re.sub(r'CONTACTO_EMAIL\s*=\s*"[^"]*"',
               f'CONTACTO_EMAIL = "{CONTACTO_EMAIL}"', c, count=1)
    if not re.search(r"CONTACTO_TELEFONO\s*=", c):
        # IMPORTANTE: string plano para que las comillas NO queden escapadas
        reemplazo = f'CONTACTO_TELEFONO = "{CONTACTO_TELEFONO}"'
        c = re.sub(r'(CONTACTO_EMAIL\s*=\s*"[^"]*")',
                   r"\1\n" + reemplazo, c, count=1)
    else:
        c = re.sub(r'CONTACTO_TELEFONO\s*=\s*"[^"]*"',
                   f'CONTACTO_TELEFONO = "{CONTACTO_TELEFONO}"', c, count=1)
    return c


def main() -> int:
    digits = re.sub(r"\D", "", CONTACTO_TELEFONO)
    if 0 < len(digits) < DIGITOS_MINIMOS:
        print(f"[WARN] telefono con {len(digits)} digitos (< {DIGITOS_MINIMOS})")

    if not APP.exists():
        print(f"[ERROR] no existe {APP}")
        _audit("AUD-UI-002-001", "ERROR", f"app.py no encontrado en {APP}")
        return 1

    c = APP.read_text(encoding="utf-8")
    if MARCADOR in c:
        print("[SKIP] bloque CONTACTO_V2 ya presente en app.py")
        _audit("AUD-UI-002-002", "SKIP", "marcador ya presente")
        return 0

    c = sincronizar_constantes(c)
    start, fin = localizar_bloque(c)
    if start == -1:
        print("[ERROR] no se encontro el bloque de contacto")
        _audit("AUD-UI-002-003", "ERROR", "bloque no localizado")
        return 1
    indent = start - (c.rfind("\n", 0, start) + 1)

    backup = APP.with_suffix(".py.bak")
    shutil.copy2(APP, backup)

    try:
        nuevo = c[:start] + snippet_contacto_v2(indent) + c[fin:]
        APP.write_text(nuevo, encoding="utf-8")
        py_compile.compile(str(APP), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"[ERROR] sintaxis invalida, revirtiendo: {e}")
        shutil.copy2(backup, APP)
        _audit("AUD-UI-002-004", "ERROR", f"sintaxis invalida: {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] fallo inesperado, revirtiendo: {e}")
        shutil.copy2(backup, APP)
        _audit("AUD-UI-002-005", "ERROR", f"fallo inesperado: {e}")
        return 1

    print("[OK] Contactenos v2: correo horneado + telefono + WhatsApp en el login")
    print(f"[INFO] backup: {backup.name}")
    _audit("AUD-UI-002-006", "OK", "bloque v2 insertado")
    return 0


if __name__ == "__main__":
    sys.exit(main())