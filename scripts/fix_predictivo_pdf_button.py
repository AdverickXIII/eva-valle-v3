"""AUD-UI-023: hotfix NameError 'res' en boton PDF de 4_Predictivo + formato Diferencia.
H1: build_predictivo_pdf(..., res, ...) -> res_ensemble (res dejo de existir en AUD-UI-022).
H2: columna Diferencia con separador de miles (:+,.0f) (cosmetico, visto en captura).
Fail-safe: anclas unicas, backup, py_compile, rollback, autotest de cero refs a 'res' suelto.
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
UI = RAIZ / "ui" / "pages" / "4_Predictivo.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

VIEJO_PDF_BTN = 'data=build_predictivo_pdf(cultivo, muni, serie, res, horizonte),'
NUEVO_PDF_BTN = 'data=build_predictivo_pdf(cultivo, muni, serie, res_ensemble, horizonte),'

VIEJO_DIF = ('"Diferencia": f"{res_ensemble[\'escenarios\'][\'tendencial\'][i] - '
             'res_estable[\'escenarios\'][\'tendencial\'][i]:+.0f}",')
NUEVO_DIF = ('"Diferencia": f"{res_ensemble[\'escenarios\'][\'tendencial\'][i] - '
             'res_estable[\'escenarios\'][\'tendencial\'][i]:+,.0f}",')


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-UI-023", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def main():
    try:
        t_ui = UI.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer 4_Predictivo.py: {e}")

    if VIEJO_PDF_BTN not in t_ui and NUEVO_PDF_BTN in t_ui:
        print("[SKIP] AUD-UI-023 ya aplicado")
        return 0

    for ancla, nombre in ((VIEJO_PDF_BTN, "boton PDF"), (VIEJO_DIF, "columna Diferencia")):
        if t_ui.count(ancla) != 1:
            return fail(f"ancla {nombre}: {t_ui.count(ancla)} coincidencias (esperaba 1)")

    t_ui_n = t_ui.replace(VIEJO_PDF_BTN, NUEVO_PDF_BTN, 1).replace(VIEJO_DIF, NUEVO_DIF, 1)

    # Autotest estatico: ninguna referencia suelta a 'res' debe quedar en la pagina
    refs = re.findall(r"\bres\b", t_ui_n)
    if refs:
        return fail(f"quedan {len(refs)} referencias sueltas a 'res' tras el parche")

    bak = UI.with_suffix(".py.bak")
    try:
        shutil.copy2(UI, bak)
        UI.write_text(t_ui_n, encoding="utf-8")
        print(f"[OK] 4_Predictivo.py actualizado | backup: {bak.name}")
    except Exception as e:
        return fail(f"fallo de escritura: {e}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(UI)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, UI)
        audit("AUD-UI-023", "ROLLBACK", r.stderr[:200])
        return fail(f"sintaxis invalida, revirtiendo: {r.stderr[:200]}")

    audit("AUD-UI-023", "OK", "boton PDF con res_ensemble + formato Diferencia")
    print("[OK] AUD-UI-023 aplicado y compilado; cero referencias sueltas a 'res'")
    print("Siguiente: commit + reboot + clic en 'Descargar proyeccion (PDF)'")
    return 0


if __name__ == "__main__":
    sys.exit(main())