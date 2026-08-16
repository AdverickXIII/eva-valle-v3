"""Imagen de exhibicion: Sentinel-2 color real (10 m) de los canaverales de Palmira."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ee
import requests

ee.Initialize(project="valledelcauca-forecast")

palmira = ee.Geometry.Point([-76.30, 3.54]).buffer(3000)

# Temporada con menos nubes (jul-sep 2024)
col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
       .filterBounds(palmira)
       .filterDate("2024-07-01", "2024-09-30")
       .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 15)))

if col.size().getInfo() == 0:
    print("[INFO] Sin imagenes en jul-sep; usando todo 2024")
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(palmira)
           .filterDate("2024-01-01", "2024-12-31")
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))

img = col.median()
rgb = img.select(["B4", "B3", "B2"])  # color real (R, G, B)

url = rgb.getThumbURL({"region": palmira, "dimensions": 1200,
                       "format": "png", "min": 0, "max": 3000})
r = requests.get(url, timeout=120)

out = Path("outputs/palmira_canaverales_sentinel2.png")
out.write_bytes(r.content)
print(f"[OK] Imagen guardada: {out} ({out.stat().st_size/1024:.0f} KB)")
print("Caption sugerido: 'Canaaverales de Palmira. Sentinel-2, resolucion 10 m, ESA.'")