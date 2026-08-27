"""El Asistente declara su horizonte: no extrapola mas alla de 2028 ni antes de 2019."""
from pathlib import Path

p = Path("core/chat/engine.py")
c = p.read_text(encoding="utf-8")
cambios = 0

# 1) Detectar cualquier ano de 4 digitos (no solo 2019-2028)
old1 = '''    ma = re.search(r"20(1[9]|2[0-8])", q)
    ano = int(ma.group(0)) if ma else None
    return (munis[0] if munis else None), cult, ano, munis'''
new1 = '''    ma = re.search(r"20(1[9]|2[0-8])", q)
    ano = int(ma.group(0)) if ma else None
    ry = re.search(r"\\b\\d{4}\\b", q)
    raw = int(ry.group(0)) if ry else None
    return (munis[0] if munis else None), cult, ano, munis, raw'''
if old1 in c:
    c = c.replace(old1, new1, 1); cambios += 1
    print("[OK] Deteccion de anos fuera de rango")

# 2) Desempaque del nuevo valor
old2 = "    muni, cult, ano, munis = _entities(q, df)"
new2 = "    muni, cult, ano, munis, raw = _entities(q, df)"
if old2 in c:
    c = c.replace(old2, new2, 1); cambios += 1
    print("[OK] Desempaque actualizado")

# 3) Guardia de horizonte antes de responder
old3 = '''    if cult:
        ctx["cult"] = cult
    intent = _intent(q)'''
new3 = '''    if cult:
        ctx["cult"] = cult
    if raw is not None and (raw > 2028 or raw < 2019):
        if raw > 2028:
            out = {"texto": f"Mi horizonte de proyeccion llega a 2028 (3 anos, con credibilidad "
                            f"declarada por backtesting). Para {raw} la incertidumbre supera el "
                            f"limite metodologico: prefiero no extrapolar. Prueba con 2026-2028.",
                   "pagina": "Predictivo"}
        else:
            out = {"texto": f"La serie oficial EVA arranca en 2019; no tengo datos para {raw}.",
                   "pagina": "Descriptivo"}
        out["ctx"] = ctx
        return out
    intent = _intent(q)'''
if old3 in c:
    c = c.replace(old3, new3, 1); cambios += 1
    print("[OK] Guardia de horizonte agregada")

if cambios:
    p.write_text(c, encoding="utf-8")
    print(f"[OK] {cambios} parches aplicados")
else:
    print("[AVISO] Bloques no encontrados")