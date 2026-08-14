"""Genera carta formal de presentacion a la Secretaria de Agricultura del Valle."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from core.reports import meta

VERDE = colors.HexColor("#2E8B57")
GRIS = colors.HexColor("#4A5568")

MESES = ["enero","febrero","marzo","abril","mayo","junio",
         "julio","agosto","septiembre","octubre","noviembre","diciembre"]


def build_carta() -> bytes:
    hoy = date.today()
    fecha = f"Cali, {hoy.day} de {MESES[hoy.month-1]} de {hoy.year}"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=2.5*cm, rightMargin=2.5*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm,
                            title="Carta Secretaria de Agricultura")
    st_ = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=14,
                          fontSize=10.5, alignment=4)  # justificado
    firma = ParagraphStyle("Firma", parent=st_["Normal"], fontSize=11,
                           textColor=VERDE)

    story = []
    story.append(Paragraph(fecha, body))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Señores<br/><b>SECRETARÍA DE AGRICULTURA Y PESCA</b><br/>"
                           "Gobernación del Valle del Cauca<br/>E. S. D.", body))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "<b>Ref:</b> Presentación del Sistema de Inteligencia Territorial Agropecuaria "
        "<b>EVA Valle v3.0</b> y propuesta de patrocinio institucional.", body))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Respetados señores:", body))
    story.append(Spacer(1, 0.3 * cm))

    parrafos = [
        "Reciban un cordial saludo. Mi nombre es <b>Moisés Zúñiga Grueso</b>, Data Analyst "
        "especializado en inteligencia territorial agropecuaria, y me permito presentar ante "
        "su despacho el sistema <b>EVA Valle v3.0</b>, una plataforma de análisis desarrollada "
        "sobre la base oficial de las Evaluaciones Agropecuarias Municipales (EVA) de la UPRA, "
        "período 2019-2025.",

        "El sistema procesa <b>10,589 registros</b> de los <b>42 municipios</b> del departamento "
        "y <b>78 cultivos</b>, y produce de forma automática indicadores, alertas y reportes "
        "ejecutivos con estándar profesional (UPRA/CEPAL). Entre los hallazgos más relevantes "
        "del período destacan:",

        "&bull; La caña de azúcar concentra el <b>95.3%</b> de la producción departamental "
        "(HHI 9,092); al excluirla, el HHI cae a <b>1,045</b>, revelando una economía no-cañera "
        "diversificada donde <b>11 cultivos explican el 80%</b> de la producción.",

        "&bull; La concentración territorial es alta (Gini <b>0.64</b>), con <b>Palmira</b> como "
        "municipio líder (17.8%).",

        "&bull; Cultivos como la <b>cebolla de rama (+22.7%)</b> y el <b>ají (+21.6%)</b> emergen "
        "como motores de diversificación, mientras la <b>malanga (-56.7%)</b> requiere atención.",

        "Con el ánimo de aportar al departamento, propongo un <b>PATROCINIO INSTITUCIONAL</b>: "
        "otorgar a la Secretaría <b>licencia gratuita del sistema por dos años</b>, capacitación "
        "al equipo técnico y <b>doce reportes ejecutivos anuales</b>, a cambio de una carta de "
        "respaldo institucional que avale la iniciativa y permita su réplica en otros territorios.",

        "Adjunto a esta comunicación la propuesta formal, el informe técnico (12 secciones, nivel "
        "FAO/CEPAL), el informe ejecutivo narrativo y el resumen ejecutivo 2019-2025, para su "
        "revisión.",

        "Solicito respetuosamente un espacio de <b>veinte (20) minutos</b> para presentar el "
        "sistema en vivo y explorar cómo puede apoyar la toma de decisiones de su despacho.",

        "Agradezco de antemano su atención.",
    ]
    for p in parrafos:
        story.append(Paragraph(p, body))
        story.append(Spacer(1, 0.3 * cm))

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Atentamente,", body))
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph(f"<b>{meta.AUTOR}</b><br/>{meta.CARGO}", firma))
    story.append(Paragraph(
        "[Tu teléfono] | [tu-correo@dominio.com] | [LinkedIn]<br/>"
        "Demo en vivo: https://eva-valle-v3.streamlit.app",
        ParagraphStyle("Contacto", parent=st_["Normal"], fontSize=9, textColor=GRIS)))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "<b>Anexos (4):</b> 1. Propuesta de Patrocinio Institucional · "
        "2. Informe Técnico 2019-2025 · 3. Informe Ejecutivo Narrativo · "
        "4. Resumen Ejecutivo 2019-2025",
        ParagraphStyle("Anexos", parent=st_["Normal"], fontSize=9, textColor=GRIS)))

    doc.build(story)
    return buf.getvalue()


def main():
    out = Path("outputs") / "carta_secretaria_agricultura.pdf"
    out.write_bytes(build_carta())
    print(f"[OK] Carta generada: {out}")
    print(f"     Tamano: {out.stat().st_size / 1024:.1f} KB")
    print("\nRecuerda reemplazar [Tu telefono], [tu-correo] y [LinkedIn] antes de enviar.")


if __name__ == "__main__":
    main()