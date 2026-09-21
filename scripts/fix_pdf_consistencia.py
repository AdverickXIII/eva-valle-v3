"""AUD-UI-024: PDF coherente con la pagina + nota de evaluacion TimesFM.
H1: _forecast_png dibuja oficial (naive+IC) + referencia punteada (antes: ensemble como oficial).
H2: llamada a _forecast_png con (serie, res_estable, res_ensemble).
H3: Tabla de escenarios del PDF = mismas columnas que la pagina (Oficial/IC/Referencia/Diferencia).
H4: parrafo TimesFM en metodologia del PDF (resultado negativo documentado).
H5: caption TimesFM en 4_Predictivo.py.
Fail-safe: anclas unicas, backup, py_compile, rollback, autotest que GENERA un PDF real.
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
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

VIEJO_PNG = '''def _forecast_png(serie, res) -> bytes:
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.plot(serie.index, serie.values, "o-", color=VERDE, lw=2.5, label="Historico")
    anos = serie.index.values
    ultimo = int(anos[-1])
    n_steps = len(res["prediccion"])
    fut = np.arange(ultimo + 1, ultimo + 1 + n_steps)
    ic_bajo = res["escenarios"]["ic_bajo"]
    ic_alto = res["escenarios"]["ic_alto"]
    ax.fill_between(fut, ic_bajo, ic_alto, alpha=0.25, color="#5FA8DC", label="IC 50%")
    ax.plot(fut, res["escenarios"]["tendencial"], "o-", color=NARANJA, lw=2.5,
            label="Tendencial")
    ax.plot(fut, res["escenarios"]["conservador"], "--", color=NARANJA, lw=1.2,
            label="Conservador (P10)")
    ax.plot(fut, res["escenarios"]["optimista"], "--", color=VERDE, lw=1.2,
            label="Optimista (P90)")
    ax.set_ylabel("Produccion (t)", fontsize=9)
    ax.set_title("Proyeccion con intervalos de confianza", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _png(fig)'''

NUEVO_PNG = '''def _forecast_png(serie, res_estable, res_ensemble) -> bytes:
    """AUD-UI-024: grafica del PDF identica a la de la pagina: oficial + IC + referencia."""
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.plot(serie.index, serie.values, "o-", color=VERDE, lw=2.5, label="Historico")
    anos = serie.index.values
    ultimo = int(anos[-1])
    n_steps = len(res_estable["prediccion"])
    fut = np.arange(ultimo + 1, ultimo + 1 + n_steps)
    ax.fill_between(fut, res_estable["escenarios"]["ic_bajo"],
                    res_estable["escenarios"]["ic_alto"], alpha=0.25,
                    color="#5FA8DC", label="IC 50% (oficial)")
    ax.plot(fut, res_estable["escenarios"]["tendencial"], "o-", color=VERDE, lw=2.5,
            label="Oficial (estable)")
    ax.plot(fut, res_ensemble["escenarios"]["tendencial"], "s--", color=NARANJA, lw=1.8,
            label="Referencia (tendencial)")
    ax.set_ylabel("Produccion (t)", fontsize=9)
    ax.set_title("Proyeccion oficial vs referencia con IC", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _png(fig)'''

VIEJO_CALL = '    _add_png(story, _forecast_png(serie, res))'
NUEVO_CALL = '    _add_png(story, _forecast_png(serie, res_estable, res_ensemble))'

VIEJA_TABLA2 = '''    story.append(Paragraph("<b>Tabla de escenarios</b>", body))
    rows2 = [["Ano", "Conservador (P10)", "Tendencial", "Optimista (P90)",
              "IC 50%"]]
    anos_fut = np.arange(ultimo + 1, ultimo + 1 + horizonte)
    for i, an in enumerate(anos_fut):
        rows2.append([
            str(int(an)),
            f"{res['escenarios']['conservador'][i]:,.0f}",
            f"{res['escenarios']['tendencial'][i]:,.0f}",
            f"{res['escenarios']['optimista'][i]:,.0f}",
            f"{res['escenarios']['ic_bajo'][i]:,.0f} - "
            f"{res['escenarios']['ic_alto'][i]:,.0f}",
        ])
    t2 = Table(rows2, hAlign="LEFT")
    t2.setStyle(_style())
    story += [t2, Spacer(1, 0.4 * cm)]'''

NUEVA_TABLA2 = '''    story.append(Paragraph("<b>Tabla de escenarios (oficial vs referencia)</b>", body))
    rows2 = [["Ano", "Oficial (estable)", "IC 50% (oficial)",
              "Referencia (tendencial)", "Diferencia"]]
    anos_fut = np.arange(ultimo + 1, ultimo + 1 + horizonte)
    for i, an in enumerate(anos_fut):
        rows2.append([
            str(int(an)),
            f"{res_estable['escenarios']['tendencial'][i]:,.0f}",
            f"{res_estable['escenarios']['ic_bajo'][i]:,.0f} - "
            f"{res_estable['escenarios']['ic_alto'][i]:,.0f}",
            f"{res_ensemble['escenarios']['tendencial'][i]:,.0f}",
            f"{res_ensemble['escenarios']['tendencial'][i] - res_estable['escenarios']['tendencial'][i]:+,.0f}",
        ])
    t2 = Table(rows2, hAlign="LEFT")
    t2.setStyle(_style())
    story += [t2, Spacer(1, 0.4 * cm)]'''

ANCLA_METODO = '''        "usa naive (ultimo valor) con IC ensanchado con sqrt(t); el ensemble "
        "se muestra como referencia tendencial (AUD-UI-022, Gate 3).", body))'''

NUEVO_METODO = '''        "usa naive (ultimo valor) con IC ensanchado con sqrt(t); el ensemble "
        "se muestra como referencia tendencial (AUD-UI-022, Gate 3).", body))
    story.append(Paragraph(
        "<b>Evaluacion de modelos fundacionales (TimesFM):</b> TimesFM 2.5 "
        "(Google, 200M parametros) se evaluo en el mismo holdout 2024-2025 "
        "(Gates 1 y 2): WAPE mediano por serie en anual 17.3% vs 11.1% del "
        "naive y 16.5% del ensemble local; en semestral 39.5% vs 33.3% y "
        "37.3%. Al no superar al baseline en ninguna rama, no se exhibe como "
        "pronostico: se documenta como resultado negativo en la auditoria.", body))'''

ANCLA_UI = '''        f"no supera al naive en el holdout 2024-2025 (Gate 3)."
    )'''

NUEVO_UI = '''        f"no supera al naive en el holdout 2024-2025 (Gate 3)."
    )
    st.caption(
        "TimesFM 2.5 (modelo fundacional, Google) fue evaluado en el mismo holdout "
        "y no supero al naive (WAPE mediano anual 17.3% vs 11.1%; semestral 39.5% "
        "vs 33.3%). Se documenta como resultado negativo en la auditoria."
    )'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-UI-024", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def rollback_or_fail(motivo, backups):
    for ruta, bak in backups.items():
        try:
            shutil.copy2(bak, ruta)
        except Exception as e:
            audit("AUD-UI-024", "ROLLBACK_FALLIDO", f"{motivo} | {ruta.name}: {e}")
            return 1
    audit("AUD-UI-024", "ROLLBACK", motivo)
    print(f"[ERROR] {motivo}; revirtiendo {len(backups)} archivos")
    return 1


def main():
    try:
        t_ui = UI.read_text(encoding="utf-8")
        t_pdf = PDF.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer archivos: {e}")

    if "res_estable, res_ensemble) -> bytes" in t_pdf and "TimesFM 2.5" in t_ui:
        print("[SKIP] AUD-UI-024 ya aplicado")
        return 0

    anclas = [
        (t_pdf, VIEJO_PNG, "pdf: _forecast_png"),
        (t_pdf, VIEJO_CALL, "pdf: llamada _forecast_png"),
        (t_pdf, VIEJA_TABLA2, "pdf: tabla de escenarios"),
        (t_pdf, ANCLA_METODO, "pdf: fin metodologia"),
        (t_ui, ANCLA_UI, "ui: fin interpretacion"),
    ]
    for texto, ancla, nombre in anclas:
        if texto.count(ancla) != 1:
            return fail(f"ancla {nombre}: {texto.count(ancla)} coincidencias (esperaba 1)")

    t_pdf_n = (t_pdf.replace(VIEJO_PNG, NUEVO_PNG, 1)
                    .replace(VIEJO_CALL, NUEVO_CALL, 1)
                    .replace(VIEJA_TABLA2, NUEVA_TABLA2, 1)
                    .replace(ANCLA_METODO, NUEVO_METODO, 1))
    t_ui_n = t_ui.replace(ANCLA_UI, NUEVO_UI, 1)

    # Chequeos estaticos: nada del esquema viejo debe quedar
    if "Conservador (P10)" in t_pdf_n:
        return fail("queda 'Conservador (P10)' en predictivo_pdf.py tras el parche")
    if "_forecast_png(serie, res)" in t_pdf_n:
        return fail("queda la llamada vieja _forecast_png(serie, res)")

    backups = {}
    try:
        for ruta, nuevo in ((PDF, t_pdf_n), (UI, t_ui_n)):
            bak = ruta.with_suffix(ruta.suffix + ".bak")
            shutil.copy2(ruta, bak)
            backups[ruta] = bak
            ruta.write_text(nuevo, encoding="utf-8")
            print(f"[OK] {ruta.name} actualizado | backup: {bak.name}")
    except Exception as e:
        return rollback_or_fail(f"fallo de escritura: {e}", backups)

    for ruta in backups:
        r = subprocess.run([sys.executable, "-m", "py_compile", str(ruta)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return rollback_or_fail(f"sintaxis invalida en {ruta.name}: {r.stderr[:200]}", backups)

    # ---------- Autotest funcional: GENERAR un PDF real de punta a punta ----------
    sys.path.insert(0, str(RAIZ))
    for name in list(sys.modules):
        if name == "core" or name.startswith("core."):
            del sys.modules[name]
    import pandas as pd
    from core.analytics.forecast import proyectar_con_ic
    from core.reports.predictivo_pdf import build_predictivo_pdf

    serie = pd.Series([41000.0, 30000.0, 30200.0, 78000.0, 77800.0, 77900.0, 81630.0],
                      index=list(range(2019, 2026)))
    res_ens = proyectar_con_ic(serie, n_steps=3)
    if res_ens["modelo"] is None:
        return rollback_or_fail("autotest: proyectar_con_ic sin modelo", backups)
    pdf_bytes = build_predictivo_pdf("Cultivo Prueba", "Muni Prueba", serie, res_ens, 3)
    if pdf_bytes[:4] != b"%PDF" or len(pdf_bytes) < 5000:
        return rollback_or_fail("autotest: el PDF generado no es valido", backups)
    print(f"[OK] autotest: PDF generado de punta a punta ({len(pdf_bytes):,} bytes)")

    audit("AUD-UI-024", "OK", "PDF coherente con pagina + nota TimesFM")
    print("[OK] AUD-UI-024 aplicado, compilado y autotesteado")
    print("Siguiente: commit + reboot + descargar PDF y comparar con la pagina")
    return 0


if __name__ == "__main__":
    sys.exit(main())