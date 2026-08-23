"""IRS: Indice de Recomendacion de Siembra (capa prescriptiva)."""
from functools import lru_cache

import pandas as pd

try:
    from config import settings
except Exception:
    from config.settings import settings

PESOS = {"lq": 0.40, "cagr": 0.30, "eff": 0.20, "div": 0.10}


@lru_cache(maxsize=1)
def load_df() -> pd.DataFrame:
    p = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    return pd.read_csv(p, low_memory=False)


def build_irs(df: pd.DataFrame) -> pd.DataFrame:
    yr = int(df["ano"].max())
    acc = df.groupby(["municipio", "cultivo"])["produccion_t"].sum().reset_index()
    ult = df[df["ano"] == yr].groupby(["municipio", "cultivo"]).agg(
        p=("produccion_t", "sum"), c=("area_cosechada_ha", "sum")).reset_index()
    ult = ult[ult.p > 0]
    if "zona" in df.columns:
        zona = df.drop_duplicates("municipio").set_index("municipio")["zona"]
    else:
        zona = pd.Series(dtype=str)

    m_tot = acc.groupby("municipio")["produccion_t"].sum()
    c_tot = acc.groupby("cultivo")["produccion_t"].sum()
    d_tot = acc["produccion_t"].sum()

    m = acc.merge(ult, on=["municipio", "cultivo"])
    m = m[m.produccion_t >= 100]
    m["share_m"] = m.produccion_t / m.municipio.map(m_tot)
    m["LQ"] = m.share_m / (m.cultivo.map(c_tot) / d_tot)

    g = df.groupby(["municipio", "cultivo", "ano"])["produccion_t"].sum()
    cagrs = {}
    for (mu, cu), s in g.groupby(level=[0, 1]):
        s2 = s.droplevel([0, 1]).sort_index()
        s2 = s2[s2 > 0]
        if len(s2) >= 2:
            n = s2.index[-1] - s2.index[0]
            if n > 0:
                cagrs[(mu, cu)] = ((s2.iloc[-1] / s2.iloc[0]) ** (1 / n) - 1) * 100
    cs = pd.Series(cagrs, name="CAGR")
    m = m.merge(cs, left_on=["municipio", "cultivo"], right_index=True, how="left")
    m = m[m.CAGR.notna() & (m.CAGR >= -5)]

    tr = ult.assign(r=ult.p / ult.c.replace(0, float("nan")))
    tr = tr[tr.p >= 500].groupby("cultivo")["r"].max()
    m["eff"] = (m.p / m.c.replace(0, float("nan")) / m.cultivo.map(tr)).clip(0, 1)

    m["div"] = 1 - m.share_m
    m["IRS"] = (PESOS["lq"] * m.LQ.clip(0, 3) / 3
                + PESOS["cagr"] * (m.CAGR.clip(-5, 30) + 5) / 35
                + PESOS["eff"] * m.eff.fillna(0)
                + PESOS["div"] * m["div"]) * 100

    def etiqueta(r):
        if r.LQ >= 1 and r.CAGR >= 5:
            return "Expandir"
        if r.LQ >= 1:
            return "Proteger"
        if r.CAGR >= 15:
            return "Apostar"
        return "Diversificar"

    m["etiqueta"] = m.apply(etiqueta, axis=1)
    m["zona"] = m.municipio.map(zona).fillna("n/d")
    return m.sort_values("IRS", ascending=False).reset_index(drop=True)


def top_cultivos(irs, municipio, n=5):
    return irs[irs.municipio == municipio].head(n)


def top_municipios(irs, cultivo, n=5):
    return irs[irs.cultivo == cultivo].head(n)
