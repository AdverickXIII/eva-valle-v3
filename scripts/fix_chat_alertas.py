"""Corrige el calculo de CAGR en la rama de alertas (MultiIndex -> anos)."""
from pathlib import Path

p = Path("core/chat/engine.py")
c = p.read_text(encoding="utf-8")

old = '''    if intent == "alertas":
        tot = df.groupby(["municipio", "ano"])["produccion_t"].sum()
        cagrs = tot.groupby("municipio").apply(_cagr).dropna().sort_values()
        decl = cagrs[cagrs < 0].head(3)
        sub = df.groupby(["municipio", "cultivo", "ano"])["produccion_t"].sum()
        em = []
        for (m, c), s in sub.groupby(level=[0, 1]):
            g = _cagr(s)
            if g and g >= 15 and s.iloc[-1] >= 300:
                em.append((m, c, g, s.iloc[-1]))
        em.sort(key=lambda x: -x[2])'''

new = '''    if intent == "alertas":
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
        em.sort(key=lambda x: -x[2])'''

if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] Rama alertas corregida (droplevel antes de CAGR)")
else:
    print("[AVISO] El bloque no coincide; revisa engine.py manualmente")