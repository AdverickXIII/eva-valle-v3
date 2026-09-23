"""
eva_baseline_v3.py
==================
Exploración + harness de pronóstico baseline para la Base Agrícola EVA-UPRA
(Valle del Cauca). Versión optimizada del notebook `explore_base_agricola_v3`.

Qué cambia respecto al notebook
-------------------------------
* Toda la lógica vive en funciones importables (el notebook queda para graficar).
* Columnas canónicas (`municipio`, `cultivo`, `ano`, ...) desde la carga:
  desaparece la clase de bug `KeyError: 'municipio'` (Celda 8b).
* Encabezado del Excel autodetectado + caché en parquet (el Excel de 166k filas
  se lee UNA vez).
* Folds, baselines y escala MASE 100 % vectorizados (sin `.apply` sobre arrays,
  sin `iterrows`, sin recalcular la escala por modelo).
* Regresión pooled en **walk-forward** (entrena solo con periodos < Y) sobre
  log-crecimiento, opcionalmente por Grupo de cultivo. Reemplaza el LOYO, que
  entrenaba con el futuro y sesgaba la selección hacia la regresión.
* Escala de respaldo MASE proporcional al nivel de cada serie (no un promedio
  global dominado por la caña).
* Detección de quiebres unificada (antes duplicada), simétrica y con la tabla
  `cobertura` que faltaba (`cov_df` nunca se definía).

Uso rápido
----------
    $env:EVA_XLSX = "C:\\ruta\\BaseAgricola.xlsx"     # PowerShell
    python eva_baseline_v3.py
"""
from __future__ import annotations

import os
import unicodedata
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

K = ["municipio", "cultivo"]  # llave de serie


# =============================================================================
# 0. Configuración
# =============================================================================
@dataclass(frozen=True)
class Config:
    ruta_xlsx: Path = Path(os.environ.get("EVA_XLSX", "BaseAgricola.xlsx"))
    hoja: int | str = 0
    departamento: str = "Valle del Cauca"
    anos_choque: tuple[int, int] = (2020, 2021)

    # Test de quiebre pre -> post (umbrales en %)
    ano_pre: int = 2021
    ano_post: int = 2022
    u_area_estable: float = 15.0
    u_salto_rend: float = 40.0
    u_prod_estable: float = 15.0
    u_rend_estable: float = 15.0
    u_rend_revision: float = 25.0
    u_area_vs_prod: float = 20.0

    # Evaluación
    n_final: int = 2          # folds finales reservados (alineado con Gates: ultimos 2 anos)
    top_k: int = 2
    dominantes: tuple[str, ...] = ("Caña",)  # cultivos que dominan el agregado


# =============================================================================
# 1. Helpers de texto / columnas
# =============================================================================
def normalizar(s) -> str:
    """'Producción (t)' -> 'produccion (t)'."""
    s = str(s)
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def detectar_columna(columnas, *patrones, obligatorio: bool = True):
    """Coincidencia EXACTA (normalizada) primero; substring como respaldo."""
    cols = {c: normalizar(c) for c in columnas}
    for p in patrones:
        exactas = [c for c, cn in cols.items() if cn == p]
        if exactas:
            return exactas[0]
    for p in patrones:
        cand = [c for c, cn in cols.items() if p in cn]
        if cand:
            return cand[0]
    if obligatorio:
        raise ValueError(f"No se encontró columna para {patrones}. "
                         f"Disponibles: {list(columnas)}")
    return None


def detectar_fila_encabezado(ruta, hoja=0, max_filas: int = 30,
                             ancla: str = "departamento") -> int:
    """Primera fila cuyo contenido incluye una celda 'Departamento' exacta."""
    raw = pd.read_excel(ruta, sheet_name=hoja, header=None, nrows=max_filas)
    for i, fila in raw.iterrows():
        if ancla in [normalizar(c) for c in fila if pd.notna(c)]:
            return int(i)
    raise ValueError(f"No se halló la fila de encabezado (celda '{ancla}') "
                     f"en las primeras {max_filas} filas.")


# =============================================================================
# 2. Carga y preparación
# =============================================================================
def _canonizar(df: pd.DataFrame) -> pd.DataFrame:
    cols = df.columns
    area = (detectar_columna(cols, "area cosechada", obligatorio=False)
            or detectar_columna(cols, "area sembrada", "hectarea", "area",
                                obligatorio=False))
    mapa = {
        "departamento": detectar_columna(cols, "departamento"),
        "municipio": detectar_columna(cols, "municipio", "munic"),
        "cultivo": detectar_columna(cols, "cultivo", "especie"),
        "ano": detectar_columna(cols, "ano", "anio", "year"),
        "periodo": detectar_columna(cols, "periodo"),
        "produccion": detectar_columna(cols, "produccion (t)", "produccion ton",
                                       "produccion_t", "produccion", "toneladas"),
        "area": area,
        "rendimiento_rep": detectar_columna(cols, "rendimiento", obligatorio=False),
        "grupo": detectar_columna(cols, "grupo cultivo", obligatorio=False),
        "ciclo": detectar_columna(cols, "ciclo del cultivo", "ciclo",
                                  obligatorio=False),
    }
    if mapa["area"] is None:
        raise ValueError("No se encontró columna de área (cosechada/sembrada).")
    return df.rename(columns={v: k for k, v in mapa.items() if v is not None})


def cargar_valle(cfg: Config, usar_cache: bool = True) -> pd.DataFrame:
    """Lee el XLSX (una sola vez), filtra el departamento y devuelve columnas
    canónicas. Cachea en parquet junto al Excel."""
    cache = cfg.ruta_xlsx.with_suffix(".valle.parquet")
    if (usar_cache and cache.exists()
            and cache.stat().st_mtime >= cfg.ruta_xlsx.stat().st_mtime):
        return pd.read_parquet(cache)

    fila = detectar_fila_encabezado(cfg.ruta_xlsx, cfg.hoja)
    df = pd.read_excel(cfg.ruta_xlsx, sheet_name=cfg.hoja, header=fila)
    df = df.dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    df = _canonizar(df)

    mask = df["departamento"].map(normalizar).str.strip() == normalizar(cfg.departamento)
    df = df.loc[mask].copy()
    if df.empty:
        raise ValueError(f"Sin filas para {cfg.departamento!r}.")

    if usar_cache:
        try:
            df.to_parquet(cache)
        except Exception as e:  # caché es opcional (falta pyarrow, tipos mixtos, ...)
            warnings.warn(f"No se pudo escribir la caché parquet: {e}")
    return df


def preparar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Año numérico, semestre, tipo_periodo y resolución de filas anual-plana
    que coexisten con A/B (se conserva el semestral). Devuelve (df, casos)."""
    df = df.copy()
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    n_sin = int(df["ano"].isna().sum())
    if n_sin:
        warnings.warn(f"{n_sin} filas sin año convertible; se excluyen")
        df = df.dropna(subset=["ano"])
    df["ano"] = df["ano"].astype(int)
    df["periodo"] = df["periodo"].astype(str).str.strip()
    df["semestre"] = df["periodo"].str.extract(r"([AB])$", expand=False)
    df["tipo_periodo"] = np.where(df["semestre"].isna(), "anual", "semestral")

    llaves = [df["municipio"], df["cultivo"], df["ano"]]
    hay_sem = ((df["tipo_periodo"] == "semestral")
               .groupby(llaves, dropna=False).transform("any"))
    mezcla = hay_sem & (df["tipo_periodo"] == "anual")

    casos = df.loc[mezcla, ["municipio", "cultivo", "ano", "produccion"]].rename(
        columns={"produccion": "prod_anual_plano"})
    if len(casos):
        sem = (df[(df["tipo_periodo"] == "semestral")]
               .groupby(["municipio", "cultivo", "ano"], as_index=False)["produccion"]
               .sum().rename(columns={"produccion": "prod_semestral_AB"}))
        casos = casos.merge(sem, on=["municipio", "cultivo", "ano"], how="left")
        casos["diferencia"] = casos["prod_semestral_AB"] - casos["prod_anual_plano"]
    return df.loc[~mezcla].copy(), casos.reset_index(drop=True)


def _rendimiento(p: pd.DataFrame) -> pd.Series:
    return np.where(p["area"] > 0, p["produccion"] / p["area"], np.nan)


def construir_paneles(df: pd.DataFrame):
    """(panel_anual, panel_semestral, meta). Agrega SIEMPRE a la granularidad real
    (municipio × cultivo × tiempo) para colapsar las 'Desagregaciones'.

    * panel_anual incluye `anio_incompleto` (cultivo semestral con un solo
      semestre reportado ese año: su suma anual está subestimada).
    * meta: grupo y ciclo por serie.
    """
    k3 = K + ["ano"]
    pa = (df.groupby(k3, as_index=False)
            .agg(produccion=("produccion", "sum"), area=("area", "sum")))
    pa["rendimiento"] = _rendimiento(pa)

    ds = df[df["tipo_periodo"] == "semestral"]
    n_sem = (ds.groupby(k3)["periodo"].nunique().rename("n_semestres").reset_index())
    pa = pa.merge(n_sem, on=k3, how="left")
    pa["anio_incompleto"] = pa["n_semestres"].notna() & (pa["n_semestres"] < 2)
    pa = pa.drop(columns="n_semestres").sort_values(k3).reset_index(drop=True)

    ps = (ds.groupby(K + ["periodo"], as_index=False)
            .agg(produccion=("produccion", "sum"), area=("area", "sum")))
    ps["ano"] = ps["periodo"].str[:4].astype(int)
    ps["rendimiento"] = _rendimiento(ps)
    ps = ps.sort_values(K + ["periodo"]).reset_index(drop=True)
    # AUD-HAR-001: huecos semestrales por serie. Si faltan semestres, shift(2)
    # NO es el mismo semestre del ano anterior: se marca para enmascarar el
    # candidato estacional en esas series.
    span = (ps.groupby(K)["ano"].transform("max")
            - ps.groupby(K)["ano"].transform("min") + 1) * 2
    obs = ps.groupby(K)["periodo"].transform("nunique")
    ps["serie_con_huecos"] = (span - obs) > 0

    extra = [c for c in ("grupo", "ciclo") if c in df.columns]
    meta = df.groupby(K, as_index=False)[extra].first() if extra else df[K].drop_duplicates()
    return pa, ps, meta


# =============================================================================
# 3. Diagnósticos
# =============================================================================
def longitud_series(panel: pd.DataFrame, col_tiempo: str):
    n = panel.groupby(K)[col_tiempo].nunique().rename("n")
    return n, n.value_counts().sort_index()


def agregado_anual(pa: pd.DataFrame, excluir: tuple[str, ...] = ()) -> pd.DataFrame:
    """Producción departamental por año, con o sin cultivos dominantes.
    Con la caña dentro el agregado casi no se mueve; sin ella se ve el resto."""
    d = pa[~pa["cultivo"].isin(excluir)]
    t = d.groupby("ano", as_index=False)["produccion"].sum()
    t["var_pct"] = t["produccion"].pct_change() * 100
    return t


def consistencia_rendimiento(df: pd.DataFrame) -> pd.Series:
    """|prod/área − rendimiento reportado| en %. OJO: ~0 % prueba que la fuente
    calcula producción = área × rendimiento (identidad aritmética), NO que el
    rendimiento sea una medición confiable."""
    d = df[(df["area"] > 0) & df["rendimiento_rep"].notna()]
    desv = ((d["produccion"] / d["area"] - d["rendimiento_rep"]).abs()
            / d["rendimiento_rep"].replace(0, np.nan) * 100)
    return desv.describe()


def rendimientos_repetidos(pa: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """% de transiciones año→año con rendimiento idéntico al anterior. Un valor
    alto sugiere rendimientos administrativos/constantes (p. ej. Plátano-Sevilla
    18 t/ha 2022-2024) y no mediciones anuales."""
    p = pa.sort_values(K + ["ano"]).copy()
    p["igual"] = (p.groupby(K)["rendimiento"].diff().abs() < 1e-9)
    p = p[p.groupby(K)["rendimiento"].shift(1).notna()]
    p = p.merge(meta, on=K, how="left")
    col = "ciclo" if "ciclo" in p.columns else "cultivo"
    return (p.groupby(col)["igual"].mean().mul(100).rename("pct_rend_repetido")
              .reset_index())


def _tipo_desde_ciclo(ciclo: pd.Series) -> pd.Series:
    c = ciclo.astype("string").str.lower()
    return np.where(c.isna(), "desconocido",
                    np.where(c.str.contains("transitor", na=False),
                             "transitorio", "permanente"))


def clasificar_quiebres(pa: pd.DataFrame, meta: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Test de quiebre pre→post para TODO el panel (una sola implementación).

    QUIEBRE_RENDIMIENTO : área estable + rendimiento salta (sube o baja)
    SIN_QUIEBRE         : producción y rendimiento estables
    REVISION_PROPORCIONAL: área y producción escalan juntas, rendimiento estable
    MIXTO_OTRO          : el resto (inspección manual)
    """
    a = pa[pa["ano"] == cfg.ano_pre].set_index(K)[["produccion", "area", "rendimiento"]]
    b = pa[pa["ano"] == cfg.ano_post].set_index(K)[["produccion", "area", "rendimiento"]]
    w = a.join(b, how="inner", lsuffix="_pre", rsuffix="_post").dropna()

    def pct(col):
        pre = w[f"{col}_pre"].replace(0, np.nan)
        return (w[f"{col}_post"] - w[f"{col}_pre"]) / pre * 100

    w["d_area_pct"], w["d_rend_pct"], w["d_prod_pct"] = pct("area"), pct("rendimiento"), pct("produccion")

    area_est = w["d_area_pct"].abs() < cfg.u_area_estable
    salto = w["d_rend_pct"].abs() > cfg.u_salto_rend
    prod_est = w["d_prod_pct"].abs() < cfg.u_prod_estable
    rend_est = w["d_rend_pct"].abs() < cfg.u_rend_estable
    proporcional = ((w["d_area_pct"] - w["d_prod_pct"]).abs() < cfg.u_area_vs_prod) & \
                   (w["d_rend_pct"].abs() < cfg.u_rend_revision)

    w["patron"] = np.select(
        [area_est & salto, prod_est & rend_est, proporcional],
        ["QUIEBRE_RENDIMIENTO", "SIN_QUIEBRE", "REVISION_PROPORCIONAL"],
        default="MIXTO_OTRO")
    w["serie_flag"] = w["patron"].map({
        "QUIEBRE_RENDIMIENTO": "quiebre_definicion_no_validado",
        "REVISION_PROPORCIONAL": "revision_fuente_real",
        "MIXTO_OTRO": "inspeccion_manual"})
    w["sentido"] = np.where(w["patron"] == "QUIEBRE_RENDIMIENTO",
                            np.where(w["d_rend_pct"] > 0, "sube", "baja"), "")
    w = w.reset_index().merge(meta, on=K, how="left")
    w["tipo"] = _tipo_desde_ciclo(w["ciclo"]) if "ciclo" in w.columns else "desconocido"
    cols = K + ["ciclo", "tipo", "patron", "sentido", "d_area_pct", "d_rend_pct",
                "d_prod_pct", "serie_flag"]
    return w[[c for c in cols if c in w.columns]]


def cobertura_quiebre(pa: pd.DataFrame, meta: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Series que aparecen/desaparecen entre ano_pre y ano_post (el `cov_df`
    que el notebook usaba sin definir)."""
    d = pa[pa["ano"].isin([cfg.ano_pre, cfg.ano_post])].assign(x=1)
    pres = (d.pivot_table(index=K, columns="ano", values="x", aggfunc="sum")
              .reindex(columns=[cfg.ano_pre, cfg.ano_post]))
    en_pre, en_post = pres[cfg.ano_pre].notna(), pres[cfg.ano_post].notna()
    pres["cobertura"] = np.select([en_pre & en_post, en_pre, en_post],
                                  ["ambos", "desaparece", "aparece"], default="ninguno")
    out = pres[["cobertura"]].reset_index().merge(meta, on=K, how="left")
    if "ciclo" in out.columns:
        out["tipo"] = _tipo_desde_ciclo(out["ciclo"])
    return out


# =============================================================================
# 4. Harness: folds expanding-window h=1 (vectorizado)
# =============================================================================
def generar_folds(panel: pd.DataFrame, col_tiempo: str, col_valor: str = "produccion",
                  lag_estacional: int | None = None, min_train: int = 1) -> pd.DataFrame:
    """Un renglón por fold. Predicciones baseline y escala MASE local calculadas
    con groupby/shift/cumsum (equivalente exacto al bucle original)."""
    p = panel.sort_values(K + [col_tiempo]).reset_index(drop=True)
    y = p[col_valor].astype(float)

    def gb(s):
        return s.groupby([p["municipio"], p["cultivo"]], sort=False)

    nt = gb(y).cumcount()                      # nº de puntos de train del fold
    n_puntos = gb(y).transform("size")
    prev = gb(y).shift(1)                      # naive
    first = gb(y).transform("first")
    csum_prev = gb(gb(y).cumsum()).shift(1)    # Σ y[:t] (solo pasado)
    nivel = csum_prev / nt.where(nt >= 1)      # media del train

    d = (y - prev).abs().fillna(0.0)
    suma_dif_prev = gb(gb(d).cumsum()).shift(1)  # Σ|Δ| dentro del train
    den = (nt - 1).where(nt >= 2)
    escala_local = (suma_dif_prev / den).where(lambda s: s > 0)
    pendiente = (prev - first) / den

    f = pd.DataFrame({
        "municipio": p["municipio"], "cultivo": p["cultivo"], "tiempo": p[col_tiempo],
        "n_train": nt, "n_puntos": n_puntos, "y": y,
        "pred_naive": prev, "pred_mean": nivel,
        "pred_drift": prev + pendiente.fillna(0.0),
        "escala_local": escala_local, "nivel_train": nivel})
    if lag_estacional:
        f["pred_seasonal_naive_1a"] = gb(y).shift(lag_estacional).fillna(prev)

    f = f[nt >= min_train].copy()
    f["fold_num"] = f["n_train"] - min_train
    f["n_folds"] = f["n_puntos"] - min_train
    return f.reset_index(drop=True)


def dividir_seleccion_final(folds: pd.DataFrame, n_final: int = 1):
    """Por serie: últimos `n_final` folds = evaluación honesta; el resto = selección.
    Series sin al menos 1 fold de selección quedan fuera."""
    umbral = folds["n_folds"] - n_final
    ok = umbral >= 1
    return (folds[ok & (folds["fold_num"] < umbral)].copy(),
            folds[ok & (folds["fold_num"] >= umbral)].copy())


def calcular_referencia_escala(sel: pd.DataFrame, modo: str = "ratio") -> float:
    """modo='ratio': mediana de (escala local / nivel) — escala de respaldo
    proporcional al tamaño de cada serie (recomendado).
    modo='global_mean': promedio global (comportamiento del notebook original)."""
    if modo == "global_mean":
        return float(sel["escala_local"].dropna().mean())
    ok = sel["escala_local"].notna() & (sel["nivel_train"] > 0)
    return float((sel.loc[ok, "escala_local"] / sel.loc[ok, "nivel_train"]).median())


def aplicar_escala(folds: pd.DataFrame, ref: float, modo: str = "ratio") -> pd.DataFrame:
    fb = folds["escala_local"].isna()
    relleno = ref if modo == "global_mean" else ref * folds["nivel_train"]
    esc = folds["escala_local"].where(~fb, relleno)
    return folds.assign(escala=esc.where(esc > 0), escala_fallback=fb)


def metricas_largas(folds: pd.DataFrame, modelos: list[str]) -> pd.DataFrame:
    base = folds[K + ["tiempo", "y", "escala"]]
    partes = []
    for m in modelos:
        pred = folds[f"pred_{m}"]
        e = (folds["y"] - pred).abs()
        den = folds["y"].abs() + pred.abs()
        partes.append(base.assign(modelo=m, abs_error=e, mase=e / folds["escala"],
                                  smape=np.where(den == 0, 0.0, 2 * e / den)))
    return pd.concat(partes, ignore_index=True)


def elegir_modelo(sel_largas: pd.DataFrame, modelos: list[str], k: int = 2,
                  eps: float = 1e-6):
    """Campeón (mín. MASE mediana) y pesos top-k ∝ 1/MASE, todo vectorizado."""
    cols = sorted(modelos)
    med = (sel_largas.groupby(K + ["modelo"])["mase"].median()
                     .unstack("modelo").reindex(columns=cols).dropna(how="all"))
    arr = med.to_numpy(float)
    # Redondear antes de ordenar: con series cortas varios baselines dan la MISMA
    # predicción y empatan; sin redondeo el ganador dependía de ruido de coma
    # flotante (1e-16). Así el desempate es determinista (orden alfabético).
    arr_o = np.round(arr, 9)
    campeon = pd.Series(np.array(cols, dtype=object)[np.nanargmin(arr_o, axis=1)],
                        index=med.index, name="modelo_campeon")
    orden = np.argsort(arr_o, axis=1, kind="stable")[:, :k]    # NaN al final
    top = np.take_along_axis(arr, orden, axis=1)
    inv = np.where(np.isnan(top), 0.0, 1.0 / (top + eps))
    w = inv / inv.sum(axis=1, keepdims=True)
    W = np.zeros_like(arr)
    np.put_along_axis(W, orden, w, axis=1)
    return campeon, pd.DataFrame(W, index=med.index, columns=cols)


def evaluar_final(fin: pd.DataFrame, campeon: pd.Series, pesos: pd.DataFrame) -> pd.DataFrame:
    """Selección pura vs ensemble top-k vs naive, en folds nunca usados para elegir."""
    cols = list(pesos.columns)
    f = fin.merge(campeon.reset_index(), on=K, how="inner")
    W = pesos.reindex(pd.MultiIndex.from_frame(f[K])).to_numpy()
    P = f[[f"pred_{m}" for m in cols]].to_numpy(float)
    f["pred_ensemble"] = (W * np.where(W > 0, P, 0.0)).sum(axis=1)
    idx = f["modelo_campeon"].map({m: i for i, m in enumerate(cols)}).to_numpy(int)
    f["pred_pura"] = P[np.arange(len(f)), idx]
    for nombre, col in (("pura", "pred_pura"), ("ensemble", "pred_ensemble"),
                        ("naive", "pred_naive")):
        f[f"abs_err_{nombre}"] = (f["y"] - f[col]).abs()
        f[f"mase_{nombre}"] = f[f"abs_err_{nombre}"] / f["escala"]
    f["gana"] = np.select([f["mase_pura"] < f["mase_ensemble"],
                           f["mase_pura"] > f["mase_ensemble"]],
                          ["pura", "ensemble"], default="empate")
    return f


# =============================================================================
# 5. Regresión pooled WALK-FORWARD sobre log-crecimiento
# =============================================================================
FEATS = ["dly_lag", "dla_lag", "desv_lag"]


def _features_regresion(panel: pd.DataFrame, col_tiempo: str,
                        meta: pd.DataFrame | None) -> pd.DataFrame:
    p = panel.sort_values(K + [col_tiempo]).reset_index(drop=True)
    if meta is not None and "grupo" in meta.columns:
        p = p.merge(meta[K + ["grupo"]], on=K, how="left")
    if "grupo" not in p.columns:
        p["grupo"] = "todos"
    p["grupo"] = p["grupo"].fillna("sin_grupo")

    p["_ly"], p["_la"] = np.log1p(p["produccion"]), np.log1p(p["area"])

    def gb(c):
        return p.groupby(K, sort=False)[c]

    nt = p.groupby(K, sort=False).cumcount()
    csum_prev = p.groupby(K, sort=False)["_ly"].cumsum().groupby(
        [p["municipio"], p["cultivo"]], sort=False).shift(1)
    media_hist = csum_prev / nt.where(nt >= 1)                         # media de ly[:t]
    ly1, la1 = gb("_ly").shift(1), gb("_la").shift(1)
    p["y_prev"] = gb("produccion").shift(1)
    p["dly_lag"] = ly1 - gb("_ly").shift(2)        # momentum (t-2 → t-1)
    p["dla_lag"] = la1 - gb("_la").shift(2)        # crecimiento de área rezagado
    p["desv_lag"] = ly1 - media_hist               # desvío vs. media histórica
    p["target"] = p["_ly"] - ly1                   # log-crecimiento a predecir
    return p


def _ajustar(train: pd.DataFrame, winsor=(1, 99)):
    cols = FEATS + ["target"]
    lo, hi = np.percentile(train[cols].to_numpy(), winsor, axis=0)
    Z = np.clip(train[cols].to_numpy(), lo, hi)
    X = np.column_stack([np.ones(len(Z)), Z[:, :-1]])
    coef = np.linalg.lstsq(X, Z[:, -1], rcond=None)[0]
    return coef, lo[:-1], hi[:-1]


def prediccion_regresion(panel: pd.DataFrame, col_tiempo: str,
                         meta: pd.DataFrame | None = None, por_grupo: bool = False,
                         min_filas: int = 30, winsor=(1, 99)) -> pd.DataFrame:
    """Predice producción del periodo Y entrenando SOLO con transiciones cuyo
    target es de un periodo < Y (lo que realmente se conocería). Winsoriza
    features/target para que un quiebre de definición no domine el ajuste."""
    p = _features_regresion(panel, col_tiempo, meta)
    listo = p.dropna(subset=FEATS + ["target"])
    salidas = []
    for Y in sorted(p[col_tiempo].unique()):
        train = listo[listo[col_tiempo] < Y]
        if len(train) < min_filas:
            continue
        test = p[p[col_tiempo] == Y].dropna(subset=FEATS + ["y_prev"])
        if test.empty:
            continue
        glob = _ajustar(train, winsor)
        por_g = ({g: _ajustar(t, winsor) for g, t in train.groupby("grupo")
                  if len(t) >= min_filas} if por_grupo else {})
        for g, te in test.groupby("grupo"):
            coef, lo, hi = por_g.get(g, glob)
            X = np.column_stack([np.ones(len(te)), np.clip(te[FEATS].to_numpy(), lo, hi)])
            hat = np.expm1(np.log1p(te["y_prev"].to_numpy()) + X @ coef)
            salidas.append(pd.DataFrame({
                "municipio": te["municipio"].to_numpy(), "cultivo": te["cultivo"].to_numpy(),
                "tiempo": te[col_tiempo].to_numpy(),
                "pred_regresion": np.clip(hat, 0, None)}))
    if not salidas:
        return pd.DataFrame(columns=K + ["tiempo", "pred_regresion"])
    return pd.concat(salidas, ignore_index=True)


def agregar_regresion(folds: pd.DataFrame, panel: pd.DataFrame, col_tiempo: str,
                      meta=None, por_grupo: bool = False) -> pd.DataFrame:
    reg = prediccion_regresion(panel, col_tiempo, meta, por_grupo)
    out = folds.merge(reg, on=K + ["tiempo"], how="left")
    out["regresion_fallback"] = out["pred_regresion"].isna()
    out["pred_regresion"] = out["pred_regresion"].fillna(out["pred_naive"])
    return out


# =============================================================================
# 6. Orquestación de una rama + resúmenes
# =============================================================================
def correr_rama(panel: pd.DataFrame, col_tiempo: str, meta: pd.DataFrame, *,
                lag_estacional: int | None = None, n_final: int = 1, k: int = 2,
                con_regresion: bool = True, por_grupo: bool = False,
                modo_escala: str = "ratio") -> dict:
    folds = generar_folds(panel, col_tiempo, lag_estacional=lag_estacional)
    if lag_estacional and "serie_con_huecos" in panel.columns:
        flag = panel[K + ["serie_con_huecos"]].drop_duplicates()
        folds = folds.merge(flag, on=K, how="left")
        folds.loc[folds["serie_con_huecos"].fillna(False),
                  "pred_seasonal_naive_1a"] = np.nan
        folds = folds.drop(columns=["serie_con_huecos"])
    if con_regresion:
        folds = agregar_regresion(folds, panel, col_tiempo, meta, por_grupo)
    modelos = [c[5:] for c in folds.columns if c.startswith("pred_")]

    sel, fin = dividir_seleccion_final(folds, n_final)
    ref = calcular_referencia_escala(sel, modo_escala)
    sel, fin = aplicar_escala(sel, ref, modo_escala), aplicar_escala(fin, ref, modo_escala)

    m_sel = metricas_largas(sel, modelos)
    campeon, pesos = elegir_modelo(m_sel, modelos, k)
    comp = evaluar_final(fin, campeon, pesos).merge(meta, on=K, how="left")
    return {"folds": folds, "seleccion": m_sel, "campeon": campeon, "pesos": pesos,
            "final": comp, "escala_ref": ref, "modelos": modelos}


def resumen_final(comp: pd.DataFrame) -> pd.Series:
    def wape(c):
        return comp[f"abs_err_{c}"].sum() / comp["y"].abs().sum() * 100
    return pd.Series({
        "series_evaluadas": len(comp),
        "MASE_mediana_pura": comp["mase_pura"].median(),
        "MASE_mediana_ensemble": comp["mase_ensemble"].median(),
        "MASE_mediana_naive": comp["mase_naive"].median(),
        "WAPE_%_pura": wape("pura"), "WAPE_%_ensemble": wape("ensemble"),
        "WAPE_%_naive": wape("naive"),
        "%_gana_pura": (comp["gana"] == "pura").mean() * 100,
        "%_escala_fallback": comp["escala_fallback"].mean() * 100,
    })


def resumen_por_tiempo(comp: pd.DataFrame) -> pd.DataFrame:
    """MASE por periodo de test: revela si el error se concentra en el quiebre."""
    return (comp.groupby("tiempo")[["mase_pura", "mase_ensemble", "mase_naive"]]
                .median().assign(n=comp.groupby("tiempo").size()))


# =============================================================================
# 7. Ejecución de punta a punta
# =============================================================================
def ejecutar(cfg: Config = Config(), *, por_grupo: bool = True) -> dict:
    df = cargar_valle(cfg)
    df, casos_mezclados = preparar(df)
    pa, ps, meta = construir_paneles(df)

    quiebres = clasificar_quiebres(pa, meta, cfg)
    res = {
        "df": df, "panel_anual": pa, "panel_semestral": ps, "meta": meta,
        "casos_mezclados": casos_mezclados,
        "quiebres": quiebres, "cobertura": cobertura_quiebre(pa, meta, cfg),
        "agregado": agregado_anual(pa), "agregado_sin_dominantes": agregado_anual(pa, cfg.dominantes),
        "anual": correr_rama(pa, "ano", meta, n_final=cfg.n_final, k=cfg.top_k,
                             por_grupo=por_grupo),
        "semestral": correr_rama(ps, "periodo", meta, lag_estacional=2,
                                 n_final=cfg.n_final, k=cfg.top_k, por_grupo=por_grupo),
    }
    quiebres.to_csv("flags_quiebre.csv", index=False, encoding="utf-8-sig")
    res["cobertura"].to_csv("cobertura_quiebre.csv", index=False, encoding="utf-8-sig")
    res["casos_mezclados"].to_csv("casos_mezclados.csv", index=False, encoding="utf-8-sig")
    return res


if __name__ == "__main__":
    pd.set_option("display.float_format", "{:,.3f}".format, "display.width", 140)
    r = ejecutar()
    for rama in ("anual", "semestral"):
        print(f"\n=== {rama.upper()} ===")
        print(resumen_final(r[rama]["final"]).to_string())
        print(resumen_por_tiempo(r[rama]["final"]).to_string())
    print("\nQuiebres:\n", r["quiebres"].groupby(["tipo", "patron"]).size().unstack(fill_value=0))
    print("\nCobertura:\n", r["cobertura"]["cobertura"].value_counts())
