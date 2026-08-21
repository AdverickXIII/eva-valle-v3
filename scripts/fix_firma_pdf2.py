"""Firma tolerante + tabla comparativa en el PDF cuando la pagina la pasa."""
import re
from pathlib import Path

p = Path("core/reports/ficha_pdf.py")
c = p.read_text(encoding="utf-8")

# 1) Firma que acepta cualquier argumento extra
m = re.search(r"def build_ficha_pdf\(.*?\) -> bytes:", c)
if m and "**kwargs" not in m.group(0):
    c = c.replace(m.group(0),
                  "def build_ficha_pdf(cultivo, ambito, agg, diag, "
                  "figs=None, comp=None, **kwargs) -> bytes:", 1)
    print("[OK] Firma tolerante: figs/comp/qualsiera quedan aceptados")
else:
    print("[INFO] La firma ya era tolerante")

# 2) Si la pagina pasa comp, se incluye como tabla en el PDF
if "Comparativa vs Departamento</b>" not in c:
    anchor = '    story += [Paragraph("<b>Interpretacion</b>", body),'
    bloque = '''    if comp is not None:
        try:
            story.append(Paragraph("<b>Comparativa vs Departamento</b>", body))
            cols = list(comp.columns)[:8]
            rows = [cols]
            for _, r in comp.head(12).iterrows():
                fila = []
                for col in cols:
                    v = r[col]
                    fila.append(f"{v:,.1f}" if isinstance(v, float) else str(v))
                rows.append(fila)
            t3 = Table(rows, hAlign="LEFT")
            t3.setStyle(_style())
            story += [t3, Spacer(1, 0.4 * cm)]
        except Exception:
            pass

'''
    if anchor in c:
        c = c.replace(anchor, bloque + anchor, 1)
        print("[OK] Tabla comparativa se incluira en el PDF de Cultivos")
    else:
        print("[AVISO] Ancla de Interpretacion no encontrada")

p.write_text(c, encoding="utf-8")
print("Reinicia Streamlit y recarga la pagina Cultivos")