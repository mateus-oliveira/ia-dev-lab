"""Testes unitários do módulo de banco de dados SQLite (ADR 0004)."""

import sqlite3
from pathlib import Path

import pytest

from player_modeling.api.database import get_connection, get_db_path, init_db


def test_init_db_creates_users_table(tmp_path: Path) -> None:
    """Testa se a função init_db cria a tabela users com a estrutura da ADR 0004.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    """
    db_file = str(tmp_path / "test_db.sqlite3")
    init_db(db_file)

    conn = get_connection(db_file)
    cursor = conn.cursor()

    # Verifica se a tabela users existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    table = cursor.fetchone()
    assert table is not None
    assert table["name"] == "users"

    # Verifica as colunas da tabela users
    cursor.execute("PRAGMA table_info(users);")
    columns = {row["name"]: row["type"] for row in cursor.fetchall()}

    assert "id" in columns
    assert "name" in columns
    assert "username" in columns
    assert "password" in columns
    conn.close()


def test_users_table_unique_username_constraint(tmp_path: Path) -> None:
    """Testa se a tabela users impõe restrição de unicidade no campo username.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    """
    db_file = str(tmp_path / "test_db.sqlite3")
    init_db(db_file)

    conn = get_connection(db_file)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (name, username, password) VALUES (?, ?, ?);",
        ("Player Zero", "player_0000", "hashed_password"),
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO users (name, username, password) VALUES (?, ?, ?);",
            ("Player Zero Duplicate", "player_0000", "another_hash"),
        )
        conn.commit()

    conn.close()


def test_get_db_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Testa a resolução do caminho do banco via parâmetro e variável de ambiente.

    :param monkeypatch: Fixture para manipulação de variáveis de ambiente.
    """
    assert get_db_path("custom.sqlite3") == "custom.sqlite3"

    monkeypatch.setenv("DATABASE_PATH", "env_test.sqlite3")
    assert get_db_path() == "env_test.sqlite3"
