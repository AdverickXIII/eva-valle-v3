"""AUD-CHAT-001: guards de datos vacios en core/chat/engine.py.
1) rama cult+mun: g.empty -> mensaje amigable (fix del IndexError de produccion).
2) rama cult+mun+ano: filtro vacio -> mensaje amigable (evita 'produjo 0 t' falso).
3) comparador: min(ta,tb)<=0 -> sin ratio (evita ZeroDivisionError).
Pre-chequeo: la UI no debe indexar r["serie"] sin .get (porque las ramas vacias
ya no incluyen esa clave). Autotest: 'pina santiago de cali' no crashea.
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENG = RAIZ / "core" / "chat" / "engine.py"
UI = RAIZ / "ui" / "pages" / "21_Asistente.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

VIEJO_CM = '''    elif cult and muni:
        g = _agg(df, muni, cult)
        out = {"texto": f"{cult} en {muni}: {_fmt(g['p'].sum())} t acumuladas; ultimo ano "
                        f"{_fmt(g['p'].iloc[-1])} t (rendimiento {_div(g['p'].iloc[-1], g['c'].iloc[-1]):.1f} t/ha).",
               "pagina": "Cultivos", "serie": _serie(df, muni, cult)}
'''

NUEVO_CM = '''    elif cult and muni:
        g = _agg(df, muni, cult)
        if g.empty:
            out = {"texto": f"No tengo registros de {cult} en {muni} dentro de la serie "
                            f"EVA 2019-2025. Prueba con otro cultivo o con el resumen del municipio.",
                   "pagina": "Cultivos"}
        else:
            out = {"texto": f"{cult} en {muni}: {_fmt(g['p'].sum())} t acumuladas; ultimo ano "
                            f"{_fmt(g['p'].iloc[-1])} t (rendimiento {_div(g['p'].iloc[-1], g['c'].iloc[-1]):.1f} t/ha).",
                   "pagina": "Cultivos", "serie": _serie(df, muni, cult)}
'''

VIEJO_ANO = '''    elif cult and muni and ano:
        v = df[(df["municipio"] == muni) & (df["cultivo"] == cult) & (df["ano"] == ano)]["produccion_t"].sum()
        out = {"texto": f"{muni} produjo {_fmt(v)} t de {cult} en {ano}.",
               "pagina": "Cultivos", "serie": _serie(df, muni, cult)}
'''

NUEVO_ANO = '''    elif cult and muni and ano:
        fa = df[(df["municipio"] == muni) & (df["cultivo"] == cult) & (df["ano"] == ano)]
        if fa.empty:
            out = {"texto": f"No tengo registros de {cult} en {muni} para {ano}. "
                            f"La serie EVA cubre 2019-2025.",
                   "pagina": "Cultivos"}
        else:
            v = fa["produccion_t"].sum()
            out = {"texto": f"{muni} produjo {_fmt(v)} t de {cult} en {ano}.",
                   "pagina": "Cultivos", "serie": _serie(df, muni, cult)}
'''

VIEJO_CMP = '''        out = {"texto": f"{a}: {_fmt(ta)} t y {ca} cultivos. {b}: {_fmt(tb)} t y {cb} cultivos. "
                        f"Ratio {max(ta, tb) / min(ta, tb):.1f}x a favor de {a if ta > tb else b}.",
               "pagina": "Comparador"}
'''

NUEVO_CMP = '''        if min(ta, tb) <= 0:
            out = {"texto": f"{a}: {_fmt(ta)} t y {ca} cultivos. {b}: {_fmt(tb)} t y {cb} cultivos. "
                            f"No hay ratio comparativo: uno de los dos no registra produccion.",
                   "pagina": "Comparador"}
        else:
            out = {"texto": f"{a}: {_fmt(ta)} t y {ca} cultivos. {b}: {_fmt(tb)} t y {cb} cultivos. "
                            f"Ratio {max(ta, tb) / min(ta, tb):.1f}x a favor de {a if ta > tb else b}.",
                   "pagina": "Comparador"}
'''


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-CHAT-001", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def rollback_or_fail(motivo, bak):
    try:
        shutil.copy2(bak, ENG)
    except Exception as e:
        audit("AUD-CHAT-001", "ROLLBACK_FALLIDO", f"{motivo} | rollback: {e}")
        print(f"[ERROR] {motivo} Y el rollback fallo: {e}")
        return 1
    audit("AUD-CHAT-001", "ROLLBACK", motivo)
    print(f"[ERROR] {motivo}; revirtiendo a {bak.name}")
    return 1


def main():
    try:
        texto = ENG.read_text(encoding="utf-8")
        ui = UI.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer archivos: {e}")

    if "No tengo registros de" in texto:
        print("[SKIP] AUD-CHAT-001 ya aplicado")
        return 0

    # Pre-chequeo UI: las ramas vacias ya no envian "serie"; la UI no debe indexarla en crudo
    if re.search(r'\[\s*"serie"\s*\]', ui) and '.get("serie"' not in ui:
        return fail("21_Asistente.py indexa r[\"serie\"] en crudo; revisar UI antes de omitir la clave")

    for ancla, nombre in ((VIEJO_CM, "rama cult+mun"), (VIEJO_ANO, "rama cult+mun+ano"),
                          (VIEJO_CMP, "comparador")):
        if texto.count(ancla) != 1:
            return fail(f"ancla de {nombre}: {texto.count(ancla)} coincidencias (esperaba 1)")

    texto_nuevo = (texto
                   .replace(VIEJO_CM, NUEVO_CM, 1)
                   .replace(VIEJO_ANO, NUEVO_ANO, 1)
                   .replace(VIEJO_CMP, NUEVO_CMP, 1))

    try:
        bak = ENG.with_suffix(".py.bak")
        shutil.copy2(ENG, bak)
        ENG.write_text(texto_nuevo, encoding="utf-8")
    except Exception as e:
        return fail(f"fallo de escritura: {e}")
    print(f"[OK] engine.py parcheado (3 guards) | backup: {bak.name}")

    r = subprocess.run([sys.executable, "-m", "py_compile", str(ENG)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return rollback_or_fail(f"sintaxis invalida: {r.stderr[:200]}", bak)

    # ---------- Autotest: el caso que crasheaba ----------
    sys.path.insert(0, str(RAIZ))
    for name in list(sys.modules):
        if name == "core" or name.startswith("core."):
            del sys.modules[name]
    from core.chat import engine
    try:
        r1 = engine.ask("piña santiago de cali", ctx=None)
    except TypeError:
        r1 = engine.ask("piña santiago de cali")
    txt = r1.get("texto", "")
    if "No tengo registros" not in txt:
        return rollback_or_fail(f"autotest: respuesta inesperada: {txt[:80]}", bak)
    print(f"[OK] autotest crash: 'piña santiago de cali' -> {txt[:70]}...")

    # Control positivo (informativo, no gate): combinacion con datos sigue funcionando
    try:
        try:
            r2 = engine.ask("platano santiago de cali", ctx=None)
        except TypeError:
            r2 = engine.ask("platano santiago de cali")
        print(f"[INFO] control positivo: {r2.get('texto', '')[:70]}...")
    except Exception as e:
        print(f"[WARN] control positivo no ejecutable: {e}")

    audit("AUD-CHAT-001", "OK", "guards de datos vacios en engine.py (3 ramas)")
    print("[OK] AUD-CHAT-001 aplicado, compilado y autotesteado")
    return 0


if __name__ == "__main__":
    sys.exit(main())