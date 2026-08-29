"""Rompe el cache de Streamlit del Recomendador y verifica que la zona este llena."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))

# 1) Romper cache agregando version al key del @st.cache_data
p = Path("ui/pages/22_Recomendador.py")
c = p.read_text(encoding="utf-8")
old_cache = '@st.cache_data(show_spinner=False)'
new_cache = '@st.cache_data(show_spinner=False, ttl=1)'  # TTL de 1 segundo fuerza recarga
if old_cache in c:
    c = c.replace(old_cache, new_cache, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Cache de Streamlit roto (ttl=1s)")
else:
    print("[INFO] Cache ya estaba configurado o no existe")

# 2) Verificar directamente el IRS (sin Streamlit)
from core.analytics.irs import build_irs, load_df
irs = build_irs(load_df())
top = irs[irs.municipio == "Alcalá"].head(5)

print("\n--- Top 5 de Alcala en el IRS (sin cache) ---")
print(top[["cultivo", "IRS", "LQ", "CAGR", "etiqueta", "zona"]].to_string(index=False))

zonas_llenas = (top["zona"] != "n/d").all()
print(f"\nZonas llenas: {'SI ✅' if zonas_llenas else 'NO ❌'}")

if not zonas_llenas:
    print("\n[!] La columna zona sigue vacia. Verificando irs.py...")
    irs_code = Path("core/analytics/irs.py").read_text(encoding="utf-8")
    if "_ZONA_MUNICIPIO" in irs_code and 'zona = pd.Series(_ZONA_MUNICIPIO)' in irs_code:
        print("    El codigo esta correcto pero no se esta aplicando.")
        print("    Ejecuta:  streamlit cache clear")
    else:
        print("    El parche no se aplico correctamente a irs.py")