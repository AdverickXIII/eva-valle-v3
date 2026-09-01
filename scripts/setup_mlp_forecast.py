"""Crea mlp_forecast.py y modifica forecast.py para integrar MLP."""
from pathlib import Path

# 1) Crear mlp_forecast.py
mlp_code = '''"""MLP para forecasting de series agricolas cortas.
Arquitectura: entrada (ano, area, rend, prod_t-1, prod_t-2) -> salida prod_t.
Entrenamiento leave-one-out sobre la serie historica."""
import numpy as np
import pandas as pd
from typing import Tuple, Optional


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


class MLPForecast:
    """MLP 5-8-4-1 con backprop desde cero, entrenado por serie."""

    def __init__(self, seed=42):
        self.seed = seed
        self.W1: Optional[np.ndarray] = None
        self.W2: Optional[np.ndarray] = None
        self.W3: Optional[np.ndarray] = None
        self.b1: Optional[np.ndarray] = None
        self.b2: Optional[np.ndarray] = None
        self.b3: Optional[np.ndarray] = None
        self.X_min: Optional[np.ndarray] = None
        self.X_max: Optional[np.ndarray] = None
        self.y_min: Optional[float] = None
        self.y_max: Optional[float] = None

    def _build_features(self, serie: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Construye features [ano, area, rend, prod_t-1, prod_t-2]."""
        # Asumimos area constante (promedio) y rendimiento = prod/area
        area_avg = np.mean(serie) if len(serie) > 0 else 1.0
        features = []
        targets = []
        for i in range(2, len(serie)):
            ano = 2019 + i
            area = area_avg
            rend = serie[i] / area if area > 0 else 0
            prod_t1 = serie[i - 1]
            prod_t2 = serie[i - 2]
            features.append([ano, area, rend, prod_t1, prod_t2])
            targets.append(serie[i])
        return np.array(features), np.array(targets)

    def fit(self, serie: pd.Series, epochs=2000, lr=0.05) -> float:
        """Entrena MLP con leave-one-out. Retorna MAPE promedio."""
        s = serie.dropna().astype(float).values
        if len(s) < 4:
            return np.inf

        X_raw, y_raw = self._build_features(s)
        if len(X_raw) < 2:
            return np.inf

        # Normalizacion min-max
        self.X_min = X_raw.min(axis=0)
        self.X_max = X_raw.max(axis=0)
        X_norm = (X_raw - self.X_min) / (self.X_max - self.X_min + 1e-8)
        self.y_min = y_raw.min()
        self.y_max = y_raw.max()
        y_norm = (y_raw - self.y_min) / (self.y_max - self.y_min + 1e-8)

        # Inicializacion Xavier
        rng = np.random.RandomState(self.seed)
        self.W1 = rng.randn(5, 8) * np.sqrt(2.0 / 13)
        self.W2 = rng.randn(8, 4) * np.sqrt(2.0 / 12)
        self.W3 = rng.randn(4, 1) * np.sqrt(2.0 / 5)
        self.b1 = np.zeros((8, 1))
        self.b2 = np.zeros((4, 1))
        self.b3 = np.zeros((1, 1))

        # Leave-one-out cross-validation
        mapes = []
        for fold in range(len(X_norm)):
            tr_idx = [i for i in range(len(X_norm)) if i != fold]
            te_idx = [fold]
            X_tr, y_tr = X_norm[tr_idx].T, y_norm[tr_idx].reshape(1, -1)
            X_te, y_te = X_norm[te_idx].T, y_norm[te_idx].reshape(1, -1)

            # Entrenamiento
            for ep in range(epochs):
                # Forward
                z1 = self.W1.T @ X_tr + self.b1
                a1 = np.maximum(0, z1)  # ReLU
                z2 = self.W2.T @ a1 + self.b2
                a2 = np.maximum(0, z2)  # ReLU
                z3 = self.W3.T @ a2 + self.b3
                y_pred = z3

                # Loss
                m = y_tr.shape[1]
                loss = np.mean((y_pred - y_tr) ** 2)

                # Backward
                dz3 = (2.0 / m) * (y_pred - y_tr)
                dW3 = a2 @ dz3.T
                db3 = np.sum(dz3, axis=1, keepdims=True)
                da2 = self.W3 @ dz3
                dz2 = da2 * (a2 > 0)
                dW2 = a1 @ dz2.T
                db2 = np.sum(dz2, axis=1, keepdims=True)
                da1 = self.W2 @ dz2
                dz1 = da1 * (a1 > 0)
                dW1 = X_tr @ dz1.T
                db1 = np.sum(dz1, axis=1, keepdims=True)

                # Update
                self.W1 -= lr * dW1
                self.b1 -= lr * db1
                self.W2 -= lr * dW2
                self.b2 -= lr * db2
                self.W3 -= lr * dW3
                self.b3 -= lr * db3

            # Evaluacion en fold
            z1 = self.W1.T @ X_te + self.b1
            a1 = np.maximum(0, z1)
            z2 = self.W2.T @ a1 + self.b2
            a2 = np.maximum(0, z2)
            z3 = self.W3.T @ a2 + self.b3
            pred_norm = z3.flatten()[0]
            pred_real = pred_norm * (self.y_max - self.y_min) + self.y_min
            real = y_raw[fold]
            if real > 1e-8:
                mapes.append(abs(pred_real - real) / real * 100)

        return float(np.mean(mapes)) if mapes else np.inf

    def predict(self, serie: pd.Series, n_steps: int = 3) -> np.ndarray:
        """Proyecta n_steps hacia adelante usando el MLP entrenado."""
        if self.W1 is None:
            return np.full(n_steps, np.nan)

        s = serie.dropna().astype(float).values
        if len(s) < 2:
            return np.full(n_steps, np.nan)

        area_avg = np.mean(s) if len(s) > 0 else 1.0
        predicciones = []
        history = list(s[-2:])  # ultimos 2 valores reales

        for _ in range(n_steps):
            ano = 2019 + len(s)
            area = area_avg
            rend = history[-1] / area if area > 0 else 0
            prod_t1 = history[-1]
            prod_t2 = history[-2]

            # Construir feature
            feat = np.array([[ano, area, rend, prod_t1, prod_t2]])
            feat_norm = (feat - self.X_min) / (self.X_max - self.X_min + 1e-8)

            # Forward
            z1 = self.W1.T @ feat_norm.T + self.b1
            a1 = np.maximum(0, z1)
            z2 = self.W2.T @ a1 + self.b2
            a2 = np.maximum(0, z2)
            z3 = self.W3.T @ a2 + self.b3
            pred_norm = z3.flatten()[0]
            pred_real = pred_norm * (self.y_max - self.y_min) + self.y_min

            predicciones.append(pred_real)
            history.append(pred_real)
            s = np.append(s, pred_real)

        return np.array(predicciones)


def modelo_mlp(serie: pd.Series) -> dict:
    """Wrapper compatible con la arquitectura de forecast.py."""
    mlp = MLPForecast(seed=42)
    mape = mlp.fit(serie, epochs=2000, lr=0.05)
    if mape == np.inf:
        return None
    # Ajuste in-sample (usar la serie completa para fitted)
    s = serie.dropna().astype(float).values
    fitted = np.full_like(s, np.nan, dtype=float)
    for i in range(2, len(s)):
        subserie = pd.Series(s[:i])
        mlp_temp = MLPForecast(seed=42)
        mlp_temp.fit(subserie, epochs=1000, lr=0.05)
        pred = mlp_temp.predict(subserie, n_steps=1)
        if len(pred) > 0 and not np.isnan(pred[0]):
            fitted[i] = pred[0]
    return {
        "nombre": "MLP (5-8-4-1)",
        "mlp": mlp,
        "fitted": fitted,
        "mape_train": mape,
    }


def proyectar_mlp(modelo: dict, n_steps: int, serie_original: pd.Series) -> np.ndarray:
    """Proyecta usando el MLP almacenado en el modelo."""
    if "mlp" not in modelo:
        return np.full(n_steps, np.nan)
    return modelo["mlp"].predict(serie_original, n_steps)
'''

Path("core/analytics/mlp_forecast.py").write_text(mlp_code, encoding="utf-8")
print("[OK] core/analytics/mlp_forecast.py creado")

# 2) Modificar forecast.py para incluir MLP
forecast_path = Path("core/analytics/forecast.py")
c = forecast_path.read_text(encoding="utf-8")

# Agregar import
if "from core.analytics.mlp_forecast" not in c:
    c = c.replace(
        "import numpy as np\nimport pandas as pd",
        "import numpy as np\nimport pandas as pd\nfrom core.analytics.mlp_forecast import modelo_mlp, proyectar_mlp"
    )
    print("[OK] import agregado a forecast.py")

# Agregar MLP a candidatos en backtest
if "modelo_mlp(serie)" not in c:
    old_candidatos = """    candidatos = [
        modelo_lineal(t_train, s_train),
        modelo_promedio(t_train, s_train, 2),
        modelo_promedio(t_train, s_train, 3),
        modelo_holt(t_train, s_train, 0.3, 0.1),
        modelo_holt(t_train, s_train, 0.5, 0.2),
    ]"""
    new_candidatos = """    serie_train = pd.Series(s_train, index=serie.index[:-n_out])
    candidatos = [
        modelo_lineal(t_train, s_train),
        modelo_promedio(t_train, s_train, 2),
        modelo_promedio(t_train, s_train, 3),
        modelo_holt(t_train, s_train, 0.3, 0.1),
        modelo_holt(t_train, s_train, 0.5, 0.2),
        modelo_mlp(serie_train),
    ]"""
    c = c.replace(old_candidatos, new_candidatos)
    print("[OK] MLP agregado a candidatos en backtest")

# Agregar MLP a la proyeccion
old_proyectar = """def _proyectar(modelo: dict, n_steps: int) -> np.ndarray:
    nombre = modelo["nombre"]
    if nombre == "Tendencia lineal":
        t_future = np.arange(len(modelo["fitted"]), len(modelo["fitted"]) + n_steps)
        return modelo["a"] + modelo["b"] * t_future
    elif nombre.startswith("Promedio movil"):
        return np.full(n_steps, modelo["last_mean"])
    else:  # Holt
        L, T = modelo["L"], modelo["T"]
        pred = np.empty(n_steps)
        for i in range(n_steps):
            L_new = L + T
            T_new = T
            pred[i] = L_new
            L, T = L_new, T_new
        return pred"""
    new_proyectar = """def _proyectar(modelo: dict, n_steps: int, serie_original: pd.Series = None) -> np.ndarray:
    nombre = modelo["nombre"]
    if nombre == "Tendencia lineal":
        t_future = np.arange(len(modelo["fitted"]), len(modelo["fitted"]) + n_steps)
        return modelo["a"] + modelo["b"] * t_future
    elif nombre.startswith("Promedio movil"):
        return np.full(n_steps, modelo["last_mean"])
    elif nombre == "MLP (5-8-4-1)":
        return proyectar_mlp(modelo, n_steps, serie_original)
    else:  # Holt
        L, T = modelo["L"], modelo["T"]
        pred = np.empty(n_steps)
        for i in range(n_steps):
            L_new = L + T
            T_new = T
            pred[i] = L_new
            L, T = L_new, T_new
        return pred"""
    c = c.replace(old_proyectar, new_proyectar)
    print("[OK] MLP agregado a _proyectar")

# Actualizar llamadas a _proyectar para pasar serie_original
c = c.replace(
    "pred = _proyectar(m, n_out)",
    "pred = _proyectar(m, n_out, serie)"
)
c = c.replace(
    "pred = _proyectar(res["modelo"], n_steps)",
    "pred = _proyectar(res["modelo"], n_steps, serie)"
)
print("[OK] llamadas a _proyectar actualizadas")

# Actualizar elegir_mejor para reentrenar MLP con serie completa
old_elegir = """    # Reentrenar con toda la serie
    if nombre == "Tendencia lineal":
        modelo_full = modelo_lineal(t_full, s_full)
    elif nombre.startswith("Promedio movil"):
        modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])
    else:
        modelo_full = modelo_holt(t_full, s_full,
                                  mejor["modelo"]["alpha"],
                                  mejor["modelo"]["beta"])"""
    new_elegir = """    # Reentrenar con toda la serie
    if nombre == "Tendencia lineal":
        modelo_full = modelo_lineal(t_full, s_full)
    elif nombre.startswith("Promedio movil"):
        modelo_full = modelo_promedio(t_full, s_full, mejor["modelo"]["ventana"])
    elif nombre == "MLP (5-8-4-1)":
        modelo_full = modelo_mlp(serie)
    else:
        modelo_full = modelo_holt(t_full, s_full,
                                  mejor["modelo"]["alpha"],
                                  mejor["modelo"]["beta"])"""
    c = c.replace(old_elegir, new_elegir)
    print("[OK] elegir_mejor actualizado para MLP")

forecast_path.write_text(c, encoding="utf-8")
print("[OK] forecast.py modificado")

# 3) Verificacion
import subprocess
r = subprocess.run(
    ["python", "-c",
     "import pandas as pd; import numpy as np; "
     "from core.analytics.forecast import elegir_mejor; "
     "serie = pd.Series([100, 120, 110, 130, 125, 140], index=range(2019, 2025)); "
     "res = elegir_mejor(serie); "
     "print('MODELOS:', [r['modelo']['nombre'] for r in res['ranking']]); "
     "print('GANADOR:', res['ganador'])"],
    capture_output=True, text=True, cwd=str(Path.cwd()))
print("\nVerificacion:")
print(r.stdout or r.stderr)