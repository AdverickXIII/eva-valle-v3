"""PDF de comparativa municipal: tabla con ganador + radar + mariposa."""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from core.reports.branding import pagina_con_logo
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image as RLImage, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from core.reports import meta

VERDE = "#2E8B57"
NARANJA = "#DD6B20"
VERDE_RL = colors.HexColor("#2E8B57")


def _style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_RL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
    ])


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()


def _add_png(story, png):
    img = RLImage(io.BytesIO(png))
    w = 16.5 * cm
    h = img.drawHeight * w / img.drawWidth
    img.drawWidth, img.drawHeight = w, h
    story += [img, Spacer(1, 0.4 * cm)]


def _radar_png(labels, ra, rb, a, b) -> bytes:
    ang = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    ra = ra + ra[:1]
    rb = rb + rb[:1]
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=(7.0, 5.4), subplot_kw=dict(polar=True))
    ax.plot(ang, ra, "o-", color=VERDE, lw=2, label=a)
    ax.fill(ang, ra, alpha=0.22, color=VERDE)
    ax.plot(ang, rb, "o-", color=NARANJA, lw=2, label=b)
    ax.fill(ang, rb, alpha=0.22, color=NARANJA)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6, color="gray")
    ax.set_title("Perfil economico (100 = el mejor de los dos)", fontsize=10, pad=16)
    ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.12), fontsize=8)
    fig.tight_layout()
    return _png(fig)


def _mariposa_png(groups, va, vb, a, b) -> bytes:
    y = np.arange(len(groups))
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.barh(y, [-v / 1000 for v in va], color=VERDE, label=a, height=0.62)
    ax.barh(y, [v / 1000 for v in vb], color=NARANJA, label=b, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(groups, fontsize=8)
    ax.invert_yaxis()
    ax.axvline(0, color="gray", lw=0.8)
    ticks = ax.get_xticks()
    ax.set_xticklabels([f"{abs(t):,.0f}" for t in ticks], fontsize=7)
    ax.set_xlabel("Miles de t", fontsize=8)
    ax.set_title("Cara a cara por grupo de cultivo", fontsize=10)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.2, axis="x")
    fig.tight_layout()
    return _png(fig)




def _rend_png(df_ab, a, b) -> bytes:
    rend = (df_ab.groupby(["ano", "municipio"])
            .agg(prod=("produccion_t", "sum"), cos=("area_cosechada_ha", "sum"))
            .reset_index())
    rend["rend"] = rend["prod"] / rend["cos"].replace(0, 1)
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    for m, col in ((a, VERDE), (b, NARANJA)):
        d = rend[rend["municipio"] == m].sort_values("ano")
        ax.plot(d["ano"], d["rend"], "o-", color=col, lw=2, label=m)
    ax.set_ylabel("t/ha", fontsize=8)
    ax.set_title("Rendimiento por ano (t/ha)", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _png(fig)


def build_comparador_pdf(a, b, sin_cana, comp_df, sa, sb, df_ab) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, onPage=pagina_con_logo, pagesize=letter, title="Comparativa municipal")
    st_ = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=st_["Title"], textColor=VERDE_RL, fontSize=16)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=11, fontSize=9)

    story = [
        Paragraph(f"Comparativa agricola: {a} vs {b}", h1),
        Paragraph(f"Escenario: {'SIN cana (economia real)' if sin_cana else 'CON cana'} | "
                  "Periodo: 2019-2025", body),
        Spacer(1, 0.4 * cm),
        Paragraph("<b>Indicadores cara a cara</b>", body),
    ]

    rows = [["Indicador", f"A: {a}", f"B: {b}", "Gana"]]
    gana_txt = []
    for _, r in comp_df.iterrows():
        g = str(r["Gana"])
        if "🅰️" in g:
            gt = f"A ({a})"
        elif "🅱️" in g:
            gt = f"B ({b})"
        elif "Empate" in g:
            gt = "Empate"
        else:
            gt = "-"
        gana_txt.append(gt)
        rows.append([str(r["Indicador"]), str(r[f"A · {a}"]), str(r[f"B · {b}"]), gt])
    t = Table(rows, hAlign="LEFT")
    t.setStyle(_style())
    story += [t, Spacer(1, 0.3 * cm)]

    n_a = sum(1 for g in gana_txt if g.startswith("A ("))
    n_b = sum(1 for g in gana_txt if g.startswith("B ("))
    story.append(Paragraph(
        f"<b>Marcador:</b> {a} gana {n_a} indicadores | {b} gana {n_b} | "
        f"escenario {'sin cana' if sin_cana else 'con cana'}.", body))
    story.append(Spacer(1, 0.4 * cm))

    # ---------- RADAR ----------
    keys = ["Produccion total (t)", "Rendimiento (t/ha)", "Diversidad (Shannon)",
            "CAGR 2019-2025 (%)", "Area sembrada (ha)"]
    labels = ["Produccion", "Rendimiento", "Diversidad", "Crecimiento", "Area"]
    ra, rb = [], []
    for k in keys:
        va, vb = max(0.0, sa[k]), max(0.0, sb[k])
        mx = max(va, vb) or 1.0
        ra.append(va / mx * 100)
        rb.append(vb / mx * 100)
    story.append(Paragraph("<b>Perfil economico</b>", body))
    _add_png(story, _radar_png(labels, ra, rb, a, b))

    # ---------- MARIPOSA ----------
    g = df_ab.groupby(["grupo_cultivo", "municipio"])["produccion_t"].sum()
    piv = g.unstack(fill_value=0)
    for col in (a, b):
        if col not in piv.columns:
            piv[col] = 0
    piv["tot"] = piv[a] + piv[b]
    piv = piv.sort_values("tot", ascending=False).head(8)
    groups = piv.index.tolist()
    story.append(Paragraph("<b>Cara a cara por grupo de cultivo</b>", body))
    _add_png(story, _mariposa_png(groups, [piv.loc[x, a] for x in groups],
                                  [piv.loc[x, b] for x in groups], a, b))

    story.append(Paragraph("<b>Rendimiento por ano (t/ha)</b>", body))
    _add_png(story, _rend_png(df_ab, a, b))

    story.append(Paragraph(
        f"Fuente: UPRA - EVA 2019-2025. {meta.firma()}.",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8)))
    doc.build(story)
    return buf.getvalue()
