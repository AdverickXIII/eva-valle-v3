"""Fusion mapa: absorbe area cosechada + KPIs en 8_Mapa y elimina 16_Mapa_Cultivos."""
from pathlib import Path

p = Path("ui/pages/8_Mapa.py")
c = p.read_text(encoding="utf-8")
cambios = 0

# 1) Agregar metrica Area Cosechada
old_met = '''METRICAS = {
    "Produccion (t)": "produccion_t",
    "Area Sembrada (ha)": "area_sembrada_ha",
    "Rendimiento (t/ha)": "rendimiento_t_ha",
}'''
new_met = '''METRICAS = {
    "Produccion (t)": "produccion_t",
    "Area Sembrada (ha)": "area_sembrada_ha",
    "Area Cosechada (ha)": "area_cosechada_ha",
    "Rendimiento (t/ha)": "rendimiento_t_ha",
}'''
if old_met in c:
    c = c.replace(old_met, new_met, 1)
    cambios += 1
    print("[OK] Metrica Area Cosechada agregada")

# 2) KPIs del filtro actual (lo unico que aportaba Mapa Cultivos)
anchor = "    # Ranking de apoyo"
kpis = '''    # KPIs del filtro actual (absorbidos de Mapa Cultivos)
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Municipios", df_map["municipio"].nunique())
    k2.metric("Produccion", f"{df_map['produccion_t'].sum():,.0f} t")
    k3.metric("Area sembrada", f"{df_map['area_sembrada_ha'].sum():,.0f} ha")
    cos = df_map["area_cosechada_ha"].sum()
    k4.metric("Rendimiento",
              f"{df_map['produccion_t'].sum()/cos:.2f} t/ha" if cos else "-")

'''
if anchor in c and "KPIs del filtro actual" not in c:
    c = c.replace(anchor, kpis + anchor, 1)
    cambios += 1
    print("[OK] KPIs agregados al Mapa")

p.write_text(c, encoding="utf-8")

# 3) Eliminar entrada del menu y el archivo duplicado
app = Path("app.py")
lines = app.read_text(encoding="utf-8").splitlines(keepends=True)
n = len(lines)
lines = [l for l in lines if "16_Mapa_Cultivos.py" not in l]
if len(lines) != n:
    app.write_text("".join(lines), encoding="utf-8")
    print("[OK] Entrada de Mapa Cultivos eliminada de app.py")

vieja = Path("ui/pages/16_Mapa_Cultivos.py")
if vieja.exists():
    vieja.unlink()
    print("[OK] ui/pages/16_Mapa_Cultivos.py eliminado")

print(f"Total: {cambios} mejoras en 8_Mapa.py")
print("Reinicia Streamlit: ahora hay UN solo Mapa con todo")