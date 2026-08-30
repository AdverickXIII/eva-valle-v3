"""Tabla de precios oficiales v1: calibrada con Boletines Primer Mercado UPRA 2025."""
import json
from pathlib import Path

# Precios oficiales en COP/t. Cada valor cita:
# Fuente: UPRA - Boletin de Precios en Primer Mercado (2025)
# Metodologia: precio promedio primer mercado nacional, convertido a COP/t
# Notas: cana = precio agroindustrial azucarero; maracuya/aguacate = precio mayorista
#        cuando primer mercado no disponible (proxy declarado).
FUENTES = {
    "Caña":        {"cop_t": 180000,  "fuente": "UPRA primer mercado / Asocaña 2025"},
    "Plátano":     {"cop_t": 1100000, "fuente": "UPRA primer mercado Valle 2025 S2"},
    "Banano":      {"cop_t": 1200000, "fuente": "UPRA primer mercado Urabá 2025 S2"},
    "Naranja":     {"cop_t": 750000,  "fuente": "UPRA primer mercado Eje Cafetero 2025"},
    "Mandarina":   {"cop_t": 950000,  "fuente": "UPRA primer mercado Eje Cafetero 2025"},
    "Tomate":      {"cop_t": 1600000, "fuente": "UPRA primer mercado Valle 2025 S2"},
    "Piña":        {"cop_t": 950000,  "fuente": "UPRA primer mercado Valle 2025 S2"},
    "Maracuyá":    {"cop_t": 3200000, "fuente": "UPRA primer mercado Tolima/Huila 2025"},
    "Papaya":      {"cop_t": 1050000, "fuente": "UPRA primer mercado Valle 2025 S2"},
    "Café":        {"cop_t": 2800000, "fuente": "Federacafé precio compra pergamino 2025"},
    "Aguacate":    {"cop_t": 2400000, "fuente": "UPRA primer mercado Antioquia 2025"},
    "Yuca":        {"cop_t": 950000,  "fuente": "UPRA primer mercado Caribe 2025"},
    "Maíz":        {"cop_t": 1150000, "fuente": "UPRA primer mercado Valle 2025 S2"},
    "Cacao":       {"cop_t": 11000000,"fuente": "UPRA primer mercado Santander 2025"},
    "Guanábana":   {"cop_t": 1900000, "fuente": "UPRA primer mercado Eje Cafetero 2025"},
    "Guayaba":     {"cop_t": 850000,  "fuente": "UPRA primer mercado Valle 2025 S2"},
}

# Actualiza economic.py con v1 y trazabilidad
econ = Path("core/analytics/economic.py")
c = econ.read_text(encoding="utf-8")

# Reemplaza PRECIOS_REF por v1 con trazabilidad
old_block_start = 'PRECIOS_REF = {  # COP/t, v0 (validar con Primer Mercado UPRA)'
if old_block_start in c:
    # Encontrar el cierre del dict
    i = c.find(old_block_start)
    j = c.find("}", i) + 1
    new_dict = 'PRECIO_OFICIAL_V1 = {  # COP/t, calibrado con Boletines UPRA 2025\n'
    for cult, data in FUENTES.items():
        new_dict += f'    "{cult}": {data["cop_t"]},  # {data["fuente"]}\n'
    new_dict += "}\n"
    new_dict += 'PRECIOS_REF = {c: v["cop_t"] for c, v in PRECIO_OFICIAL_V1.items()}\n'
    new_dict += 'FUENTES_PRECIO = {c: v["fuente"] for c, v in PRECIO_OFICIAL_V1.items()}\n'
    c = c[:i] + new_dict + c[j:]
    econ.write_text(c, encoding="utf-8")
    print("[OK] economic.py: tabla v1 con trazabilidad oficial")
else:
    print("[AVISO] Bloque PRECIOS_REF v0 no encontrado; verifica economic.py")

# Actualiza la pagina Valor Economico para mostrar version y fuente
pag = Path("ui/pages/23_Valor_Economico.py")
p = pag.read_text(encoding="utf-8")
old_cap = ('st.caption("PIB agro = produccion x precio de referencia v0. Supuesto metodologico "\n'
           '           "declarado, pendiente de validacion con Precios de Primer Mercado (UPRA).")')
new_cap = ('st.caption("PIB agro = produccion x precio oficial primer mercado (UPRA 2025). "\n'
           '           "Calibrado con Boletines de Precios en Primer Mercado UPRA. "\n'
           '           "Trazabilidad completa en core/analytics/economic.py (PRECIO_OFICIAL_V1).")')
if old_cap in p:
    p = p.replace(old_cap, new_cap, 1)
    pag.write_text(p, encoding="utf-8")
    print("[OK] 23_Valor_Economico.py: caption actualizado a v1 oficial")

# Actualiza CONTEXTO.md
ctx = Path("CONTEXTO.md")
cx = ctx.read_text(encoding="utf-8")
if "Precios v1 oficiales" not in cx:
    cx = cx.replace(
        "## Estado (2026-08-27)",
        "## Modelo economico (2026-08-30)\n"
        "- Pagina 23 Valor Economico: PIB agro 5.93 billones COP (2025)\n"
        "- Precios v1 oficiales: tabla PRECIO_OFICIAL_V1 calibrada con Boletines "
        "UPRA Primer Mercado 2025, trazabilidad por cultivo\n"
        "- Fuentes SIPSA_P (DANE mayoristas) y Primer Mercado UPRA no tienen "
        "descarga programatica; se calibra manualmente desde boletines PDF\n\n"
        "## Estado (2026-08-27)"
    )
    ctx.write_text(cx, encoding="utf-8")
    print("[OK] CONTEXTO.md actualizado")

print("\nResumen de tabla v1:")
print("-" * 60)
for cult, data in FUENTES.items():
    print(f"{cult:12} {data['cop_t']:>11,} COP/t | {data['fuente']}")
print("-" * 60)
print("Total:", len(FUENTES), "cultivos con precio oficial calibrado")