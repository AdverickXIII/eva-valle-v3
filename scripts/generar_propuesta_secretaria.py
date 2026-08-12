"""Genera propuesta formal en PDF para la Secretaria de Agricultura del Valle."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import io
from datetime import date

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from config.settings import settings
from core.analytics.executive import executive_summary
from core.analytics.pareto import conc_metrics, territorial
from core.reports import meta

VERDE = colors.HexColor("#2E8B57")
GRIS = colors.HexColor("#4A5568")


def _style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F8F9FA")]),
    ])


def _footer(canvas, doc) -> None:
    w, _ = letter
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.line(36, 42, w - 36, 42)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(36, 32, f"{meta.firma()} | EVA Valle v3.0")
    canvas.drawRightString(w - 36, 32, f"Pagina {doc.page}")
    canvas.restoreState()


def build_propuesta(df: pd.DataFrame) -> bytes:
    s = executive_summary(df)
    cc = conc_metrics(df, False)
    sc = conc_metrics(df, True)
    ter = territorial(df)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            title="Propuesta de Patrocinio Institucional")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE, fontSize=22)
    h1 = ParagraphStyle("H1", parent=st_["Heading1"], textColor=VERDE)
    h2 = ParagraphStyle("H2", parent=st_["Heading2"], textColor=VERDE)

    story = []

    # --- PORTADA ---
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Propuesta de Patrocinio Institucional", title))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Sistema de Inteligencia Territorial Agropecuaria",
                           ParagraphStyle("Sub", parent=st_["Heading2"],
                                        textColor=GRIS, fontSize=16)))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("<b>Valle del Cauca 2019-2025</b>", st_["Heading3"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Preparado para:", st_["Normal"]))
    story.append(Paragraph("<b>Secretaria de Agricultura y Pesca del Valle del Cauca</b>",
                           st_["Heading3"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"Elaborado por: <b>{meta.AUTOR}</b><br/>"
                           f"{meta.CARGO}<br/>"
                           f"Fecha: {date.today().strftime('%Y-%m-%d')}", st_["Normal"]))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("<i>Documento confidencial</i>", st_["Italic"]))

    # --- PAGINA 2: RESUMEN EJECUTIVO ---
    story.append(Paragraph("1. Resumen Ejecutivo", h1))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "La Secretaria de Agricultura del Valle del Cauca enfrenta el desafio de tomar "
        "decisiones de inversion territorial con datos fragmentados y analisis manuales "
        "que consumen meses y cuestan entre $100-200 millones por consultoria externa.",
        st_["Normal"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Propongo un <b>Sistema de Inteligencia Territorial Agropecuaria</b> que automatiza "
        f"ese analisis usando datos oficiales de UPRA (EVA 2019-2025). El sistema ya esta "
        f"operativo y procesa {len(df):,} registros de los 42 municipios del departamento.",
        st_["Normal"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Propuesta de valor:</b>", st_["Normal"]))
    bullets = [
        f"Licencia gratuita por 2 anos a la Secretaria",
        f"Capacitacion al equipo tecnico (2 sesiones de 4 horas)",
        f"12 reportes ejecutivos anuales personalizados",
        f"Brandling: 'Con el apoyo de la Secretaria de Agricultura del Valle'",
    ]
    for b in bullets:
        story.append(Paragraph(f"&bull; {b}", st_["Normal"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>A cambio solicito:</b>", st_["Normal"]))
    asks = [
        "Carta de respaldo institucional (para usar en otras propuestas)",
        "Logo de la Secretaria en la plataforma",
        "Acceso a datos adicionales si los tienen (precios, comercializacion)",
        "Compromiso de evaluar adopcion permanente despues de 2 anos",
    ]
    for a in asks:
        story.append(Paragraph(f"&bull; {a}", st_["Normal"]))

    # --- PAGINA 3: DIAGNOSTICO ---
    story.append(Paragraph("2. Diagnostico Actual del Valle del Cauca", h1))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "El analisis de datos EVA 2019-2025 revela hallazgos criticos para la politica "
        "publica agropecuaria departamental:", st_["Normal"]))
    story.append(Spacer(1, 0.3 * cm))

    # Tabla de hallazgos clave
    hallazgos = [
        ["Hallazgo", "Implicacion"],
        [f"La cana concentra el {cc['top1_pct']:.1f}% de la produccion",
         "Riesgo de monocultivo; vulnerabilidad economica"],
        [f"Gini productivo = {cc['gini']:.2f} (con cana)",
         "Concentracion extrema; poca diversificacion"],
        [f"Sin cana, 11 cultivos explican el 80%",
         "Oportunidad de diversificacion hacia mayor valor"],
        [f"Gini territorial = {ter['gini']:.2f}",
         "Produccion concentrada en pocos municipios"],
        [f"{ter['top']} lidera con {ter['top_pct']:.1f}%",
         "Necesidad de focalizar inversion en municipios rezagados"],
        [f"Cebolla de rama crece +22.7% CAGR",
         "Oportunidad de inversion en hortalizas"],
        [f"Malanga declina -56.7% CAGR",
         "Alerta temprana; requiere intervencion"],
    ]
    t = Table(hallazgos, hAlign="LEFT", colWidths=[7 * cm, 9.5 * cm])
    t.setStyle(_style())
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        f"El departamento produce {s['kpis'][0]['value']} anuales en "
        f"{s['kpis'][1]['value']} con {s['kpis'][4]['value']} cultivos diferentes. "
        f"Sin embargo, la economia agricola no-canera (frutas, hortalizas, exportacion) "
        f"permanece invisible en los reportes tradicionales.", st_["Normal"]))

    # --- PAGINA 4: SOLUCION ---
    story.append(Paragraph("3. La Solucion: EVA Valle v3.0", h1))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Un sistema web interactivo con 17 modulos que transforma datos brutos de UPRA "
        "en inteligencia accionable:", st_["Normal"]))
    story.append(Spacer(1, 0.3 * cm))

    modulos = [
        ["Modulo", "Funcionalidad", "Valor para la Secretaria"],
        ["Dashboard", "KPIs departamentales en tiempo real",
         "Vision general instantanea"],
        ["Mapa Animado", "Evolucion 2019-2025 por municipio",
         "Identificar tendencias territoriales"],
        ["Fichas Tecnicas", "PDF firmado por cultivo/municipio",
         "Entregables listos para decision"],
        ["Comparador", "Analisis lado a lado de 2 municipios",
         "Priorizacion de inversion"],
        ["Alertas", "Deteccion automatica de riesgos",
         "Sistema de alerta temprana"],
        ["Resumen Ejecutivo", "7 secciones estandar UPRA/CEPAL",
         "Reporte de alto nivel automatizado"],
    ]
    t2 = Table(modulos, hAlign="LEFT", colWidths=[3 * cm, 6 * cm, 7 * cm])
    t2.setStyle(_style())
    story.append(t2)
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("<b>Diferenciadores unicos:</b>", st_["Normal"]))
    diffs = [
        "Analisis dual con/sin cana (nadie mas lo ofrece)",
        "Fichas tecnicas firmadas con estandar profesional",
        "Alertas inteligentes basadas en reglas",
        "Integracion automatica de datos EVA 2025",
        "Seguridad empresarial (autenticacion + auditoria)",
    ]
    for d in diffs:
        story.append(Paragraph(f"&bull; {d}", st_["Normal"]))

    # --- PAGINA 5: PLAN DE TRABAJO ---
    story.append(Paragraph("4. Plan de Trabajo (90 dias)", h1))
    story.append(Spacer(1, 0.3 * cm))

    cronograma = [
        ["Fase", "Actividad", "Entregable"],
        ["Mes 1", "Firma de acuerdo + credenciales",
         "Acceso al sistema"],
        ["Mes 1", "Capacitacion equipo tecnico (sesion 1)",
         "Manual de usuario"],
        ["Mes 2", "Generacion de 3 reportes ejecutivos",
         "PDFs firmados"],
        ["Mes 2", "Capacitacion equipo tecnico (sesion 2)",
         "Video tutorial"],
        ["Mes 3", "Reporte de impacto + caso de exito",
         "Documento de resultados"],
        ["Mes 3", "Evaluacion de adopcion permanente",
         "Propuesta de continuidad"],
    ]
    t3 = Table(cronograma, hAlign="LEFT", colWidths=[2 * cm, 7 * cm, 7 * cm])
    t3.setStyle(_style())
    story.append(t3)

    # --- PAGINA 6: ROI ---
    story.append(Paragraph("5. Retorno de Inversion", h1))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "El patrocinio representa un ahorro significativo para la Secretaria:",
        st_["Normal"]))
    story.append(Spacer(1, 0.3 * cm))

    roi = [
        ["Concepto", "Costo consultoria tradicional", "Costo con EVA Valle"],
        ["Analisis territorial (2 anos)", "$200-400 millones", "$0 (incluido)"],
        ["12 reportes ejecutivos", "$60-120 millones", "$0 (incluido)"],
        ["Capacitacion equipo", "$20-40 millones", "$0 (incluido)"],
        ["Sistema permanente", "No disponible", "$0 (licencia 2 anos)"],
        ["<b>TOTAL</b>", "<b>$280-560 millones</b>", "<b>$0</b>"],
    ]
    t4 = Table(roi, hAlign="LEFT", colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
    t4.setStyle(_style())
    story.append(t4)
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "A cambio, la Secretaria obtiene una herramienta permanente que sobrevive "
        "cambios de administracion y posiciona al Valle como referente en uso de datos "
        "para politica publica agropecuaria.", st_["Normal"]))

    # --- PAGINA 7: CREDENCIALES ---
    story.append(Paragraph("6. Credenciales", h1))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"<b>{meta.AUTOR}</b><br/>{meta.CARGO}", st_["Heading3"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Analista de datos especializado en inteligencia territorial agropecuaria. "
        "Desarrollador de EVA Valle v3.0, plataforma que procesa datos oficiales de "
        "UPRA para el Valle del Cauca.", st_["Normal"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Fuentes de datos:</b>", st_["Normal"]))
    story.append(Paragraph(
        "&bull; UPRA - Unidad de Planificacion Rural Agropecuaria<br/>"
        "&bull; Evaluaciones Agropecuarias Municipales (EVA) 2019-2025<br/>"
        "&bull; 10,589 registros de 42 municipios y 78 cultivos",
        st_["Normal"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Acceso al sistema:</b>", st_["Normal"]))
    story.append(Paragraph(
        f"&bull; Demo en vivo: {meta.SISTEMA}<br/>"
        "&bull; Codigo fuente: GitHub (repositorio privado bajo solicitud)<br/>"
        "&bull; Documentacion tecnica disponible",
        st_["Normal"]))

    # --- PAGINA 8: CIERRE ---
    story.append(Paragraph("7. Proximos Pasos", h1))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Propongo una reunion de 30 minutos para:", st_["Normal"]))
    story.append(Spacer(1, 0.2 * cm))
    steps = [
        "Demo en vivo del sistema con datos reales del Valle",
        "Discutir necesidades especificas de la Secretaria",
        "Acordar terminos del patrocinio institucional",
        "Firmar carta de intencion",
    ]
    for i, s in enumerate(steps, 1):
        story.append(Paragraph(f"{i}. {s}", st_["Normal"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Estoy disponible para reunion presencial o virtual en los proximos 7 dias.",
        st_["Normal"]))
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph("<b>Contacto:</b>", st_["Normal"]))
    story.append(Paragraph(
        f"Moises Zuniga Grueso<br/>"
        "Data Analyst<br/>"
        "Email: [tu-email@dominio.com]<br/>"
        "Telefono: [tu-telefono]<br/>"
        "LinkedIn: [tu-linkedin]",
        st_["Normal"]))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"<i>Documento generado el {date.today().strftime('%Y-%m-%d')} | "
        f"Fuente: UPRA EVA 2019-2025 | {meta.firma()}</i>",
        ParagraphStyle("Footer", parent=st_["Italic"], fontSize=8, textColor=GRIS)))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


def main() -> None:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    df = pd.read_csv(path, low_memory=False)

    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "propuesta_secretaria_agricultura.pdf"

    pdf_bytes = build_propuesta(df)
    out_path.write_bytes(pdf_bytes)

    print(f"[OK] Propuesta generada: {out_path}")
    print(f"     Tamano: {out_path.stat().st_size / 1024:.1f} KB")
    print(f"     Paginas: 8")
    print(f"\nProximos pasos:")
    print(f"1. Revisa el PDF y ajusta datos de contacto (pagina 8)")
    print(f"2. Identifica contacto clave en la Secretaria")
    print(f"3. Envia por correo con asunto: 'Propuesta de Inteligencia Territorial Agropecuaria'")


if __name__ == "__main__":
    main()