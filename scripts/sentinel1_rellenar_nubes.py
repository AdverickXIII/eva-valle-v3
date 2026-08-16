"""Opcion A: Sentinel-1 (radar) rellena los registros perdidos por nubosidad."""
import sys
import math
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ee
import pandas as pd

ee.Initialize(project="valledelcauca-forecast")

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

df = pd.read_csv("outputs/sentinel_ndvi_VALLE_COMPLETO.csv")
faltantes = df[df["ndvi_mean"].isna()][["municipio", "ano"]].drop_duplicates()
print(f"Registros nublados a rellenar con radar: {len(faltantes)}\n")

radar = []
for i, (_, row) in enumerate(faltantes.iterrows(), 1):
    m, ano = row["municipio"], int(row["ano"])
    if m not in MUNICIPIOS_COORDS:
        continue
    lon, lat = MUNICIPIOS_COORDS[m]
    zona = ee.Geometry.Point([lon, lat]).buffer(10000)
    try:
        s1 = (ee.ImageCollection("COPERNICUS/S1_GRD")
              .filterBounds(zona)
              .filterDate(f"{ano}-01-01", f"{ano}-12-31")
              .filter(ee.Filter.eq("instrumentMode", "IW"))
              .filter(ee.Filter.eq("transmitterReceiverPolarisation", "VV_VH"))
              .select(["VV", "VH"]))
        n = s1.size().getInfo()
        if n == 0:
            radar.append({"municipio": m, "ano": ano, "rvi": None,
                          "vh_db": None, "n_img_radar": 0})
            print(f"[{i}/{len(faltantes)}] {m} {ano}: sin imagenes radar")
            continue

        def con_rvi(img):
            vv = img.select("VV")
            vh = img.select("VH")
            rvi = vh.multiply(4).divide(vv.add(vh)).rename("RVI")
            return img.addBands(rvi)

        comp = s1.map(con_rvi).median()
        st = comp.select(["VH", "RVI"]).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=zona,
            scale=20, maxPixels=1e9).getInfo()

        vh_db = 10 * math.log10(st["VH"]) if st.get("VH") else None
        rvi_v = st.get("RVI")
        radar.append({"municipio": m, "ano": ano, "rvi": round(rvi_v, 3) if rvi_v else None,
                      "vh_db": round(vh_db, 2) if vh_db else None, "n_img_radar": n})
        print(f"[{i}/{len(faltantes)}] {m} {ano}: RVI={rvi_v:.3f} VH={vh_db:.1f} dB ({n} img)")
    except Exception as e:
        print(f"[{i}/{len(faltantes)}] {m} {ano}: ERROR {str(e)[:60]}")
        radar.append({"municipio": m, "ano": ano, "rvi": None, "vh_db": None, "n_img_radar": 0})
    time.sleep(0.5)

df_radar = pd.DataFrame(radar)
df_radar.to_csv("outputs/sentinel_radar_complemento.csv", index=False)

# --- Merge optico + radar y nueva coherencia ---
df = df.merge(df_radar, on=["municipio", "ano"], how="left")

def coherencia_final(row):
    if not pd.isna(row["ndvi_mean"]):
        return row["coherencia"], "Optico"
    if not pd.isna(row.get("vh_db")):
        vh, area = row["vh_db"], row["area_cosechada_eva"]
        if -20 <= vh <= -10 and area > 1000:
            return "✅ Coherente (radar)", "Radar"
        if vh < -20 and area > 10000:
            return "⚠️ Anomalía radar: superficie lisa vs area alta", "Radar"
        return "➖ Indeterminado (radar)", "Radar"
    return "Sin datos", "Ninguna"

res = df.apply(coherencia_final, axis=1, result_type="expand")
df["coherencia_final"] = res[0]
df["fuente"] = res[1]

df.to_csv("outputs/validacion_optica_radar.csv", index=False)

print(f"\n{'='*70}")
print("COBERTURA COMBINADA OPTICO + RADAR")
print(f"{'='*70}")
print(df["fuente"].value_counts())
print("\nCoherencia final:")
print(df["coherencia_final"].value_counts())
print("\nGuardado: outputs/validacion_optica_radar.csv")