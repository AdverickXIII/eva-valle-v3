"""Corrige el error de sintaxis en storytelling_report.py."""
from pathlib import Path

p = Path("core/reports/storytelling_report.py")
c = p.read_text(encoding="utf-8")

# Buscar y reemplazar la linea problematica
old = '''    story.append(Paragraph(
        f"<b>La frase de la agricultura:</b><br/><br/>"
        f"<i>"{frase}"</i>",
        ParagraphStyle("Cierre", parent=st_["Normal"], fontSize=12,
                       textColor=VERDE, alignment=1, leading=16)))'''

new = '''    story.append(Paragraph(
        f'<b>La frase de la agricultura:</b><br/><br/>'
        f'<i>"{frase}"</i>',
        ParagraphStyle("Cierre", parent=st_["Normal"], fontSize=12,
                       textColor=VERDE, alignment=1, leading=16)))'''

if old in c:
    c = c.replace(old, new)
    p.write_text(c, encoding="utf-8")
    print("[OK] Sintaxis corregida")
else:
    print("[INFO] No se encontro el patron exacto, intentando busqueda flexible...")
    # Busqueda mas flexible
    lines = c.split('\n')
    for i, line in enumerate(lines):
        if 'La frase de la agricultura' in line and 'f"' in line:
            # Encontramos la linea, corregir las siguientes 3 lineas
            lines[i] = "        f'<b>La frase de la agricultura:</b><br/><br/>'"
            if i+1 < len(lines) and 'frase' in lines[i+1]:
                lines[i+1] = "        f'<i>\"{frase}\"</i>',"
            break
    c = '\n'.join(lines)
    p.write_text(c, encoding="utf-8")
    print("[OK] Sintaxis corregida (busqueda flexible)")

print("Reintenta: python scripts\\generar_storytelling_final.py")