"""Zonas: separadores de miles en tabla dual + nota explicativa de Pacifico."""
from pathlib import Path

p = Path("ui/pages/19_Zonas.py")
c = p.read_text(encoding="utf-8")
cambios = 0

old1 = '"Prod. con cana (t)": ic["produccion_t"].round(0),'
new1 = '"Prod. con cana (t)": ic["produccion_t"].map("{:,.0f}".format),'
old2 = '"Prod. sin cana (t)": isn["produccion_t"].round(0),'
new2 = '"Prod. sin cana (t)": isn["produccion_t"].map("{:,.0f}".format),'
if old1 in c:
    c = c.replace(old1, new1, 1); cambios += 1
if old2 in c:
    c = c.replace(old2, new2, 1); cambios += 1

anchor = 'st.subheader("Comparativa dual: con cana vs sin cana")'
nota = ('st.caption("Nota: Pacifico = 1 municipio (Buenaventura) -> Gini territorial = 0 "\n'
        '                   "por definicion (sin desigualdad interna posible).")\n')
if anchor in c and "Gini territorial = 0" not in c:
    c = c.replace(anchor, nota + anchor, 1); cambios += 1

if cambios:
    p.write_text(c, encoding="utf-8")
    print(f"[OK] {cambios} ajuste(s) aplicados a 19_Zonas.py")
else:
    print("[INFO] Sin cambios pendientes")