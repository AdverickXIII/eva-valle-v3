"""Agrega save_png al helper."""
from pathlib import Path
p = Path("core/ml/io_utils.py")
c = p.read_text(encoding="utf-8")
fn = '''

def save_png(name, fig):
    RESULTS.mkdir(parents=True, exist_ok=True)
    p = RESULTS / name
    fig.savefig(p, dpi=120, bbox_inches="tight")
    print(f"[OK] guardado: {p}")
    return p
'''
if "def save_png" not in c:
    p.write_text(c + fn, encoding="utf-8")
    print("[OK] save_png agregado a io_utils.py")