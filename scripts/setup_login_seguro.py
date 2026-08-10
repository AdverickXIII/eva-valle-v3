"""Integra las 3 mejoras de seguridad en el sistema de login."""
from pathlib import Path

# Leer login.py actual
login_path = Path("ui/components/login.py")
if not login_path.exists():
    print(f"[ERROR] No encontrado: {login_path}")
    exit(1)

content = login_path.read_text(encoding="utf-8")

# 1. Agregar imports de seguridad
imports_security = '''
# Seguridad: rate limiting + session timeout + validacion
from core.security.integration import secure_login_attempt, on_login_success
from core.security.session_manager import check_session_timeout
'''

if "from core.security" not in content:
    # Insertar después de los imports existentes
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            # Encontrar el último import
            last_import = i
    lines.insert(last_import + 1, imports_security)
    content = "\n".join(lines)
    print("[OK] Imports de seguridad agregados")

# 2. Agregar check de session timeout al inicio de cada render
if "check_session_timeout()" not in content:
    # Buscar la función principal (probablemente render_login o similar)
    if "def render_login" in content:
        content = content.replace(
            "def render_login",
            "def render_login():\n    # Verificar timeout de sesion\n    if 'user' in st.session_state:\n        check_session_timeout()\n"
        )
        print("[OK] Session timeout integrado en render_login")

# 3. Modificar la lógica de login para usar secure_login_attempt
# Buscar el bloque donde se valida usuario/contraseña
if "secure_login_attempt" not in content:
    # Agregar validación antes del login real
    old_pattern = "if username and password:"
    new_pattern = '''    # Validacion de seguridad (rate limiting + sanitizacion)
    validation = secure_login_attempt(username, password)
    if not validation["success"]:
        st.error(validation["message"])
        return
    
    # Login original
    if username and password:'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("[OK] Rate limiting integrado en validacion")
    
    # Agregar on_login_success después de login exitoso
    old_success = 'st.session_state["user"] = username'
    new_success = '''st.session_state["user"] = username
        on_login_success(username)  # Limpiar rate limiter'''
    
    if old_success in content:
        content = content.replace(old_success, new_success)
        print("[OK] on_login_success integrado")

login_path.write_text(content, encoding="utf-8")
print(f"\n[OK] {login_path} actualizado con las 3 mejoras")
print("\nVerifica con: streamlit run app.py")