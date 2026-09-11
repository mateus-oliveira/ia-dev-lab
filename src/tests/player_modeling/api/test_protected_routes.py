"""Testes de integração para rotas protegidas por Bearer Token (User Story 3)."""

import sqlite3
from collections.abc import Callable, Generator
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from player_modeling.api.app import app
from player_modeling.api.database import get_connection, get_db
from player_modeling.api.security import create_access_token, hash_password


@pytest.fixture
def client(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> Generator[TestClient, None, None]:
    """Fixture com cliente HTTP e usuário autenticável configurado no banco SQLite."""
    db_file = str(tmp_path / "test_protected.sqlite3")
    apply_migrations(db_file)

    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, username, password) VALUES (?, ?, ?);",
        ("Jogador Teste", "player_0000", hash_password("secretpass123")),
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


def test_protected_routes_without_token(client: TestClient) -> None:
    """Valida rejeição imediata com 401 para requisição sem cabeçalho Authorization."""
    response_me = client.get("/auth/me")
    assert response_me.status_code == status.HTTP_401_UNAUTHORIZED

    response_sample = client.get("/protected-sample")
    assert response_sample.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_routes_with_invalid_token(client: TestClient) -> None:
    """Valida rejeição com 401 para token adulterado."""
    headers = {"Authorization": "Bearer token.invalido.adulterado"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_routes_with_expired_token(client: TestClient) -> None:
    """Valida rejeição com 401 para token expirado."""
    token = create_access_token({"sub": "player_0000"}, expires_delta=timedelta(seconds=-30))
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expirado" in response.json()["detail"]


def test_get_me_success(client: TestClient) -> None:
    """Valida retorno correto dos dados do usuário autenticado no endpoint /auth/me."""
    token = create_access_token({"sub": "player_0000"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["username"] == "player_0000"
    assert data["name"] == "Jogador Teste"
    assert "id" in data
    assert "password" not in data


def test_protected_sample_success(client: TestClient) -> None:
    """Valida acesso autorizado ao endpoint de exemplo /protected-sample."""
    token = create_access_token({"sub": "player_0000"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected-sample", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["message"] == "Acesso autorizado com sucesso!"
    assert data["user"]["username"] == "player_0000"
