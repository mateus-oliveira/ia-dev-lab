"""Testes unitários dos utilitários de segurança, hashing e JWT."""

from datetime import timedelta

import jwt
import pytest

from player_modeling.api.security import (
    create_access_token,
    decode_access_token,
    get_access_token_expire_minutes,
    get_algorithm,
    get_secret_key,
    hash_password,
    verify_password,
)


def test_hash_password_and_verify() -> None:
    """Valida o hashing com bcrypt e verificação positiva e negativa."""
    plain = "minhasenhasecreta123"
    hashed = hash_password(plain)

    assert hashed != plain
    assert hashed.startswith("$2")
    assert verify_password(plain, hashed) is True
    assert verify_password("outrasenhaerrada", hashed) is False
    assert verify_password(plain, "hash_invalido") is False


def test_create_and_decode_access_token() -> None:
    """Valida a emissão e decodificação correta de um token JWT."""
    data = {"sub": "player_0000", "role": "player"}
    token = create_access_token(data)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == "player_0000"
    assert payload["role"] == "player"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_expired_token() -> None:
    """Valida que tokens expirados disparam jwt.ExpiredSignatureError."""
    data = {"sub": "player_0000"}
    expired_token = create_access_token(data, expires_delta=timedelta(seconds=-10))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_decode_tampered_token() -> None:
    """Valida que tokens adulterados disparam jwt.PyJWTError."""
    data = {"sub": "player_0000"}
    token = create_access_token(data)
    tampered_token = token[:-5] + "XXXXX"

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered_token)


def test_environment_variable_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida leitura e fallback de variáveis de ambiente para segurança."""
    monkeypatch.setenv("JWT_SECRET_KEY", "custom-secret-for-test-override-12345")
    monkeypatch.setenv("JWT_ALGORITHM", "HS384")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "45")

    assert get_secret_key() == "custom-secret-for-test-override-12345"
    assert get_algorithm() == "HS384"
    assert get_access_token_expire_minutes() == 45

    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "invalid_number")
    assert get_access_token_expire_minutes() == 30
