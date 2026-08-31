"""
RNN y LSTM desde cero — EVA Valle v3.0 (Modulo 2)
Solo NumPy. BPTT completo + verificacion numerica + demo de vanishing gradient.
"""
import json
from pathlib import Path

import numpy as np

RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(parents=True, exist_ok=True)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


class RNN:
    """h_t = tanh(W_xh x_t + W_hh h_{t-1} + b_h);  y = W_y h_T + b_y."""

    def __init__(self, d, H, seed=42):
        self.d, self.H = d, H
        rng = np.random.RandomState(seed)
        s = 1.0 / np.sqrt(H)
        self.W_xh = rng.randn(H, d) * s
        self.W_hh = rng.randn(H, H) * s
        self.b_h = np.zeros((H, 1))
        self.W_y = rng.randn(1, H) * s
        self.b_y = np.zeros((1, 1))
        self.params = ["W_xh", "W_hh", "b_h", "W_y", "b_y"]

    def _set_flat(self, name, flat):
        setattr(self, name, flat.reshape(getattr(self, name).shape))

    def forward(self, X):
        T = X.shape[1]
        h = np.zeros((self.H, 1)); hs = [h]
        for t in range(T):
            h = np.tanh(self.W_xh @ X[:, [t]] + self.W_hh @ h + self.b_h)
            hs.append(h)
        self.X, self.hs = X, hs
        return self.W_y @ hs[-1] + self.b_y

    def backward(self, y_true):
        X, hs = self.X, self.hs
        T = X.shape[1]
        y_pred = self.W_y @ hs[-1] + self.b_y
        loss = float(np.mean((y_pred - y_true) ** 2))
        dy = 2.0 * (y_pred - y_true)
        G = {"W_y": dy @ hs[-1].T, "b_y": dy,
             "W_xh": np.zeros_like(self.W_xh), "W_hh": np.zeros_like(self.W_hh),
             "b_h": np.zeros_like(self.b_h)}
        dX = np.zeros_like(X)
        dh = self.W_y.T @ dy
        for t in reversed(range(T)):
            dz = dh * (1 - hs[t + 1] ** 2)
            G["W_xh"] += dz @ X[:, [t]].T
            G["W_hh"] += dz @ hs[t].T
            G["b_h"] += dz
            dX[:, [t]] = self.W_xh.T @ dz
            dh = self.W_hh.T @ dz
        return loss, G, dX

    def predict(self, X):
        return self.forward(X)

    def step(self, G, lr):
        for k in self.params:
            setattr(self, k, getattr(self, k) - lr * G[k])


class LSTM:
    """LSTM completo (Hochreiter & Schmidhuber 1997), BPTT exacto."""

    def __init__(self, d, H, seed=42):
        self.d, self.H = d, H
        rng = np.random.RandomState(seed)
        s = 1.0 / np.sqrt(H + d)
        for p in ["W_f", "W_i", "W_o", "W_g"]:
            setattr(self, p, rng.randn(H, H + d) * s)
            setattr(self, "b_" + p[-1], np.zeros((H, 1)))
        self.b_f[0, 0] = 1.0  # sesgo inicial de olvido (practica estandar)
        self.W_y = rng.randn(1, H) * s
        self.b_y = np.zeros((1, 1))
        self.params = ["W_f", "b_f", "W_i", "b_i", "W_o", "b_o",
                       "W_g", "b_g", "W_y", "b_y"]

    def _set_flat(self, name, flat):
        setattr(self, name, flat.reshape(getattr(self, name).shape))

    def forward(self, X):
        T = X.shape[1]; H = self.H
        h = np.zeros((H, 1)); c = np.zeros((H, 1))
        cache = []
        for t in range(T):
            z = np.vstack([h, X[:, [t]]])
            f = sigmoid(self.W_f @ z + self.b_f)
            i = sigmoid(self.W_i @ z + self.b_i)
            o = sigmoid(self.W_o @ z + self.b_o)
            g = np.tanh(self.W_g @ z + self.b_g)
            c = f * c + i * g
            h = o * np.tanh(c)
            cache.append((z, f, i, o, g, c, h))
        self.X, self.cache = X, cache
        return self.W_y @ h + self.b_y

    def backward(self, y_true):
        X, cache = self.X, self.cache
        T = X.shape[1]; H = self.H
        y_pred = self.W_y @ cache[-1][6] + self.b_y
        loss = float(np.mean((y_pred - y_true) ** 2))
        dy = 2.0 * (y_pred - y_true)
        G = {"W_y": dy @ cache[-1][6].T, "b_y": dy}
        for p in ["W_f", "W_i", "W_o", "W_g"]:
            G[p] = np.zeros_like(getattr(self, p))
            G["b_" + p[-1]] = np.zeros((H, 1))
        dX = np.zeros_like(X)
        dh = self.W_y.T @ dy
        dc_next = np.zeros((H, 1))
        for t in reversed(range(T)):
            z, f, i, o, g, c, h = cache[t]
            h_prev = cache[t - 1][6] if t > 0 else np.zeros((H, 1))
            c_prev = cache[t - 1][5] if t > 0 else np.zeros((H, 1))
            f_next = cache[t + 1][1] if t + 1 < T else np.zeros((H, 1))
            do = dh * np.tanh(c) * o * (1 - o)
            dc = dh * o * (1 - np.tanh(c) ** 2) + dc_next * f_next
            df = dc * c_prev * f * (1 - f)
            di = dc * g * i * (1 - i)
            dg = dc * i * (1 - g * g)
            G["W_f"] += df @ z.T; G["b_f"] += df
            G["W_i"] += di @ z.T; G["b_i"] += di
            G["W_o"] += do @ z.T; G["b_o"] += do
            G["W_g"] += dg @ z.T; G["b_g"] += dg
            dz = np.vstack([df, di, do, dg])
            W_all = np.vstack([self.W_f, self.W_i, self.W_o, self.W_g])
            dh = W_all[:, :H].T @ dz
            dX[:, [t]] = W_all[:, H:].T @ dz
            dc_next = dc
        return loss, G, dX

    def predict(self, X):
        return self.forward(X)

    def step(self, G, lr):
        for k in self.params:
            setattr(self, k, getattr(self, k) - lr * G[k])


def gradient_check(model, X, y, n_check=15, eps=1e-6):
    """Error relativo max entre gradiente analitico (BPTT) y numerico."""
    model.forward(X)
    _, G, _ = model.backward(y)
    worst = 0.0
    for name in model.params:
        flat = getattr(model, name).flatten()
        ga = G[name].flatten()
        for idx in range(min(n_check, flat.size)):
            old = flat[idx]
            flat[idx] = old + eps; model._set_flat(name, flat)
            lp = float(np.mean((model.forward(X) - y) ** 2))
            flat[idx] = old - eps; model._set_flat(name, flat)
            lm = float(np.mean((model.forward(X) - y) ** 2))
            flat[idx] = old; model._set_flat(name, flat)
            gn = (lp - lm) / (2 * eps)
            worst = max(worst, abs(gn - ga[idx]) / (abs(gn) + abs(ga[idx]) + 1e-8))
    return worst


if __name__ == "__main__":
    print("=" * 62)
    print("MODULO 2: Verificacion RNN y LSTM desde cero")
    print("=" * 62)

    rng = np.random.RandomState(0)
    X = rng.randn(2, 6); y = rng.randn(1, 1)

    print("\n--- Test 1: Gradient Check RNN ---")
    e_rnn = gradient_check(RNN(2, 4), X, y)
    print(f"Error relativo: {e_rnn:.2e}", "✅" if e_rnn < 1e-5 else "❌")

    print("\n--- Test 2: Gradient Check LSTM ---")
    e_lstm = gradient_check(LSTM(2, 4), X, y)
    print(f"Error relativo: {e_lstm:.2e}", "✅" if e_lstm < 1e-5 else "❌")

    print("\n--- Test 3: Vanishing gradient (T=20) ---")
    T = 20
    Xl = rng.randn(1, T)
    for nombre, modelo in [("RNN", RNN(1, 8)), ("LSTM", LSTM(1, 8))]:
        modelo.forward(Xl)
        _, _, dX = modelo.backward(np.zeros((1, 1)) + 1.0)
        ratio = float(np.abs(dX[:, 0]).mean() / (np.abs(dX[:, -1]).mean() + 1e-12))
        print(f"{nombre}: |dL/dx_1| / |dL/dx_T| = {ratio:.2e}"
              + ("  <- gradiente desaparece" if ratio < 1e-3 else "  <- gradiente fluye"))

    out = {"rnn_gc": e_rnn, "lstm_gc": e_lstm}
    (RESULTS / "m2_scratch_checks.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(f"\n[OK] guardado: {RESULTS / 'm2_scratch_checks.json'}")