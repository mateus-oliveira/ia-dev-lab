"""Testes para scripts/check_sensitive_paths.py (deteccao de arquivos sensiveis)."""

import pytest
from check_sensitive_paths import is_sensitive_path, main


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.local",
        "venv/lib/python3.13/site-packages/pkg.py",
        ".venv/bin/python",
        "src/player_modeling/__pycache__/mod.cpython-313.pyc",
        "scripts/foo.pyc",
    ],
)
def test_caminhos_sensiveis_sao_detectados(path: str) -> None:
    """Arquivos de segredo, venv e artefatos de execucao devem ser sinalizados."""
    assert is_sensitive_path(path) is True


@pytest.mark.parametrize(
    "path",
    [
        ".env.example",
        "src/player_modeling/ml/model.py",
        "tests/test_check_branch.py",
        "README.md",
    ],
)
def test_caminhos_normais_nao_sao_sinalizados(path: str) -> None:
    """Codigo-fonte comum e o `.env.example` versionado nao devem ser bloqueados."""
    assert is_sensitive_path(path) is False


def test_main_bloqueia_quando_ha_arquivo_sensivel_na_lista() -> None:
    """O hook deve retornar codigo de saida 1 quando algum arquivo listado for sensivel."""
    assert main(["check_sensitive_paths.py", "src/app.py", ".env"]) == 1


def test_main_permite_quando_nenhum_arquivo_e_sensivel() -> None:
    """O hook deve retornar codigo de saida 0 quando nenhum arquivo listado for sensivel."""
    assert main(["check_sensitive_paths.py", "src/app.py", "README.md"]) == 0
