"""Testes para scripts/block_git_push_hook.py (bloqueio tecnico de push por IA)."""

import pytest
from block_git_push_hook import command_has_git_push

_PUSH_COMMANDS = [
    "git push",
    "git push origin main",
    "git push --force origin dev",
    "cd /tmp && git push",
    "git push origin HEAD:refs/heads/dev",
]

_NON_PUSH_COMMANDS = [
    "git status",
    "git commit -m 'ADD: exemplo'",
    "git merge feature/x",
    "git log --oneline",
    "echo hello",
    'git commit -m "ADD: bloqueio tecnico de git push por agentes de IA"',
]


@pytest.mark.parametrize("command", _PUSH_COMMANDS)
def test_comandos_com_git_push_sao_detectados(command: str) -> None:
    """Qualquer variante de `git push` deve ser detectada pelo hook."""
    assert command_has_git_push(command) is True


@pytest.mark.parametrize("command", _NON_PUSH_COMMANDS)
def test_comandos_sem_push_nao_sao_bloqueados(command: str) -> None:
    """git commit, git merge e outros comandos git sem push nao devem ser bloqueados."""
    assert command_has_git_push(command) is False
