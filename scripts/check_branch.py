"""Bloqueia commits feitos diretamente nas branches protegidas (main, dev) da ADR 0002."""

import subprocess
import sys

PROTECTED_BRANCHES = ("main", "dev")


def is_protected_branch(branch: str) -> bool:
    """Verifica se a branch informada e uma branch protegida (main ou dev).

    :param branch: Nome da branch a ser verificada.

    :return: True se a branch estiver entre as branches protegidas, False caso contrario.
    """
    return branch in PROTECTED_BRANCHES


def get_current_branch() -> str:
    """Obtem o nome da branch git atual do repositorio.

    :return: Nome da branch atual (`HEAD` quando em estado "detached").
    """
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> int:
    """Ponto de entrada do hook: bloqueia o commit quando a branch atual e main ou dev.

    :return: 0 se a branch atual for uma branch de tarefa segura, 1 se for main ou dev.
    """
    branch = get_current_branch()
    if is_protected_branch(branch):
        print(
            f"Commit bloqueado: a branch atual e '{branch}'. "
            "Crie uma branch de tarefa (feature/, fix/, refactor/, docs/, test/, chore/) "
            "a partir de 'dev' antes de commitar (ver docs/adr/0002-git-flow.md).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
