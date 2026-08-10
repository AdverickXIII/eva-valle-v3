"""Funciones de integracion para aplicar seguridad en login."""
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
