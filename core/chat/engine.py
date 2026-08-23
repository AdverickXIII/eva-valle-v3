"""Motor determinista del Asistente EVA v2: fuzzy + contexto + serie grafica."""
import re
import unicodedata
from difflib import get_close_matches
from functools import lru_cache

import pandas as pd

try:
    from config import settings
except Exception:
    from config.settings import settings


def _norm(s) -> str:
    s = str(s)
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


SINONIMOS = {
    "banano": "platano",
    "cachaco": "platano",
    "cana": "cana de azucar",
    "fruta de la pasion": "maracuya",
}


@lru_cache(maxsize=1)
def load_df() -> pd.DataFrame:
    p = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    return pd.read_csv(p, low_memory=False)


def _fmt(v) -> str:
    return f"{v:,.0f}"


def _div(a, b):
    return a / b if b else 0.0


def _cagr(serie):
    s = serie[serie > 0].sort_index()
    if len(s) < 2:
        return None
    n = s.index[-1] - s.index[0]
    if n <= 0:
        return None
    return ((s.iloc[-1] / s.iloc[0]) ** (1 / n) - 1) * 100


def _es_cana(nombre) -> bool:
    return "cana" in _norm(nombre)


def _match_norm(qn, nombres):
    for n in nombres:
        nn = _norm(n)
        if nn and nn in qn:
            return n, qn.replace(nn, " ", 1)
    palabras = qn.split()
    frags = []
    for i in range(len(palabras)):
        for j in range(i + 1, min(i + 3, len(palabras)) + 1):
            frags.append(" ".join(palabras[i:j]))
    for n in nombres:
        nn = _norm(n)
        if len(nn) < 4:
            continue
        if get_close_matches(nn, frags, n=1, cutoff=0.8):
            return n, qn
    return None, qn


def _entities(q, df):
    qn = _norm(q)
    for alias, target in SINONIMOS.items():
        qn = re.sub(r"\b" + re.escape(alias) + r"\b", target, qn)
    mun_names = sorted(df["municipio"].dropna().unique().tolist(), key=len, reverse=True)
    cult_names = sorted(df["cultivo"].dropna().unique().tolist(), key=len, reverse=True)
    munis = []
    tmp = qn
    for _ in range(2):
        m, tmp = _match_norm(tmp, mun_names)
        if not m:
            break
        munis.append(m)
    cult, _ = _match_norm(qn, cult_names)
    ma = re.search(r"20(1[9]|2[0-8])", q)
    ano = int(ma.group(0)) if ma else None
    return (munis[0] if munis else None), cult, ano, munis


def _intent(q) -> str:
    qn = _norm(q)
    reglas = [
        ("confiabilidad", ["confiable", "satelite", "validacion", "anomalia", "verif"]),
        ("proyeccion", ["proyeccion", "proyect", "pronostic", "futuro", "2026", "2027", "2028"]),
        ("ranking", ["ranking", "posicion", "lider", "primer", "top", "quien produce mas", "#1", "numero 1"]),
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


def _serie(df, muni=None, cult=None):
    g = _agg(df, muni, cult)
    if g.empty:
        return None
    tit = "Produccion"
    if cult:
        tit += f" de {cult}"
    if muni:
        tit += f" en {muni}"
    tit += " (t)"
    return {"x": [int(i) for i in g.index], "y": [round(float(v), 0) for v in g["p"]],
            "titulo": tit}


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
    ranking = df.groupby("municipio")["produccion_t"].sum().sort_values(ascending=False)
    pos = int(ranking.index.get_loc(muni)) + 1 if muni in ranking.index else 0
    top = sub.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    return (f"{muni}: {_fmt(tot.sum())} t acumuladas (#{pos} de {len(ranking)} en el dpto). "
            f"Top cultivos: " + ", ".join(f"{c} ({_fmt(v)} t)" for c, v in top.head(3).items()) + ".")


def _ranking_cultivo(df, cult, muni=None, q=""):
    m = re.search(r"top\s+(\d+)", q or "", re.I)
    n = int(m.group(1)) if m else 5
    n = max(1, min(n, 42))
    sub = df[df["cultivo"] == cult].groupby("municipio")["produccion_t"].sum()
    sub = sub.sort_values(ascending=False)
    lines = [f"Top {n} en {cult}:"]
    for i, (mu, v) in enumerate(sub.head(n).items(), 1):
        lines.append(f"{i}. {mu}: {_fmt(v)} t")
    txt = "\n".join(lines)
    if muni and muni in sub.index:
        txt += f"\n\n{muni} ocupa la posicion #{int(sub.index.get_loc(muni)) + 1} de {len(sub)}."
    return txt


def ask(q: str, ctx=None) -> dict:
    ctx = dict(ctx or {})
    df = load_df()
    muni, cult, ano, munis = _entities(q, df)
    muni = muni or ctx.get("muni")
    cult = cult or ctx.get("cult")
    if muni:
        ctx["muni"] = muni
    if cult:
        ctx["cult"] = cult
    intent = _intent(q)
    out = {}

    if intent == "confiabilidad":
        out = {"texto": "Validacion satelital Sentinel-1/2: 0 anomalias en 42 municipios "
                        "x 7 anos. La base EVA del Valle es confiable.",
               "pagina": "Validacion Satelital"}

    elif intent == "proyeccion":
        g = _agg(df, muni, cult)
        if g.empty or len(g) < 3:
            out = {"texto": "No tengo datos suficientes para proyectar esa combinacion. "
                            "Prueba: 'que producira Alcala en 2027'."}
        else:
            ult = g["p"].tail(3)
            out = {"texto": f"Proyeccion {'de ' + cult + ' ' if cult else ''}"
                            f"{'en ' + muni if muni else 'Valle del Cauca'}: tendencial "
                            f"{_fmt(ult.mean())} t/año; conservador {_fmt(ult.min())} (min ult. 3A); "
                            f"optimista {_fmt(ult.max())} (max ult. 3A). Modelo ganador y MAPE en "
                            f"la pagina Predictivo.",
                   "pagina": "Predictivo", "serie": _serie(df, muni, cult)}

    elif intent == "ranking":
        if cult:
            out = {"texto": _ranking_cultivo(df, cult, muni, q=q), "pagina": "Cultivos"}
        else:
            tot = df.groupby("municipio")["produccion_t"].sum().sort_values(ascending=False)
            txt = "Top 5 municipal: " + ", ".join(f"{m} ({_fmt(v)} t)" for m, v in tot.head(5).items())
            if muni and muni in tot.index:
                txt += f"\n{muni}: posicion #{int(tot.index.get_loc(muni)) + 1} de {len(tot)}."
            out = {"texto": txt, "pagina": "Dashboard"}

    elif intent == "alertas":
        tot = df.groupby(["municipio", "ano"])["produccion_t"].sum()
        cagrs = {}
        for m, s in tot.groupby(level="municipio"):
            g = _cagr(s.droplevel("municipio"))
            if g is not None:
                cagrs[m] = g
        cagrs = pd.Series(cagrs).sort_values()
        decl = cagrs[cagrs < 0].head(3)
        sub = df.groupby(["municipio", "cultivo", "ano"])["produccion_t"].sum()
        em = []
        for (m, c), s in sub.groupby(level=["municipio", "cultivo"]):
            g = _cagr(s.droplevel(["municipio", "cultivo"]))
            if g is not None and g >= 15 and s.iloc[-1] >= 300:
                em.append((m, c, g, s.iloc[-1]))
        em.sort(key=lambda x: -x[2])
        txt = "Declive sostenido: " + (", ".join(f"{m} ({v:+.1f}%)" for m, v in decl.items()) or "ninguno")
        txt += "\nApuestas emergentes: " + (", ".join(f"{c} en {m} ({g:+.0f}%)" for m, c, g, _ in em[:5]) or "ninguna")
        out = {"texto": txt, "pagina": "Alertas"}

    elif intent == "motor":
        if not cult:
            out = {"texto": "Indicame el cultivo (y municipio si quieres), ej: 'por que crecio "
                            "el platano en Sevilla'."}
        else:
            g = _agg(df, muni, cult)
            cp, ca, cr = _cagr(g["p"]), _cagr(g["a"]), _cagr(g["p"] / g["c"].replace(0, float("nan")))
            tipo = _tipo_motor(ca, cr)
            if cp is not None and cp < -2:
                tipo = "declive sostenido"
            txt = (f"{cult}{' en ' + muni if muni else ''}: CAGR produccion "
                   f"{cp:+.1f}% (area {ca:+.1f}% / rendimiento {cr:+.1f}%). "
                   f"Motor: {tipo}.")
            out = {"texto": txt, "pagina": "Cultivos", "serie": _serie(df, muni, cult)}

    elif intent == "zonas":
        if "zona" not in df.columns:
            out = {"texto": "La zonificacion no esta disponible en el dataset."}
        else:
            qn = _norm(q)
            sub = df if "sin" not in qn else df[~df["cultivo"].map(_es_cana)]
            gz = sub.groupby("zona").agg(p=("produccion_t", "sum"), c=("area_cosechada_ha", "sum"))
            lid = gz["p"].idxmax()
            efi = (gz["p"] / gz["c"].replace(0, float("nan"))).idxmax()
            esc = "sin cana" if "sin" in qn else "con cana"
            out = {"texto": f"Escenario {esc}: lidera {lid} ({_fmt(gz.loc[lid, 'p'])} t); "
                            f"mas eficiente: {efi} ({gz.loc[efi, 'p'] / gz.loc[efi, 'c']:.1f} t/ha).",
                   "pagina": "Zonas"}

    elif intent == "comparar" and len(munis) >= 2:
        a, b = munis[0], munis[1]
        ta = df[df["municipio"] == a]["produccion_t"].sum()
        tb = df[df["municipio"] == b]["produccion_t"].sum()
        ca = df[df["municipio"] == a]["cultivo"].nunique()
        cb = df[df["municipio"] == b]["cultivo"].nunique()
        out = {"texto": f"{a}: {_fmt(ta)} t y {ca} cultivos. {b}: {_fmt(tb)} t y {cb} cultivos. "
                        f"Ratio {max(ta, tb) / min(ta, tb):.1f}x a favor de {a if ta > tb else b}.",
               "pagina": "Comparador"}

    elif cult and muni and ano:
        v = df[(df["municipio"] == muni) & (df["cultivo"] == cult) & (df["ano"] == ano)]["produccion_t"].sum()
        out = {"texto": f"{muni} produjo {_fmt(v)} t de {cult} en {ano}.",
               "pagina": "Cultivos", "serie": _serie(df, muni, cult)}

    elif cult and muni:
        g = _agg(df, muni, cult)
        out = {"texto": f"{cult} en {muni}: {_fmt(g['p'].sum())} t acumuladas; ultimo ano "
                        f"{_fmt(g['p'].iloc[-1])} t (rendimiento {_div(g['p'].iloc[-1], g['c'].iloc[-1]):.1f} t/ha).",
               "pagina": "Cultivos", "serie": _serie(df, muni, cult)}

    elif cult:
        out = {"texto": _ranking_cultivo(df, cult, q=q), "pagina": "Cultivos"}

    elif muni:
        out = {"texto": _resumen_municipio(df, muni), "pagina": "Dashboard",
               "serie": _serie(df, muni)}

    else:
        out = {"texto": "Soy el asistente del agro vallecaucano. Prueba: 'cuanto platano produjo "
                        "Sevilla en 2025', 'quien es el #1 en naranja', 'por que crecio el platano "
                        "en Sevilla', 'que producira Alcala en 2027', 'hay municipios en declive'."}

    out["ctx"] = ctx
    return out
