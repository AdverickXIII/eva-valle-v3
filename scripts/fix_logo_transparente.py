"""Quita el fondo crema del logo y lo vuelve transparente (canal alfa)."""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

p = Path("ui/assets/img/logo.png")
bak = Path("ui/assets/img/logo_original.png")
if not bak.exists():
    shutil.copy(p, bak)
    print("[OK] Respaldo guardado en logo_original.png")

img = Image.open(p).convert("RGBA")
a = np.array(img).astype(np.int32)
bg = a[0, 0, :3]                      # color de fondo tomado de la esquina
d = np.sqrt(((a[..., :3] - bg) ** 2).sum(axis=-1))
alpha = np.clip((d - 25.0) / (60.0 - 25.0) * 255.0, 0, 255).astype(np.uint8)
a[..., 3] = alpha
Image.fromarray(a.astype(np.uint8), "RGBA").save(p)
print(f"[OK] Fondo removido (crema {tuple(bg)} -> transparente)")

# Regenera los PDF oficiales para que embeban el logo limpio
sys.path.insert(0, str(Path(".").resolve()))
try:
    from core.reports.presentacion_oficial import (build_ficha_tecnica_pdf,
                                                   build_presentacion_pdf)
    Path("outputs/ficha_tecnica_EVA_Valle.pdf").write_bytes(build_ficha_tecnica_pdf())
    Path("outputs/presentacion_ejecutiva_EVA_Valle.pdf").write_bytes(build_presentacion_pdf())
    print("[OK] PDFs oficiales regenerados con logo transparente")
except Exception as e:
    print("[AVISO] Regenera los PDFs desde la pagina Reportes:", e)