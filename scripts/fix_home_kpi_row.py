"""AUD-UI-004: 0_Home.py adopta la fila KPI del sistema de diseno.
Reemplaza titulo+markdown por import + titulo + render_kpi_row + separador.
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
HOME = RAIZ / "ui" / "pages" / "0_Home.py"
MC = RAIZ / "ui" / "components" / "metrics_cards.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    if not HOME.is_file():
        print(f"[ERROR] no existe {HOME}")
        return 1

    # --- Pre-chequeo 1 y 2: componente existe y firma compatible ----------
    if not MC.is_file():
        print(f"[ERROR] no existe {MC}: el import del bloque nuevo fallaria")
        return 1
    mc = MC.read_text(encoding="utf-8")
    if "def render_kpi_row" not in mc:
        print("[ERROR] metrics_cards.py no define render_kpi_row")
        return 1
    for token in ("cols", "icon", "label", "value"):
        if token not in mc:
            print(f"[ERROR] render_kpi_row no parece aceptar '{token}'; revisa su firma")
            return 1
    firma = [l.strip() for l in mc.splitlines()
             if l.strip().startswith("def render_kpi_row")]
    print(f"[OK] componente: {firma[0] if firma else '?'}")
    if "eva-metric-card" not in mc:
        print("[WARN] metrics_cards no emite .eva-metric-card: el CSS v2 no lo vestira")

    # --- Pre-chequeo 3 y 4: bloque viejo unico + idempotencia -------------
    viejo = re.compile(
        r'st\.title\([^\n]*EVA Agricola 2019-2025[^\n]*\)\n'
        r'st\.markdown\(\n\s*"Dashboard analitico.*?\)\n'
        r'st\.markdown\("---"\)',
        re.S,
    )
    texto = HOME.read_text(encoding="utf-8")
    if "render_kpi_row" in texto:
        print("[SKIP] 0_Home.py ya tiene render_kpi_row (cambio ya aplicado)")
        return 0
    if len(viejo.findall(texto)) != 1:
        print(f"[ERROR] bloque viejo no encontrado exactamente 1 vez; nada tocado")
        return 1

    nuevo = r'''from ui.components.metrics_cards import render_kpi_row

st.title("\U0001F33E EVA Agricola 2019-2025 - Valle del Cauca")
st.markdown("Dashboard analitico de produccion agricola basado en datos de la UPRA.")

render_kpi_row([
    {"label": "Municipios", "value": "42", "icon": "\U0001F4CD"},
    {"label": "Cultivos", "value": "78", "icon": "\U0001F33F"},
    {"label": "Años de datos", "value": "7", "icon": "\U0001F4C5"},
], cols=3)

st.markdown("---")'''

    # --- Backup + reemplazo exacto ----------------------------------------
    bak = HOME.with_suffix(".py.bak")
    shutil.copy2(HOME, bak)
    HOME.write_text(viejo.sub(lambda m: nuevo, texto, count=1), encoding="utf-8")
    print(f"[OK] bloque reemplazado | backup: {bak.name}")

    # --- py_compile + rollback --------------------------------------------
    r = subprocess.run([sys.executable, "-m", "py_compile", str(HOME)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, HOME)
        audit("AUD-UI-004", "ROLLBACK", r.stderr[:300])
        print(f"[ERROR] sintaxis invalida, revirtiendo: {r.stderr[:300]}")
        return 1

    audit("AUD-UI-004", "OK", "0_Home.py: fila KPI render_kpi_row")
    print("[OK] AUD-UI-004 aplicado y compilado")
    print("Siguiente: streamlit run app.py -> verificar 3 tarjetas KPI en portada")
    return 0


if __name__ == "__main__":
    sys.exit(main())