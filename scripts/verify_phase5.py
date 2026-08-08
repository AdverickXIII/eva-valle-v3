"""Verificacion integral de la Fase 5."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ═══════════════════════════════════════════════════════════
# VERIFICACION DE ESTRUCTURA DE ARCHIVOS
# ═══════════════════════════════════════════════════════════
ARCHIVOS_REQUERIDOS = {
    # Infraestructura
    "app.py": "Punto de entrada Streamlit",
    "ui/assets/css/style.css": "Tema CSS",
    "ui/components/__init__.py": "Paquete de componentes",
    "ui/components/metrics_cards.py": "Cards de KPIs",
    "ui/components/filter_panel.py": "Panel de filtros",
    "ui/components/loading_states.py": "Estados de carga",
    "ui/components/download_section.py": "Botones de descarga",

    # Páginas
    "ui/pages/1_\U0001F4CA_Dashboard.py": "Página Dashboard",
    "ui/pages/2_\U0001F4C8_Descriptivo.py": "Página Descriptivo",
    "ui/pages/3_\U0001F52C_Diagnostico.py": "Página Diagnóstico",
    "ui/pages/4_\U0001F916_Predictivo.py": "Página Predictivo",
    "ui/pages/5_\U0001F50D_Auditoria.py": "Página Auditoría",
    "ui/pages/6_\u2699\uFE0F_Configuracion.py": "Página Configuración",

    # Gráficos
    "ui/charts/__init__.py": "Paquete de gráficos",
    "ui/charts/theme.py": "Tema Plotly",
    "ui/charts/historical.py": "Gráficos históricos",
    "ui/charts/distributions.py": "Distribuciones",
    "ui/charts/concentration.py": "Concentración",
    "ui/charts/growth.py": "Crecimiento",
    "ui/charts/spatial.py": "Espacial",
    "ui/charts/diagnostics.py": "Diagnóstico",

    # Core (verificación de que existe)
    "core/analytics/__init__.py": "Módulo analytics",
    "core/diagnostics/__init__.py": "Módulo diagnostics",
    "core/ml/__init__.py": "Módulo ML",
    "core/audit/__init__.py": "Módulo audit",
    "core/modeling/__init__.py": "Módulo modeling",

    # Scripts
    "scripts/run_pipeline.py": "Script pipeline",
    "scripts/run_audit.py": "Script auditoría",
    "scripts/download_data.py": "Script descarga",
}


def verificar_archivos() -> tuple[int, int]:
    """Verifica que todos los archivos requeridos existen."""
    print("\n" + "=" * 70)
    print("  VERIFICACION DE ESTRUCTURA DE ARCHIVOS")
    print("=" * 70)

    existentes = 0
    faltantes = 0

    for ruta, descripcion in ARCHIVOS_REQUERIDOS.items():
        path = Path(ruta)
        if path.exists():
            print(f"  ✅ {ruta:<50} [{descripcion}]")
            existentes += 1
        else:
            print(f"  ❌ {ruta:<50} [{descripcion}]")
            faltantes += 1

    print(f"\n  Resultado: {existentes} existentes, {faltantes} faltantes")
    return existentes, faltantes


def verificar_imports() -> tuple[int, int]:
    """Verifica que los módulos principales se importan correctamente."""
    print("\n" + "=" * 70)
    print("  VERIFICACION DE IMPORTS")
    print("=" * 70)

    imports_exitosos = 0
    imports_fallidos = 0

    modulos = [
        ("config.settings", "settings"),
        ("core.analytics", "run_all_analytics"),
        ("core.diagnostics", "run_all_diagnostics"),
        ("core.ml", "run_all_ml"),
        ("core.audit", "run_all_audits"),
        ("core.modeling", "run_conceptual_modeling"),
        ("ui.charts", "plot_historico_cruces"),
        ("ui.components", "render_kpi_card"),
    ]

    for modulo, simbolo in modulos:
        try:
            exec(f"from {modulo} import {simbolo}")
            print(f"  ✅ from {modulo} import {simbolo}")
            imports_exitosos += 1
        except Exception as e:
            print(f"  ❌ from {modulo} import {simbolo} → {e}")
            imports_fallidos += 1

    print(f"\n  Resultado: {imports_exitosos} exitosos, {imports_fallidos} fallidos")
    return imports_exitosos, imports_fallidos


def verificar_datos() -> tuple[int, int]:
    """Verifica que los datos del pipeline existen."""
    print("\n" + "=" * 70)
    print("  VERIFICACION DE DATOS DEL PIPELINE")
    print("=" * 70)

    from config.settings import settings

    datos_existentes = 0
    datos_faltantes = 0

    archivos_clave = {
        "Dataset estandarizado": settings.DATA_PROCESSED_PATH / "01_clean" / "eva_agricola_valle_2019_2024_estandarizado.csv",
        "Modelo conceptual": settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
        "Reporte de auditoría": settings.OUTPUTS_TABLES_PATH / "auditoria_agricola_valle_2019_2024.csv",
        "Análisis descriptivo": settings.OUTPUTS_TABLES_PATH / "4_6_concentracion.csv",
        "Diagnóstico": settings.OUTPUTS_TABLES_PATH / "6_1_matriz_correlacion.csv",
        "Predictivo": settings.OUTPUTS_TABLES_PATH / "7_2_metricas_regresion.csv",
    }

    for nombre, path in archivos_clave.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {nombre:<30} ({size_mb:.2f} MB)")
            datos_existentes += 1
        else:
            print(f"  ❌ {nombre:<30} (no encontrado)")
            print(f"     → Ejecuta: python scripts\\run_pipeline.py --skip-download")
            datos_faltantes += 1

    print(f"\n  Resultado: {datos_existentes} existentes, {datos_faltantes} faltantes")
    return datos_existentes, datos_faltantes


def main() -> int:
    """Ejecuta todas las verificaciones."""
    print("\n" + "═" * 70)
    print("  VERIFICACION INTEGRAL — FASE 5 (Diseño UI/UX)")
    print("═" * 70)

    # 1. Verificar archivos
    arch_ok, arch_faltan = verificar_archivos()

    # 2. Verificar imports
    imp_ok, imp_fallan = verificar_imports()

    # 3. Verificar datos
    datos_ok, datos_faltan = verificar_datos()

    # Resumen final
    print("\n" + "═" * 70)
    print("  RESUMEN DE VERIFICACION")
    print("═" * 70)
    print(f"  Archivos   : {arch_ok}/{arch_ok + arch_faltan}")
    print(f"  Imports    : {imp_ok}/{imp_ok + imp_fallan}")
    print(f"  Datos      : {datos_ok}/{datos_ok + datos_faltan}")

    total_ok = arch_ok + imp_ok + datos_ok
    total = (arch_ok + arch_faltan) + (imp_ok + imp_fallan) + (datos_ok + datos_faltan)

    print(f"\n  TOTAL      : {total_ok}/{total} verificaciones exitosas")

    if arch_faltan == 0 and imp_fallan == 0 and datos_faltan == 0:
        print("\n  🎉 FASE 5 VERIFICADA EXITOSAMENTE")
        print("  → Ejecuta: streamlit run app.py")
        return 0
    else:
        print("\n  ⚠️  HAY ELEMENTOS PENDIENTES")
        if arch_faltan > 0:
            print("  → Verifica los scripts de la Fase 5")
        if imp_fallan > 0:
            print("  → Verifica las dependencias: pip install -r requirements.txt")
        if datos_faltan > 0:
            print("  → Ejecuta: python scripts\\run_pipeline.py --skip-download")
        return 1


if __name__ == "__main__":
    sys.exit(main())