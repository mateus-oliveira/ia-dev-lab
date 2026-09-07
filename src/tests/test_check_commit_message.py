"""Testes para scripts/check_commit_message.py (validacao da mensagem de commit, ADR 0002)."""

import pytest
from check_commit_message import VALID_PREFIXES, is_valid_commit_message


@pytest.mark.parametrize("prefix", VALID_PREFIXES)
def test_mensagem_com_prefixo_valido_e_aceita(prefix: str) -> None:
    """Uma mensagem com um dos prefixos validos da ADR 0002 deve ser aceita."""
    assert is_valid_commit_message(f"{prefix}: descricao objetiva da mudanca") is True


@pytest.mark.parametrize(
    "message",
    [
        "ajustes diversos",
        "Fix bug no worker",
        "add: prefixo em minusculo",
        "ADD sem dois pontos",
        "",
    ],
)
def test_mensagem_fora_do_padrao_e_rejeitada(message: str) -> None:
    """Mensagens sem um prefixo valido seguido de ': ' devem ser rejeitadas."""
    assert is_valid_commit_message(message) is False


def test_considera_apenas_a_primeira_linha() -> None:
    """Apenas a primeira linha da mensagem de commit deve ser validada."""
    message = "ADD: script de validacao de branch\n\nDetalhes adicionais no corpo do commit."
    assert is_valid_commit_message(message) is True
