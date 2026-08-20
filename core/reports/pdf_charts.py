"""Graficos matplotlib para el PDF (deterministas, sin kaleido)."""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VERDE = "#2E8B57"
AZUL = "#5FA8DC"
ROJO = "#D62728"


def serie_png(agg) -> bytes:
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 6.2), sharex=True)
    axes[0].plot(agg.index, agg.p / 1000.0, marker="o", color=VERDE, lw=2)
    axes[0].set_title("Produccion (miles de t)")
    axes[0].grid(alpha=0.3)
    axes[1].plot(agg.index, agg.p / agg.c, marker="o", color=AZUL, lw=2)
    axes[1].set_title("Rendimiento (t/ha)")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()


def motor_png(diag) -> bytes:
    vals = [diag["cagr_prod"], diag["cagr_area"], diag["cagr_rend"]]
    labs = ["CAGR produccion", "CAGR area", "CAGR rendimiento"]
    cols = [VERDE if v >= 0 else ROJO for v in vals]
    fig, ax = plt.subplots(figsize=(8.5, 2.6))
    ax.barh(labs, vals, color=cols)
    for i, v in enumerate(vals):
        ax.text(v + (0.3 if v >= 0 else -0.3), i, f"{v:+.1f}%",
                va="center", ha="left" if v >= 0 else "right", fontsize=9)
    ax.axvline(0, color="gray", lw=0.8)
    ax.set_title("Motor del crecimiento (%)")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()
