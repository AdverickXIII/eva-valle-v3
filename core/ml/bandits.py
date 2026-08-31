"""
Multi-Armed Bandits para seleccion de modelos — EVA Valle v3.0 (Modulo 3)
Implementaciones desde cero: epsilon-greedy, UCB1, Thompson Gaussiano.
Mas test de Diebold-Mariano para comparacion rigurosa de pronosticos.
"""
import numpy as np
from scipy.stats import norm


class EpsilonGreedy:
    def __init__(self, n_arms, eps=0.1, seed=0):
        self.n, self.eps = n_arms, eps
        self.rng = np.random.RandomState(seed)
        self.counts = np.zeros(n_arms)
        self.means = np.zeros(n_arms)

    def select(self, t):
        if self.counts.sum() == 0 or self.rng.rand() < self.eps:
            return int(self.rng.randint(self.n))
        return int(np.argmax(self.means))

    def update(self, a, r):
        self.counts[a] += 1
        self.means[a] += (r - self.means[a]) / self.counts[a]


class UCB1:
    """Auer, Cesa-Bianchi & Fischer (2002). Regret O(sqrt(T log T))."""

    def __init__(self, n_arms, c=np.sqrt(2), seed=0):
        self.n, self.c = n_arms, c
        self.counts = np.zeros(n_arms)
        self.means = np.zeros(n_arms)

    def select(self, t):
        if self.counts.sum() < self.n:          # ronda de inicializacion
            return int(self.counts.sum())
        bonus = self.c * np.sqrt(np.log(t + 1) / self.counts)
        return int(np.argmax(self.means + bonus))

    def update(self, a, r):
        self.counts[a] += 1
        self.means[a] += (r - self.means[a]) / self.counts[a]


class ThompsonGaussian:
    """Thompson con posterior normal-normal (varianza conocida sigma)."""

    def __init__(self, n_arms, sigma=10.0, seed=0):
        self.n, self.sigma = n_arms, sigma
        self.rng = np.random.RandomState(seed)
        self.counts = np.zeros(n_arms)
        self.sumr = np.zeros(n_arms)

    def select(self, t):
        draws = []
        for a in range(self.n):
            n = self.counts[a]
            if n == 0:
                draws.append(self.rng.normal(0, 3))     # prior difusa
            else:
                mu = self.sumr[a] / n
                draws.append(self.rng.normal(mu, self.sigma / np.sqrt(n)))
        return int(np.argmax(draws))

    def update(self, a, r):
        self.counts[a] += 1
        self.sumr[a] += r


def simulate(policy, losses, order):
    """
    losses: (T, n_arms) matriz de perdidas por ronda.
    order:  permutacion de rondas (semilla externa).
    Devuelve (regret_acumulado, elecciones).
    """
    best = losses.min(axis=1)
    reg, picks = [], []
    cum = 0.0
    for t, k in enumerate(order):
        a = policy.select(t)
        cum += losses[k, a] - best[k]
        policy.update(a, -losses[k, a])     # recompensa = -perdida
        reg.append(cum)
        picks.append(a)
    return np.array(reg), np.array(picks)


def diebold_mariano(e1, e2):
    """
    Test DM (1995) con perdida cuadratica.
    H0: E[d_t] = 0, d_t = e1_t^2 - e2_t^2.
    DM < 0 y p pequeno => el modelo 2 es significativamente mejor.
    """
    d = np.asarray(e1) ** 2 - np.asarray(e2) ** 2
    n = len(d)
    gamma0 = d.var(ddof=1)
    dm = d.mean() / np.sqrt(gamma0 / n + 1e-12)
    p = 2 * (1 - norm.cdf(abs(dm)))
    return float(dm), float(p)