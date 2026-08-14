"""Corrige columnas duplicadas en Seccion 4 del Resumen Ejecutivo."""
from pathlib import Path

p = Path("core/reports/executive_report.py")
c = p.read_text(encoding="utf-8")

# Buscar la Seccion 4
i = c.find("# 4. Tendencias y dinamica")
j = c.find("# 5. Calidad")

if i == -1 or j == -1:
    print("[ERROR] No encontre marcadores de Seccion 4")
    raise SystemExit(1)

# Nueva Seccion 4 con columnas correctas
NEW4 = '''# 4. Tendencias y dinamica
    d4 = [["Ano", "Produccion (t)", "Rendimiento (t/ha)"]]
    for _, r in s["tendencia"].iterrows():
        d4.append([str(int(r["ano"])), f"{r['produccion']:,.0f}",
                   f"{r['rendimiento']:.2f}"])
    t4 = Table(d4, hAlign="LEFT", colWidths=[3*cm, 5*cm, 5*cm])
    t4.setStyle(_style())
    story.append(KeepTogether([
        Paragraph("4. Tendencias y dinamica (2019-2025)", st_["Heading2"]),
        t4, Spacer(1, 0.2*cm)]))

    # Tabla de dinamica de cultivos
    d4b = [["Dinamica", "Cultivo", "CAGR"]]
    for _, r in s["crecen"].iterrows():
        d4b.append(["Crecen", r["cultivo"], f"+{r['cagr']:.1f}%"])
    for _, r in s["declinan"].iterrows():
        d4b.append(["Declinan", r["cultivo"], f"{r['cagr']:.1f}%"])
    t4b = Table(d4b, hAlign="LEFT", colWidths=[3*cm, 7*cm, 3*cm])
    t4b.setStyle(_style())
    story.append(KeepTogether([t4b, Spacer(1, 0.4*cm)]))
'''

c = c[:i] + NEW4 + "    " + c[j:]
p.write_text(c, encoding="utf-8")
print("[OK] Seccion 4 corregida: columnas sin duplicar")
print("Regenera el PDF: streamlit run app.py -> Resumen Ejecutivo -> Descargar")