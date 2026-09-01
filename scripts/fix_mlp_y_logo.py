"""Diagnostico + fix robusto: MLP en forecast.py y deteccion de logo en PDFs."""
import re
from pathlib import Path

fc = Path("core/analytics/forecast.py")
c = fc.read_text(encoding="utf-8")
print("=== DIAGNOSTICO forecast.py ===")
print("contiene import mlp_forecast:", "from core.analytics.mlp_forecast" in c)
print("contiene modelo_mlp(       :", "modelo_mlp(" in c)
print("contiene MLP (5-8-4-1)     :", "MLP (5-8-4-1)" in c)

cambios = 0
if "from core.analytics.mlp_forecast" not in c:
    c = c.replace("import pandas as pd",
                  "import pandas as pd\nfrom core.analytics.mlp_forecast import modelo_mlp, proyectar_mlp", 1)
    cambios += 1
if "modelo_mlp(" not in c:
    c = c.replace("modelo_holt(t_train, s_train, 0.5, 0.2),\n    ]",
                  "modelo_holt(t_train, s_train, 0.5, 0.2),\n        modelo_mlp(pd.Series(s_train)),\n    ]", 1)
    cambios += 1
if "serie_original" not in c:
    c = c.replace("def _proyectar(modelo: dict, n_steps: int) -> np.ndarray:",
                  "def _proyectar(modelo: dict, n_steps: int, serie_original=None) -> np.ndarray:", 1)
    cambios += 1
if 'nombre == "MLP (5-8-4-1)"' not in c:
    c = c.replace('return np.full(n_steps, modelo["last_mean"])\n    else:  # Holt',
                  'return np.full(n_steps, modelo["last_mean"])\n'
                  '    elif nombre == "MLP (5-8-4-1)":\n'
                  '        return proyectar_mlp(modelo, n_steps, modelo.get("serie_train", serie_original))\n'
                  '    else:  # Holt', 1)
    cambios += 1
if "_proyectar(m, n_out, serie)" not in c:
    c = c.replace("pred = _proyectar(m, n_out)", "pred = _proyectar(m, n_out, serie)", 1)
    cambios += 1
if "modelo_full = modelo_mlp(serie)" not in c:
    c = c.replace('modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])\n    else:',
                  'modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])\n'
                  '    elif nombre == "MLP (5-8-4-1)":\n'
                  '        modelo_full = modelo_mlp(serie)\n'
                  '    else:', 1)
    cambios += 1
fc.write_text(c, encoding="utf-8")
print(f"[OK] forecast.py: {cambios} cambios aplicados")

# serie_train en mlp_forecast (para backtest sin fuga de datos)
mf = Path("core/analytics/mlp_forecast.py")
m = mf.read_text(encoding="utf-8")
if "serie_train" not in m:
    m = m.replace('"mape_train": mape}', '"mape_train": mape, "serie_train": serie.copy()}')
    mf.write_text(m, encoding="utf-8")
    print("[OK] mlp_forecast.py: serie_train agregada (backtest sin fuga)")
else:
    print("[OK] mlp_forecast.py ya tiene serie_train")

# Diagnostico de logo en reportes
print("\n=== DIAGNOSTICO logo en core/reports ===")
for p in sorted(Path("core/reports").glob("*.py")):
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if re.search(r"logo|drawImage|add_picture|Image", line, re.I):
            print(f"{p.name}:{i}: {line.strip()}")
print("\nArchivos de logo en el repo:")
for p in Path(".").rglob("*logo*"):
    if ".git" not in str(p) and ".venv" not in str(p):
        print(" ", p)