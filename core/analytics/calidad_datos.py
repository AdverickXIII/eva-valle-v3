"""AUD-UI-025: calidad de datos D1 - quiebre de definicion 2021->2022.

Mismos umbrales que el harness de registro (eva_baseline_v3.Config):
area estable < 15% y salto de rendimiento > 40% (en valor absoluto).
"""
from __future__ import annotations

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
