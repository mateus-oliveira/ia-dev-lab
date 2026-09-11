"""Módulo de conexão com o banco de dados SQLite.

O schema (tabela `users` da ADR 0004 e futuras tabelas) é gerenciado por
migrações versionadas com Alembic (ADR 0006), não por este módulo.
"""

import os
import sqlite3
from collections.abc import Generator

DEFAULT_DATABASE_PATH = "db.sqlite3"


def get_db_path(custom_path: str | None = None) -> str:
    """Retorna o caminho do banco de dados SQLite a ser utilizado.

    :param custom_path: Caminho customizado para o banco (útil para testes).
    :return: Caminho em string para o arquivo de banco de dados.
    """
    if custom_path is not None:
        return custom_path
    return os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH)


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Abre e retorna uma conexão com o banco de dados SQLite.

    :param db_path: Caminho customizado para o banco de dados.
    :return: Objeto de conexão sqlite3 com row_factory configurado para sqlite3.Row.
    """
    path = get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Retorna uma conexão aberta com o SQLite para injeção de dependência.

    Fecha a conexão automaticamente após o término da requisição.

    :return: Gerador de conexão com o banco de dados.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
