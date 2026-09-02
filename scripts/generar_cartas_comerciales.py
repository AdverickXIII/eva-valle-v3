"""Genera tres cartas comerciales (no open source) con membrete institucional.
Destinatarios: Secretaria Agricultura Valle, MinTIC, CiberPaz.
Adjunto: proyeccion_platano_alcala.pdf (MLP ganador, escenarios cuerdos)."""
import re
import sys
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

out = ROOT / "cartas_comerciales"
out.mkdir(exist_ok=True)
fecha = datetime.now().strftime("%d de %B de %Y")

# ======================================================================
# CARTA 1: Secretaria de Agricultura del Valle del Cauca
# ======================================================================
carta_valle = f"""Cali, {fecha}

Dra.
Angela Yaneth Reyes Becerra
Secretaria de Desarrollo Rural, Agricultura y Pesca
Gobernación del Valle del Cauca
Cali

Asunto: Presentación de herramienta analítica propietaria para la planificación agrícola del Valle del Cauca — solicitud de audiencia técnica

Respetada Dra. Reyes:

Me dirijo a usted para presentarle EVA Valle v3.0, una herramienta analítica que he desarrollado durante los últimos meses, actualmente en producción y operando sobre los datos oficiales de la Unidad de Planificación Rural Agropecuaria (UPRA) del departamento.

La herramienta está diseñada específicamente para la toma de decisiones de política agropecuaria a nivel departamental y municipal. Sus capacidades centrales son:

1. Proyecciones con selección automática de modelo: para cada combinación municipio-cultivo, la herramienta compite seis algoritmos estadísticos y de machine learning (incluyendo redes neuronales entrenadas desde cero) y selecciona el de menor error, validado por backtesting. El modelo ganador firma la proyección con su MAPE, credibilidad y firma de autor.

2. Escenarios de riesgo con intervalos de confianza: para cada proyección se calculan escenarios conservador (P10), tendencial y optimista (P90) a partir de los residuos del entrenamiento, permitiendo planificar bajo incertidumbre.

3. Valor económico del suelo: PIB agro municipal, productividad COP por hectárea y ranking de eficiencia territorial — insumo directo para decisiones de inversión pública.

4. Pirámide analítica de seis niveles: descriptivo, diagnóstico, predictivo, prescriptivo, económico y adaptativo (selector dinámico de modelos).

La herramienta ya se encuentra desplegada y operativa. Adjunto como evidencia un reporte oficial de proyección para plátano en Alcalá: modelo MLP (5-8-4-1) seleccionado con MAPE de 5.4%, credibilidad alta, escenarios diferenciados y sello institucional en todas las hojas.

Por lo anterior, solicito respetuosamente una audiencia técnica para:
- Demostrar en vivo la herramienta sobre los datos del Valle.
- Presentar una propuesta de licenciamiento institucional (modalidad SaaS multi-municipio, con soporte y actualización continua).
- Explorar la posibilidad de que la Gobernación adopte EVA Valle como herramienta oficial de planificación agrícola departamental.

Quedo atento a su agenda y disposición para concretar la reunión.

Cordialmente,

Moisés Zúñiga Grueso
Data Analyst
moises.zuniga.grueso@gmail.com
Adjunto: Proyección oficial Plátano-Alcalá (PDF institucional)
"""

# ======================================================================
# CARTA 2: MinTIC — Evaluación para adquisición nacional
# ======================================================================
carta_mintic = f"""Cali, {fecha}

Señores
Ministerio de Tecnologías de la Información y las Comunicaciones
Dirección de Gobierno Digital
Bogotá D. C.

Asunto: Presentación de solución analítica para secretarías de agricultura departamentales — solicitud de evaluación técnica para adquisición vía Colombia Compra Eficiente

Respetados señores:

Me permito presentar EVA Valle v3.0, una solución analítica que he desarrollado y puesto en producción para la planificación agrícola del Valle del Cauca, la cual postulo a evaluación técnica para su eventual adquisición nacional por parte de las secretarías de agricultura departamentales.

El problema que resuelve: las 32 secretarías de agricultura del país toman decisiones de política agropecuaria con datos históricos crudos, sin herramientas accesibles que integren proyección, escenarios de riesgo y valor económico del suelo. EVA Valle cierra esa brecha con una solución web desplegable sobre datos oficiales (UPRA, Dane) y exportación de reportes PDF institucionales.

Capacidades técnicas verificables en producción:
- Proyección con selección automática de modelo por backtesting (lineal, promedios móviles, Holt y redes neuronales entrenadas desde cero).
- Escenarios de riesgo con intervalos de confianza por percentiles de residuos.
- Valor económico del suelo: PIB agro municipal, productividad COP/ha y ranking territorial.
- Pirámide analítica de seis niveles (descriptivo → adaptativo).
- Gobernanza del dato: trazabilidad de fuentes, control de acceso por roles, validación satelital.

Propuesta al Ministerio:
1. Evaluación técnica por parte del equipo de Gobierno Digital.
2. Inclusión en el Acuerdo Marco de precio de TI de Colombia Compra Eficiente como solución de analítica sectorial.
3. Licenciamiento institucional a las secretarías interesadas, con modelo de pricing escalable por volumen de municipios.

La herramienta está en producción: https://eva-valle-v3.streamlit.app. Adjunto un reporte oficial de proyección como evidencia del nivel técnico y de entrega.

Solicito una reunión técnica con el equipo de Gobierno Digital para presentar la herramienta y formalizar el proceso de evaluación.

Cordialmente,

Moisés Zúñiga Grueso
Data Analyst
moises.zuniga.grueso@gmail.com
Adjunto: Proyección oficial Plátano-Alcalá (PDF institucional)
"""

# ======================================================================
# CARTA 3: CiberPaz — Material educativo para sus formaciones
# ======================================================================
carta_ciberpaz = f"""Cali, {fecha}

Señores
CIBERPAZ — Universidad de Pamplona
Ministerio TIC
E. S. D.

Asunto: Herramienta analítica en producción para el agro — propuesta de caso de estudio para sus formaciones en empleabilidad e innovación

Respetados señores:

En el marco de su oferta de formación virtual orientada a empleabilidad, emprendimiento e innovación para 15.000 colombianos en 2026, me permito presentar EVA Valle v3.0, una herramienta analítica que he desarrollado y puesto en producción sobre datos oficiales del agro colombiano.

Diferencial pedagógico: la herramienta enseña competencias reales del mercado laboral (Python, ciencia de datos, machine learning, visualización, exportación de reportes institucionales) a través de un caso completo: de la serie histórica a la decisión de política pública. Su arquitectura incluye:

- Proyección con selección automática de modelo y validación por backtesting.
- Redes neuronales y algoritmos de aprendizaje implementados desde cero en NumPy, con verificación numérica de gradientes.
- Motor de escenarios con intervalos de confianza.
- Gobernanza del dato y trazabilidad de fuentes.
- Exportación de reportes PDF institucionales con firma de autor.

Propuesta concreta para CiberPaz:
- Integrar la herramienta como caso de estudio avanzado en las formaciones de IA y ciencia de datos.
- Desarrollar conjuntamente un módulo educativo ("De datos a decisiones: analítica agrícola aplicada") con materiales, ejercicios y certificación.
- Modalidad comercial: licenciamiento educativo anual con soporte pedagógico y adaptación territorial.

La herramienta está en producción y disponible para demostración. Adjunto un reporte oficial de proyección como evidencia del nivel técnico alcanzado.

Solicito una reunión virtual para presentar el caso y explorar la modalidad de colaboración educativa y comercial.

Cordialmente,

Moisés Zúñiga Grueso
Data Analyst
moises.zuniga.grueso@gmail.com
Adjunto: Proyección oficial Plátano-Alcalá (PDF institucional)
"""

# ======================================================================
# GENERACION DE PDFs con membrete
# ======================================================================
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate
from core.reports.branding import build_con_logo

estilo = ParagraphStyle("carta", parent=getSampleStyleSheet()["Normal"],
                        fontSize=10.5, leading=15, spaceAfter=8)

def txt_a_flowables(texto):
    texto = escape(texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    flujo = []
    for p in [x.strip() for x in texto.split("\n\n") if x.strip()]:
        flujo.append(Paragraph(p.replace("\n", "<br/>"), estilo))
        flujo.append(Spacer(1, 4))
    return flujo

cartas = {
    "carta_1_secretaria_valle.pdf": carta_valle,
    "carta_2_mintic_adquisicion.pdf": carta_mintic,
    "carta_3_ciberpaz_educativa.pdf": carta_ciberpaz,
}

for nombre, contenido in cartas.items():
    out_pdf = out / nombre
    doc = SimpleDocTemplate(str(out_pdf), pagesize=letter,
                            title=nombre.replace(".pdf", "").replace("_", " ").title())
    build_con_logo(doc, txt_a_flowables(contenido))
    print(f"[OK] {nombre} ({out_pdf.stat().st_size:,} bytes)")

# Correos de presentacion
correos = {
    "correo_1_valle.txt": ("ayreyes@valledelcauca.gov.co",
        "Solicitud de audiencia técnica — herramienta analítica EVA Valle v3.0"),
    "correo_2_mintic.txt": ("minticresponde@mintic.gov.co",
        "Solicitud de evaluación técnica para adquisición nacional — EVA Valle v3.0"),
    "correo_3_ciberpaz.txt": ("mesa.ayuda1@unipamplona.edu.co",
        "Herramienta analítica para sus formaciones — propuesta de caso de estudio EVA Valle v3.0"),
}

email_base = """Respetados señores:

Adjunto carta formal en la que presento EVA Valle v3.0, herramienta analítica
que he desarrollado y que se encuentra actualmente en producción sobre datos
oficiales del agro colombiano (UPRA 2019-2025).

La herramienta genera proyecciones con selección automática de modelo,
escenarios de riesgo con intervalos de confianza y reportes institucionales
PDF — capacidades verificables en el adjunto.

Solicito una reunión técnica para presentar la herramienta en vivo y explorar
la modalidad de adquisición/licenciamiento propuesta en la carta.

- Demo en vivo: https://eva-valle-v3.streamlit.app
- Adjunto: carta formal + reporte oficial de proyección

Cordialmente,

Moisés Zúñiga Grueso
Data Analyst
moises.zuniga.grueso@gmail.com
"""

for nombre, (dest, asunto) in correos.items():
    cuerpo = f"Para: {dest}\nAsunto: {asunto}\n\n{email_base}"
    (out / nombre).write_text(cuerpo, encoding="utf-8")
    print(f"[OK] {nombre}")

print("\n=== ORDEN DE ENVIO RECOMENDADO ===")
print("1. Secretaria del Valle (primera, porque ya conocen tus datos)")
print("2. MinTIC (apertura de canal nacional)")
print("3. CiberPaz (respuesta a su invitación)")
print("\nEn cada envio adjunta: carta PDF + proyeccion_platano_alcala.pdf")