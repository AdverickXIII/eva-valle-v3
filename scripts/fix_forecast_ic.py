"""Fix escenarios: residuos centrados (IC abraza el tendencial) + piso en 0."""
from pathlib import Path

p = Path("core/analytics/forecast.py")
c = p.read_text(encoding="utf-8")

old_blk = '''    pred = _proyectar(res["modelo"], n_steps)
    residuos = res["residuos"]
    cuantiles = {f"P{int(p*100)}": float(np.quantile(residuos, p)) for p in niveles}
    escenarios = {
        "conservador": pred + cuantiles["P10"],
        "tendencial": pred,
        "optimista": pred + cuantiles["P90"],
        "ic_bajo": pred + cuantiles["P25"],
        "ic_alto": pred + cuantiles["P75"],
    }'''

new_blk = '''    pred = _proyectar(res["modelo"], n_steps)
    residuos = np.asarray(res["residuos"], dtype=float)
    # Centrar residuos: quita el sesgo sistematico del ajuste in-sample para que
    # el IC y los escenarios abracen al tendencial (P10 <= 0 <= P90)
    if len(residuos) and float(np.std(residuos)) > 0:
        residuos = residuos - float(np.mean(residuos))
    cuantiles = {f"P{int(p*100)}": float(np.quantile(residuos, p)) for p in niveles}
    # Piso en cero: la produccion negativa no existe
    escenarios = {
        "conservador": np.maximum(0.0, pred + cuantiles["P10"]),
        "tendencial": np.maximum(0.0, pred),
        "optimista": np.maximum(0.0, pred + cuantiles["P90"]),
        "ic_bajo": np.maximum(0.0, pred + cuantiles["P25"]),
        "ic_alto": np.maximum(0.0, pred + cuantiles["P75"]),
    }'''

if old_blk in c:
    c = c.replace(old_blk, new_blk, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Residuos centrados + piso en cero aplicados")
else:
    print("[AVISO] Bloque distinto; revisa manualmente forecast.py")

print("Reinicia Streamlit y regenera las 3 proyecciones de Andalucia")