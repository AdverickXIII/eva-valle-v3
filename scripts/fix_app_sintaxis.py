"""Repara el \\n literal en app.py y blinda la zona en irs.py."""
import ast
from pathlib import Path

# 1) app.py: convertir el backslash-n literal en salto de linea real
p = Path("app.py")
c = p.read_text(encoding="utf-8")
old = 'icon="\\U0001F3AF")),\\n'
new = 'icon="\\U0001F3AF")),\n'
if old in c:
    c = c.replace(old, new, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] app.py: salto de linea reparado")
else:
    print("[INFO] app.py ya estaba limpio o el patron difiere")

# 2) irs.py: guardia por si la columna zona no existe
q = Path("core/analytics/irs.py")
s = q.read_text(encoding="utf-8")
old_z = '    zona = df.drop_duplicates("municipio").set_index("municipio")["zona"]'
new_z = ('    if "zona" in df.columns:\n'
         '        zona = df.drop_duplicates("municipio").set_index("municipio")["zona"]\n'
         '    else:\n'
         '        zona = pd.Series(dtype=str)')
if old_z in s:
    s = s.replace(old_z, new_z, 1)
    s = s.replace('    m["zona"] = m.municipio.map(zona)',
                  '    m["zona"] = m.municipio.map(zona).fillna("n/d")', 1)
    q.write_text(s, encoding="utf-8")
    print("[OK] irs.py: columna zona blindada")

# 3) Verificacion de sintaxis de los 3 archivos
for f in ["app.py", "ui/pages/22_Recomendador.py", "core/analytics/irs.py"]:
    ast.parse(Path(f).read_text(encoding="utf-8"))
    print(f"[OK] sintaxis correcta: {f}")