"""Módulo de conexão e gerenciamento do banco de dados SQLite.

Implementa a inicialização da tabela users conforme a ADR 0004.
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


def init_db(db_path: str | None = None) -> None:
    """Inicializa as tabelas do banco de dados SQLite caso ainda não existam.

    Cria a tabela users conforme especificado na ADR 0004.

    :param db_path: Caminho customizado para o banco de dados.
    :return: None
    """
    create_users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(255) NOT NULL,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    );
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(create_users_table_sql)
        conn.commit()


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
