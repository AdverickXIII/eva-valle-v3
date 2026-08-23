"""Acepta el rol 'usuario' en la navegacion por niveles."""
from pathlib import Path

p = Path("app.py")
c = p.read_text(encoding="utf-8")
old = 'nivel = {"user": 0, "analista": 1, "admin": 2}[role]'
new = 'nivel = {"user": 0, "usuario": 0, "analista": 1, "admin": 2}.get(role, 0)'
if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] Rol 'usuario' reconocido (y cualquier rol desconocido cae a nivel 0)")
else:
    print("[AVISO] Linea no encontrada; revisa app.py")