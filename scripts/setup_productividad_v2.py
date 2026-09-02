"""
Agrega la seccion 'Productividad economica COP/ha' a la pagina Valor Economico.

Uso:
    python agregar_productividad_economica.py

Mejoras sobre la version original:
- Backup automatico (.bak) antes de escribir.
- Rollback automatico si el archivo resultante no compila (py_compile).
- Chequeo de idempotencia por marcador exacto, no por substring suelto.
- Valida que las dependencias que usa la seccion (anio, sin_cana,
  productividad_ha) existan en la pagina destino antes de inyectar.
- Ruta resuelta via eva_config.EVA_PROJECT_ROOT si esta disponible,
  con fallback a ruta relativa.
"""
from __future__ import annotations

import py_compile
import shutil
import sys
import textwrap
from pathlib import Path

# --- Resolucion de ruta -----------------------------------------------
try:
    from eva_config import EVA_PROJECT_ROOT  # single source of truth del proyecto
    PROJECT_ROOT = Path(EVA_PROJECT_ROOT)
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGINA = PROJECT_ROOT / "ui" / "pages" / "23_Valor_Economico.py"

# --- Config de la seccion ----------------------------------------------
TOP_N = 15
MARCADOR = "# --- SECCION AUTOGENERADA: productividad_economica ---"
DEPENDENCIAS_REQUERIDAS = ("anio", "sin_cana", "productividad_ha")

SECCION = textwrap.dedent(f'''
{MARCADOR}
st.markdown("---")
st.markdown("### Productividad economica (COP/ha/ano)")
st.caption("Valor generado por hectarea cosechada. Mide eficiencia productiva, no valor del suelo.")

prod = productividad_ha(anio, sin_cana)
if not prod.empty:
    top_prod = prod.index[0]
    v_top = prod.loc[top_prod, "cop_ha"]
    st.metric(f"Mayor productividad {{anio}}", top_prod, f"{{v_top / 1e6:.1f}} M COP/ha")

    c1, c2 = st.columns([3, 2])
    with c1:
        tp = prod.head({TOP_N}).copy()
        tp["M_COP_ha"] = (tp.cop_ha / 1e6).round(2)
        tp["area_ha"] = tp.area.round(0)
        tp["M_COP_total"] = (tp.valor / 1e6).round(0)
        st.table(tp[["M_COP_ha", "area_ha", "M_COP_total"]])
    with c2:
        fig = go.Figure(go.Bar(
            x=(prod.head({TOP_N}).cop_ha / 1e6).round(2),
            y=prod.head({TOP_N}).index,
            orientation="h",
            marker_color="#C98A2B"))
        fig.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.caption("Fuente: PIB agro (precios oficiales UPRA 2025) / area cosechada EVA 2025.")
else:
    st.info("No hay datos de productividad economica para el filtro seleccionado.")
''')


def validar_dependencias(contenido: str) -> list[str]:
    """Devuelve la lista de nombres requeridos que NO aparecen en el archivo."""
    return [dep for dep in DEPENDENCIAS_REQUERIDAS if dep not in contenido]


def asegurar_import_plotly(contenido: str) -> str:
    """Agrega el import de plotly.graph_objects al tope si aun no existe."""
    if "plotly.graph_objects" in contenido:
        return contenido
    lineas = contenido.splitlines(keepends=True)
    # Inserta despues del bloque de imports iniciales (primera linea en blanco tras imports)
    idx_insert = 0
    for i, linea in enumerate(lineas):
        if linea.startswith(("import ", "from ")):
            idx_insert = i + 1
    lineas.insert(idx_insert, "import plotly.graph_objects as go\n")
    return "".join(lineas)


def main() -> int:
    if not PAGINA.exists():
        print(f"[ERROR] no existe la pagina: {PAGINA}")
        return 1

    original = PAGINA.read_text(encoding="utf-8")

    if MARCADOR in original:
        print("[AVISO] la seccion ya existe; nada que hacer")
        return 0

    faltantes = validar_dependencias(original)
    if faltantes:
        print(f"[ERROR] la pagina no define: {', '.join(faltantes)}. "
              f"Abortando para no inyectar codigo roto.")
        return 1

    nuevo_contenido = asegurar_import_plotly(original)
    nuevo_contenido = nuevo_contenido.rstrip("\n") + "\n" + SECCION

    backup = PAGINA.with_suffix(PAGINA.suffix + ".bak")
    shutil.copy2(PAGINA, backup)

    PAGINA.write_text(nuevo_contenido, encoding="utf-8")

    try:
        py_compile.compile(str(PAGINA), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"[ERROR] sintaxis invalida tras la insercion, revirtiendo: {e}")
        shutil.copy2(backup, PAGINA)
        return 1

    print(f"[OK] seccion de productividad agregada a {PAGINA.name}")
    print(f"[OK] backup guardado en {backup.name}")
    print("\nVerifica local: reinicia Streamlit y entra a Valor Economico")
    return 0


if __name__ == "__main__":
    sys.exit(main())