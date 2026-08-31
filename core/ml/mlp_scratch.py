"""
MLP desde cero para EVA Valle v3.0
Curso de Deep Learning Aplicado — Modulo 1
Autor: Moises Zuñiga Grueso

Sin PyTorch, sin TensorFlow. Solo NumPy.
Cada linea tiene justificacion matematica.
"""
import numpy as np
from typing import List, Tuple, Callable

# ============================================================
# 1) FUNCIONES DE ACTIVACION Y SUS DERIVADAS
# ============================================================

def sigmoid(z: np.ndarray) -> np.ndarray:
    """σ(z) = 1/(1+e^{-z}). Rango: (0,1). Problema: vanishing gradient."""
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))

def sigmoid_prime(z: np.ndarray) -> np.ndarray:
    """σ'(z) = σ(z)(1 - σ(z)). Max en z=0: 0.25 → vanishing en capas profundas."""
    s = sigmoid(z)
    return s * (1.0 - s)

def tanh_act(z: np.ndarray) -> np.ndarray:
    """tanh(z). Rango: (-1,1). Centrada en 0 → mejor que sigmoid en capas ocultas."""
    return np.tanh(z)

def tanh_prime(z: np.ndarray) -> np.ndarray:
    """tanh'(z) = 1 - tanh²(z). Max en z=0: 1.0 → menos vanishing que sigmoid."""
    return 1.0 - np.tanh(z) ** 2

def relu(z: np.ndarray) -> np.ndarray:
    """ReLU(z) = max(0,z). No satura para z>0. Problema: dying ReLU si z<0 siempre."""
    return np.maximum(0, z)

def relu_prime(z: np.ndarray) -> np.ndarray:
    """ReLU'(z) = 1 si z>0, 0 si z≤0. Gradiente constante → no vanishing."""
    return (z > 0).astype(float)

def linear(z: np.ndarray) -> np.ndarray:
    """Identidad. Para capa de salida en regresion."""
    return z

def linear_prime(z: np.ndarray) -> np.ndarray:
    """Derivada de la identidad = 1."""
    return np.ones_like(z)

# Registro de activaciones
ACTIVATIONS = {
    "sigmoid": (sigmoid, sigmoid_prime),
    "tanh":    (tanh_act, tanh_prime),
    "relu":    (relu, relu_prime),
    "linear":  (linear, linear_prime),
}


# ============================================================
# 2) FUNCIONES DE PERDIDA
# ============================================================

def mse_loss(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    """L = (1/N) Σ (ŷ - y)². Diferenciable, convexa."""
    return float(np.mean((y_pred - y_true) ** 2))

def mse_grad(y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
    """∂L/∂ŷ = (2/N)(ŷ - y). Factor 2/N para escalar correctamente."""
    n = y_true.shape[0]
    return (2.0 / n) * (y_pred - y_true)

def mape(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    """MAPE = (100/N) Σ |ŷ-y|/|y|. Metrica de reporte, no de optimizacion."""
    mask = np.abs(y_true) > 1e-8
    return float(100 * np.mean(np.abs(y_pred[mask] - y_true[mask]) / np.abs(y_true[mask])))


# ============================================================
# 3) CLASE MLP — IMPLEMENTACION COMPLETA
# ============================================================

class MLP:
    """
    Perceptron Multicapa desde cero.
    
    Arquitectura: [n_input, h1, h2, ..., n_output]
    Activaciones: lista de strings, una por capa (excepto entrada)
    
    Inicializacion: Xavier/Glorot (varianza = 2/(fan_in + fan_out))
    Justificacion: mantiene la varianza de las activaciones constante
    entre capas, evitando explosion/vanishing de gradientes.
    
    Referencia: Glorot & Bengio (2010), "Understanding the difficulty
    of training deep feedforward neural networks", AISTATS.
    """
    
    def __init__(self, layer_dims: List[int], activations: List[str], seed: int = 42):
        """
        Args:
            layer_dims:   [input_dim, hidden1, hidden2, ..., output_dim]
            activations:  ["relu", "relu", ..., "linear"] (len = len(layer_dims)-1)
            seed:         semilla para reproducibilidad
        """
        assert len(activations) == len(layer_dims) - 1, \
            f"Necesitas {len(layer_dims)-1} activaciones, recibí {len(activations)}"
        
        np.random.seed(seed)
        self.L = len(layer_dims) - 1  # numero de capas (sin contar entrada)
        self.dims = layer_dims
        self.act_names = activations
        
        # Inicializacion Xavier/Glorot
        self.W: List[np.ndarray] = []
        self.b: List[np.ndarray] = []
        for l in range(self.L):
            fan_in, fan_out = layer_dims[l], layer_dims[l + 1]
            std = np.sqrt(2.0 / (fan_in + fan_out))  # Xavier
            self.W.append(np.random.randn(fan_out, fan_in) * std)
            self.b.append(np.zeros((fan_out, 1)))
        
        # Cache para backprop
        self._cache: List[Tuple[np.ndarray, np.ndarray]] = []
        self._input: np.ndarray = np.array([])
        
        # Historial de entrenamiento
        self.history = {"loss": [], "mape": [], "val_loss": [], "val_mape": []}
    
    def forward(self, X: np.ndarray) -> np.ndarray:
        """
        Paso forward completo.
        
        X: (n_features, n_samples) — cada columna es una muestra
        Returns: (n_output, n_samples)
        
        Guarda cache de (z_l, a_l) para cada capa → necesario para backprop.
        """
        self._cache = []
        self._input = X
        a = X
        for l in range(self.L):
            z = self.W[l] @ a + self.b[l]           # z_l = W_l · a_{l-1} + b_l
            act_fn, _ = ACTIVATIONS[self.act_names[l]]
            a = act_fn(z)                             # a_l = σ_l(z_l)
            self._cache.append((z, a))
        return a  # salida final
    
    def backward(self, y_true: np.ndarray, lr: float) -> float:
        """
        Backpropagation + actualizacion de pesos.
        
        Implementa exactamente las ecuaciones de la seccion 1.2:
        - δ_L = ∂L/∂z_L
        - δ_l = (W_{l+1}^T · δ_{l+1}) ⊙ σ'_l(z_l)
        - W_l ← W_l - η · δ_l · a_{l-1}^T
        - b_l ← b_l - η · mean(δ_l, axis=1)
        
        Returns: loss (MSE)
        """
        m = y_true.shape[1]  # numero de muestras
        y_pred = self._cache[-1][1]  # a_L (salida del forward)
        
        loss = mse_loss(y_pred.flatten(), y_true.flatten())
        
        # Gradiente de la perdida respecto a la salida
        dL_da = mse_grad(y_pred, y_true)  # (n_output, m)
        
        # Backprop capa por capa (desde L hasta 1)
        delta = dL_da
        for l in reversed(range(self.L)):
            z_l, a_l = self._cache[l]
            _, act_prime = ACTIVATIONS[self.act_names[l]]
            
            # δ_l = delta ⊙ σ'(z_l)
            delta = delta * act_prime(z_l)
            
            # a_{l-1}: activacion de la capa anterior (o input si l=0)
            a_prev = self._cache[l - 1][1] if l > 0 else self._input
            
            # Gradientes
            dW = (1.0 / m) * (delta @ a_prev.T)  # ∂L/∂W_l
            db = (1.0 / m) * np.sum(delta, axis=1, keepdims=True)  # ∂L/∂b_l
            
            # Propagar delta hacia atras ANTES de actualizar W
            delta = self.W[l].T @ delta  # δ_{l-1} = W_l^T · δ_l
            
            # Actualizacion SGD
            self.W[l] -= lr * dW
            self.b[l] -= lr * db
        
        return loss
    
    def fit(self, X_train: np.ndarray, y_train: np.ndarray,
            X_val: np.ndarray = None, y_val: np.ndarray = None,
            epochs: int = 1000, lr: float = 0.01,
            verbose: int = 100) -> dict:
        """
        Entrenamiento completo con historial.
        
        X_train: (n_features, n_samples)
        y_train: (n_output, n_samples)
        """
        for epoch in range(1, epochs + 1):
            # Forward + Backward
            y_pred = self.forward(X_train)
            loss = self.backward(y_train, lr)
            
            # Metricas de entrenamiento
            m = mape(y_pred.flatten(), y_train.flatten())
            self.history["loss"].append(loss)
            self.history["mape"].append(m)
            
            # Validacion
            if X_val is not None:
                y_val_pred = self.forward(X_val)
                val_loss = mse_loss(y_val_pred.flatten(), y_val.flatten())
                val_m = mape(y_val_pred.flatten(), y_val.flatten())
                self.history["val_loss"].append(val_loss)
                self.history["val_mape"].append(val_m)
                # Restaurar cache de entrenamiento
                self.forward(X_train)
            
            if verbose and epoch % verbose == 0:
                msg = f"Epoch {epoch:5d} | Loss: {loss:.6f} | MAPE: {m:.2f}%"
                if X_val is not None:
                    msg += f" | Val Loss: {val_loss:.6f} | Val MAPE: {val_m:.2f}%"
                print(msg)
        
        return self.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prediccion sin guardar cache."""
        a = X
        for l in range(self.L):
            z = self.W[l] @ a + self.b[l]
            act_fn, _ = ACTIVATIONS[self.act_names[l]]
            a = act_fn(z)
        return a
    
    def summary(self) -> str:
        """Resumen de la arquitectura."""
        lines = [f"MLP: {self.dims}", "=" * 50]
        total_params = 0
        for l in range(self.L):
            n_params = self.W[l].size + self.b[l].size
            total_params += n_params
            lines.append(
                f"Capa {l+1}: {self.dims[l]} -> {self.dims[l+1]} "
                f"| {self.act_names[l]:8s} | params: {n_params:,}"
            )
        lines.append("=" * 50)
        lines.append(f"Total parametros: {total_params:,}")
        return "\n".join(lines)


# ============================================================
# 4) VERIFICACION NUMERICA DEL GRADIENTE
# ============================================================

def gradient_check(model: MLP, X: np.ndarray, y: np.ndarray,
                   epsilon: float = 1e-7) -> float:
    """
    Verificacion numerica del gradiente (finite differences).
    
    Para cada parametro θ:
        grad_numerico = [L(θ+ε) - L(θ-ε)] / (2ε)
        grad_analitico = ∂L/∂θ (de backprop)
    
    Error relativo = ||grad_num - grad_anal|| / (||grad_num|| + ||grad_anal||)
    
    Si error < 1e-5: backprop correcto ✅
    Si error > 1e-3: hay un bug ❌
    
    Referencia: Karpathy, CS231n Stanford, "Gradient checking".
    """
    # Obtener gradientes analiticos via backprop
    model.forward(X)
    model.backward(y, lr=0.0)  # lr=0 para no actualizar pesos
    
    # Para simplificar, verificamos solo W[0]
    W_flat = model.W[0].flatten()
    grad_anal = np.zeros_like(W_flat)
    grad_num = np.zeros_like(W_flat)
    
    # Recalcular gradientes analiticos
    model.forward(X)
    y_pred = model._cache[-1][1]
    dL_da = mse_grad(y_pred, y)
    delta = dL_da
    for l in reversed(range(model.L)):
        z_l, a_l = model._cache[l]
        _, act_prime = ACTIVATIONS[model.act_names[l]]
        delta_l = delta * act_prime(z_l)
        if l == 0:
            a_prev = model._input
            m = y.shape[1]
            grad_anal = ((1.0 / m) * (delta_l @ a_prev.T)).flatten()
        delta = model.W[l].T @ delta_l if l > 0 else delta
    
    # Gradientes numericos (finite differences)
    for i in range(min(len(W_flat), 50)):  # solo primeros 50 para velocidad
        old_val = model.W[0].flat[i]
        
        model.W[0].flat[i] = old_val + epsilon
        y_plus = model.predict(X)
        loss_plus = mse_loss(y_plus.flatten(), y.flatten())
        
        model.W[0].flat[i] = old_val - epsilon
        y_minus = model.predict(X)
        loss_minus = mse_loss(y_minus.flatten(), y.flatten())
        
        grad_num[i] = (loss_plus - loss_minus) / (2 * epsilon)
        model.W[0].flat[i] = old_val
    
    # Error relativo
    diff = np.linalg.norm(grad_num[:50] - grad_anal[:50])
    norm_sum = np.linalg.norm(grad_num[:50]) + np.linalg.norm(grad_anal[:50])
    rel_error = diff / (norm_sum + 1e-8)
    
    print(f"Gradient Check — Error relativo: {rel_error:.2e}")
    if rel_error < 1e-5:
        print("✅ Backpropagation correcto")
    elif rel_error < 1e-3:
        print("⚠️ Posible error numerico (aceptable con float32)")
    else:
        print("❌ Bug en backpropagation")
    
    return rel_error


if __name__ == "__main__":
    print("=" * 60)
    print("MODULO 1: Verificacion del MLP desde cero")
    print("=" * 60)
    
    # Test basico: XOR (problema no-linealmente separable)
    print("\n--- Test 1: XOR ---")
    X_xor = np.array([[0, 0, 1, 1],
                       [0, 1, 0, 1]])  # (2, 4)
    y_xor = np.array([[0, 1, 1, 0]])   # (1, 4)
    
    net = MLP([2, 4, 1], ["tanh", "sigmoid"], seed=42)
    print(net.summary())
    net.fit(X_xor, y_xor, epochs=5000, lr=0.5, verbose=1000)
    
    pred = net.predict(X_xor)
    print(f"\nPredicciones XOR: {pred.round(3).flatten()}")
    print(f"Esperado:          [0, 1, 1, 0]")
    
    # Test 2: Gradient check
    print("\n--- Test 2: Gradient Check ---")
    net2 = MLP([3, 5, 2], ["relu", "linear"], seed=7)
    X_test = np.random.randn(3, 10)
    y_test = np.random.randn(2, 10)
    gradient_check(net2, X_test, y_test)