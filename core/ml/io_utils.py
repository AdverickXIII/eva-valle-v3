"""Convencion unica de guardado de resultados del curso."""
import json
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
DATA = Path(__file__).resolve().parent / "data"


def save_json(name, obj):
    RESULTS.mkdir(parents=True, exist_ok=True)
    p = RESULTS / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] guardado: {p}")
    return p


def save_csv(name, df):
    RESULTS.mkdir(parents=True, exist_ok=True)
    p = RESULTS / name
    df.to_csv(p, index=False)
    print(f"[OK] guardado: {p}")
    return p


def save_png(name, fig):
    RESULTS.mkdir(parents=True, exist_ok=True)
    p = RESULTS / name
    fig.savefig(p, dpi=120, bbox_inches="tight")
    print(f"[OK] guardado: {p}")
    return p
