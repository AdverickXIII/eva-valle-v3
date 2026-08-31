"""
LSTM v2 — regularizacion completa (EVA Valle v3.0, Modulo 2 iteracion)
Dropout recurrente invertido + L2 + early stopping. BPTT exacto a traves del dropout.
"""
import numpy as np


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


class LSTMv2:
    def __init__(self, d, H, p_drop=0.2, l2=1e-4, seed=42):
        self.d, self.H, self.p, self.l2 = d, H, p_drop, l2
        rng = np.random.RandomState(seed)
        s = 1.0 / np.sqrt(H + d)
        for g in ["f", "i", "o", "g"]:
            setattr(self, f"W_{g}", rng.randn(H, H + d) * s)
            setattr(self, f"b_{g}", np.zeros((H, 1)))
        self.b_f += 1.0
        self.W_y = rng.randn(1, H) * s
        self.b_y = np.zeros((1, 1))
        self.params = ["W_f", "b_f", "W_i", "b_i", "W_o", "b_o",
                       "W_g", "b_g", "W_y", "b_y"]

    def snapshot(self):
        return {k: getattr(self, k).copy() for k in self.params}

    def restore(self, snap):
        for k, v in snap.items():
            setattr(self, k, v.copy())

    def forward(self, X, train=False):
        T = X.shape[1]; H = self.H
        h = np.zeros((H, 1)); c = np.zeros((H, 1)); hd = h
        cache = []
        for t in range(T):
            z = np.vstack([hd, X[:, [t]]])
            f = sigmoid(self.W_f @ z + self.b_f)
            i = sigmoid(self.W_i @ z + self.b_i)
            o = sigmoid(self.W_o @ z + self.b_o)
            gg = np.tanh(self.W_g @ z + self.b_g)
            c = f * c + i * gg
            h = o * np.tanh(c)
            m = ((np.random.rand(H, 1) > self.p) / (1 - self.p)) if train and self.p > 0 \
                else np.ones((H, 1))
            hd = h * m
            cache.append((z, f, i, o, gg, c, h, m, hd))
        self.X, self.cache = X, cache
        return self.W_y @ hd + self.b_y

    def backward(self, y_true):
        X, cache = self.X, self.cache
        T = X.shape[1]; H = self.H
        y_pred = self.W_y @ cache[-1][8] + self.b_y
        loss = float(np.mean((y_pred - y_true) ** 2))
        dy = 2.0 * (y_pred - y_true)
        G = {"W_y": dy @ cache[-1][8].T + self.l2 * self.W_y, "b_y": dy}
        for p in ["W_f", "W_i", "W_o", "W_g"]:
            G[p] = self.l2 * getattr(self, p)
            G["b_" + p[-1]] = np.zeros((H, 1))
        dh_d = self.W_y.T @ dy
        dc_next = np.zeros((H, 1))
        for t in reversed(range(T)):
            z, f, i, o, gg, c, h, m, hd = cache[t]
            h_prev_d = cache[t - 1][8] if t > 0 else np.zeros((H, 1))
            c_prev = cache[t - 1][5] if t > 0 else np.zeros((H, 1))
            f_next = cache[t + 1][1] if t + 1 < T else np.zeros((H, 1))
            dh = dh_d * m
            do = dh * np.tanh(c) * o * (1 - o)
            dc = dh * o * (1 - np.tanh(c) ** 2) + dc_next * f_next
            df = dc * c_prev * f * (1 - f)
            di = dc * gg * i * (1 - i)
            dg = dc * i * (1 - gg * gg)
            G["W_f"] += df @ z.T; G["b_f"] += df
            G["W_i"] += di @ z.T; G["b_i"] += di
            G["W_o"] += do @ z.T; G["b_o"] += do
            G["W_g"] += dg @ z.T; G["b_g"] += dg
            dz = np.vstack([df, di, do, dg])
            W_all = np.vstack([self.W_f, self.W_i, self.W_o, self.W_g])
            dh_d = W_all[:, :H].T @ dz
            dc_next = dc
        return loss, G

    def step(self, G, lr):
        for k in self.params:
            setattr(self, k, getattr(self, k) - lr * G[k])