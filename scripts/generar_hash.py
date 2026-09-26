"""Genera el bloque TOML de un usuario para pegar en los Secrets de Streamlit Cloud.

Uso:
    python scripts/generar_hash.py admin admin
    python scripts/generar_hash.py analista analista

Pide la contrasena de forma oculta (no queda en el historial de la terminal) y
muestra el bloque para: App -> Settings -> Secrets. Nada se guarda en disco.
"""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ui.services.auth import hash_password  # noqa: E402


def es_segura(pw: str) -> tuple[bool, str]:
    if len(pw) < 10:
        return False, "debe tener minimo 10 caracteres"
    if not (any(c.isupper() for c in pw) and any(c.islower() for c in pw) and any(c.isdigit() for c in pw)):
        return False, "debe mezclar mayusculas, minusculas y numeros"
    return True, "OK"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    usuario, rol = sys.argv[1], sys.argv[2]
    pw = getpass.getpass(f"Contrasena para '{usuario}': ")
    ok, msg = es_segura(pw)
    if not ok:
        print(f"[ERROR] La contrasena {msg}.")
        return 1
    if pw != getpass.getpass("Repite la contrasena: "):
        print("[ERROR] No coinciden.")
        return 1
    print("\nPega esto en Secrets (una seccion [users.<nombre>] por usuario):\n")
    print(f"[users.{usuario}]")
    print(f'hash = "{hash_password(pw)}"')
    print(f'role = "{rol}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
