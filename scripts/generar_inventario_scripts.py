"""Inventario auditable de scripts -> docs/inventario_scripts.md.
Escanea scripts/, cruza con el catalogo y marca lo desconocido como POR REVISAR."""
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCR = ROOT / "scripts"

CATALOGO = {
    "run_pipeline.py": ("Pipeline de datos UPRA: descarga, limpieza y modelo conceptual", "ACTIVO"),
    "setup_precios_oficiales_v1.py": ("Precios oficiales UPRA 2025; bug de formato corregido por fix_economic_cloud.py", "SUPERSEDED"),
    "setup_productividad_ha.py": ("Productividad COP/ha v1; reemplazado por v2 + fix_economic_cloud", "SUPERSEDED"),
    "setup_logo_global.py": ("Logo global en UI (fase anterior)", "PREEXISTENTE"),
    "setup_logo_login.py": ("Logo en login (fase anterior)", "PREEXISTENTE"),
    "setup_logo_pdf2.py": ("Logo en PDFs v2 (fase anterior)", "PREEXISTENTE"),
    "fix_logo_municipal.py": ("Logo en PDF municipal (fase anterior)", "PREEXISTENTE"),
    "fix_logo_transparente.py": ("Logo transparente (fase anterior)", "PREEXISTENTE"),
    "setup_notebook04.py": ("Genera notebook del Modulo 4 (CNN)", "ACTIVO"),
    "fix_io_utils_png.py": ("Agrega save_png a core/ml/io_utils.py", "ACTIVO"),
    "update_contexto_m4.py": ("Registra Modulo 4 en CONTEXTO.md", "ACTIVO"),
    "setup_productividad_v2.py": ("Seccion productividad COP/ha en pagina 23", "ACTIVO"),
    "fix_economic_cloud.py": ("Hotfix PRECIOS_REF tolerante a formato + productividad_ha", "ACTIVO"),
    "setup_mlp_forecast.py": ("Integracion MLP v1 (IndentationError)", "HISTORICO"),
    "setup_mlp_forecast_v2.py": ("Integracion MLP v2 (SyntaxError de comillas)", "HISTORICO"),
    "setup_mlp_forecast_v3.py": ("Integracion MLP v3 (aplicacion parcial)", "SUPERSEDED"),
    "fix_mlp_y_logo.py": ("Diagnostico MLP + logo (parcial)", "SUPERSEDED"),
    "verify_final_mlp_logo.py": ("Verificacion v1 MLP+logo", "SUPERSEDED"),
    "fix_login_sidebar.py": ("Login sin sidebar residual + Contáctenos", "ACTIVO"),
    "fix_logo_pdf_final.py": ("Logo compuesto sobre blanco v1", "SUPERSEDED"),
    "fix_explosion_y_logo.py": ("Clip MLP + residuos + branding v1", "SUPERSEDED"),
    "fix_urgente_proyecciones.py": ("Hotfix profesional del usuario (estandar AUD-*)", "SUPERSEDED"),
    "verify_escenarios_v2.py": ("Verificacion estricta: IC con ancho real", "ACTIVO"),
    "hotfix_logo_brand.py": ("Logo final: build_con_logo con callbacks en build()", "ACTIVO"),
    "update_contexto_cierre_paso2.py": ("Cierre paso 2 + estandar de hotfixes en CONTEXTO", "ACTIVO"),
    "generar_cartas_institucionales.py": ("Cartas open source (estrategia abandonada)", "HISTORICO"),
    "generar_correos_y_cartas_pdf.py": ("Correos open source + PDFs con membrete", "HISTORICO"),
    "generar_cartas_comerciales.py": ("Cartas de monetizacion vigentes (Valle, MinTIC, CiberPaz)", "ACTIVO"),
    "generar_inventario_scripts.py": ("Este inventario auditable", "ACTIVO"),
}

docs = ROOT / "docs"
docs.mkdir(exist_ok=True)
lineas = ["# Inventario de scripts — EVA Valle v3.0",
          f"Generado: {datetime.now().isoformat(timespec='seconds')}", ""]
conteo = {}
for f in sorted(SCR.glob("*.py")):
    proposito, estado = CATALOGO.get(f.name, ("Sin clasificar: revisar contenido", "POR REVISAR"))
    conteo[estado] = conteo.get(estado, 0) + 1
    lineas.append(f"- **{f.name}** [{estado}] — {proposito} "
                  f"({f.stat().st_size:,} bytes)")
lineas.append("")
lineas.append("## Resumen")
for k, v in sorted(conteo.items()):
    lineas.append(f"- {k}: {v}")
(docs / "inventario_scripts.md").write_text("\n".join(lineas), encoding="utf-8")
print(f"[OK] docs/inventario_scripts.md ({len(list(SCR.glob('*.py')))} scripts)")
print("Resumen:", conteo)