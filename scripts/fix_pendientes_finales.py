"""Aplica los 2 pendientes: Seccion 4 limpia + Home actualizado."""
from pathlib import Path

# =====================================================================
# FIX 1: executive_report.py - Seccion 4 con 3 columnas por tabla
# =====================================================================
p1 = Path("core/reports/executive_report.py")
c = p1.read_text(encoding="utf-8")

ini = None
for patron in ["# 4. Tendencias", "# 4."]:
    k = c.find(patron)
    if k != -1:
        ini = k
        break

fin = None
for patron in ["# 5. Calidad", "# 5."]:
    k = c.find(patron, ini if ini else 0)
    if k != -1:
        fin = k
        break

if ini is None or fin is None:
    print(f"[AVISO] Marcadores no encontrados (ini={ini}, fin={fin}).")
    print('Pega la salida de: findstr /N "Tendencias Calidad" core\\reports\\executive_report.py')
else:
    NEW4 = '''# 4. Tendencias y dinamica (2019-2025)
    d4 = [["Ano", "Produccion (t)", "Rendimiento (t/ha)"]]
    for _, r in s["tendencia"].iterrows():
        d4.append([str(int(r["ano"])), f"{r['produccion']:,.0f}",
                   f"{r['rendimiento']:.2f}"])
    t4 = Table(d4, hAlign="LEFT", colWidths=[3*cm, 5*cm, 5*cm])
    t4.setStyle(_style())
    story.append(KeepTogether([
        Paragraph("4. Tendencias y dinamica (2019-2025)", st_["Heading2"]),
        t4, Spacer(1, 0.3*cm)]))

    d4b = [["Dinamica", "Cultivo", "CAGR"]]
    for _, r in s["crecen"].iterrows():
        d4b.append(["Crecen", r["cultivo"], f"+{r['cagr']:.1f}%"])
    for _, r in s["declinan"].iterrows():
        d4b.append(["Declinan", r["cultivo"], f"{r['cagr']:.1f}%"])
    t4b = Table(d4b, hAlign="LEFT", colWidths=[3*cm, 9*cm, 4.5*cm])
    t4b.setStyle(_style())
    story.append(KeepTogether([t4b, Spacer(1, 0.4*cm)]))

'''
    c = c[:ini] + NEW4 + "    " + c[fin:]
    p1.write_text(c, encoding="utf-8")
    print("[OK] Seccion 4 reescrita: 3 columnas por tabla")

# =====================================================================
# FIX 2: Home - cifras actualizadas
# =====================================================================
p2 = Path("ui/pages/0_Home.py")
h = p2.read_text(encoding="utf-8")
cambios = 0
for viejo, nuevo in [
    ("97 desagregaciones de cultivo", "78 cultivos"),
    ("97 desagregaciones", "78 cultivos"),
    ("6 anos de datos", "7 anos de datos (2019-2025)"),
    ("6 años de datos", "7 años de datos (2019-2025)"),
]:
    if viejo in h:
        h = h.replace(viejo, nuevo)
        cambios += 1

if cambios:
    p2.write_text(h, encoding="utf-8")
    print(f"[OK] Home actualizado ({cambios} cambios)")
else:
    print("[AVISO] Texto del Home no encontrado. Pega la salida de:")
    print('findstr /N "desagregaciones" ui\\pages\\0_Home.py')

print("\nAhora:")
print("1. Ctrl+R en el navegador (Home con cifras nuevas)")
print("2. Resumen Ejecutivo -> Descargar PDF -> verifica 3 columnas en Seccion 4")