"""Testes de integração para o endpoint POST /auth/login (User Story 2)."""

import sqlite3
from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from player_modeling.api.app import app
from player_modeling.api.database import get_connection, get_db
from player_modeling.api.security import decode_access_token, hash_password


@pytest.fixture
def client(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> Generator[TestClient, None, None]:
    """Fixture para criar um cliente HTTP com banco SQLite populado com um usuário."""
    db_file = str(tmp_path / "test_login.sqlite3")
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


def test_login_success(client: TestClient) -> None:
    """Valida login bem-sucedido com emissão de Bearer Token JWT."""
    payload = {"username": "player_0000", "password": "secretpass123"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    token_data = decode_access_token(data["access_token"])
    assert token_data["sub"] == "player_0000"


def test_login_wrong_password(client: TestClient) -> None:
    """Valida rejeição 401 Unauthorized para senha incorreta."""
    payload = {"username": "player_0000", "password": "wrong_password"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Credenciais inválidas" in response.json()["detail"]


def test_login_user_not_found(client: TestClient) -> None:
    """Valida rejeição 401 Unauthorized para usuário não cadastrado."""
    payload = {"username": "player_9999", "password": "secretpass123"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Credenciais inválidas" in response.json()["detail"]
