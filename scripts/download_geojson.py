"""Descarga GeoJSON de municipios de Colombia y filtra el Valle del Cauca."""
import json
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/santiblanko/colombia.geojson/master/mpio.json"

print("Descargando GeoJSON de municipios de Colombia...")
with urllib.request.urlopen(URL) as r:
    data = json.load(r)

# Filtrar solo Valle del Cauca (codigo DANE departamento = 76)
valle = [f for f in data["features"] if str(f["properties"].get("DPTO")) == "76"]

out = {"type": "FeatureCollection", "features": valle}
Path("data/external").mkdir(parents=True, exist_ok=True)
dest = Path("data/external/valle_municipios.geojson")
dest.write_text(json.dumps(out), encoding="utf-8")

print(f"[OK] {len(valle)} municipios del Valle guardados en {dest}")
print(f"     Tamano: {dest.stat().st_size/1024:.0f} KB")