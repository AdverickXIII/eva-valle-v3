"""Modelo economico paso 1: notebook de exploracion + modulo de valorizacion."""
import json
from pathlib import Path

Path("notebooks").mkdir(exist_ok=True)

PRECIOS = '''PRECIOS_REF = {  # COP/t, supuesto metodologico v0 (validar con Primer Mercado UPRA)
    "Caña de azúcar": 160000, "Plátano": 1200000, "Naranja": 700000,
    "Mandarina": 900000, "Tomate": 1500000, "Piña": 900000,
    "Maracuyá": 3500000, "Papaya": 1000000, "Café": 2800000,
    "Aguacate": 2500000, "Yuca": 900000, "Maíz": 1100000,
    "Cacao": 12000000, "Guanábana": 2000000, "Guayaba": 800000,
}'''

# ---------------- Notebook ----------------
cells = []
def md(src):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": src.splitlines(keepends=True)})
def code(src):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": src.splitlines(keepends=True)})

md("# Modelo economico EVA Valle - Exploracion 1\n"
   "Objetivo: convertir toneladas en pesos (PIB agro municipal) usando\n"
   "precios de referencia v0 (supuesto declarado) + precios de tierra (datos.gov.co).\n"
   "Ejecuta las celdas en orden.")

code("import sys\n"
     "from pathlib import Path\n"
     "import pandas as pd\n"
     "\n"
     "sys.path.insert(0, str(Path.cwd()))\n"
     "from config.settings import settings\n"
     "\n"
     "df = pd.read_csv(settings.DATA_MODEL_PATH / 'eva_agricola_valle_modelo_conceptual.csv',\n"
     "                 low_memory=False)\n"
     "print('EVA:', df.shape)\n"
     "df.head()")

md("## 1) Precios comerciales de la tierra rural (UPRA, datos.gov.co)\n"
   "Descarga directa del dataset abierto rttb-pk7n.")

code("URL_TIERRA = 'https://www.datos.gov.co/resource/rttb-pk7n.csv'\n"
     "tierra = None\n"
     "try:\n"
     "    tierra = pd.read_csv(URL_TIERRA, nrows=20000)\n"
     "    print('[OK] tierra:', tierra.shape)\n"
     "    tierra.head()\n"
     "except Exception as e:\n"
     "    print('[AVISO] sin descarga de tierra:', e)")

md("## 2) Precios de referencia v0 (supuesto metodologico)\n"
   "Tabla editable: ajusta valores y re-ejecuta. La celda reporta cobertura.")

code(PRECIOS + "\n"
     "precios = pd.Series(PRECIOS_REF, name='precio_t')\n"
     "cub = df['cultivo'].map(precios).notna()\n"
     "print(f'Cobertura filas: {cub.mean():.1%} | tonelaje cubierto: '\n"
     "      f\"{df.loc[cub, 'produccion_t'].sum() / df['produccion_t'].sum():.1%}\")\n"
     "if cub.mean() < 0.8:\n"
     "    print('Cultivos sin precio:', sorted(set(df.loc[~cub, 'cultivo'].unique())))")

md("## 3) PIB agro municipal 2025: ranking en PESOS vs ranking en TONELADAS\n"
   "Aqui aparece la sorpresa economica: el ranking en pesos NO es el ranking en toneladas.")

code("d = df.copy()\n"
     "d['valor'] = d['produccion_t'] * d['cultivo'].map(precios)\n"
     "g25 = d[d.ano == 2025].groupby('municipio')['valor'].sum()\n"
     "t25 = d[d.ano == 2025].groupby('municipio')['produccion_t'].sum()\n"
     "comp = pd.DataFrame({'PIB_agro_2025_M_COP': (g25 / 1e6).round(0),\n"
     "                     'ton_2025': t25}).dropna()\n"
     "comp['rank_pesos'] = comp['PIB_agro_2025_M_COP'].rank(ascending=False).astype(int)\n"
     "comp['rank_ton'] = comp['ton_2025'].rank(ascending=False).astype(int)\n"
     "comp['salto_rank'] = comp['rank_ton'] - comp['rank_pesos']\n"
     "comp.sort_values('PIB_agro_2025_M_COP', ascending=False).head(10)")

md("## 4) PIB agro departamental anual y CAGR en pesos")

code("serie = d.groupby('ano')['valor'].sum() / 1e9\n"
     "print('PIB agro departamental (miles de M COP):')\n"
     "print(serie.round(1))\n"
     "n = serie.index[-1] - serie.index[0]\n"
     "cagr_pesos = ((serie.iloc[-1] / serie.iloc[0]) ** (1 / n) - 1) * 100\n"
     "print(f'CAGR en pesos 2019-2025: {cagr_pesos:+.1f}%')")

md("## 5) Exportar para la app")

code("out = Path('data'); out.mkdir(exist_ok=True)\n"
     "comp.to_csv(out / 'economia_municipal_2025.csv')\n"
     "serie.rename('pib_miles_M').to_csv(out / 'pib_agro_anual.csv')\n"
     "print('[OK] exportado a data/economia_municipal_2025.csv y data/pib_agro_anual.csv')")

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                  "name": "python3"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
Path("notebooks/01_exploracion_economica.ipynb").write_text(
    json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("[OK] notebooks/01_exploracion_economica.ipynb creado")

# ---------------- Modulo para la app (paso 2) ----------------
MOD = '''"""Modelo economico: valorizacion de la produccion con precios de referencia v0."""
from functools import lru_cache

import pandas as pd

try:
    from config import settings
except Exception:
    from config.settings import settings

''' + PRECIOS + '''


@lru_cache(maxsize=1)
def load_df() -> pd.DataFrame:
    return pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                       low_memory=False)


def valorizar(df=None):
    df = df if df is not None else load_df()
    d = df.copy()
    d["valor"] = d.produccion_t * d.cultivo.map(pd.Series(PRECIOS_REF))
    return d


def pib_municipal(anio=2025):
    d = valorizar()
    return d[d.ano == anio].groupby("municipio")["valor"].sum().sort_values(ascending=False)
'''
Path("core/analytics/economic.py").write_text(MOD, encoding="utf-8")
print("[OK] core/analytics/economic.py creado")
print("\nAbre el notebook:  jupyter notebook  (o VS Code sobre el .ipynb)")