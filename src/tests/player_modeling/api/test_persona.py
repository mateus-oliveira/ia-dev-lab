"""Testes de integração para o endpoint GET /players/{player_id}/persona (User Stories 1 e 2)."""

import sqlite3
from collections.abc import Callable, Generator
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from player_modeling.api.app import app
from player_modeling.api.database import get_connection, get_db
from player_modeling.api.routes.players import resolve_mock_persona
from player_modeling.api.schemas import BartlePersona
from player_modeling.api.security import create_access_token, hash_password


@pytest.fixture
def client(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> Generator[TestClient, None, None]:
    """Fixture com cliente HTTP e banco SQLite isolado contendo usuário de teste."""
    db_file = str(tmp_path / "test_persona.sqlite3")
    apply_migrations(db_file)

    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, username, password) VALUES (?, ?, ?);",
        ("Jogador Teste", "player_0000", hash_password("pass123")),
    )
    conn.commit()
    conn.close()

    def override_get_db() -> Generator[sqlite3.Connection, None, None]:
        test_conn = get_connection(db_file)
        try:
            yield test_conn
        finally:
            test_conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_get_persona_success(client: TestClient) -> None:
    """Valida consulta de persona com token válido e resposta no formato PersonaResponse."""
    token = create_access_token({"sub": "player_0000"})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/players/player_0000/persona", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["player_id"] == "player_0000"
    assert data["persona"] in [p.value for p in BartlePersona]


def test_get_persona_without_token(client: TestClient) -> None:
    """Valida rejeição imediata com 401 para requisição sem autenticação."""
    response = client.get("/players/player_0000/persona")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_persona_expired_token(client: TestClient) -> None:
    """Valida rejeição com 401 para token JWT expirado."""
    token = create_access_token({"sub": "player_0000"}, expires_delta=timedelta(seconds=-30))
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/players/player_0000/persona", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expirado" in response.json()["detail"]


def test_get_persona_invalid_token(client: TestClient) -> None:
    """Valida rejeição com 401 para token JWT inválido ou malformado."""
    headers = {"Authorization": "Bearer token.completamente.invalido"}

    response = client.get("/players/player_0000/persona", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_persona_invalid_player_id_format(client: TestClient) -> None:
    """Valida rejeição com 422 para player_id fora do padrão player_xxxx."""
    token = create_access_token({"sub": "player_0000"})
    headers = {"Authorization": f"Bearer {token}"}

    invalid_ids = ["player_12", "admin", "player_abc", "PLAYER_0000", "p_0000"]
    for pid in invalid_ids:
        response = client.get(f"/players/{pid}/persona", headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_persona_deterministic_stub(client: TestClient) -> None:
    """Valida que o stub é determinístico para um mesmo identificador de jogador."""
    token = create_access_token({"sub": "player_0000"})
    headers = {"Authorization": f"Bearer {token}"}

    resp1 = client.get("/players/player_0001/persona", headers=headers)
    resp2 = client.get("/players/player_0001/persona", headers=headers)

    assert resp1.status_code == status.HTTP_200_OK
    assert resp2.status_code == status.HTTP_200_OK
    assert resp1.json()["persona"] == resp2.json()["persona"]


def test_resolve_mock_persona_returns_bartle_persona() -> None:
    """Valida a função de resolução mockada retornando tipos válidos do Enum."""
    persona = resolve_mock_persona("player_0000")
    assert isinstance(persona, BartlePersona)
