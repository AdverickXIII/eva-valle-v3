"""MLP 5-8-4-1 desde cero para forecasting de series agricolas cortas.
Features: [ano, area, rendimiento, prod_t-1, prod_t-2] -> prod_t.
Entrenamiento leave-one-out; proyeccion recursiva multi-paso."""
import numpy as np
import pandas as pd


class MLPForecast:
    def __init__(self, seed=42):
        self.seed = seed
        self.W1 = self.W2 = self.W3 = None
        self.b1 = self.b2 = self.b3 = None
        self.X_min = self.X_max = None
        self.y_min = self.y_max = None

    def _build_features(self, s):
        area_avg = float(np.mean(s)) if len(s) > 0 else 1.0
        X, y = [], []
        for i in range(2, len(s)):
            rend = s[i] / area_avg if area_avg > 0 else 0.0
            X.append([2019 + i, area_avg, rend, s[i - 1], s[i - 2]])
            y.append(s[i])
        return np.array(X), np.array(y)

    def _forward(self, Xn):
        a1 = np.maximum(0, self.W1.T @ Xn + self.b1)
        a2 = np.maximum(0, self.W2.T @ a1 + self.b2)
        return self.W3.T @ a2 + self.b3

    def fit(self, serie, epochs=2000, lr=0.05):
        s = serie.dropna().astype(float).values
        if len(s) < 4:
            return np.inf
        X_raw, y_raw = self._build_features(s)
        if len(X_raw) < 2:
            return np.inf

        self.X_min, self.X_max = X_raw.min(0), X_raw.max(0)
        Xn = (X_raw - self.X_min) / (self.X_max - self.X_min + 1e-8)
        self.y_min, self.y_max = float(y_raw.min()), float(y_raw.max())
        yn = (y_raw - self.y_min) / (self.y_max - self.y_min + 1e-8)

        rng = np.random.RandomState(self.seed)
        self.W1 = rng.randn(5, 8) * np.sqrt(2.0 / 13)
        self.W2 = rng.randn(8, 4) * np.sqrt(2.0 / 12)
        self.W3 = rng.randn(4, 1) * np.sqrt(2.0 / 5)
        self.b1, self.b2, self.b3 = (np.zeros((8, 1)), np.zeros((4, 1)), np.zeros((1, 1)))

        mapes = []
        for fold in range(len(Xn)):
            tr = [i for i in range(len(Xn)) if i != fold]
            X_tr, y_tr = Xn[tr].T, yn[tr].reshape(1, -1)
            X_te = Xn[[fold]].T
            for _ in range(epochs):
                pred = self._forward(X_tr)
                m = y_tr.shape[1]
                dz3 = (2.0 / m) * (pred - y_tr)
                a1 = np.maximum(0, self.W1.T @ X_tr + self.b1)
                a2 = np.maximum(0, self.W2.T @ a1 + self.b2)
                dW3, db3 = a2 @ dz3.T, dz3.sum(1, keepdims=True)
                dz2 = (self.W3 @ dz3) * (a2 > 0)
                dW2, db2 = a1 @ dz2.T, dz2.sum(1, keepdims=True)
                dz1 = (self.W2 @ dz2) * (a1 > 0)
                dW1, db1 = X_tr @ dz1.T, dz1.sum(1, keepdims=True)
                self.W1 -= lr * dW1; self.b1 -= lr * db1
                self.W2 -= lr * dW2; self.b2 -= lr * db2
                self.W3 -= lr * dW3; self.b3 -= lr * db3
            p_norm = float(self._forward(X_te).flatten()[0])
            p_real = p_norm * (self.y_max - self.y_min) + self.y_min
            real = float(y_raw[fold])
            if real > 1e-8:
                mapes.append(abs(p_real - real) / real * 100)
        return float(np.mean(mapes)) if mapes else np.inf

    def predict(self, serie, n_steps=3):
        if self.W1 is None:
            return np.full(n_steps, np.nan)
        s = serie.dropna().astype(float).values
        if len(s) < 2:
            return np.full(n_steps, np.nan)
        area_avg = float(np.mean(s))
        preds, hist = [], list(s[-2:])
        n = len(s)
        for _ in range(n_steps):
            rend = hist[-1] / area_avg if area_avg > 0 else 0.0
            feat = np.array([[2019 + n, area_avg, rend, hist[-1], hist[-2]]])
            fn = (feat - self.X_min) / (self.X_max - self.X_min + 1e-8)
            p = float(self._forward(fn.T).flatten()[0])
            p = p * (self.y_max - self.y_min) + self.y_min
            preds.append(p)
            hist.append(p)
            n += 1
        return np.array(preds)


def modelo_mlp(serie):
    """Wrapper compatible con forecast.py. Devuelve dict de modelo o None."""
    mlp = MLPForecast(seed=42)
    mape = mlp.fit(serie, epochs=2000, lr=0.05)
    if not np.isfinite(mape):
        return None
    s = serie.dropna().astype(float).values
    fitted = np.full_like(s, np.nan, dtype=float)
    for i in range(2, len(s)):
        sub = pd.Series(s[:i])
        tmp = MLPForecast(seed=42)
        tmp.fit(sub, epochs=1000, lr=0.05)
        p = tmp.predict(sub, n_steps=1)
        if len(p) and not np.isnan(p[0]):
            fitted[i] = p[0]
    return {"nombre": "MLP (5-8-4-1)", "mlp": mlp, "fitted": fitted,
            "mape_train": mape, "serie_train": serie.copy()}


def proyectar_mlp(modelo, n_steps, serie_original):
    if "mlp" not in modelo:
        return np.full(n_steps, np.nan)
    return modelo["mlp"].predict(serie_original, n_steps)