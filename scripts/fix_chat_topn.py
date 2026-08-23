"""Top N dinamico + salto de linea + motor 'declive' cuando cae."""
from pathlib import Path

p = Path("core/chat/engine.py")
c = p.read_text(encoding="utf-8")
cambios = 0

# 1) Funcion de ranking con N dinamico y formato limpio
old_fn = '''def _ranking_cultivo(df, cult, muni=None):
    sub = df[df["cultivo"] == cult].groupby("municipio")["produccion_t"].sum()
    sub = sub.sort_values(ascending=False)
    lines = [f"Top 5 en {cult}:"]
    for i, (m, v) in enumerate(sub.head(5).items(), 1):
        lines.append(f"  {i}. {m}: {_fmt(v)} t")
    if muni and muni in sub.index:
        lines.append(f"{muni} ocupa la posicion #{int(sub.index.get_loc(muni)) + 1} de {len(sub)}.")
    return "\\n".join(lines)'''

new_fn = '''def _ranking_cultivo(df, cult, muni=None, q=""):
    m = re.search(r"top\\s+(\\d+)", q or "", re.I)
    n = int(m.group(1)) if m else 5
    n = max(1, min(n, 42))
    sub = df[df["cultivo"] == cult].groupby("municipio")["produccion_t"].sum()
    sub = sub.sort_values(ascending=False)
    lines = [f"Top {n} en {cult}:"]
    for i, (mu, v) in enumerate(sub.head(n).items(), 1):
        lines.append(f"{i}. {mu}: {_fmt(v)} t")
    txt = "\\n".join(lines)
    if muni and muni in sub.index:
        txt += f"\\n\\n{muni} ocupa la posicion #{int(sub.index.get_loc(muni)) + 1} de {len(sub)}."
    return txt'''

if old_fn in c:
    c = c.replace(old_fn, new_fn, 1); cambios += 1
    print("[OK] Ranking con N dinamico (top 20 -> 20) y formato limpio")

# 2) Pasar la pregunta a las llamadas
old_c1 = 'out = {"texto": _ranking_cultivo(df, cult, muni), "pagina": "Cultivos"}'
new_c1 = 'out = {"texto": _ranking_cultivo(df, cult, muni, q=q), "pagina": "Cultivos"}'
if old_c1 in c:
    c = c.replace(old_c1, new_c1, 1); cambios += 1
old_c2 = 'out = {"texto": _ranking_cultivo(df, cult), "pagina": "Cultivos"}'
new_c2 = 'out = {"texto": _ranking_cultivo(df, cult, q=q), "pagina": "Cultivos"}'
if old_c2 in c:
    c = c.replace(old_c2, new_c2, 1); cambios += 1
print("[OK] Llamadas actualizadas con q")

# 3) Motor 'declive sostenido' cuando la produccion cae
old_m = '''            txt = (f"{cult}{' en ' + muni if muni else ''}: CAGR produccion "
                   f"{cp:+.1f}% (area {ca:+.1f}% / rendimiento {cr:+.1f}%). "
                   f"Motor: {_tipo_motor(ca, cr)}.")'''
new_m = '''            tipo = _tipo_motor(ca, cr)
            if cp is not None and cp < -2:
                tipo = "declive sostenido"
            txt = (f"{cult}{' en ' + muni if muni else ''}: CAGR produccion "
                   f"{cp:+.1f}% (area {ca:+.1f}% / rendimiento {cr:+.1f}%). "
                   f"Motor: {tipo}.")'''
if old_m in c:
    c = c.replace(old_m, new_m, 1); cambios += 1
    print("[OK] Motor declara 'declive sostenido' cuando cae")

if cambios:
    p.write_text(c, encoding="utf-8")
    print(f"[OK] {cambios} mejoras aplicadas")
else:
    print("[AVISO] Bloques no encontrados; revisa engine.py")