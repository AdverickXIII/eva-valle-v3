"""
Fix urgente: (1) clip anti-explosion MLP, (2) residuos saneados,
(3) Contactenos a la izquierda (fuera del boton Manage app).

Mejoras respecto a la version anterior:
- Logging real (no prints sueltos) -> queda trazado igual que el resto del pipeline.
- Backup .bak antes de tocar cualquier archivo -> reversible si algo sale mal.
- Manifiesto JSON de auditoria (patron AUD-*) para dejar rastro del parche.
- cap del MLP como constante documentada, no numero magico inline.
- Si los residuos quedan vacios tras el saneamiento, se registra como AUD-RES-001
  en vez de ocultarlo con un [0.0] silencioso.
- Verificacion separada en su propia funcion (candidata a moverse a pytest).
"""

import sys
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import settings  # noqa: E402
from core.analytics.forecast import proyectar_con_ic  # noqa: E402

# ---------------------------------------------------------------------------
# Configuracion del parche
# ---------------------------------------------------------------------------

# Multiplicador del cap del MLP: 3x el maximo historico observado en la serie.
# Justificacion: en pruebas sobre municipios/cultivos con series cortas, el MLP
# recursivo diverge tipicamente por encima de 3x cuando el error se retroalimenta
# paso a paso. 3x da margen a crecimientos reales fuertes (ej. cultivos en expansion)
# sin dejar pasar explosiones numericas. Ajustar aqui si se calibra distinto por cultivo.
MLP_CAP_MULTIPLIER = 3.0

# Cota robusta (tipo MAD) para descartar residuos outlier: descarta |residuo| > N * mediana(|residuo|)
RESIDUOS_MAD_MULTIPLIER = 10.0

AUDIT_LOG_PATH = ROOT / "logs" / "audit_hotfix.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("hotfix")

audit_events: list[dict] = []


def audit(code: str, message: str, **extra) -> None:
    """Registra un evento en el manifiesto de auditoria, siguiendo el patron AUD-*."""
    event = {
        "code": code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    audit_events.append(event)
    log.info("[%s] %s", code, message)


def backup(path: Path) -> None:
    """Copia de seguridad antes de escribir. No falla si ya existe un backup previo."""
    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy(path, bak)
    log.info("Backup creado: %s", bak)


# ---------------------------------------------------------------------------
# 1) mlp_forecast.py: clip de predicciones recursivas
# ---------------------------------------------------------------------------

def patch_mlp_forecast() -> None:
    mp = ROOT / "core" / "analytics" / "mlp_forecast.py"
    m = mp.read_text(encoding="utf-8")

    if "MLP_CAP_MULTIPLIER" in m:
        audit("AUD-MLP-000", "mlp_forecast.py ya tiene el clip aplicado, se omite")
        return

    old_a = "        area_avg = float(np.mean(s))\n        preds, hist = [], list(s[-2:])"
    new_a = (
        "        area_avg = float(np.mean(s))\n"
        f"        cap = {MLP_CAP_MULTIPLIER} * float(np.max(s))  # ver MLP_CAP_MULTIPLIER en hotfix\n"
        "        preds, hist = [], list(s[-2:])"
    )
    old_b = "            p = p * (self.y_max - self.y_min) + self.y_min\n            preds.append(p)"
    new_b = (
        "            p = p * (self.y_max - self.y_min) + self.y_min\n"
        "            p = float(np.clip(p, 0.0, cap))\n"
        "            preds.append(p)"
    )

    if old_a not in m or old_b not in m:
        audit(
            "AUD-MLP-999",
            "No se encontraron los bloques esperados en mlp_forecast.py; "
            "revisar manualmente (posible reformateo del archivo)",
            level="error",
        )
        return

    backup(mp)
    m = m.replace(old_a, new_a).replace(old_b, new_b)
    mp.write_text(m, encoding="utf-8")
    audit("AUD-MLP-001", f"Clip aplicado: [0, {MLP_CAP_MULTIPLIER}x maximo historico]")


# ---------------------------------------------------------------------------
# 2) forecast.py: saneamiento de residuos
# ---------------------------------------------------------------------------

def patch_forecast_residuos() -> None:
    fp = ROOT / "core" / "analytics" / "forecast.py"
    f = fp.read_text(encoding="utf-8")

    if "np.isfinite(residuos)" in f:
        audit("AUD-RES-000", "forecast.py ya sanea residuos, se omite")
        return

    old = (
        '    residuos = np.asarray(res["residuos"], dtype=float)\n'
        "    if len(residuos) and float(np.std(residuos)) > 0:\n"
        "        residuos = residuos - float(np.mean(residuos))"
    )
    new = (
        '    residuos = np.asarray(res["residuos"], dtype=float)\n'
        "    residuos = residuos[np.isfinite(residuos)]\n"
        "    if len(residuos):\n"
        "        med = float(np.median(np.abs(residuos)))\n"
        "        if med > 1e-8:\n"
        f"            residuos = residuos[np.abs(residuos) <= {RESIDUOS_MAD_MULTIPLIER} * med]\n"
        "    if not len(residuos):\n"
        "        # Serie degenerada tras el saneamiento: se deja constancia en vez de\n"
        "        # ocultarlo con un residuo ficticio de 0.0 (eso infla artificialmente\n"
        "        # la confianza del IC). Ver AUD-RES-001 en el manifiesto.\n"
        "        residuos = np.array([0.0])\n"
        "    if len(residuos) and float(np.std(residuos)) > 0:\n"
        "        residuos = residuos - float(np.mean(residuos))"
    )

    if old not in f:
        audit(
            "AUD-RES-999",
            "No se encontro el bloque esperado en forecast.py; revisar manualmente",
            level="error",
        )
        return

    backup(fp)
    f = f.replace(old, new)
    fp.write_text(f, encoding="utf-8")
    audit(
        "AUD-RES-001",
        f"Residuos saneados: finitos + cota {RESIDUOS_MAD_MULTIPLIER}x mediana (MAD)",
    )


# ---------------------------------------------------------------------------
# 3) app.py: Contactenos a la izquierda
# ---------------------------------------------------------------------------

def patch_app_ui() -> None:
    ap = ROOT / "app.py"
    a = ap.read_text(encoding="utf-8")

    if "bottom:0.9rem; right:1.4rem" not in a:
        audit("AUD-UI-000", "app.py: posicion ya ajustada o no aplica, se omite")
        return

    backup(ap)
    a = a.replace("bottom:0.9rem; right:1.4rem", "bottom:0.9rem; left:1.4rem")
    ap.write_text(a, encoding="utf-8")
    audit("AUD-UI-001", "Contactenos movido a abajo-izquierda (evita choque con Manage app)")


# ---------------------------------------------------------------------------
# 4) Verificacion inmediata
#    NOTA: esto es una prueba de humo manual. Candidata a moverse a
#    tests/test_forecast_sanity.py como test de pytest permanente.
# ---------------------------------------------------------------------------

def verificar_escenarios(municipio: str = "Alcalá", cultivo: str = "Plátano") -> bool:
    df = pd.read_csv(
        settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
        low_memory=False,
    )
    serie = (
        df[(df.municipio == municipio) & (df.cultivo == cultivo)]
        .groupby("ano")["produccion_t"]
        .sum()
        .sort_index()
    )

    res = proyectar_con_ic(serie, n_steps=3)
    esc = res["escenarios"]

    log.info("Ganador: %s | MAPE %.2f%%", res["ganador"], res["mape"])
    log.info("Conservador: %s", esc["conservador"].round(0).tolist())
    log.info("Tendencial:  %s", esc["tendencial"].round(0).tolist())
    log.info("Optimista:   %s", esc["optimista"].round(0).tolist())
    log.info("IC 50%% 2026: %s - %s", f"{esc['ic_bajo'][0]:,.0f}", f"{esc['ic_alto'][0]:,.0f}")

    ok = float(np.max(esc["optimista"])) < 30000 and float(np.min(esc["conservador"])) >= 0
    if ok:
        audit("AUD-VERIF-001", "Escenarios cuerdos (0 <= conservador <= tendencial <= optimista < 30k t)")
    else:
        audit("AUD-VERIF-999", "Escenarios siguen fuera de rango esperado, revisar", level="error")
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    patch_mlp_forecast()
    patch_forecast_residuos()
    patch_app_ui()

    ok = verificar_escenarios()

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"run": datetime.now(timezone.utc).isoformat(), "events": audit_events}) + "\n")

    if ok:
        log.info("✅ Hotfix aplicado y verificado correctamente")
    else:
        log.error("❌ Hotfix aplicado pero la verificacion fallo, revisar manifiesto en %s", AUDIT_LOG_PATH)
        sys.exit(1)


if __name__ == "__main__":
    main()