"""Configuracao compartilhada de testes: torna os scripts do harness importaveis."""

import os
import sys
from collections.abc import Callable, Generator
from pathlib import Path

import pytest

from alembic import command
from alembic.config import Config

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

ALEMBIC_INI_PATH = REPO_ROOT / "alembic.ini"

TEST_JWT_SECRET_KEY = "segredo-exclusivo-de-teste-nao-usar-em-execucao-real-0123456789"


@pytest.fixture(autouse=True, scope="session")
def jwt_secret_key_for_tests() -> Generator[None, None, None]:
    """Define o segredo JWT usado pela suíte inteira.

    `get_secret_key()` não tem valor padrão (ADR 0012): sem esta fixture,
    todo teste que emite ou valida token falharia. O segredo é declarado
    aqui, explicitamente, em vez de vir de um fallback escondido no código
    de produção.

    :return: Gerador que restaura o valor anterior da variável ao fim da sessão.
    """
    previous = os.environ.get("JWT_SECRET_KEY")
    os.environ["JWT_SECRET_KEY"] = TEST_JWT_SECRET_KEY
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("JWT_SECRET_KEY", None)
        else:
            os.environ["JWT_SECRET_KEY"] = previous


@pytest.fixture
def apply_migrations() -> Callable[[str], None]:
    """Fábrica que aplica as migrações Alembic a um banco de dados de teste.

    Substitui o antigo `init_db()` na configuração de bancos SQLite
    isolados usados pelos testes de integração da API (ver ADR 0006).

    :return: Função que recebe o caminho do banco e aplica `alembic upgrade head`.
    """

    def _apply(db_path: str) -> None:
        previous_db_path = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = db_path
        try:
            config = Config(str(ALEMBIC_INI_PATH))
            command.upgrade(config, "head")
        finally:
            if previous_db_path is None:
                os.environ.pop("DATABASE_PATH", None)
            else:
                os.environ["DATABASE_PATH"] = previous_db_path

    return _apply
