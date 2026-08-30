"""Explora el paquete SIPSA_P 2024 (ZIP) de datos.gov.co."""
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

VIEW = "gkqq-k3k5"
meta = requests.get(f"https://www.datos.gov.co/api/views/{VIEW}", timeout=60).json()
atts = meta.get("metadata", {}).get("attachments", []) or meta.get("attachments", [])
print("Adjuntos del dataset:")
for a in atts:
    print(" -", a.get("name"), "| assetId:", a.get("assetId"))

target = next((a for a in atts if "2024" in str(a.get("name", ""))), None)
if target is None and atts:
    target = atts[-1]
if target is None:
    print("[!] Sin adjuntos en metadata")
    raise SystemExit(1)

url = (f"https://www.datos.gov.co/api/views/{VIEW}/files/{target['assetId']}"
       f"?download=true&filename={target.get('name', 'sipsa.zip')}")
print("\nDescargando:", target.get("name"), "...")
z = requests.get(url, timeout=600)
print("MB:", round(len(z.content) / 1e6, 1))

raw = Path("data/raw")
raw.mkdir(parents=True, exist_ok=True)
(raw / "sipsa_p_2024.zip").write_bytes(z.content)

with zipfile.ZipFile(io.BytesIO(z.content)) as zfile:
    names = zfile.namelist()
    print("\nArchivos internos:")
    for n in names[:15]:
        print(" -", n)
    cand = [n for n in names if n.lower().endswith((".csv", ".xlsx", ".xls"))]
    if cand:
        with zfile.open(cand[0]) as f:
            d = (pd.read_csv(f, nrows=2000) if cand[0].lower().endswith(".csv")
                 else pd.read_excel(f, nrows=2000))
        print(f"\nVista de {cand[0]} -> {d.shape}")
        print("Columnas:", list(d.columns))
        print(d.head(3).to_string())