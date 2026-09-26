"""Servicio de autenticacion con roles (admin / analista / usuario).

Almacenamiento de usuarios (en este orden de prioridad):

1. ``st.secrets["users"]`` -- RECOMENDADO en produccion (Streamlit Cloud).
   Los hashes viven en los secretos de la app, nunca en el repositorio.
2. ``config/users.json`` -- solo para desarrollo local. Esta en .gitignore.

Hash de contrasenas: scrypt (memoria-dura) con sal aleatoria por usuario.
Formato almacenado: ``scrypt$<N>$<r>$<p>$<sal_hex>$<hash_hex>``.

Compatibilidad: los registros antiguos (sha256 + sal, campos ``salt``/``hash``)
se siguen aceptando y se migran a scrypt automaticamente en el primer login
correcto cuando el usuario vive en ``config/users.json``.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime
from pathlib import Path

import streamlit as st

from core.security.input_validator import sanitize_password, sanitize_username

USERS_PATH = Path(__file__).parent.parent.parent / "config" / "users.json"

# Parametros scrypt (recomendacion OWASP: N=2**17 es lo ideal; 2**15 mantiene
# ~100 ms y ~32 MB por verificacion, razonable para el plan gratuito de Cloud).
_N, _R, _P = 2**15, 8, 1
_MAXMEM = 128 * 1024 * 1024
_PREFIX = "scrypt"


# --- Hash de contrasenas ----------------------------------------------
def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=n, r=r, p=p, maxmem=_MAXMEM, dklen=32
    )


def hash_password(password: str) -> str:
    """Devuelve el hash scrypt autocontenido de ``password``."""
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, _N, _R, _P)
    return f"{_PREFIX}${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def _check_scrypt(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt_hex, hash_hex = stored.split("$")
        expected = bytes.fromhex(hash_hex)
        got = _scrypt(password, bytes.fromhex(salt_hex), int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(got, expected)


def _check_legacy_sha256(password: str, salt: str, stored: str) -> bool:
    got = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hmac.compare_digest(got, stored)


def _is_legacy(rec: dict) -> bool:
    return not str(rec.get("hash", "")).startswith(f"{_PREFIX}$")


def _check_record(password: str, rec: dict) -> bool:
    stored = str(rec.get("hash", ""))
    if not _is_legacy(rec):
        return _check_scrypt(password, stored)
    return _check_legacy_sha256(password, str(rec.get("salt", "")), stored)


# Hash de relleno para que verificar un usuario inexistente tarde lo mismo que
# uno existente (evita enumerar usuarios midiendo tiempos de respuesta).
_DUMMY_HASH = hash_password(secrets.token_hex(16))


# --- Almacen de usuarios ----------------------------------------------
def _secret_users() -> dict:
    """Usuarios definidos en st.secrets['users'] (solo lectura)."""
    try:
        raw = st.secrets.get("users")
        return {str(u): dict(rec) for u, rec in raw.items()} if raw else {}
    except Exception:  # sin secrets.toml, o secreto mal formado
        return {}


def _file_users() -> dict:
    if not USERS_PATH.exists():
        return {}
    try:
        return json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def has_secret_users() -> bool:
    """True si hay usuarios en st.secrets (en Cloud, editar el panel no es permanente)."""
    return bool(_secret_users())


def load_users() -> dict:
    """Une ambas fuentes; los secretos tienen prioridad sobre el archivo local."""
    return {**_file_users(), **_secret_users()}


def save_users(users: dict) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


# --- Operaciones ------------------------------------------------------
def verify(username: str, password: str) -> bool:
    """Verifica credenciales con inputs sanitizados y comparacion en tiempo constante."""
    username = sanitize_username(username)
    password = sanitize_password(password)
    rec = load_users().get(username)
    if not rec:
        _check_scrypt(password, _DUMMY_HASH)  # igualar tiempos
        return False
    ok = _check_record(password, rec)
    if ok and _is_legacy(rec):
        _migrate_to_scrypt(username, password)
    return ok


def _migrate_to_scrypt(username: str, password: str) -> None:
    """Sube un hash sha256 antiguo a scrypt (solo si vive en el archivo local)."""
    if username in _secret_users():
        return  # los secretos son solo lectura; se regeneran con scripts/generar_hash.py
    users = _file_users()
    if username in users:
        users[username] = {"hash": hash_password(password), "role": users[username].get("role", "usuario")}
        try:
            save_users(users)
        except OSError:
            pass  # sistema de archivos de solo lectura: se migrara en otro login


def get_role(username: str) -> str:
    return load_users().get(username, {}).get("role", "usuario")


def add_user(username: str, password: str, role: str = "usuario") -> None:
    """Crea/actualiza un usuario en config/users.json (almacen local)."""
    username = sanitize_username(username)
    password = sanitize_password(password)
    if not username or not password:
        raise ValueError("Usuario y contrasena no pueden quedar vacios tras sanitizar.")
    users = _file_users()
    users[username] = {"hash": hash_password(password), "role": role}
    save_users(users)


def remove_user(username: str) -> None:
    users = _file_users()
    users.pop(username, None)
    save_users(users)


def list_users() -> dict:
    return {u: rec.get("role", "usuario") for u, rec in load_users().items()}


# --- Sesion -----------------------------------------------------------
def login(username: str) -> None:
    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = get_role(username)
    st.session_state["last_activity"] = datetime.now()


def logout() -> None:
    for k in ("authenticated", "username", "role", "last_activity"):
        st.session_state.pop(k, None)


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def current_role() -> str:
    return st.session_state.get("role", "usuario")
