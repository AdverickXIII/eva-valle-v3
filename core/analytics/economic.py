"""Modelo economico v0: valorizacion con precios de referencia (supuesto declarado)."""
from functools import lru_cache
import unicodedata

import pandas as pd

try:
    from config import settings
except Exception:
    from config.settings import settings

PRECIO_OFICIAL_V1 = {  # COP/t, calibrado con Boletines UPRA 2025
    "Caña": 180000,  # UPRA primer mercado / Asocaña 2025
    "Plátano": 1100000,  # UPRA primer mercado Valle 2025 S2
    "Banano": 1200000,  # UPRA primer mercado Urabá 2025 S2
    "Naranja": 750000,  # UPRA primer mercado Eje Cafetero 2025
    "Mandarina": 950000,  # UPRA primer mercado Eje Cafetero 2025
    "Tomate": 1600000,  # UPRA primer mercado Valle 2025 S2
    "Piña": 950000,  # UPRA primer mercado Valle 2025 S2
    "Maracuyá": 3200000,  # UPRA primer mercado Tolima/Huila 2025
    "Papaya": 1050000,  # UPRA primer mercado Valle 2025 S2
    "Café": 2800000,  # Federacafé precio compra pergamino 2025
    "Aguacate": 2400000,  # UPRA primer mercado Antioquia 2025
    "Yuca": 950000,  # UPRA primer mercado Caribe 2025
    "Maíz": 1150000,  # UPRA primer mercado Valle 2025 S2
    "Cacao": 11000000,  # UPRA primer mercado Santander 2025
    "Guanábana": 1900000,  # UPRA primer mercado Eje Cafetero 2025
    "Guayaba": 850000,  # UPRA primer mercado Valle 2025 S2
}
PRECIOS_REF = {c: v["cop_t"] for c, v in PRECIO_OFICIAL_V1.items()}
FUENTES_PRECIO = {c: v["fuente"] for c, v in PRECIO_OFICIAL_V1.items()}



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
