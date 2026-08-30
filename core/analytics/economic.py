"""Modelo economico v0: valorizacion con precios de referencia (supuesto declarado)."""
from functools import lru_cache
import unicodedata

import pandas as pd

try:
    from config import settings
except Exception:
    from config.settings import settings

PRECIOS_REF = {  # COP/t, v0 (validar con Primer Mercado UPRA)
    "Caña": 160000, "Caña de azúcar": 160000,
    "Plátano": 1200000, "Banano": 1200000,
    "Naranja": 700000, "Mandarina": 900000, "Tomate": 1500000,
    "Piña": 900000, "Maracuyá": 3500000, "Papaya": 1000000,
    "Café": 2800000, "Aguacate": 2500000, "Yuca": 900000,
    "Maíz": 1100000, "Cacao": 12000000, "Guanábana": 2000000,
    "Guayaba": 800000,
}


def _norm(s) -> str:
    s = str(s)
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def _es_cana(nombre) -> bool:
    return "cana" in _norm(nombre)


@lru_cache(maxsize=1)
def load_df() -> pd.DataFrame:
    return pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                       low_memory=False)


def valorizar(df=None):
    df = df if df is not None else load_df()
    d = df.copy()
    d["precio_t"] = d.cultivo.map(PRECIOS_REF)
    d["valor"] = d.produccion_t * d.precio_t
    return d


def tabla_rank(anio=2025, excluye_cana=False):
    d = valorizar()
    d = d[d.ano == anio]
    if excluye_cana:
        d = d[~d.cultivo.map(_es_cana)]
    g = d.groupby("municipio").agg(valor=("valor", "sum"), ton=("produccion_t", "sum"))
    g = g[g.valor > 0]
    g["rank_pesos"] = g.valor.rank(ascending=False).astype(int)
    g["rank_ton"] = g.ton.rank(ascending=False).astype(int)
    g["salto"] = g.rank_ton - g.rank_pesos
    return g.sort_values("valor", ascending=False)


def serie_pib(excluye_cana=False):
    d = valorizar()
    d = d[d.valor > 0]
    if excluye_cana:
        d = d[~d.cultivo.map(_es_cana)]
    return d.groupby("ano")["valor"].sum()
