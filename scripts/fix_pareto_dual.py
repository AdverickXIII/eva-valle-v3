"""Agrega Pareto CON cana y SIN cana, compactos y lado a lado, en la Seccion 2."""
from pathlib import Path

p = Path("core/reports/executive_report.py")
c = p.read_text(encoding="utf-8")

# --- 1. Reemplazar _pareto_sin_cana por _pareto generico ---
i1 = c.find("def _pareto_sin_cana")
j1 = c.find("def build_executive_pdf")
if i1 == -1 or j1 == -1:
    print("[ERROR] No encontre la funcion _pareto_sin_cana")
    raise SystemExit(1)

NEW_FUNC = '''def _pareto(df: pd.DataFrame, exclude_cana: bool, color=VERDE,
            width: float = 230, height: float = 140) -> Drawing:
    """Pareto horizontal compacto (con o sin cana)."""
    p = pareto(df, exclude_cana, 8)
    d = Drawing(width, height)
    bc = HorizontalBarChart()
    bc.x = 80
    bc.y = 6
    bc.height = height - 16
    bc.width = width - 88
    bc.data = [list(p["share"])]
    bc.categoryAxis.categoryNames = list(p["cultivo"])
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 6
    bc.valueAxis.valueMin = 0
    bc.valueAxis.labels.fontSize = 6
    bc.bars[0].fillColor = color
    bc.barWidth = 9
    d.add(bc)
    return d


'''

c = c[:i1] + NEW_FUNC + c[j1:]

# --- 2. Reemplazar bloque de Seccion 2 (marcador real: "# 3. Territorial") ---
i2 = c.find("# 2. Concentracion dual")
j2 = c.find("# 3. Territorial")
if j2 == -1:
    j2 = c.find("# 3. Distribucion territorial")
if i2 == -1 or j2 == -1:
    print("[ERROR] No encontre los marcadores de la Seccion 2")
    raise SystemExit(1)

NEW_SEC2 = '''# 2. Concentracion dual
    d2 = [["Indicador", "Con cana", "Sin cana"],
          ["HHI", f"{cc['hhi']:,.0f}", f"{sc['hhi']:,.0f}"],
          ["Gini", str(cc["gini"]), str(sc["gini"])],
          ["Top 1 (%)", f"{cc['top1_pct']:.1f} ({cc['top1']})",
           f"{sc['top1_pct']:.1f} ({sc['top1']})"],
          ["Cultivos que explican 80%", str(cc["n80"]), str(sc["n80"])]]
    graf_cana = _pareto(df, False, color=VERDE)
    graf_sin = _pareto(df, True, color=colors.HexColor("#DD6B20"))
    tabla_grafs = Table(
        [[Paragraph("<b>Pareto CON cana (%)</b>", st_["Normal"]),
          Paragraph("<b>Pareto SIN cana (%)</b>", st_["Normal"])],
         [graf_cana, graf_sin]],
        colWidths=[234, 234])
    tabla_grafs.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    b = [Paragraph("2. Concentracion productiva: con cana vs sin cana",
                   st_["Heading2"]),
         _tabla(d2), Spacer(1, 0.2 * cm), tabla_grafs, Spacer(1, 0.4 * cm)]
    story.append(KeepTogether(b))
'''

c = c[:i2] + NEW_SEC2 + "    " + c[j2:]
p.write_text(c, encoding="utf-8")
print("[OK] Seccion 2 con dos Paretos compactos lado a lado")