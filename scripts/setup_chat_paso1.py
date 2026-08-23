"""Paso 1 del chatbot: motor determinista + pruebas de 10 preguntas."""
from pathlib import Path

Path("core/chat").mkdir(parents=True, exist_ok=True)
Path("core/chat/__init__.py").write_text("", encoding="utf-8")

ENGINE = '''"""Motor determinista del Asistente EVA: dato oficial, cero alucinacion."""
import re
import unicodedata
from functools import lru_cache

import pandas as pd

from config.settings import settings


def _norm(s) -> str:
    s = str(s)
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


@lru_cache(maxsize=1)
def load_df() -> pd.DataFrame:
    p = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    return pd.read_csv(p, low_memory=False)


def _fmt(v) -> str:
    return f"{v:,.0f}"


def _cagr(serie) -> float:
    s = serie[serie > 0].sort_index()
    if len(s) < 2:
        return None
    n = s.index[-1] - s.index[0]
    if n <= 0:
        return None
    return ((s.iloc[-1] / s.iloc[0]) ** (1 / n) - 1) * 100


def _es_cana(nombre) -> bool:
    return "cana" in _norm(nombre)


def _entities(q, df):
    qn = _norm(q)
    munis = []
    for m in sorted(df["municipio"].dropna().unique().tolist(), key=len, reverse=True):
        n = _norm(m)
        if n and n in qn:
            munis.append(m)
            qn = qn.replace(n, " ", 1)
    cult = None
    for c in sorted(df["cultivo"].dropna().unique().tolist(), key=len, reverse=True):
        if _norm(c) in _norm(q):
            cult = c
            break
    ma = re.search(r"20(1[9]|2[0-8])", q)
    ano = int(ma.group(0)) if ma else None
    return (munis[0] if munis else None), cult, ano, munis


def _intent(q) -> str:
    qn = _norm(q)
    reglas = [
        ("confiabilidad", ["confiable", "satelite", "validacion", "anomalia", "verif"]),
        ("proyeccion", ["proyeccion", "proyect", "pronostic", "futuro", "2026", "2027", "2028"]),
        ("ranking", ["ranking", "posicion", "lider", "primer", "top", "quien produce mas"]),
        ("alertas", ["alerta", "declive", "riesgo", "cay", "caida", "critic", "emergente", "apuesta"]),
        ("motor", ["porque", "por que", "motor", "cagr", "creci", "elasticidad", "intensif"]),
        ("zonas", ["zona", "region", "norte", "centro", "sur", "pacifico"]),
        ("comparar", [" vs ", "versus", "compara", "contra", "frente a"]),
    ]
    for nombre, claves in reglas:
        if any(k in qn for k in claves):
            return nombre
    return "dato"


def _agg(df, muni=None, cult=None):
    sub = df
    if muni:
        sub = sub[sub["municipio"] == muni]
    if cult:
        sub = sub[sub["cultivo"] == cult]
    g = sub.groupby("ano").agg(p=("produccion_t", "sum"),
                               a=("area_sembrada_ha", "sum"),
                               c=("area_cosechada_ha", "sum"))
    return g.sort_index()


def _tipo_motor(ca, cr):
    if ca is None or cr is None:
        return "n/d"
    if ca > 2 and cr > 2:
        return "expansion con tecnologia"
    if ca > 2:
        return "extensivo (mas area)"
    if cr > 2:
        return "intensificacion (mas rendimiento)"
    return "estable"


def _resumen_municipio(df, muni):
    sub = df[df["municipio"] == muni]
    tot = sub.groupby("municipio")["produccion_t"].sum()
    pos = int((tot.sort_values(ascending=False).index.get_loc(muni)) + 1)
    top = sub.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    txt = (f"{muni}: {_fmt(tot.sum())} t acumuladas (#{pos} de {len(tot)} en el dpto). "
           f"Top cultivos: " + ", ".join(f"{c} ({_fmt(v)} t)" for c, v in top.head(3).items()) + ".")
    return txt


def _ranking_cultivo(df, cult, muni=None):
    sub = df[df["cultivo"] == cult].groupby("municipio")["produccion_t"].sum()
    sub = sub.sort_values(ascending=False)
    lines = [f"Top 5 en {cult}:"]
    for i, (m, v) in enumerate(sub.head(5).items(), 1):
        lines.append(f"  {i}. {m}: {_fmt(v)} t")
    if muni and muni in sub.index:
        lines.append(f"{muni} ocupa la posicion #{int(sub.index.get_loc(muni)) + 1} de {len(sub)}.")
    return "\\n".join(lines)


def ask(q: str) -> dict:
    df = load_df()
    muni, cult, ano, munis = _entities(q, df)
    intent = _intent(q)
    pagina = None

    if intent == "confiabilidad":
        return {"texto": "Validacion satelital Sentinel-1/2: 0 anomalias en 42 municipios "
                         "x 7 anos. La base EVA del Valle es confiable.", "pagina": "Validacion Satelital"}

    if intent == "proyeccion":
        g = _agg(df, muni, cult)
        if g.empty:
            return {"texto": "No tengo datos para esa combinacion. Prueba con un municipio "
                             "y/o cultivo, ej: 'que producira Alcala en 2027'."}
        base = g["p"].tail(3).mean()
        return {"texto": f"Proyeccion {'de ' + cult + ' en ' if cult else ''}{muni or 'el ambito'}: "
                         f"{_fmt(base)} t/año (metodo: promedio movil 3A, el mismo que gano el "
                         f"backtesting). Escenarios completos con credibilidad MAPE en la pagina "
                         f"Predictivo.", "pagina": "Predictivo"}

    if intent == "ranking":
        if cult:
            return {"texto": _ranking_cultivo(df, cult, muni), "pagina": "Cultivos"}
        tot = df.groupby("municipio")["produccion_t"].sum().sort_values(ascending=False)
        txt = "Top 5 municipal: " + ", ".join(f"{m} ({_fmt(v)} t)" for m, v in tot.head(5).items())
        if muni:
            txt += f"\\n{muni}: posicion #{int(tot.index.get_loc(muni)) + 1} de {len(tot)}."
        return {"texto": txt, "pagina": "Dashboard"}

    if intent == "alertas":
        tot = df.groupby(["municipio", "ano"])["produccion_t"].sum()
        cagrs = tot.groupby("municipio").apply(_cagr).dropna().sort_values()
        decl = cagrs[cagrs < 0].head(3)
        sub = df.groupby(["municipio", "cultivo", "ano"])["produccion_t"].sum()
        em = []
        for (m, c), s in sub.groupby(level=[0, 1]):
            g = _cagr(s)
            if g and g >= 15 and s.iloc[-1] >= 300:
                em.append((m, c, g, s.iloc[-1]))
        em.sort(key=lambda x: -x[2])
        txt = "Declive sostenido: " + (", ".join(f"{m} ({v:+.1f}%)" for m, v in decl.items()) or "ninguno")
        txt += "\\nApuestas emergentes: " + (", ".join(f"{c} en {m} ({g:+.0f}%)" for m, c, g, _ in em[:5]) or "ninguna")
        return {"texto": txt, "pagina": "Alertas"}

    if intent == "motor":
        if not cult:
            return {"texto": "Indicame el cultivo (y municipio si quieres), ej: 'por que crecio "
                             "el platano en Sevilla'."}
        g = _agg(df, muni, cult)
        cp, ca, cr = _cagr(g["p"]), _cagr(g["a"]), _cagr(g["p"] / g["c"])
        txt = (f"{cult}{' en ' + muni if muni else ''}: CAGR produccion {cp:+.1f}% "
               f"(area {ca:+.1f}% / rendimiento {cr:+.1f}%). Motor: {_tipo_motor(ca, cr)}.")
        return {"texto": txt, "pagina": "Cultivos"}

    if intent == "zonas":
        qn = _norm(q)
        sub = df if "sin" not in qn else df[~df["cultivo"].map(_es_cana)]
        gz = sub.groupby("zona").agg(p=("produccion_t", "sum"), c=("area_cosechada_ha", "sum"))
        lid = gz["p"].idxmax()
        efi = (gz["p"] / gz["c"]).idxmax()
        esc = "sin cana" if "sin" in qn else "con cana"
        return {"texto": f"Escenario {esc}: lidera {lid} ({_fmt(gz.loc[lid, 'p'])} t); "
                         f"mas eficiente: {efi} ({gz.loc[efi, 'p'] / gz.loc[efi, 'c']:.1f} t/ha).",
                "pagina": "Zonas"}

    if intent == "comparar" and len(munis) >= 2:
        a, b = munis[0], munis[1]
        ta = df[df["municipio"] == a]["produccion_t"].sum()
        tb = df[df["municipio"] == b]["produccion_t"].sum()
        ca = df[df["municipio"] == a]["cultivo"].nunique()
        cb = df[df["municipio"] == b]["cultivo"].nunique()
        return {"texto": f"{a}: {_fmt(ta)} t y {ca} cultivos. {b}: {_fmt(tb)} t y {cb} cultivos. "
                         f"Ratio {max(ta, tb) / min(ta, tb):.1f}x a favor de {a if ta > tb else b}.",
                "pagina": "Comparador"}

    # ---- dato / resumen ----
    if cult and muni and ano:
        v = df[(df["municipio"] == muni) & (df["cultivo"] == cult) & (df["ano"] == ano)]["produccion_t"].sum()
        return {"texto": f"{muni} produjo {_fmt(v)} t de {cult} en {ano}.", "pagina": "Cultivos"}
    if cult and muni:
        g = _agg(df, muni, cult)
        return {"texto": f"{cult} en {muni}: {_fmt(g['p'].sum())} t acumuladas; ultimo ano "
                         f"{_fmt(g['p'].iloc[-1])} t (rendimiento {g['p'].iloc[-1] / g['c'].iloc[-1]:.1f} t/ha).",
                "pagina": "Cultivos"}
    if cult:
        return {"texto": _ranking_cultivo(df, cult), "pagina": "Cultivos"}
    if muni:
        return {"texto": _resumen_municipio(df, muni), "pagina": "Dashboard"}
    return {"texto": "Soy el asistente del agro vallecaucano. Prueba: 'cuanto platano produjo "
                     "Sevilla en 2025', 'quien es el #1 en naranja', 'por que crecio el platano "
                     "en Sevilla', 'que producira Alcala en 2027', 'hay municipios en declive'."}
'''

Path("core/chat/engine.py").write_text(ENGINE, encoding="utf-8")
print("[OK] core/chat/engine.py creado")

TEST = '''"""Pruebas del motor del chatbot: 10 preguntas reales."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.chat.engine import ask

QS = [
    "Cuanto platano produjo Sevilla en 2025?",
    "Quien es el #1 en naranja?",
    "Como va Alcala en el ranking departamental?",
    "Por que crecio el platano en Sevilla?",
    "Que producira Alcala en 2027?",
    "Hay municipios en declive?",
    "Que zona produce mas sin cana?",
    "El dato de EVA es confiable?",
    "Dame un resumen de Alcala",
    "Compara Sevilla vs Alcala",
]
for q in QS:
    r = ask(q)
    print("\\n" + "=" * 70)
    print("PREGUNTA:", q)
    print("RESPUESTA:", r["texto"])
'''
Path("scripts/test_chat.py").write_text(TEST, encoding="utf-8")
print("[OK] scripts/test_chat.py creado")
print("\nEjecuta:  python scripts\\test_chat.py")