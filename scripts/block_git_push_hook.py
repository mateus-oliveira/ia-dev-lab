"""Hook PreToolUse do Claude Code: bloqueia `git push` disparado pelo agente de IA."""

import json
import shlex
import sys

_OPERATOR_TOKENS = {";", "&&", "||", "|"}


def _split_into_simple_commands(command: str) -> list[list[str]]:
    """Tokeniza um comando de shell e o divide em sub-comandos simples.

    Respeita aspas (um argumento entre aspas vira um unico token, preservando
    espacos internos) e usa `;`, `&&`, `||` e `|` como separadores de
    sub-comandos quando aparecem como tokens isolados.

    :param command: Texto bruto do comando de shell.

    :return: Lista de sub-comandos, cada um representado como uma lista de tokens.
    """
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    simple_commands: list[list[str]] = [[]]
    for token in tokens:
        if token in _OPERATOR_TOKENS:
            simple_commands.append([])
        else:
            simple_commands[-1].append(token)
    return [cmd for cmd in simple_commands if cmd]


def command_has_git_push(command: str) -> bool:
    """Verifica se o comando invoca `git push` como sub-comando real.

    Tokeniza o comando respeitando aspas, para que a palavra "push" dentro de
    uma mensagem de commit entre aspas (ex.: `git commit -m "fala sobre push"`)
    nao seja confundida com uma invocacao real de `git push`.

    :param command: Texto do comando que a ferramenta Bash tentaria executar.

    :return: True se algum sub-comando contiver os tokens `git` e `push`, False caso contrario.
    """
    for tokens in _split_into_simple_commands(command):
        if "git" in tokens and "push" in tokens:
            return True
    return False


def main() -> int:
    """Le o payload do hook PreToolUse via stdin e bloqueia comandos com `git push`.

    Segue o protocolo de hooks do Claude Code: o codigo de saida 2 bloqueia a
    execucao da ferramenta e devolve a mensagem em stderr como motivo ao agente.

    :return: 0 se o comando for permitido; 2 se contiver `git push`.
    """
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")

    if command_has_git_push(command):
        print(
            "Bloqueado pelo harness: 'git push' nao pode ser executado pelo agente de IA. "
            "O push para o repositorio remoto deve ser feito manualmente pelo desenvolvedor, "
            "apos revisao (ver docs/adr/0003-harness-desenvolvimento.md).",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
