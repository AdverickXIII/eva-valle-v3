"""
CNN desde cero — EVA Valle v3.0 (Modulo 4)
Conv2D (im2col), MaxPool2D, Dense, softmax-CE. BPTT verificado numericamente.
"""
import numpy as np


def im2col(X, kh, kw):
    C, H, W = X.shape
    Ho, Wo = H - kh + 1, W - kw + 1
    cols = np.empty((C * kh * kw, Ho * Wo))
    idx = 0
    for c in range(C):
        for i in range(kh):
            for j in range(kw):
                cols[idx] = X[c, i:i + Ho, j:j + Wo].reshape(-1)
                idx += 1
    return cols


def col2im_accum(dcols, dX, kh, kw):
    C, H, W = dX.shape
    Ho, Wo = H - kh + 1, W - kw + 1
    idx = 0
    for c in range(C):
        for i in range(kh):
            for j in range(kw):
                dX[c, i:i + Ho, j:j + Wo] += dcols[idx].reshape(Ho, Wo)
                idx += 1


class Conv2D:
    def __init__(self, C, F, kh=3, kw=3, seed=0):
        rng = np.random.RandomState(seed)
        self.kh, self.kw = kh, kw
        self.K = rng.randn(F, C, kh, kw) * np.sqrt(2.0 / (C * kh * kw))
        self.b = np.zeros(F)

    def forward(self, X):
        self.X = X
        F = self.K.shape[0]
        Ho = X.shape[1] - self.kh + 1
        Wo = X.shape[2] - self.kw + 1
        self.cols = im2col(X, self.kh, self.kw)
        Kf = self.K.reshape(F, -1)
        Z = (Kf @ self.cols).T.reshape(Ho, Wo, F).transpose(2, 0, 1) + self.b[:, None, None]
        return Z

    def backward(self, dZ):
        F = self.K.shape[0]
        Kf = self.K.reshape(F, -1)
        dZf = dZ.reshape(F, -1)
        self.dK = (dZf @ self.cols.T).reshape(self.K.shape)
        self.db = dZf.sum(1)
        dcols = Kf.T @ dZf
        dX = np.zeros_like(self.X)
        col2im_accum(dcols, dX, self.kh, self.kw)
        return dX


class MaxPool2D:
    def __init__(self, p=2):
        self.p = p

    def forward(self, Z):
        F, H, W = Z.shape
        self.input_shape = (F, H, W)  # ← GUARDAR shape original completo
        p = self.p
        Ho, Wo = H // p, W // p
        Zr = Z[:, :Ho * p, :Wo * p].reshape(F, Ho, p, Wo, p)
        Zr = Zr.transpose(0, 1, 3, 2, 4).reshape(F, Ho, Wo, p * p)
        self.arg = Zr.argmax(-1)
        self.out_shape = (F, Ho, Wo)
        return Zr.max(-1)

    def backward(self, dout):
        F, H, W = self.input_shape  # ← USAR shape original, no el truncado
        p = self.p
        Ho, Wo = H // p, W // p
        dZ = np.zeros((F, H, W))  # ← Reconstruir shape completo
        for f in range(F):
            for i in range(Ho):
                for j in range(Wo):
                    a = self.arg[f, i, j]
                    dZ[f, i * p + a // p, j * p + a % p] = dout[f, i, j]
        return dZ

class Dense:
    def __init__(self, n_in, n_out, seed=0):
        rng = np.random.RandomState(seed)
        self.W = rng.randn(n_out, n_in) * np.sqrt(2.0 / (n_in + n_out))
        self.b = np.zeros(n_out)

    def forward(self, v):
        self.v = v
        return self.W @ v + self.b

    def backward(self, dlogits):
        self.dW = np.outer(dlogits, self.v)
        self.db = dlogits
        return self.W.T @ dlogits

    def step(self, lr):
        self.W -= lr * self.dW
        self.b -= lr * self.db


def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


class CNN:
    """Conv3x3 -> ReLU -> MaxPool2 -> Dense -> softmax."""

    def __init__(self, C=1, F=4, n_classes=3, seed=0):
        self.conv = Conv2D(C, F, 3, 3, seed)
        self.pool = MaxPool2D(2)
        self.dense = None
        self.n_classes = n_classes

    def logits(self, x):
        self.Z = self.conv.forward(x)
        A = np.maximum(0, self.Z)
        P = self.pool.forward(A)
        v = P.reshape(-1)
        if self.dense is None:
            self.dense = Dense(v.size, self.n_classes, seed=1)
        return self.dense.forward(v), v

    def loss_grad(self, logits, y):
        p = softmax(logits)
        loss = -np.log(p[y] + 1e-12)
        d = p.copy()
        d[y] -= 1.0
        return loss, d

    def backward(self, dlogits):
        dv = self.dense.backward(dlogits)
        dP = dv.reshape(self.pool.out_shape)  # ← USAR out_shape
        dA = self.pool.backward(dP)
        dZ = dA * (self.Z > 0)
        return self.conv.backward(dZ)

    def step(self, lr):
        self.conv.K -= lr * self.conv.dK
        self.conv.b -= lr * self.conv.db
        self.dense.step(lr)

    def predict(self, x):
        lg, _ = self.logits(x)
        return int(np.argmax(lg))


def gradient_check_cnn(x, y, n_check=12, eps=1e-6):
    """Error relativo max entre BPTT y diferencias finitas (pesos conv y dense)."""
    net = CNN(1, 2, 3, seed=3)
    lg, _ = net.logits(x)
    loss, d = net.loss_grad(lg, y)
    net.backward(d)
    worst = 0.0
    for name, P, G in [("K", net.conv.K, net.conv.dK),
                       ("W", net.dense.W, net.dense.dW)]:
        flatG = G.flatten()
        # Usar .flat para modificar el array original in-place
        flatP = P.flat
        for i in range(min(n_check, flatG.size)):
            old = flatP[i]
            flatP[i] = old + eps
            lg, _ = net.logits(x)
            lp, _ = net.loss_grad(lg, y)
            flatP[i] = old - eps
            lg, _ = net.logits(x)
            lm, _ = net.loss_grad(lg, y)
            flatP[i] = old
            gn = (lp - lm) / (2 * eps)
            worst = max(worst, abs(gn - flatG[i]) / (abs(gn) + abs(flatG[i]) + 1e-8))
    return worst

if __name__ == "__main__":
    print("=" * 60)
    print("MODULO 4: Verificacion CNN desde cero")
    print("=" * 60)
    rng = np.random.RandomState(0)
    x = rng.randn(1, 8, 6)
    err = gradient_check_cnn(x, 1)
    print(f"\nGradient Check CNN: {err:.2e}", "✅" if err < 1e-5 else "❌")