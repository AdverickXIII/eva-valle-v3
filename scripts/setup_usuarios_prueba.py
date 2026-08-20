"""Crea 3 usuarios de prueba con los 3 roles: usuario/analista/admin."""
from pathlib import Path
import json

# Importar el módulo de usuarios
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from ui.services.auth import add_user, list_users, load_users, save_users

# Roles válidos del sistema
ROLES_VALIDOS = {
    "usuario": "Gremios, alcaldías, contratistas (8 pestañas)",
    "analista": "Técnicos de Secretaría/UPRA (14 pestañas)",
    "admin": "Administrador del sistema (todas las pestañas)"
}

print("=" * 70)
print("SISTEMA DE USUARIOS EVA VALLE v3.0")
print("=" * 70)
print()
print("Roles válidos:")
for rol, desc in ROLES_VALIDOS.items():
    print(f"  - {rol:10s} → {desc}")
print()

# Verificar usuarios existentes
users_existentes = list_users()
print(f"Usuarios existentes: {len(users_existentes)}")
for u, r in users_existentes.items():
    print(f"  - {u} ({r})")
print()

# Crear usuarios de prueba si no existen
usuarios_prueba = [
    ("admin", "admin123", "admin"),
    ("analista", "analista123", "analista"),
    ("usuario", "usuario123", "usuario"),
]

creados = []
for username, password, role in usuarios_prueba:
    if username not in users_existentes:
        add_user(username, password, role)
        creados.append((username, role))
        print(f"✅ Creado: {username} ({role})")
    else:
        print(f"ℹ️  Ya existe: {username} ({users_existentes[username]})")

print()
if creados:
    print(f"Se crearon {len(creados)} usuario(s) nuevo(s).")
    print()
    print("Credenciales de prueba:")
    print("-" * 70)
    for username, password, role in usuarios_prueba:
        print(f"  Usuario: {username:12s} | Contraseña: {password:12s} | Rol: {role}")
    print("-" * 70)
else:
    print("Todos los usuarios de prueba ya existían.")

print()
print("Usuarios finales:")
users_final = list_users()
for u, r in users_final.items():
    print(f"  - {u} ({r})")

print()
print("=" * 70)
print("Próximos pasos:")
print("1. Reinicia Streamlit: Ctrl+C → streamlit run app.py")
print("2. Inicia sesión con cada usuario para validar:")
print("   - admin/admin123 → ve 17 pestañas")
print("   - analista/analista123 → ve 14 pestañas")
print("   - usuario/usuario123 → ve 8 pestañas")
print("=" * 70)