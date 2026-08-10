"""Crea modulos de seguridad: rate limiting, session timeout, input validation."""
from pathlib import Path

# 1. Rate Limiting
RATE_LIMITER = '''"""Rate limiting para prevenir ataques de fuerza bruta."""
from collections import defaultdict
from datetime import datetime, timedelta


class RateLimiter:
    """Limita intentos de login por usuario/IP."""
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window = timedelta(minutes=window_minutes)
        self.attempts = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        """Retorna True si el intento es permitido."""
        now = datetime.now()
        cutoff = now - self.window
        
        # Limpiar intentos antiguos
        self.attempts[key] = [t for t in self.attempts[key] if t > cutoff]
        
        if len(self.attempts[key]) >= self.max_attempts:
            return False
        
        self.attempts[key].append(now)
        return True
    
    def get_remaining_attempts(self, key: str) -> int:
        """Retorna intentos restantes."""
        now = datetime.now()
        cutoff = now - self.window
        recent = [t for t in self.attempts[key] if t > cutoff]
        return max(0, self.max_attempts - len(recent))
    
    def reset(self, key: str) -> None:
        """Reinicia contador (ej: después de login exitoso)."""
        self.attempts[key] = []


# Instancia global
login_limiter = RateLimiter(max_attempts=5, window_minutes=15)
'''

# 2. Session Timeout
SESSION_MANAGER = '''"""Manejo de timeout de sesion por inactividad."""
from datetime import datetime, timedelta
import streamlit as st


SESSION_TIMEOUT_MINUTES = 30


def check_session_timeout() -> bool:
    """Verifica si la sesion ha expirado. Retorna True si esta activa."""
    if "user" not in st.session_state:
        return False
    
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = datetime.now()
        return True
    
    elapsed = datetime.now() - st.session_state.last_activity
    if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        # Sesión expirada
        user = st.session_state.get("user", "unknown")
        st.session_state.clear()
        st.warning("⚠️ Sesión expirada por inactividad. Por favor inicia sesión nuevamente.")
        st.rerun()
        return False
    
    # Actualizar timestamp
    st.session_state.last_activity = datetime.now()
    return True


def get_session_remaining_minutes() -> int:
    """Retorna minutos restantes de sesion."""
    if "last_activity" not in st.session_state:
        return SESSION_TIMEOUT_MINUTES
    
    elapsed = datetime.now() - st.session_state.last_activity
    remaining = timedelta(minutes=SESSION_TIMEOUT_MINUTES) - elapsed
    return max(0, int(remaining.total_seconds() / 60))
'''

# 3. Input Validation
INPUT_VALIDATOR = '''"""Validacion y sanitizacion de inputs."""
import re
from typing import Any


def sanitize_string(text: str, max_length: int = 500) -> str:
    """Sanitiza strings para prevenir inyecciones."""
    if not isinstance(text, str):
        return ""
    
    # Eliminar tags HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Eliminar javascript: y otros protocolos peligrosos
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'data:', '', text, flags=re.IGNORECASE)
    
    # Eliminar caracteres de control
    text = re.sub(r'[\\x00-\\x1F\\x7F]', '', text)
    
    # Limitar longitud
    return text[:max_length].strip()


def sanitize_username(username: str) -> str:
    """Sanitiza nombres de usuario (solo alfanumerico + guion bajo)."""
    username = sanitize_string(username, max_length=50)
    return re.sub(r'[^a-zA-Z0-9_]', '', username)


def sanitize_password(password: str) -> str:
    """Sanitiza contrasenas (permite mas caracteres pero elimina peligrosos)."""
    if not isinstance(password, str):
        return ""
    # Eliminar caracteres de control pero permitir símbolos
    return re.sub(r'[\\x00-\\x1F\\x7F]', '', password)[:200]


def validate_email(email: str) -> bool:
    """Valida formato de email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_numeric(value: Any, min_val: float = None, max_val: float = None) -> float | None:
    """Valida y convierte valores numericos."""
    try:
        num = float(value)
        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None
        return num
    except (ValueError, TypeError):
        return None
'''

# 4. Integration helper
INTEGRATION = '''"""Funciones de integracion para aplicar seguridad en login."""
from core.security.rate_limiter import login_limiter
from core.security.session_manager import check_session_timeout
from core.security.input_validator import sanitize_username, sanitize_password


def secure_login_attempt(username: str, password: str, ip: str = "unknown") -> dict:
    """
    Intento de login seguro con rate limiting y validacion.
    Retorna dict con success, message, remaining_attempts.
    """
    # Sanitizar inputs
    username = sanitize_username(username)
    password = sanitize_password(password)
    
    if not username or not password:
        return {
            "success": False,
            "message": "Usuario y contraseña requeridos",
            "remaining_attempts": None
        }
    
    # Rate limiting
    key = f"{username}_{ip}"
    if not login_limiter.is_allowed(key):
        remaining = login_limiter.get_remaining_attempts(key)
        return {
            "success": False,
            "message": f"Demasiados intentos. Espera 15 minutos. Intentos restantes: {remaining}",
            "remaining_attempts": remaining
        }
    
    return {
        "success": True,
        "message": "Validacion pasada",
        "remaining_attempts": login_limiter.get_remaining_attempts(key)
    }


def on_login_success(username: str, ip: str = "unknown") -> None:
    """Limpiar rate limiter después de login exitoso."""
    key = f"{username}_{ip}"
    login_limiter.reset(key)
'''

# Crear estructura
security_dir = Path("core/security")
security_dir.mkdir(parents=True, exist_ok=True)

(security_dir / "__init__.py").write_text(
    '"""Modulos de seguridad: rate limiting, session, validation."""\n',
    encoding="utf-8"
)
(security_dir / "rate_limiter.py").write_text(RATE_LIMITER, encoding="utf-8")
(security_dir / "session_manager.py").write_text(SESSION_MANAGER, encoding="utf-8")
(security_dir / "input_validator.py").write_text(INPUT_VALIDATOR, encoding="utf-8")
(security_dir / "integration.py").write_text(INTEGRATION, encoding="utf-8")

print("[OK] core/security/ creado con 4 modulos:")
print("     - rate_limiter.py")
print("     - session_manager.py")
print("     - input_validator.py")
print("     - integration.py")
print("\nSigue: python scripts\\setup_login_seguro.py")