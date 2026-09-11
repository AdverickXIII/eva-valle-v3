"""AUD-UI-015: gate interno de rol admin en 5_Auditoria.py y 6_Configuracion.py.
Inserta import de auth + chequeo is_authenticated/current_role al inicio de main().
Defensa en profundidad: la pagina se protege sola aunque el filtro de navegacion falle.
Fail-safe: pre-chequeos, backups, py_compile, rollback, auditoria JSONL.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"
OBJETIVOS = [RAIZ / "ui" / "pages" / "5_Auditoria.py",
             RAIZ / "ui" / "pages" / "6_Configuracion.py"]

IMPORT_LINE = "from ui.services.auth import current_role, is_authenticated\n"

GATE = ('    if not is_authenticated() or current_role() != "admin":\n'
        '        st.error("⛔ Acceso restringido: requiere rol de administrador.")\n'
        '        st.stop()\n')


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def procesar(ruta):
    """Devuelve el texto nuevo, None si ya tiene gate, False si fallo."""
    lineas = ruta.read_text(encoding="utf-8").splitlines(keepends=True)
    if any("current_role" in l for l in lineas):
        print(f"[SKIP] {ruta.name} ya tiene gate interno")
        return None

    i_imp = next((i for i, l in enumerate(lineas)
                  if l.strip() == "from ui.services.error_handler import run_safe"), None)
    if i_imp is None:
        print(f"[ERROR] {ruta.name}: ancla de import run_safe no encontrada")
        return False

    i_main = next((i for i, l in enumerate(lineas)
                   if l.startswith("def main()")), None)
    if i_main is None:
        print(f"[ERROR] {ruta.name}: def main() no encontrada")
        return False

    lineas.insert(i_main + 1, GATE)      # gate como 1a instruccion de main()
    lineas.insert(i_imp + 1, IMPORT_LINE)  # import tras run_safe
    nuevo = "".join(lineas)

    for tok in ("is_authenticated()", 'current_role() != "admin"', "st.stop()",
                "from ui.services.auth import"):
        if tok not in nuevo:
            print(f"[ERROR] {ruta.name}: falta '{tok}' tras insertar")
            return False
    return nuevo


def main():
    resultados = {}
    for ruta in OBJETIVOS:
        if not ruta.is_file():
            print(f"[ERROR] no existe {ruta}")
            return 1
        r = procesar(ruta)
        if r is False:
            return 1
        resultados[ruta] = r

    pendientes = {r: t for r, t in resultados.items() if t is not None}
    if not pendientes:
        print("[SKIP] ambas paginas ya tienen gate (nada que hacer)")
        return 0

    backups = {}
    for ruta, texto in pendientes.items():
        bak = ruta.with_suffix(".py.bak")
        shutil.copy2(ruta, bak)
        backups[ruta] = bak
        ruta.write_text(texto, encoding="utf-8")
        print(f"[OK] {ruta.name}: gate admin insertado | backup: {bak.name}")

    for ruta in pendientes:
        r = subprocess.run([sys.executable, "-m", "py_compile", str(ruta)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            for r2, b2 in backups.items():
                shutil.copy2(b2, r2)
            audit("AUD-UI-015", "ROLLBACK", r.stderr[:300])
            print(f"[ERROR] sintaxis invalida en {ruta.name}, revirtiendo todo")
            return 1

    audit("AUD-UI-015", "OK", f"gates admin en: {[r.name for r in pendientes]}")
    print("[OK] AUD-UI-015 aplicado y compilado")
    return 0


if __name__ == "__main__":
    sys.exit(main())