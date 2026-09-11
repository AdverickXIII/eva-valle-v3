"""AUD-UI-018: recorta logo.png al bloque del icono (el mas alto del lockup).
Analiza bloques horizontales por canal alfa, elige el de mayor altura (el circulo),
y lo guarda como logo.png. Original reservado en logo.png.bak.
Idempotente: si el recorte ya cubre todo el canvas, no hace nada.
"""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
LOGO = RAIZ / "ui" / "assets" / "img" / "logo.png"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def main():
    if not LOGO.is_file():
        print(f"[ERROR] no existe {LOGO}")
        return 1

    bak = LOGO.with_suffix(".png.bak")
    if not bak.exists():
        shutil.copy2(LOGO, bak)
        print(f"[OK] original reservado: {bak.name}")

    im = Image.open(LOGO).convert("RGBA")
    a = np.array(im.getchannel("A"))
    cols = (a > 8).sum(axis=0)

    # Bloques horizontales separados por columnas vacias
    bloques = []
    start = None
    for i, v in enumerate(cols):
        if v > 0 and start is None:
            start = i
        elif v == 0 and start is not None:
            if i - start >= 10:
                bloques.append((start, i))
            start = None
    if start is not None and len(cols) - start >= 10:
        bloques.append((start, len(cols)))
    if not bloques:
        print("[ERROR] sin contenido no transparente; nada que recortar")
        return 1

    # Alto real de cada bloque (filas con contenido dentro de sus columnas)
    info = []
    for (x0, x1) in bloques:
        rows = (a[:, x0:x1] > 8).sum(axis=1)
        ys = np.nonzero(rows)[0]
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        info.append((x0, x1, y0, y1))
        print(f"[INFO] bloque x:{x0}-{x1} (ancho {x1-x0}) | alto {y1-y0}")

    icono = max(info, key=lambda t: t[3] - t[2])  # el bloque mas alto = el circulo
    x0, x1, y0, y1 = icono
    w, h = im.size
    if (x0, y0, x1, y1) == (0, 0, w, h):
        print("[SKIP] el canvas ya es solo el icono; nada que recortar")
        return 0

    rec = im.crop((x0, y0, x1, y1))
    rec.save(LOGO)
    print(f"[OK] logo.png recortado a {rec.size[0]}x{rec.size[1]} | antes: {w}x{h}")
    audit("AUD-UI-018", "OK", f"logo {w}x{h} -> {rec.size[0]}x{rec.size[1]} (bloque icono)")
    print("Siguiente: streamlit run app.py -> circulo pleno en sidebar, login y Home")
    return 0


if __name__ == "__main__":
    sys.exit(main())