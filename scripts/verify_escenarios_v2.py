"""Verificación estricta: el IC debe tener ANCHO (P10 < tendencial < P90).

QA gate de publicabilidad del forecast. Read-only: solo lee y certifica;
no modifica datos, modelos ni reportes.
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from config.settings import settings
from core.analytics.forecast import proyectar_con_ic

TOL = 1e-6          # tolerancia numérica para comparaciones de orden
TOL_ANCHO = 1.0     # ancho mínimo de IC / separación mínima entre escenarios (t)
FACTOR_TECHO = 3.0  # techo por defecto = 3x el máximo histórico de la serie


def cargar_serie(municipio: str, cultivo: str) -> pd.Series:
    """Carga y agrega la serie histórica de producción para municipio/cultivo."""
    csv_path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    df = pd.read_csv(csv_path, low_memory=False)

    faltantes = {"municipio", "cultivo", "ano", "produccion_t"} - set(df.columns)
    if faltantes:
        raise ValueError(f"Columnas faltantes en el CSV: {faltantes}")

    mask = (df["municipio"] == municipio) & (df["cultivo"] == cultivo)
    serie = df.loc[mask].groupby("ano")["produccion_t"].sum().sort_index()

    if serie.empty:
        msg = f"No hay datos para municipio={municipio!r}, cultivo={cultivo!r}"
        sug_c = difflib.get_close_matches(cultivo, sorted(df.cultivo.unique()), n=3)
        sug_m = difflib.get_close_matches(municipio, sorted(df.municipio.unique()), n=3)
        if sug_c:
            msg += f" | cultivos cercanos: {sug_c}"
        if sug_m:
            msg += f" | municipios cercanos: {sug_m}"
        raise ValueError(msg)
    return serie


def validar_escenarios(
    serie: pd.Series, res: dict, n_steps: int, techo_t: float
) -> dict[str, bool]:
    """Corre los checks de sensatez sobre los escenarios proyectados."""
    esc = res["escenarios"]
    for clave in ("conservador", "tendencial", "optimista", "ic_bajo", "ic_alto"):
        if clave not in esc:
            raise KeyError(f"'escenarios' no contiene la clave esperada: {clave}")

    c, t, o = esc["conservador"], esc["tendencial"], esc["optimista"]
    ic_bajo, ic_alto = esc["ic_bajo"], esc["ic_alto"]

    for nombre, arr in (("conservador", c), ("tendencial", t), ("optimista", o),
                        ("ic_bajo", ic_bajo), ("ic_alto", ic_alto)):
        if len(arr) != n_steps:
            raise ValueError(
                f"'{nombre}' tiene longitud {len(arr)}, se esperaba n_steps={n_steps}"
            )

    ultimo_ano = int(serie.index.max())
    anos_forecast = [ultimo_ano + i for i in range(1, n_steps + 1)]

    print(f"Ganador: {res['ganador']} | MAPE {res['mape']:.2f}%")
    print(f"Años proyectados: {anos_forecast}")
    print(f"Conservador: {np.round(c).tolist()}")
    print(f"Tendencial:  {np.round(t).tolist()}")
    print(f"Optimista:   {np.round(o).tolist()}")
    print(f"IC 50% {anos_forecast[0]}: {ic_bajo[0]:,.0f} - {ic_alto[0]:,.0f}")

    checks = {
        "c <= t siempre": bool(np.all(c <= t + TOL)),
        "t <= o siempre": bool(np.all(t <= o + TOL)),
        "IC con ancho (>0) todos los anos": bool(np.all(ic_alto > ic_bajo + TOL_ANCHO)),
        "o > t en algún año": bool(np.any(o > t + TOL_ANCHO)),
        "c < t en algún año": bool(np.any(c < t - TOL_ANCHO)),
        f"max < {techo_t:,.0f} t (techo)": bool(float(np.max(o)) < techo_t),
    }
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--municipio", default="Alcalá")
    parser.add_argument("--cultivo", default="Plátano")
    parser.add_argument("--n-steps", type=int, default=3)
    parser.add_argument("--techo-t", type=float, default=None,
                        help="Cota absoluta opcional; por defecto 3x el máximo histórico")
    args = parser.parse_args()

    try:
        serie = cargar_serie(args.municipio, args.cultivo)
        res = proyectar_con_ic(serie, n_steps=args.n_steps)
        techo = args.techo_t if args.techo_t is not None else FACTOR_TECHO * float(serie.max())
        checks = validar_escenarios(serie, res, args.n_steps, techo)
    except (ValueError, KeyError) as e:
        print(f"❌ Error de validación: {e}")
        return 1

    for k, v in checks.items():
        print(f"  {'✅' if v else '❌'} {k}")

    ok = all(checks.values())
    print("\n✅ ESCENARIOS REALMENTE CUERDOS" if ok
          else "\n❌ IC sigue degenerado: NO publicar")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())