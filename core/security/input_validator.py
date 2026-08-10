"""Validacion y sanitizacion de inputs."""
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
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    
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
    return re.sub(r'[\x00-\x1F\x7F]', '', password)[:200]


def validate_email(email: str) -> bool:
    """Valida formato de email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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
