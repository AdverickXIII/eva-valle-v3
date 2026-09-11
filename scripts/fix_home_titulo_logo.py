"""AUD-UI-016: reemplaza st.title() con emoji por logo real + titulo con .eva-header
y subtitulo con color muted. Mejora coherencia visual (mismo logo que sidebar/login).
Fail-safe: pre-chequeos, backup, py_compile, rollback, auditoria JSONL.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HOME = RAIZ / "ui" / "pages" / "0_Home.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

VIEJO = '''st.title("\\U0001F33E EVA Agricola 2019-2025 - Valle del Cauca")
st.markdown("Dashboard analitico de produccion agricola basado en datos de la UPRA.")'''

NUEVO = '''_logo_path = _Path(__file__).parent.parent / "assets" / "img" / "logo.png"
_logo_html = ""
if _logo_path.exists():
    _logo_b64 = _b64.b64encode(_logo_path.read_bytes()).decode()
    _logo_html = f'<img src="data:image/png;base64,{_logo_b64}" width="42" style="vertical-align:middle; margin-right:.6rem;" />'

st.markdown(
    f"""<div class="eva-header" style="border-bottom:none; margin-bottom:.2rem;">
    <h1 style="display:flex; align-items:center; gap:.5rem;">
        {_logo_html}EVA Agrícola 2019-2025 - Valle del Cauca
    </h1>
    </div>""",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="color:var(--eva-muted); margin-top:0;">'
    'Dashboard analítico de producción agrícola basado en datos de la UPRA.</p>',
    unsafe_allow_html=True,
)'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    texto = HOME.read_text(encoding="utf-8")

    # Idempotencia
    if "eva-header" in texto and "_logo_path" in texto and "\\U0001F33E" not in texto:
        print("[SKIP] titulo ya usa logo real + .eva-header")
        return 0

    # Pre-chequeo: ancla exacta, una sola vez
    n = texto.count(VIEJO)
    if n != 1:
        print(f"[ERROR] bloque de titulo encontrado {n} veces (esperaba 1)")
        return 1

    # Reemplazo
    texto_nuevo = texto.replace(VIEJO, NUEVO, 1)

    # Verificaciones en memoria
    if "\\U0001F33E" in texto_nuevo:
        print("[ERROR] emoji 🌾 sigue presente en app.py")
        return 1
    for token in ("eva-header", "_logo_path", "logo.png", "var(--eva-muted)"):
        if token not in texto_nuevo:
            print(f"[ERROR] falta '{token}' tras el reemplazo")
            return 1
    if "EVA Agrícola 2019-2025 - Valle del Cauca" not in texto_nuevo:
        print("[ERROR] titulo corregido no quedo")
        return 1

    bak = HOME.with_suffix(".py.bak")
    shutil.copy2(HOME, bak)
    HOME.write_text(texto_nuevo, encoding="utf-8")
    print(f"[OK] titulo con logo real insertado | backup: {bak.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(HOME)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, HOME)
        audit("AUD-UI-016", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-016", "OK", "Home con logo real + titulo .eva-header + subtitulo muted")
    print("[OK] AUD-UI-016 aplicado y compilado")
    return 0


if __name__ == "__main__":
    sys.exit(main())