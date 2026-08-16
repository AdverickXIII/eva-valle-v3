"""Opcion B: imagen Planet NICFI 4.77m de Palmira para exhibicion."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ee
import requests

ee.Initialize(project="valledelcauca-forecast")

palmira = ee.Geometry.Point([-76.30, 3.54]).buffer(3000)

col = (ee.ImageCollection("projects/planet-nicfi/assets/basemaps/tropics")
       .filterBounds(palmira)
       .filterDate("2023-06-01", "2024-12-31"))

img = col.sort("system:time_start", False).first()
if img is None:
    print("[ERROR] Sin imagenes NICFI. Debes aceptar los terminos de Planet NICFI:")
    print("https://developers.planet.com/docs/integrations/google-earth-engine/")
    raise SystemExit(1)

fecha = img.get("system:time_start").format("YYYY-MM").getInfo()
print(f"Mosaico NICFI seleccionado: {fecha} (4.77 m)")

rgb = img.select("R", "G", "B")
url = rgb.getThumbURL({"region": palmira, "dimensions": 1200, "format": "png"})
r = requests.get(url, timeout=120)

out = Path("outputs/palmira_alta_resolucion.png")
out.write_bytes(r.content)
print(f"[OK] Imagen guardada: {out} ({out.stat().st_size/1024:.0f} KB)")
print("Usala como portada del capitulo de Validacion Satelital.")