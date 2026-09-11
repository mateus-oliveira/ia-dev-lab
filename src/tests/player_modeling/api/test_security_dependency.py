"""Testes unitários da dependência FastAPI get_current_user (User Story 3)."""

import sqlite3
from collections.abc import Callable, Generator
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from player_modeling.api.database import get_connection
from player_modeling.api.security import (
    create_access_token,
    get_current_user,
    hash_password,
)


@pytest.fixture
def test_db_conn(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> Generator[sqlite3.Connection, None, None]:
    """Fixture para criar um banco de dados SQLite com um usuário de teste."""
    db_file = str(tmp_path / "test_auth_dep.sqlite3")
    apply_migrations(db_file)
    conn = get_connection(db_file)

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, username, password) VALUES (?, ?, ?);",
        ("Jogador Teste", "player_0000", hash_password("pass123")),
    )
    conn.commit()

    yield conn
    conn.close()


def test_get_current_user_no_credentials(test_db_conn: sqlite3.Connection) -> None:
    """Valida rejeição 401 quando nenhuma credencial é enviada."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None, db=test_db_conn)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "não fornecido" in exc_info.value.detail


def test_get_current_user_invalid_scheme(test_db_conn: sqlite3.Connection) -> None:
    """Valida rejeição 401 quando o scheme não é Bearer."""
    creds = HTTPAuthorizationCredentials(scheme="Basic", credentials="some_credentials")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=creds, db=test_db_conn)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_expired_token(test_db_conn: sqlite3.Connection) -> None:
    """Valida rejeição 401 quando o token está expirado."""
    token = create_access_token({"sub": "player_0000"}, expires_delta=timedelta(seconds=-10))
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=creds, db=test_db_conn)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expirado" in exc_info.value.detail


def test_get_current_user_invalid_token(test_db_conn: sqlite3.Connection) -> None:
    """Valida rejeição 401 para token JWT adulterado."""
    token = create_access_token({"sub": "player_0000"})
    corrupted_token = token[:-4] + "invalid"
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=corrupted_token)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=creds, db=test_db_conn)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "inválido" in exc_info.value.detail


def test_get_current_user_user_not_found(test_db_conn: sqlite3.Connection) -> None:
    """Valida rejeição 401 se o token possui um usuário inexistente no banco."""
    token = create_access_token({"sub": "player_9999"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=creds, db=test_db_conn)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "não encontrado" in exc_info.value.detail


def test_get_current_user_success(test_db_conn: sqlite3.Connection) -> None:
    """Valida sucesso na autenticação com Bearer token e injeção do usuário."""
    token = create_access_token({"sub": "player_0000"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    user = get_current_user(credentials=creds, db=test_db_conn)
    assert user["username"] == "player_0000"
    assert user["name"] == "Jogador Teste"
    assert "id" in user
