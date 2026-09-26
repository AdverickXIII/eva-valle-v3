"""Tests del servicio de autenticacion (hash scrypt, migracion, secretos)."""
import hashlib
import json

import pytest

from ui.services import auth


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Aisla config/users.json en un directorio temporal y sin secretos."""
    path = tmp_path / "users.json"
    monkeypatch.setattr(auth, "USERS_PATH", path)
    monkeypatch.setattr(auth, "_secret_users", lambda: {})
    return path


def _legacy_record(password: str, role: str = "usuario") -> dict:
    salt = "abcd1234abcd1234"
    return {"salt": salt, "hash": hashlib.sha256((salt + password).encode()).hexdigest(), "role": role}


def test_hash_roundtrip_y_sal_unica():
    h1, h2 = auth.hash_password("Clave-Segura-1"), auth.hash_password("Clave-Segura-1")
    assert h1 != h2  # sal aleatoria distinta
    assert h1.startswith("scrypt$")
    assert auth._check_scrypt("Clave-Segura-1", h1)
    assert not auth._check_scrypt("otra", h1)


@pytest.mark.parametrize("basura", ["", "scrypt$", "scrypt$1$2$3$zz$zz", "no-es-un-hash"])
def test_hash_malformado_no_lanza_y_rechaza(basura):
    assert auth._check_scrypt("x", basura) is False


def test_add_user_y_verify(store):
    auth.add_user("maria", "Clave-Segura-1", role="analista")
    assert auth.verify("maria", "Clave-Segura-1")
    assert not auth.verify("maria", "incorrecta")
    assert auth.get_role("maria") == "analista"
    assert "salt" not in json.loads(store.read_text())["maria"]  # ya no se guarda sal aparte


def test_usuario_inexistente_devuelve_false(store):
    assert auth.verify("fantasma", "lo-que-sea") is False


def test_add_user_rechaza_vacios(store):
    with pytest.raises(ValueError):
        auth.add_user("!!!", "Clave-Segura-1")  # el usuario queda vacio tras sanitizar


def test_registro_legacy_sha256_se_acepta_y_migra_a_scrypt(store):
    store.write_text(json.dumps({"ana": _legacy_record("Vieja-Clave-1", "admin")}))
    assert not auth.verify("ana", "incorrecta")
    assert json.loads(store.read_text())["ana"].get("salt")  # sin login correcto no cambia nada
    assert auth.verify("ana", "Vieja-Clave-1")
    rec = json.loads(store.read_text())["ana"]
    assert rec["hash"].startswith("scrypt$") and "salt" not in rec and rec["role"] == "admin"
    assert auth.verify("ana", "Vieja-Clave-1")  # sigue funcionando ya migrado


def test_secretos_tienen_prioridad_y_no_se_migran(store, monkeypatch):
    store.write_text(json.dumps({"ana": _legacy_record("Archivo-1")}))
    monkeypatch.setattr(auth, "_secret_users", lambda: {"ana": {"hash": auth.hash_password("Secreto-1"), "role": "admin"}})
    assert auth.verify("ana", "Secreto-1")
    assert not auth.verify("ana", "Archivo-1")
    assert auth.get_role("ana") == "admin"
    assert auth.has_secret_users()
