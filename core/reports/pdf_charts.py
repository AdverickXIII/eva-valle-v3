"""Graficos matplotlib para el PDF (deterministas, sin kaleido)."""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VERDE = "#2E8B57"
AZUL = "#5FA8DC"
NARANJA = "#F4A261"


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


def indice_png(agg) -> bytes:
    base_p = float(agg.p.iloc[0])
    base_a = float(agg.a.iloc[0])
    base_r = float((agg.p / agg.c).iloc[0])
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.plot(agg.index, agg.p / base_p * 100, marker="o", color=VERDE, lw=2,
            label="Produccion")
    ax.plot(agg.index, agg.a / base_a * 100, marker="o", color=NARANJA, lw=2,
            label="Area sembrada")
    ax.plot(agg.index, (agg.p / agg.c) / base_r * 100, marker="o", color=AZUL, lw=2,
            label="Rendimiento")
    ax.axhline(100, color="gray", ls="--", lw=0.8)
    ax.set_title("Motor del crecimiento (indice 2019=100)")
    ax.set_ylabel("Indice (2019=100)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()
