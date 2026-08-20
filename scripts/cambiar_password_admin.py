"""Cambia la contrasena del administrador (admin)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ui.services.auth import add_user, load_users, list_users

USUARIO_ADMIN = "admin"


def es_segura(pw: str) -> tuple[bool, str]:
    if len(pw) < 8:
        return False, "debe tener minimo 8 caracteres"
    if not any(c.isupper() for c in pw):
        return False, "debe tener al menos una mayuscula"
    if not any(c.islower() for c in pw):
        return False, "debe tener al menos una minuscula"
    if not any(c.isdigit() for c in pw):
        return False, "debe tener al menos un numero"
    return True, "OK"


def main() -> int:
    print("=" * 60)
    print("CAMBIO DE CONTRASENA - ADMINISTRADOR EVA VALLE")
    print("=" * 60)

    users = load_users()
    if USUARIO_ADMIN not in users:
        print(f"[ERROR] El usuario '{USUARIO_ADMIN}' no existe.")
        return 1

    # Tomar password de argumento o pedir interactiva
    if len(sys.argv) >= 2:
        nueva = sys.argv[1]
        interactiva = False
    else:
        nueva = input("Nueva contrasena: ").strip()
        confirmar = input("Confirmar contrasena: ").strip()
        interactiva = True
        if nueva != confirmar:
            print("[ERROR] Las contrasenas no coinciden.")
            return 1

    ok, msg = es_segura(nueva)
    if not ok:
        print(f"[ERROR] Contrasena debil: {msg}.")
        return 1

    # add_user sobrescribe el registro con nuevo salt + hash
    add_user(USUARIO_ADMIN, nueva, role=users[USUARIO_ADMIN].get("role", "admin"))

    print()
    print(f"✅ Contrasena de '{USUARIO_ADMIN}' actualizada.")
    if not interactiva:
        print("   (Recuerda borrar el argumento del historial con: history -d N)")
    print()
    print("Siguiente inicio de sesion:")
    print(f"   Usuario: {USUARIO_ADMIN}")
    print(f"   Contrasena: {nueva}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())