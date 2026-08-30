"""Diagnostico de fuentes oficiales de precios para EVA Valle."""
import requests
import pandas as pd

FUENTES = {
    "SIPSA_P_DANE": "gkqq-k3k5",
    "SIPSA_A_ABASTECIMIENTO": "ymnp-apvk",
    "SIPSA_I_INSUMOS": "cpad-s27y",
    "TIERRA_RURAL_UPRA": "rttb-pk7n",
}

print("=== 1) Metadatos Socrata datos.gov.co ===")
for nombre, dsid in FUENTES.items():
    url = f"https://www.datos.gov.co/api/views/{dsid}"
    try:
        r = requests.get(url, timeout=30)
        print(f"\n--- {nombre} ({dsid}) ---")
        if r.status_code != 200:
            print("HTTP", r.status_code)
            continue
        meta = r.json()
        print("Nombre:", meta.get("name"))
        print("Agencia:", meta.get("metadata", {}).get("custom_fields", {}).get("Entidad", {}))
        print("Filas aprox:", meta.get("columns", [{}])[0].get("cachedContents", {}).get("count"))
        print("Columnas:")
        for col in meta.get("columns", [])[:20]:
            print("  -", col.get("name"), "|", col.get("dataTypeName"))
    except Exception as e:
        print("[ERROR]", nombre, e)

print("\n=== 2) Prueba de descarga CSV tierra rural ===")
try:
    tierra = pd.read_csv("https://www.datos.gov.co/resource/rttb-pk7n.csv?$limit=5000")
    print("Tierra:", tierra.shape)
    print(tierra.head(3).to_string())
except Exception as e:
    print("[ERROR tierra]", e)

print("\n=== 3) Intento CSV directo SIPSA_P ===")
try:
    sipsa = pd.read_csv("https://www.datos.gov.co/resource/gkqq-k3k5.csv?$limit=5000")
    print("SIPSA_P:", sipsa.shape)
    print(sipsa.head(3).to_string())
except Exception as e:
    print("[AVISO SIPSA_P directo]", e)
    print("Es posible que el dataset sea paquete ZIP por año, no tabla Socrata directa.")

print("\n=== 4) Busqueda ampliada en catalogo ===")
queries = [
    "precios primer mercado",
    "primer mercado UPRA",
    "boletines precios primer mercado",
    "SIPSA precios mayoristas",
    "precios mayoristas productos agropecuarios",
    "plátano precio mayorista",
]

for q in queries:
    r = requests.get(
        "https://www.datos.gov.co/api/catalog/v1",
        params={"only": "dataset", "q": q, "limit": 5},
        timeout=30,
    )
    cats = r.json().get("results", [])
    print(f"\n--- '{q}': {len(cats)} candidatos ---")
    for c in cats:
        res = c.get("resource", {})
        print(res.get("id"), "|", res.get("name"))