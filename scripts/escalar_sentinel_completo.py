"""Escalamiento completo: NDVI satelital de los 42 municipios del Valle (2019-2025)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ee
import pandas as pd
import time
from config.settings import settings

print("Inicializando Earth Engine...")
ee.Initialize(project="valledelcauca-forecast")

# Cargar datos EVA
path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
df = pd.read_csv(path, low_memory=False)

# Coordenadas aproximadas de los 42 municipios (centroide)
MUNICIPIOS_COORDS = {
    "Palmira": (-76.30, 3.54), "Cali": (-76.53, 3.45), "Buenaventura": (-77.03, 3.89),
    "Tuluá": (-76.20, 4.09), "Cartago": (-75.91, 4.75), "Buga": (-76.69, 3.90),
    "Jamundí": (-76.54, 3.26), "Florida": (-76.15, 3.32), "Candelaria": (-76.34, 3.41),
    "Yumbo": (-76.49, 3.58), "Pradera": (-76.04, 3.42), "El Cerrito": (-76.30, 3.68),
    "Dagua": (-76.69, 3.66), "La Cumbre": (-76.56, 3.72), "Vijes": (-76.55, 3.72),
    "Restrepo": (-76.53, 3.82), "La Victoria": (-76.03, 4.52), "Obando": (-75.95, 4.59),
    "Zarzal": (-76.08, 4.39), "Bugalagrande": (-76.16, 4.21), "Guacarí": (-76.33, 3.76),
    "Ansermanuevo": (-76.03, 4.63), "Roldanillo": (-76.15, 4.41), "El Dovio": (-76.23, 4.52),
    "Versalles": (-76.12, 4.67), "El Águila": (-76.08, 4.75), "Argelia": (-76.15, 4.73),
    "Riofrío": (-76.28, 4.58), "Trujillo": (-76.34, 4.48), "Bolívar": (-76.18, 4.33),
    "San Pedro": (-76.23, 3.97), "Ginebra": (-76.22, 3.83), "Guadalajara de Buga": (-76.69, 3.90),
    "Toro": (-76.08, 4.62), "La Unión": (-76.13, 4.59), "Alcalá": (-75.85, 4.68),
    "Ulloa": (-75.92, 4.72), "Caicedonia": (-75.83, 4.33), "Sevilla": (-75.93, 4.27),
    "Calima": (-76.65, 3.92), "Yotoco": (-76.52, 3.86), "Darien": (-76.55, 3.91),
}

municipios_eva = df['municipio'].unique()
municipios_a_procesar = [m for m in municipios_eva if m in MUNICIPIOS_COORDS]
print(f"Municipios a procesar: {len(municipios_a_procesar)}\n")

resultados = []

# 👇 QUITAMOS EL LIMITE DE 10 PARA PROCESAR TODOS
for idx, municipio in enumerate(municipios_a_procesar, 1):
    print(f"[{idx}/{len(municipios_a_procesar)}] Procesando {municipio}...")
    
    lon, lat = MUNICIPIOS_COORDS[municipio]
    zona = ee.Geometry.Point([lon, lat]).buffer(10000)  # 10km buffer
    
    for ano in range(2019, 2026):
        try:
            s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterDate(f"{ano}-01-01", f"{ano}-12-31")
                  .filterBounds(zona)
                  .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)))
            
            n_imagenes = s2.size().getInfo()
            
            if n_imagenes < 5:
                resultados.append({"municipio": municipio, "ano": ano, "ndvi_mean": None, "n_imagenes": n_imagenes, "error": "Nublado"})
                continue
            
            def add_ndvi(image):
                return image.addBands(image.normalizedDifference(['B8', 'B4']).rename('NDVI'))
            
            median_ndvi = s2.map(add_ndvi).median()
            ndvi_mean = median_ndvi.select('NDVI').reduceRegion(
                reducer=ee.Reducer.mean(), geometry=zona, scale=10, maxPixels=1e9
            ).get('NDVI').getInfo()
            
            print(f"  {ano}: NDVI={ndvi_mean:.3f} ({n_imagenes} img)")
            resultados.append({"municipio": municipio, "ano": ano, "ndvi_mean": ndvi_mean, "n_imagenes": n_imagenes, "error": None})
            
        except Exception as e:
            print(f"  {ano}: ERROR - {str(e)[:50]}")
            resultados.append({"municipio": municipio, "ano": ano, "ndvi_mean": None, "n_imagenes": 0, "error": str(e)})
    
    time.sleep(1) # Pausa de respeto a la API

df_ndvi = pd.DataFrame(resultados)

# Cruce con EVA (Codigo optimizado para evitar warnings de pandas)
print("\n\nCruzando con datos EVA...")
df_eva_agg = df.groupby(['municipio', 'ano']).apply(
    lambda g: pd.Series({
        'area_cosechada_eva': g['area_cosechada_ha'].sum(),
        'produccion_eva': g['produccion_t'].sum(),
        'area_cana': g.loc[g['cultivo'] == 'Caña', 'area_cosechada_ha'].sum()
    })
).reset_index()

df_final = df_ndvi.merge(df_eva_agg, on=['municipio', 'ano'], how='left')

# Evaluar coherencia
def evaluar_coherencia(row):
    if pd.isna(row['ndvi_mean']): return "Sin datos satelitales"
    ndvi, area = row['ndvi_mean'], row['area_cosechada_eva']
    if pd.isna(area) or area == 0: return "Sin datos EVA"
    
    if ndvi > 0.6 and area > 5000: return "✅ Coherente (Alto NDVI / Alta Area)"
    elif ndvi > 0.4 and area > 1000: return "✅ Coherente"
    elif ndvi < 0.3 and area > 10000: return "⚠️ Anomalía: NDVI bajo vs Area alta"
    elif ndvi > 0.7 and area < 500: return "⚠️ Anomalía: NDVI alto vs Area baja"
    else: return "➖ Indeterminado"

df_final['coherencia'] = df_final.apply(evaluar_coherencia, axis=1)

# Guardar
out_path = Path("outputs/sentinel_ndvi_VALLE_COMPLETO.csv")
df_final.to_csv(out_path, index=False)

print(f"\n{'='*70}")
print(f"✅ PROCESAMIENTO COMPLETADO DEL VALLE DEL CAUCA")
print(f"{'='*70}")
print(f"Resultados guardados en: {out_path}")
print(f"Total registros: {len(df_final)}")
print(f"\nResumen por coherencia:\n{df_final['coherencia'].value_counts()}")

print(f"\nTop 5 municipios con mayor NDVI promedio:")
print(df_final.groupby('municipio')['ndvi_mean'].mean().sort_values(ascending=False).head())

print(f"\nMunicipios con anomalías detectadas:")
anomalías = df_final[df_final['coherencia'].str.contains('Anomalía', na=False)]
if len(anomalías) > 0:
    print(anomalías[['municipio', 'ano', 'ndvi_mean', 'area_cosechada_eva', 'coherencia']])
else:
    print("Ninguna anomalía detectada en el departamento.")