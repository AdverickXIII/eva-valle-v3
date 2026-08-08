"""Cambia las contrasenas de admin y usuario (guarda solo hashes)."""
import hashlib
import json
import secrets
from pathlib import Path

USERS = Path("config/users.json")

def _hash(pw: str, salt: str) -> str:
    return hashlib.sha256((salt + pw).encode("utf-8")).hexdigest()

users = json.loads(USERS.read_text(encoding="utf-8"))

for u in ("admin", "usuario"):
    if u in users:
        nueva = input(f"Nueva contrasena para '{u}' (Enter = dejar igual): ").strip()
        if nueva:
            salt = secrets.token_hex(8)
            users[u]["salt"] = salt
            users[u]["hash"] = _hash(nueva, salt)
            print(f"[OK] contrasena de '{u}' actualizada")

USERS.write_text(json.dumps(users, indent=2), encoding="utf-8")
print("\nListo. Anota tus nuevas contrasenas en un lugar seguro.")