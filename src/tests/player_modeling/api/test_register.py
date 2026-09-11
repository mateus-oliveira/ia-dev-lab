"""Testes de integração para o endpoint POST /auth/register (User Story 1)."""

import sqlite3
from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from player_modeling.api.app import app
from player_modeling.api.database import get_connection, get_db


@pytest.fixture
def client(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> Generator[TestClient, None, None]:
    """Fixture para criar um cliente de teste HTTP com banco SQLite isolado."""
    db_file = str(tmp_path / "test_register.sqlite3")
    apply_migrations(db_file)

    def override_get_db() -> Generator[sqlite3.Connection, None, None]:
        conn = get_connection(db_file)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_register_success(client: TestClient) -> None:
    """Valida o registro bem-sucedido de usuário com HTTP 201 e senha protegida."""
    payload = {
        "name": "Jogador Zero",
        "username": "player_0000",
        "password": "strongpassword123",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["name"] == "Jogador Zero"
    assert data["username"] == "player_0000"
    assert "id" in data
    assert "password" not in data


def test_register_duplicate_username(client: TestClient) -> None:
    """Valida rejeição HTTP 409 Conflict ao tentar cadastrar username repetido."""
    payload = {
        "name": "Jogador Original",
        "username": "player_0001",
        "password": "password123",
    }
    resp1 = client.post("/auth/register", json=payload)
    assert resp1.status_code == status.HTTP_201_CREATED

    resp2 = client.post("/auth/register", json=payload)
    assert resp2.status_code == status.HTTP_409_CONFLICT
    assert "já está em uso" in resp2.json()["detail"]


def test_register_invalid_payload(client: TestClient) -> None:
    """Valida erro 422 ao omitir campos obrigatórios ou enviar formato inválido."""
    # Username fora do padrão player_xxxx
    invalid_payload = {
        "name": "Nome",
        "username": "invalid_username",
        "password": "validpassword",
    }
    resp = client.post("/auth/register", json=invalid_payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Senha curta
    short_pwd_payload = {
        "name": "Nome",
        "username": "player_0002",
        "password": "123",
    }
    resp_short = client.post("/auth/register", json=short_pwd_payload)
    assert resp_short.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
