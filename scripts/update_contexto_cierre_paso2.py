"""Registra el cierre del paso 2 en CONTEXTO.md + diagnostico de ficha BID.

Estandar de generadores del proyecto: ruta absoluta desde __file__,
marcador exacto HTML (no substring), backup con shutil.copy2,
verificacion post-escritura con rollback y codigos de salida reales.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXTO_PATH = ROOT / "CONTEXTO.md"
MARCADOR = "<!-- CIERRE-PASO-2 -->"
LEGACY = "- Cierre paso 2"  # formato de la version original (ya aplicado en tu repo)
EXCLUIR_DIRS = {".git", ".venv"}

BLOQUE = """<!-- CIERRE-PASO-2 -->
- Cierre paso 2 (MLP en produccion + logo institucional):
  - MLP (5-8-4-1) firma la proyeccion oficial (platano Alcala: 5.4% vs PM2A 5.5%)
  - Escenarios saneados: AUD-MLP-002 (residuos LOO) + clip [0, 3x max] (AUD-MLP-001)
  - Logo en todos los PDFs: AUD-BRAND-001..006 (build_con_logo; callbacks en build())
  - Leccion reportlab: onPage= en constructor es atributo muerto; los callbacks van
    en build(onFirstPage/onLaterPages)
  - Regla QA reforzada: toda verificacion inspecciona el artefacto (p. ej.
    /Subtype /Image en el PDF), no solo el exit code
  - Estandar de hotfixes del proyecto (propuesto por el usuario): backups .bak +
    manifiesto JSONL AUD-* + logging estructurado + verificacion candidata a pytest
"""


def registrar_cierre_paso2() -> int:
    """Inserta el bloque de cierre en CONTEXTO.md si aún no está. Devuelve exit code."""
    if not CONTEXTO_PATH.exists():
        print(f"[ERROR] no existe el archivo: {CONTEXTO_PATH}")
        return 1

    contenido = CONTEXTO_PATH.read_text(encoding="utf-8")

    if MARCADOR in contenido or LEGACY in contenido:
        print("[SKIP] el cierre del paso 2 ya esta registrado en CONTEXTO.md")
        return 0

    backup_path = CONTEXTO_PATH.with_suffix(".md.bak")
    try:
        shutil.copy2(CONTEXTO_PATH, backup_path)
    except OSError as e:
        print(f"[ERROR] no se pudo crear backup: {e}")
        return 1

    nuevo = contenido.rstrip("\n")
    nuevo = (nuevo + "\n\n" if nuevo else "") + BLOQUE

    CONTEXTO_PATH.write_text(nuevo, encoding="utf-8")

    # Verificacion post-escritura con rollback
    if MARCADOR not in CONTEXTO_PATH.read_text(encoding="utf-8"):
        print("[ERROR] el marcador no quedo escrito; restaurando backup")
        shutil.copy2(backup_path, CONTEXTO_PATH)
        return 1

    print("[OK] CONTEXTO.md: cierre paso 2 + estandar de hotfixes registrado")
    print(f"[INFO] backup guardado en: {backup_path}")
    return 0


def diagnosticar_fichas_bid() -> None:
    """Lista archivos (no directorios) cuyo nombre contenga 'bid', sin distinguir mayúsculas."""
    print("\nArchivos BID existentes en el repo:")
    count = 0
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file():
            continue
        if EXCLUIR_DIRS & set(f.relative_to(ROOT).parts):
            continue
        if "bid" not in f.name.lower():
            continue
        print("  ", f.relative_to(ROOT))
        count += 1

    if not count:
        print("   (ninguno -> la estrategia vigente vive en cartas_comerciales/)")


def main() -> int:
    exit_code = registrar_cierre_paso2()
    diagnosticar_fichas_bid()  # siempre se ejecuta, independiente del resultado anterior
    return exit_code


if __name__ == "__main__":
    sys.exit(main())