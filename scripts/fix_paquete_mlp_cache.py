"""AUD-ML-006 v3: paquete reconciliado + rename completo del nombre del modelo.
Fix 1: mlp_forecast sin features fugadas/muertas, W1 3->8, rename MLP (3-8-4-1)
       en mlp_forecast (funcional+docstring), forecast (funcional+docstring) y
       predictivo_pdf (prosa del reporte).
Fix 4: cache de proyectar_con_ic en 4_Predictivo via _proyectar_cacheado.
Fix 2/3: ya en disco via AUD-ML-004 v3 (forma mejor); solo se verifican.
v3: predictivo_pdf entra al rename; grep de terceros excluye tools fix_*.py.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MLP = RAIZ / "core" / "analytics" / "mlp_forecast.py"
FC = RAIZ / "core" / "analytics" / "forecast.py"
PDFR = RAIZ / "core" / "reports" / "predictivo_pdf.py"
PRED = RAIZ / "ui" / "pages" / "4_Predictivo.py"
LOG = RAIZ / "logs" / "audit_hotfix.jsonl"

# ---------- Fix 1: mlp_forecast ----------
VIEJO_DOC_MLP = '''"""MLP 5-8-4-1 desde cero para forecasting de series agricolas cortas.
Features: [ano, area, rendimiento, prod_t-1, prod_t-2] -> prod_t.
AUD-MLP-002: residuos leave-one-out trazables (loo_fitted_) reemplazan el
bucle de re-entrenamiento degenerado; clip [0, 3x max historico] (AUD-MLP-001)."""'''

NUEVO_DOC_MLP = '''"""MLP 3-8-4-1 desde cero para forecasting de series agricolas cortas.
AUD-MLP-003: features [ano, prod_t-1, prod_t-2] -> prod_t. Se eliminan
'rendimiento' (fuga: target/constante) y 'area' (columna muerta tras
normalizar); capa de entrada reducida de 5 a 3 (nombre acorde en AUD-ML-006).
AUD-MLP-002: residuos leave-one-out trazables (loo_fitted_) reemplazan el
bucle de re-entrenamiento degenerado; clip [0, 3x max historico] (AUD-MLP-001)."""'''

VIEJO_FEAT = '''    def _build_features(self, s):
        area_avg = float(np.mean(s)) if len(s) > 0 else 1.0
        X, y = [], []
        for i in range(2, len(s)):
            rend = s[i] / area_avg if area_avg > 0 else 0.0
            X.append([2019 + i, area_avg, rend, s[i - 1], s[i - 2]])
            y.append(s[i])
        return np.array(X), np.array(y)'''

NUEVO_FEAT = '''    def _build_features(self, s):
        # AUD-MLP-003: sin rend (fuga: target/cte) ni area_avg (columna muerta).
        X, y = [], []
        for i in range(2, len(s)):
            X.append([2019 + i, s[i - 1], s[i - 2]])
            y.append(s[i])
        return np.array(X), np.array(y)'''

VIEJO_W1 = '''        self.W1 = rng.randn(5, 8) * np.sqrt(2.0 / 13)'''
NUEVO_W1 = '''        self.W1 = rng.randn(3, 8) * np.sqrt(2.0 / 11)'''

VIEJO_PRED = '''        area_avg = float(np.mean(s))
        cap = MLP_CAP_MULTIPLIER * float(np.max(s))
        preds, hist = [], list(s[-2:])
        n = len(s)
        for _ in range(n_steps):
            rend = hist[-1] / area_avg if area_avg > 0 else 0.0
            feat = np.array([[2019 + n, area_avg, rend, hist[-1], hist[-2]]])'''

NUEVO_PRED = '''        cap = MLP_CAP_MULTIPLIER * float(np.max(s))
        preds, hist = [], list(s[-2:])
        n = len(s)
        for _ in range(n_steps):
            feat = np.array([[2019 + n, hist[-1], hist[-2]]])'''

VIEJO_NOMBRE = '''    return {"nombre": "MLP (5-8-4-1)", "mlp": mlp, "fitted": fitted,'''
NUEVO_NOMBRE = '''    return {"nombre": "MLP (3-8-4-1)", "mlp": mlp, "fitted": fitted,'''

# ---------- Fix 4: cache en 4_Predictivo ----------
FUNCION_CACHE = '''@st.cache_data(ttl=3600, show_spinner="Calculando proyeccion (ensemble + MLP)...")
def _proyectar_cacheado(serie: pd.Series, horizonte: int) -> dict:
    return proyectar_con_ic(serie, n_steps=horizonte)


'''
VIEJA_LLAMADA = 'res = proyectar_con_ic(serie, n_steps=horizonte)'
NUEVA_LLAMADA = 'res = _proyectar_cacheado(serie, horizonte)'


def audit(evento, estado, detalle=""):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "evento": evento, "estado": estado,
                            "detalle": detalle}, ensure_ascii=False) + "\n")


def fail(motivo):
    audit("AUD-ML-006", "FALLO", motivo)
    print(f"[ERROR] {motivo}")
    return 1


def main():
    try:
        t_mlp = MLP.read_text(encoding="utf-8")
        t_fc = FC.read_text(encoding="utf-8")
        t_pdf = PDFR.read_text(encoding="utf-8")
        t_pred = PRED.read_text(encoding="utf-8")
    except Exception as e:
        return fail(f"no se pudo leer archivos: {e}")

    if "pronostico de un paso: L_{i-1}" not in t_fc or "holdout de 1" not in t_fc:
        return fail("AUD-ML-004 v3 no esta en forecast.py; ejecutarlo antes")
    print("[INFO] Fix 2 y Fix 3 ya estan en disco via AUD-ML-004 v3 (forma mejor): no se tocan")

    # Grep de terceros: excluye .venv, scripts/, .bak, tools fix_*.py y los 3 objetivos
    terceros = []
    for p in RAIZ.rglob("*.py"):
        rel = p.relative_to(RAIZ)
        if ".venv" in rel.parts or "scripts" in rel.parts or p.name.endswith(".bak"):
            continue
        if p.name.startswith("fix_") or p in (MLP, FC, PDFR):
            continue
        if "5-8-4-1" in p.read_text(encoding="utf-8"):
            terceros.append(str(rel))
    if terceros:
        return fail(f"rename bloqueado: '5-8-4-1' tambien vive en {terceros}")

    # ---------- mlp_forecast ----------
    doc_mlp = VIEJO_DOC_MLP in t_mlp
    func_mlp = "AUD-MLP-003: sin rend" in t_mlp
    if func_mlp and not doc_mlp:
        t_mlp_n = None
        print("[INFO] Fix 1 ya aplicado por completo en mlp_forecast.py")
    elif func_mlp and doc_mlp:
        t_mlp_n = t_mlp.replace(VIEJO_DOC_MLP, NUEVO_DOC_MLP, 1)
    else:
        for ancla, nombre in ((VIEJO_DOC_MLP, "docstring"), (VIEJO_FEAT, "_build_features"),
                              (VIEJO_W1, "W1"), (VIEJO_PRED, "predict"),
                              (VIEJO_NOMBRE, "nombre modelo")):
            if t_mlp.count(ancla) != 1:
                return fail(f"mlp: ancla {nombre} = {t_mlp.count(ancla)} coincidencias")
        t_mlp_n = (t_mlp.replace(VIEJO_DOC_MLP, NUEVO_DOC_MLP, 1)
                        .replace(VIEJO_FEAT, NUEVO_FEAT, 1)
                        .replace(VIEJO_W1, NUEVO_W1, 1)
                        .replace(VIEJO_PRED, NUEVO_PRED, 1)
                        .replace(VIEJO_NOMBRE, NUEVO_NOMBRE, 1))

    # ---------- forecast: rename funcional + docstring ----------
    n_fc = t_fc.count('"MLP (5-8-4-1)"')
    if n_fc == 2:
        t_fc_n = t_fc.replace('"MLP (5-8-4-1)"', '"MLP (3-8-4-1)"')
    elif n_fc == 0:
        t_fc_n = None
    else:
        return fail(f"forecast: {n_fc} coincidencias del nombre funcional (esperaba 2)")
    base_fc = t_fc_n if t_fc_n is not None else t_fc
    if "MLP 5-8-4-1" in base_fc:
        t_fc_n = base_fc.replace("MLP 5-8-4-1", "MLP 3-8-4-1")
    if t_fc_n is None:
        print("[INFO] forecast.py ya sin cadenas 5-8-4-1")

    # ---------- predictivo_pdf: prosa del reporte ----------
    n_pdf = t_pdf.count("MLP 5-8-4-1")
    if n_pdf == 1:
        t_pdf_n = t_pdf.replace("MLP 5-8-4-1", "MLP 3-8-4-1")
    elif n_pdf == 0:
        t_pdf_n = None
        print("[INFO] predictivo_pdf.py ya sin cadenas 5-8-4-1")
    else:
        return fail(f"predictivo_pdf: {n_pdf} coincidencias (esperaba 1)")

    # ---------- 4_Predictivo: cache ----------
    if "_proyectar_cacheado" in t_pred:
        t_pred_n = None
        print("[INFO] Fix 4 ya aplicado en 4_Predictivo.py")
    else:
        if t_pred.count(VIEJA_LLAMADA) != 1:
            return fail(f"predictivo: llamada = {t_pred.count(VIEJA_LLAMADA)} coincidencias")
        lineas = t_pred.splitlines(keepends=True)
        i_main = next((i for i, l in enumerate(lineas) if l.startswith("def main(")), None)
        if i_main is None:
            return fail("predictivo: def main( no encontrada")
        lineas[i_main:i_main] = FUNCION_CACHE.splitlines(keepends=True)
        t_pred_n = "".join(lineas).replace(VIEJA_LLAMADA, NUEVA_LLAMADA, 1)

    if t_mlp_n is None and t_fc_n is None and t_pdf_n is None and t_pred_n is None:
        print("[SKIP] paquete ya aplicado por completo")
        return 0

    for txt, nombre in ((t_mlp_n, "mlp_forecast"), (t_fc_n, "forecast"), (t_pdf_n, "predictivo_pdf")):
        if txt is not None and "5-8-4-1" in txt:
            return fail(f"higiene: queda '5-8-4-1' en {nombre} tras el parche")

    backups = {}
    try:
        for ruta, nuevo in ((MLP, t_mlp_n), (FC, t_fc_n), (PDFR, t_pdf_n), (PRED, t_pred_n)):
            if nuevo is not None:
                bak = ruta.with_suffix(ruta.suffix + ".bak")
                shutil.copy2(ruta, bak)
                backups[ruta] = bak
                ruta.write_text(nuevo, encoding="utf-8")
                print(f"[OK] {ruta.name} actualizado | backup: {bak.name}")
    except Exception as e:
        for r2, b2 in backups.items():
            shutil.copy2(b2, r2)
        return fail(f"fallo de escritura, revirtiendo {len(backups)} archivos: {e}")

    for ruta in backups:
        r = subprocess.run([sys.executable, "-m", "py_compile", str(ruta)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            for r2, b2 in backups.items():
                shutil.copy2(b2, r2)
            audit("AUD-ML-006", "ROLLBACK", r.stderr[:300])
            return fail(f"sintaxis invalida en {ruta.name}, revirtiendo todo")

    # ---------- Autotests con modulos frescos ----------
    sys.path.insert(0, str(RAIZ))
    for name in list(sys.modules):
        if name == "core" or name.startswith("core."):
            del sys.modules[name]
    import numpy as np
    import pandas as pd
    from core.analytics.mlp_forecast import MLPForecast
    from core.analytics import forecast

    s = pd.Series([100.0, 110.0, 121.0, 133.0, 140.0, 150.0, 160.0])
    m = MLPForecast(seed=42)
    X, y = m._build_features(s.values)
    if X.shape[1] != 3:
        return fail(f"autotest: X con {X.shape[1]} columnas (esperaba 3)")
    yn = (y - y.min()) / (y.max() - y.min() + 1e-8)
    for k in range(3):
        xk = (X[:, k] - X[:, k].min()) / (X[:, k].max() - X[:, k].min() + 1e-8)
        if np.allclose(xk, yn):
            return fail(f"autotest: columna {k} sigue fugando el target")
    m.fit(s, epochs=50, lr=0.05)
    if not np.all(np.isfinite(m.predict(s, 3))):
        return fail("autotest: predict no finito")
    mod = forecast.modelo_mlp(s)
    if mod["nombre"] != "MLP (3-8-4-1)":
        return fail(f"autotest: nombre = {mod['nombre']}")
    if not np.all(np.isfinite(forecast._proyectar(mod, 2, s))):
        return fail("autotest: _proyectar no rutea el nombre nuevo")
    r_e = forecast.elegir_mejor(s)
    if r_e["modelo"] is None:
        return fail("autotest: elegir_mejor sin modelo")
    print(f"[OK] autotests: fuga eliminada, nombre ruteado, ensemble vivo "
          f"(ganador '{r_e['ganador']}')")

    audit("AUD-ML-006", "OK", "v3: Fix 1 + Fix 4 + rename en 3 consumidores + docstrings")
    print("[OK] AUD-ML-006 v3 aplicado, compilado y autotesteado")
    return 0


if __name__ == "__main__":
    sys.exit(main())