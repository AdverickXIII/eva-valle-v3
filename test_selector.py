"""Prueba del selector de modelos para Alcala / Platano."""
from core.analytics.model_selector import recomendar

r = recomendar("Alcalá", "Plátano")
print("=" * 60)
print("Modelo recomendado:", r["modelo"])
print("APE estimado:", r["ape_est"], "%")
print("IC 95%:       ", r["ic"])
print("Explorar:     ", "SI" if r["explorar"] else "NO")
print("Alternativa:  ", r["alternativa"])
print("=" * 60)
print("\nTabla completa:")
print(r["tabla"].to_string())