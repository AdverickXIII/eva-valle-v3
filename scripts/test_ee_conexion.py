"""Test de conexion a Earth Engine con proyecto ValledelCauca-Forecast."""
import ee

ee.Initialize(project="valledelcauca-forecast")
print("[OK] Conectado a Earth Engine")

# Palmira (centro aproximado) con buffer de 5 km
palmira = ee.Geometry.Point([-76.30, 3.54]).buffer(5000)

# Sentinel-2 sobre Palmira en 2024, nubes < 20%
s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
      .filterDate("2024-01-01", "2024-12-31")
      .filterBounds(palmira)
      .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))

n = s2.size().getInfo()
print(f"[OK] Imagenes Sentinel-2 sobre Palmira en 2024: {n}")
if n and n > 10:
    print("Cobertura satelital suficiente para calcular NDVI")
else:
    print("Pocas imagenes: revisar filtro de nubes")