"""Fix doble: (1) clip anti-explosion del MLP + saneamiento de residuos,
(2) branding.py con logo tamanyado correctamente."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ---------- 1) mlp_forecast.py: clip de predicciones ----------
mp = ROOT / "core" / "analytics" / "mlp_forecast.py"
m = mp.read_text(encoding="utf-8")

old1 = """        area_avg = float(np.mean(s))
        preds, hist = [], list(s[-2:])
        n = len(s)"""
new1 = """        area_avg = float(np.mean(s))
        cap = 3.0 * float(np.max(s))
        preds, hist = [], list(s[-2:])
        n = len(s)"""
if "cap = 3.0" not in m:
    m = m.replace(old1, new1)
    old2 = """            p = p * (self.y_max - self.y_min) + self.y_min
            preds.append(p)"""
    new2 = """            p = p * (self.y_max - self.y_min) + self.y_min
            p = float(np.clip(p, 0.0, cap))
            preds.append(p)"""
    m = m.replace(old2, new2)
    mp.write_text(m, encoding="utf-8")
    print("[OK] mlp_forecast.py: clip [0, 3x max historico] aplicado")
else:
    print("[OK] mlp_forecast.py ya tiene clip")

# ---------- 2) forecast.py: saneamiento de residuos ----------
fp = ROOT / "core" / "analytics" / "forecast.py"
f = fp.read_text(encoding="utf-8")
old3 = """    residuos = np.asarray(res["residuos"], dtype=float)
    if len(residuos) and float(np.std(residuos)) > 0:
        residuos = residuos - float(np.mean(residuos))"""
new3 = """    residuos = np.asarray(res["residuos"], dtype=float)
    residuos = residuos[np.isfinite(residuos)]
    if len(residuos):
        med = float(np.median(np.abs(residuos)))
        if med > 1e-8:
            residuos = residuos[np.abs(residuos) <= 10.0 * med]
    if not len(residuos):
        residuos = np.array([0.0])
    if len(residuos) and float(np.std(residuos)) > 0:
        residuos = residuos - float(np.mean(residuos))"""
if "np.isfinite(residuos)" not in f:
    f = f.replace(old3, new3)
    fp.write_text(f, encoding="utf-8")
    print("[OK] forecast.py: residuos saneados (finitos + cota 10x mediana)")
else:
    print("[OK] forecast.py ya sanea residuos")

# ---------- 3) branding.py: reescrito con logo tamanyado ----------
bp = ROOT / "core" / "reports" / "branding.py"
bp.write_text('''"""Marca institucional: logo en cada pagina de todos los PDF."""
from pathlib import Path

from reportlab.lib.units import cm

_IMG = Path(__file__).resolve().parents[2] / "ui" / "assets" / "img"
LOGO = _IMG / "logo_pdf.png"
if not LOGO.exists():
    LOGO = _IMG / "logo.png"


def pagina_con_logo(canvas, doc):
    if not LOGO.exists():
        return
    canvas.drawImage(str(LOGO), 18.4 * cm, 24.6 * cm,
                     width=2.4 * cm, height=2.4 * cm,
                     preserveAspectRatio=True, mask="auto")
''', encoding="utf-8")
print("[OK] branding.py reescrito: logo 2.4x2.4 cm arriba a la derecha")

# ---------- 4) Verificacion inmediata ----------
import pandas as pd
from config.settings import settings
from core.analytics.forecast import proyectar_con_ic

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)
serie = (df[(df.municipio == "Alcalá") & (df.cultivo == "Plátano")]
         .groupby("ano")["produccion_t"].sum().sort_index())
res = proyectar_con_ic(serie, n_steps=3)
esc = res["escenarios"]
print(f"\nGanador: {res['ganador']} | MAPE {res['mape']:.2f}%")
print(f"Tendencial: {esc['tendencial'].round(0).tolist()}")
print(f"Conservador: {esc['conservador'].round(0).tolist()}")
print(f"Optimista: {esc['optimista'].round(0).tolist()}")
ok = float(np.max(esc["optimista"])) < 1e6 if 'np' in dir() else True
import numpy as np
ok = float(np.max(esc["optimista"])) < 1e6
print("\n✅ ESCENARIOS CUERDOS (< 1M t)" if ok else "\n❌ SIGUE EXPLOTANDO")