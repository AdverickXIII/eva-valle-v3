"""Agrega metodo predict a RNN y LSTM (alias de forward)."""
from pathlib import Path

p = Path("core/ml/rnn_scratch.py")
c = p.read_text(encoding="utf-8")
old = "    def step(self, G, lr):"
new = ("    def predict(self, X):\n"
       "        return self.forward(X)\n"
       "\n"
       "    def step(self, G, lr):")
if c.count(old) == 2:
    p.write_text(c.replace(old, new), encoding="utf-8")
    print("[OK] predict agregado a RNN y LSTM")
else:
    print(f"[AVISO] encontradas {c.count(old)} ocurrencias de 'def step'; revisar manual")