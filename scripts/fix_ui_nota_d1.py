"""AUD-UI-025: nota metodologica D1 (quiebre 2021-2022) en UI y PDF.
H0: nuevo modulo core/analytics/calidad_datos.py (flag por serie + nota panel).
H1: import en 4_Predictivo.py.
H2: warning por serie flaggeada tras construir la serie anual.
H3: caption panel con NOTA_PANEL_D1 tras el caption de TimesFM.
H4: el boton PDF pasa nota_quiebre.
H5: predictivo_pdf acepta nota_quiebre e imprime parrafos D1.
Fail-safe: anclas unicas, backup, py_compile, rollback, autotests.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
UI = RAIZ / "ui" / "pages" / "4_Predictivo.py"
PDF = RAIZ / "core" / "reports" / "predictivo_pdf.py"
CD = RAIZ / "core" / "analytics" / "calidad_datos.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

MODULO_CALIDAD = '''"""AUD-UI-025: calidad de datos D1 - quiebre de definicion 2021->2022.

Mismos umbrales que el harness de registro (eva_baseline_v3.Config):
area estable < 15% y salto de rendimiento > 40% (en valor absoluto).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

U_AREA = 15.0
U_SALTO = 40.0

NOTA_PANEL_D1 = (
    "Calidad de datos (D1): 79 series del panel (62 permanentes, 17 transitorios) "
    "muestran quiebre de definicion entre 2021 y 2022 (area estable con salto de "
    "rendimiento >40%), consistente con el cambio metodologico documentado por UPRA "
    "(de siembras del periodo a cosechas efectivas) que se filtra a permanentes en "
    "municipios especificos; 24 series aparecen y 13 desaparecen justo en ese corte, "
    "y el error de todos los modelos se concentra en 2021 (MASE naive 6.8 vs 0.25 en "
    "2025). Fuentes: UPRA-EVA, datos.gov.co, Observatorio Agropecuario y Pesquero "
    "del Valle del Cauca."
)


def flag_quiebre_2021_2022(serie_prod: pd.Series,
                           serie_area: pd.Series | None = None,
                           ano_pre: int = 2021, ano_post: int = 2022,
                           u_area: float = U_AREA, u_salto: float = U_SALTO):
    """Devuelve (flag, detalle). flag=True si area estable y rendimiento salta.
    Sin columna de area no se flaggea (no se puede verificar estabilidad)."""
    if ano_pre not in serie_prod.index or ano_post not in serie_prod.index:
        return False, ""
    p1, p2 = float(serie_prod.loc[ano_pre]), float(serie_prod.loc[ano_post])
    if p1 <= 0:
        return False, ""
    d_prod = (p2 - p1) / p1 * 100
    if serie_area is None:
        return False, ""
    if ano_pre not in serie_area.index or ano_post not in serie_area.index:
        return False, ""
    a1, a2 = float(serie_area.loc[ano_pre]), float(serie_area.loc[ano_post])
    if a1 <= 0 or a2 <= 0:
        return False, ""
    d_area = (a2 - a1) / a1 * 100
    r1, r2 = p1 / a1, p2 / a2
    if r1 <= 0:
        return False, ""
    d_rend = (r2 - r1) / r1 * 100
    flag = bool(abs(d_area) < u_area and abs(d_rend) > u_salto)
    detalle = (f"area {d_area:+.1f}%, rendimiento {d_rend:+.1f}%, "
               f"produccion {d_prod:+.1f}%") if flag else ""
    return flag, detalle
'''

ANCLA_IMPORT_UI = '''from core.analytics.forecast import (elegir_mejor, proyectar_con_ic,
                                      proyectar_estable_con_ic)'''
NUEVO_IMPORT_UI = '''from core.analytics.forecast import (elegir_mejor, proyectar_con_ic,
                                      proyectar_estable_con_ic)
from core.analytics.calidad_datos import NOTA_PANEL_D1, flag_quiebre_2021_2022'''

ANCLA_SERIE_UI = '''    # Serie anual
    serie = df_c.groupby("ano")["produccion_t"].sum().sort_index()
    if len(serie) < 4:
        st.error("Serie demasiado corta (se necesitan al menos 4 anos).")
        return'''
NUEVO_SERIE_UI = '''    # Serie anual
    serie = df_c.groupby("ano")["produccion_t"].sum().sort_index()
    if len(serie) < 4:
        st.error("Serie demasiado corta (se necesitan al menos 4 anos).")
        return

    # AUD-UI-025: flag de quiebre de definicion 2021-2022 para esta serie
    area_col = next((c for c in ("area_ha", "area_cosechada_ha", "area")
                     if c in df.columns), None)
    serie_area = (df_c.groupby("ano")[area_col].sum().sort_index()
                  if area_col else None)
    flag_quiebre, detalle_quiebre = flag_quiebre_2021_2022(serie, serie_area)
    if flag_quiebre:
        st.warning(
            f"**Quiebre de definicion 2021-2022 sin validar** en esta serie "
            f"({detalle_quiebre}). La fuente cambio de 'siembras del periodo' a "
            f"'cosechas efectivas' (UPRA); en cultivos permanentes el salto no esta "
            f"validado con la fuente. La proyeccion oficial usa el nivel "
            f"post-quiebre como piso honesto; interprete tendencias con cautela."
        )'''

ANCLA_CAPTION_UI = '''    st.caption(
        "TimesFM 2.5 (modelo fundacional, Google) fue evaluado en el mismo holdout "
        "y no supero al naive (WAPE mediano anual 17.3% vs 11.1%; semestral 39.5% "
        "vs 33.3%). Se documenta como resultado negativo en la auditoria."
    )'''
NUEVO_CAPTION_UI = '''    st.caption(
        "TimesFM 2.5 (modelo fundacional, Google) fue evaluado en el mismo holdout "
        "y no supero al naive (WAPE mediano anual 17.3% vs 11.1%; semestral 39.5% "
        "vs 33.3%). Se documenta como resultado negativo en la auditoria."
    )
    st.caption(NOTA_PANEL_D1)'''

ANCLA_PDF_BTN = 'data=build_predictivo_pdf(cultivo, muni, serie, res_ensemble, horizonte),'
NUEVO_PDF_BTN = ('data=build_predictivo_pdf(cultivo, muni, serie, res_ensemble,\n'
                 '                                   horizonte,\n'
                 '                                   nota_quiebre=(detalle_quiebre or None)),')

ANCLA_IMPORT_PDF = 'from core.analytics.forecast import proyectar_estable_con_ic'
NUEVO_IMPORT_PDF = ('from core.analytics.forecast import proyectar_estable_con_ic\n'
                    'from core.analytics.calidad_datos import NOTA_PANEL_D1')

ANCLA_FIRMA_PDF = 'def build_predictivo_pdf(cultivo, muni, serie, res, horizonte) -> bytes:'
NUEVO_FIRMA_PDF = ('def build_predictivo_pdf(cultivo, muni, serie, res, horizonte,\n'
                   '                         nota_quiebre: str | None = None) -> bytes:')

ANCLA_TIMESFM_PDF = '''        "pronostico: se documenta como resultado negativo en la auditoria.", body))'''
NUEVO_TIMESFM_PDF = '''        "pronostico: se documenta como resultado negativo en la auditoria.", body))
    story.append(Paragraph(NOTA_PANEL_D1, body))
    if nota_quiebre:
        story.append(Paragraph(
            "<b>Calidad de datos (D1) - esta serie:</b> presenta un quiebre de "
            f"definicion entre 2021 y 2022 ({nota_quiebre}) no validado con la "
            "fuente. La proyeccion oficial usa el nivel post-quiebre como piso "
            "honesto; interprete las tendencias con cautela.", body))'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-UI-025", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def rollback_or_fail(motivo, backups, creado):
    for ruta, bak in backups.items():
        try:
            shutil.copy2(bak, ruta)
        except Exception as e:
            audit("AUD-UI-025", "ROLLBACK_FALLIDO", f"{motivo} | {ruta.name}: {e}")
            return 1
    if creado and CD.exists():
        CD.unlink()
    audit("AUD-UI-025", "ROLLBACK", motivo)
    print(f"[ERROR] {motivo}; revirtiendo {len(backups)} archivos")
    return 1


def main():
    try:
        t_ui = UI.read_text(encoding="utf-8")
        t_pdf = PDF.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer archivos: {e}")

    if CD.exists() and "nota_quiebre" in t_pdf:
        print("[SKIP] AUD-UI-025 ya aplicado")
        return 0

    anclas = [(t_ui, ANCLA_IMPORT_UI, "ui: import forecast"),
              (t_ui, ANCLA_SERIE_UI, "ui: serie anual"),
              (t_ui, ANCLA_CAPTION_UI, "ui: caption TimesFM"),
              (t_ui, ANCLA_PDF_BTN, "ui: boton PDF"),
              (t_pdf, ANCLA_IMPORT_PDF, "pdf: import forecast"),
              (t_pdf, ANCLA_FIRMA_PDF, "pdf: firma"),
              (t_pdf, ANCLA_TIMESFM_PDF, "pdf: parrafo TimesFM")]
    for texto, ancla, nombre in anclas:
        if texto.count(ancla) != 1:
            return fail(f"ancla {nombre}: {texto.count(ancla)} coincidencias (esperaba 1)")

    creado = not CD.exists()
    t_ui_n = (t_ui.replace(ANCLA_IMPORT_UI, NUEVO_IMPORT_UI, 1)
                  .replace(ANCLA_SERIE_UI, NUEVO_SERIE_UI, 1)
                  .replace(ANCLA_CAPTION_UI, NUEVO_CAPTION_UI, 1)
                  .replace(ANCLA_PDF_BTN, NUEVO_PDF_BTN, 1))
    t_pdf_n = (t_pdf.replace(ANCLA_IMPORT_PDF, NUEVO_IMPORT_PDF, 1)
                    .replace(ANCLA_FIRMA_PDF, NUEVO_FIRMA_PDF, 1)
                    .replace(ANCLA_TIMESFM_PDF, NUEVO_TIMESFM_PDF, 1))

    backups = {}
    try:
        if creado:
            CD.write_text(MODULO_CALIDAD, encoding="utf-8")
            print(f"[OK] {CD.name} creado")
        for ruta, nuevo in ((UI, t_ui_n), (PDF, t_pdf_n)):
            bak = ruta.with_suffix(ruta.suffix + ".bak")
            shutil.copy2(ruta, bak)
            backups[ruta] = bak
            ruta.write_text(nuevo, encoding="utf-8")
            print(f"[OK] {ruta.name} actualizado | backup: {bak.name}")
    except Exception as e:
        return rollback_or_fail(f"fallo de escritura: {e}", backups, creado)

    for ruta in list(backups) + ([CD] if creado else []):
        r = subprocess.run([sys.executable, "-m", "py_compile", str(ruta)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return rollback_or_fail(f"sintaxis invalida en {ruta.name}: {r.stderr[:200]}",
                                    backups, creado)

    # ---------- Autotests ----------
    sys.path.insert(0, str(RAIZ))
    for name in list(sys.modules):
        if name == "core" or name.startswith("core."):
            del sys.modules[name]
    import pandas as pd
    from core.analytics.calidad_datos import flag_quiebre_2021_2022, NOTA_PANEL_D1

    # 1) Serie con quiebre (area quieta, rendimiento salta) -> flag True
    prod = pd.Series([41000.0, 30000.0, 30200.0, 77800.0, 77900.0, 77796.0, 81630.0],
                     index=list(range(2019, 2026)))
    area = pd.Series([1700.0, 1650.0, 1660.0, 1670.0, 1665.0, 1668.0, 1672.0],
                     index=list(range(2019, 2026)))
    flag, detalle = flag_quiebre_2021_2022(prod, area)
    if not flag or "rendimiento" not in detalle:
        return rollback_or_fail("autotest: serie con quiebre no flaggeada", backups, creado)
    print(f"[OK] autotest 1: quiebre detectado ({detalle})")

    # 2) Serie estable -> flag False
    plana = pd.Series([100.0, 98.0, 101.0, 100.0, 99.0, 100.0, 101.0],
                      index=list(range(2019, 2026)))
    if flag_quiebre_2021_2022(plana, area)[0]:
        return rollback_or_fail("autotest: serie estable flaggeada por error", backups, creado)
    print("[OK] autotest 2: serie estable sin flag")

    # 3) Sin columna de area -> sin flag (conservador)
    if flag_quiebre_2021_2022(prod, None)[0]:
        return rollback_or_fail("autotest: flag sin area (deberia ser conservador)", backups, creado)
    print("[OK] autotest 3: sin area no se flaggea")

    # 4) PDF con y sin nota se genera
    from core.analytics.forecast import proyectar_con_ic
    from core.reports.predictivo_pdf import build_predictivo_pdf
    res = proyectar_con_ic(prod, n_steps=3)
    for nota in (detalle, None):
        b = build_predictivo_pdf("Cultivo Prueba", "Muni Prueba", prod, res, 3,
                                 nota_quiebre=nota)
        if b[:4] != b"%PDF" or len(b) < 5000:
            return rollback_or_fail(f"autotest: PDF invalido con nota={nota}", backups, creado)
    print("[OK] autotest 4: PDF generado con y sin nota D1")

    if "NOTA_PANEL_D1" not in t_ui_n or "NOTA_PANEL_D1" not in t_pdf_n:
        return rollback_or_fail("autotest: nota panel ausente en UI o PDF", backups, creado)
    print("[OK] autotest 5: nota panel presente en UI y PDF")

    audit("AUD-UI-025", "OK", "nota D1 por serie + nota panel en UI y PDF")
    print("[OK] AUD-UI-025 aplicado, compilado y autotesteado")
    print("Siguiente: commit (incluye artefactos harness pendientes) + reboot")
    return 0


if __name__ == "__main__":
    sys.exit(main())