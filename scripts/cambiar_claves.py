"""Cambia contrasenas en config/users.json (solo desarrollo local; guarda hashes scrypt).

En Streamlit Cloud los usuarios van en Secrets: usa scripts/generar_hash.py.
"""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ui.services.auth import add_user, list_users  # noqa: E402

for usuario, rol in list_users().items():
    nueva = getpass.getpass(f"Nueva contrasena para '{usuario}' (Enter = dejar igual): ").strip()
    if nueva:
        add_user(usuario, nueva, role=rol)
        print(f"[OK] contrasena de '{usuario}' actualizada")

print("\nListo. Anota tus nuevas contrasenas en un lugar seguro.")
