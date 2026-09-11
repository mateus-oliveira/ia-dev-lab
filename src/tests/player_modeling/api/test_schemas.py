"""Testes unitários dos schemas Pydantic de autenticação."""

import pytest
from pydantic import ValidationError

from player_modeling.api.schemas import (
    LoginRequest,
    TokenPayload,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)


def test_user_register_request_valid() -> None:
    """Valida a criação bem-sucedida do schema de registro com username player_0000."""
    data = {"name": "Jogador Um", "username": "player_0000", "password": "supersecretpassword"}
    req = UserRegisterRequest(**data)
    assert req.name == "Jogador Um"
    assert req.username == "player_0000"
    assert req.password == "supersecretpassword"


def test_user_register_request_invalid_username_pattern() -> None:
    """Valida rejeição de username fora do padrão player_0000."""
    invalid_usernames = ["user123", "player_12", "player_abc", "admin", "PLAYER_0000"]
    for username in invalid_usernames:
        with pytest.raises(ValidationError):
            UserRegisterRequest(name="Nome", username=username, password="password123")


def test_user_register_request_short_password() -> None:
    """Valida rejeição de senha curta demais (< 6 caracteres)."""
    with pytest.raises(ValidationError):
        UserRegisterRequest(name="Nome", username="player_1234", password="123")


def test_user_response() -> None:
    """Valida a serialização dos dados públicos do usuário sem expor senha."""
    resp = UserResponse(id=1, name="Player 1", username="player_0001")
    assert resp.id == 1
    assert resp.name == "Player 1"
    assert resp.username == "player_0001"
    assert "password" not in resp.model_dump()


def test_login_request_valid() -> None:
    """Valida criação do schema de login."""
    login = LoginRequest(username="player_0000", password="secretpassword")
    assert login.username == "player_0000"
    assert login.password == "secretpassword"


def test_token_response_defaults() -> None:
    """Valida que o token_type padrão é 'bearer'."""
    token = TokenResponse(access_token="fake.jwt.token")
    assert token.access_token == "fake.jwt.token"
    assert token.token_type == "bearer"


def test_token_payload() -> None:
    """Valida schema do payload decodificado do JWT."""
    payload = TokenPayload(sub="player_0000", exp=1700000000)
    assert payload.sub == "player_0000"
    assert payload.exp == 1700000000
