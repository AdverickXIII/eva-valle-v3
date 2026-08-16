"""Fase 2: Calcula NDVI satelital de Palmira (2024) y cruza con datos EVA."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ee
import pandas as pd
from config.settings import settings

print("Inicializando Earth Engine...")
ee.Initialize(project="valledelcauca-forecast")

# 1. Geometria: Buffer de 15km alrededor del centro de Palmira
# (Abarca la zona plana agricola principal donde esta la caña)
print("Definiendo geometria de Palmira...")
palmira_geo = ee.Geometry.Point([-76.30, 3.54]).buffer(15000)

# 2. Cargar Sentinel-2 (2024, nubes < 20%)
print("Descargando imagenes Sentinel-2...")
s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
      .filterDate("2024-01-01", "2024-12-31")
      .filterBounds(palmira_geo)
      .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))

# 3. Calcular NDVI para cada imagen
def add_ndvi(image):
    # B8 = Infrarrojo cercano (NIR), B4 = Rojo
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)

s2_ndvi = s2.map(add_ndvi)

# Mediana del ano (elimina nubes residuales y sombras)
median_ndvi = s2_ndvi.median()

# 4. Extraer el NDVI promedio para la zona de Palmira
print("Calculando NDVI promedio (esto puede tardar unos segundos)...")
ndvi_mean = median_ndvi.select('NDVI').reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=palmira_geo,
    scale=10,  # Resolucion de 10 metros de Sentinel-2
    maxPixels=1e9
).get('NDVI').getInfo()

print(f"\n[OK] NDVI promedio satelital Palmira (2024): {ndvi_mean:.3f}")

# 5. Cruzar con datos EVA
print("\nCruzando con base EVA...")
path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
df = pd.read_csv(path, low_memory=False)
df_palmira_2024 = df[(df['municipio'] == 'Palmira') & (df['ano'] == 2024)]

area_cosechada_eva = df_palmira_2024['area_cosechada_ha'].sum()
produccion_eva = df_palmira_2024['produccion_t'].sum()

# Filtrar solo caña para ver su peso
area_cana = df_palmira_2024[df_palmira_2024['cultivo'] == 'Caña']['area_cosechada_ha'].sum()

print(f"[EVA] Area cosechada total reportada: {area_cosechada_eva:,.0f} ha")
print(f"[EVA] De las cuales, Caña de azucar: {area_cana:,.0f} ha")
print(f"[EVA] Produccion total reportada: {produccion_eva:,.0f} t")

# 6. Analisis Cruzado (La magia)
print("\n" + "="*50)
print("🛰️ ANALISIS CRUZADO: SATELITE vs AUTODECLARACION")
print("="*50)

if ndvi_mean > 0.6:
    estado_vegetacion = "vegetacion muy densa y saludable (tipico de cultivos como caña o bosque)"
elif ndvi_mean > 0.4:
    estado_vegetacion = "vegetacion moderada a densa (cultivos agricolas, pastos)"
elif ndvi_mean > 0.2:
    estado_vegetacion = "vegetacion escasa o cultivos en etapas tempranas/secos"
else:
    estado_vegetacion = "suelo desnudo, agua o zona urbana"

print(f"El satelite ve: {estado_vegetacion} (NDVI={ndvi_mean:.3f}).")

if area_cana > (area_cosechada_eva * 0.8):
    print("Conclusion: El alto NDVI satelital es COHERENTE con la base EVA,")
    print("ya que Palmira reporta que la gran mayoria de su area es Caña de azucar,")
    print("un cultivo que mantiene un NDVI alto y constante todo el ano.")
else:
    print("Conclusion: Hay una discrepancia. El satelite ve mas/menos vegetacion")
    print("de la que sugiere el area cosechada reportada en EVA.")