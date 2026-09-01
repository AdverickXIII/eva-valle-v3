"""Crea mlp_forecast.py y modifica forecast.py para integrar MLP (v3 corregida)."""
from pathlib import Path

# ============================================================
# 1) Crear core/analytics/mlp_forecast.py
# ============================================================
mlp_code = '''"""MLP para forecasting de series agricolas cortas."""
import numpy as np
import pandas as pd
from typing import Tuple, Optional


class MLPForecast:
    """MLP 5-8-4-1 con backprop desde cero."""

    def __init__(self, seed=42):
        self.seed = seed
        self.W1 = self.W2 = self.W3 = None
        self.b1 = self.b2 = self.b3 = None
        self.X_min = self.X_max = None
        self.y_min = self.y_max = None

    def _build_features(self, serie):
        area_avg = float(np.mean(serie)) if len(serie) > 0 else 1.0
        features, targets = [], []
        for i in range(2, len(serie)):
            ano = 2019 + i
            rend = serie[i] / area_avg if area_avg > 0 else 0.0
            features.append([ano, area_avg, rend, serie[i - 1], serie[i - 2]])
            targets.append(serie[i])
        return np.array(features), np.array(targets)

    def fit(self, serie, epochs=2000, lr=0.05):
        s = serie.dropna().astype(float).values
        if len(s) < 4:
            return np.inf
        X_raw, y_raw = self._build_features(s)
        if len(X_raw) < 2:
            return np.inf

        self.X_min, self.X_max = X_raw.min(0), X_raw.max(0)
        X_norm = (X_raw - self.X_min) / (self.X_max - self.X_min + 1e-8)
        self.y_min, self.y_max = float(y_raw.min()), float(y_raw.max())
        y_norm = (y_raw - self.y_min) / (self.y_max - self.y_min + 1e-8)

        rng = np.random.RandomState(self.seed)
        self.W1 = rng.randn(5, 8) * np.sqrt(2.0 / 13)
        self.W2 = rng.randn(8, 4) * np.sqrt(2.0 / 12)
        self.W3 = rng.randn(4, 1) * np.sqrt(2.0 / 5)
        self.b1 = np.zeros((8, 1))
        self.b2 = np.zeros((4, 1))
        self.b3 = np.zeros((1, 1))

        mapes = []
        for fold in range(len(X_norm)):
            tr = [i for i in range(len(X_norm)) if i != fold]
            X_tr, y_tr = X_norm[tr].T, y_norm[tr].reshape(1, -1)
            X_te = X_norm[[fold]].T
            y_te = y_norm[[fold]]

            for _ in range(epochs):
                z1 = self.W1.T @ X_tr + self.b1
                a1 = np.maximum(0, z1)
                z2 = self.W2.T @ a1 + self.b2
                a2 = np.maximum(0, z2)
                z3 = self.W3.T @ a2 + self.b3
                m = y_tr.shape[1]
                dz3 = (2.0 / m) * (z3 - y_tr)
                dW3 = a2 @ dz3.T
                db3 = dz3.sum(1, keepdims=True)
                dz2 = (self.W3 @ dz3) * (a2 > 0)
                dW2 = a1 @ dz2.T
                db2 = dz2.sum(1, keepdims=True)
                dz1 = (self.W2 @ dz2) * (a1 > 0)
                dW1 = X_tr @ dz1.T
                db1 = dz1.sum(1, keepdims=True)
                self.W1 -= lr * dW1
                self.b1 -= lr * db1
                self.W2 -= lr * dW2
                self.b2 -= lr * db2
                self.W3 -= lr * dW3
                self.b3 -= lr * db3

            z1 = self.W1.T @ X_te + self.b1
            a1 = np.maximum(0, z1)
            z2 = self.W2.T @ a1 + self.b2
            a2 = np.maximum(0, z2)
            z3 = self.W3.T @ a2 + self.b3
            pred = float(z3.flatten()[0]) * (self.y_max - self.y_min) + self.y_min
            if y_te[0][0] > 1e-8:
                mapes.append(abs(pred - y_raw[fold]) / y_raw[fold] * 100)
        return float(np.mean(mapes)) if mapes else np.inf

    def predict(self, serie, n_steps=3):
        if self.W1 is None:
            return np.full(n_steps, np.nan)
        s = serie.dropna().astype(float).values
        if len(s) < 2:
            return np.full(n_steps, np.nan)
        area_avg = float(np.mean(s))
        preds, history = [], list(s[-2:])
        for _ in range(n_steps):
            ano = 2019 + len(s)
            rend = history[-1] / area_avg if area_avg > 0 else 0.0
            feat = np.array([[ano, area_avg, rend, history[-1], history[-2]]])
            feat_norm = (feat - self.X_min) / (self.X_max - self.X_min + 1e-8)
            z1 = self.W1.T @ feat_norm.T + self.b1
            a1 = np.maximum(0, z1)
            z2 = self.W2.T @ a1 + self.b2
            a2 = np.maximum(0, z2)
            z3 = self.W3.T @ a2 + self.b3
            pred = float(z3.flatten()[0]) * (self.y_max - self.y_min) + self.y_min
            preds.append(pred)
            history.append(pred)
            s = np.append(s, pred)
        return np.array(preds)


def modelo_mlp(serie):
    mlp = MLPForecast(seed=42)
    mape = mlp.fit(serie, epochs=2000, lr=0.05)
    if mape == np.inf:
        return None
    s = serie.dropna().astype(float).values
    fitted = np.full_like(s, np.nan, dtype=float)
    for i in range(2, len(s)):
        sub = pd.Series(s[:i])
        mlp_t = MLPForecast(seed=42)
        mlp_t.fit(sub, epochs=1000, lr=0.05)
        pred = mlp_t.predict(sub, n_steps=1)
        if len(pred) > 0 and not np.isnan(pred[0]):
            fitted[i] = pred[0]
    return {"nombre": "MLP (5-8-4-1)", "mlp": mlp, "fitted": fitted,
            "mape_train": mape}


def proyectar_mlp(modelo, n_steps, serie_original):
    if "mlp" not in modelo:
        return np.full(n_steps, np.nan)
    return modelo["mlp"].predict(serie_original, n_steps)
'''

Path("core/analytics/mlp_forecast.py").write_text(mlp_code, encoding="utf-8")
print("[OK] core/analytics/mlp_forecast.py creado")

# ============================================================
# 2) Modificar core/analytics/forecast.py
# ============================================================
fp = Path("core/analytics/forecast.py")
c = fp.read_text(encoding="utf-8")

# 2.1 Import
if "from core.analytics.mlp_forecast" not in c:
    c = c.replace(
        "import numpy as np\nimport pandas as pd",
        "import numpy as np\nimport pandas as pd\nfrom core.analytics.mlp_forecast import modelo_mlp, proyectar_mlp"
    )
    print("[OK] import agregado")

# 2.2 Candidatos en backtest
old_cand = "        modelo_holt(t_train, s_train, 0.5, 0.2),\n    ]"
new_cand = "        modelo_holt(t_train, s_train, 0.5, 0.2),\n        modelo_mlp(pd.Series(s_train)),\n    ]"
if "modelo_mlp" not in c:
    c = c.replace(old_cand, new_cand)
    print("[OK] MLP agregado a candidatos")

# 2.3 Firma de _proyectar
old_sig = "def _proyectar(modelo: dict, n_steps: int) -> np.ndarray:"
new_sig = "def _proyectar(modelo: dict, n_steps: int, serie_original=None) -> np.ndarray:"
c = c.replace(old_sig, new_sig)
print("[OK] firma de _proyectar actualizada")

# 2.4 Caso MLP en _proyectar
old_cases = '    elif nombre.startswith("Promedio movil"):\n        return np.full(n_steps, modelo["last_mean"])\n    else:  # Holt'
new_cases = '    elif nombre.startswith("Promedio movil"):\n        return np.full(n_steps, modelo["last_mean"])\n    elif nombre == "MLP (5-8-4-1)":\n        return proyectar_mlp(modelo, n_steps, serie_original)\n    else:  # Holt'
if "MLP (5-8-4-1)" not in c:
    c = c.replace(old_cases, new_cases)
    print("[OK] caso MLP agregado a _proyectar")

# 2.5 Llamadas a _proyectar (comillas simples para evitar conflicto)
c = c.replace("pred = _proyectar(m, n_out)", "pred = _proyectar(m, n_out, serie)")
c = c.replace('pred = _proyectar(res["modelo"], n_steps)', 'pred = _proyectar(res["modelo"], n_steps, serie)')
print("[OK] llamadas a _proyectar actualizadas")

# 2.6 elegir_mejor: reentrenar MLP
old_elegir = '    elif nombre.startswith("Promedio movil"):\n        modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])\n    else:'
new_elegir = '    elif nombre.startswith("Promedio movil"):\n        modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])\n    elif nombre == "MLP (5-8-4-1)":\n        modelo_full = modelo_mlp(serie)\n    else:'
if "modelo_full = modelo_mlp" not in c:
    c = c.replace(old_elegir, new_elegir)
    print("[OK] elegir_mejor actualizado para MLP")

fp.write_text(c, encoding="utf-8")
print("[OK] forecast.py modificado")

print("\nVerifica: reinicia Streamlit -> Predictivo -> Alcala + Platano")
print("Debes ver MLP (5-8-4-1) en el ranking de modelos")