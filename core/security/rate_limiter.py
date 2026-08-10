"""Rate limiting para prevenir ataques de fuerza bruta."""
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
