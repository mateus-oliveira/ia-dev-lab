"""Dependency de banco de dados da API FastAPI.

A abertura de conexão em si vive em `player_modeling.persistence.database`,
compartilhada com o worker subscriber e com as migrações Alembic. Aqui fica
apenas o que é específico do framework web: o generator usado como
dependency das rotas, que fecha a conexão ao fim da requisição.
"""

import sqlite3
from collections.abc import Generator

from player_modeling.persistence.database import get_connection


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
