"""Valida mensagens de commit contra o padrao `<PREFIXO>: <descricao>` da ADR 0002."""

import re
import sys

VALID_PREFIXES = ("ADD", "UPDATE", "FIX", "REMOVE", "REFACTOR", "DOCS", "TEST")

_COMMIT_MESSAGE_PATTERN = re.compile(r"^(" + "|".join(VALID_PREFIXES) + r"): .+")


def is_valid_commit_message(message: str) -> bool:
    """Verifica se a mensagem de commit segue o padrao `<PREFIXO>: <descricao>` da ADR 0002.

    :param message: Mensagem de commit completa; apenas a primeira linha e considerada.

    :return: True se a primeira linha da mensagem segue o padrao, False caso contrario.
    """
    lines = message.strip().splitlines()
    if not lines:
        return False
    return bool(_COMMIT_MESSAGE_PATTERN.match(lines[0]))


def main(argv: list[str]) -> int:
    """Ponto de entrada do hook `commit-msg`: le o arquivo de mensagem e valida seu conteudo.

    :param argv: Argumentos de linha de comando; `argv[1]` deve ser o caminho do arquivo
        de mensagem de commit fornecido pelo git ao hook `commit-msg`.

    :return: 0 se a mensagem for valida, 1 caso contrario ou se o argumento estiver ausente.
    """
    if len(argv) < 2:
        print("Uso: check_commit_message.py <caminho-do-arquivo-de-mensagem>", file=sys.stderr)
        return 1

    with open(argv[1], encoding="utf-8") as handle:
        message = handle.read()

    if is_valid_commit_message(message):
        return 0

    prefixes = ", ".join(VALID_PREFIXES)
    print(
        "Mensagem de commit invalida. Use o padrao '<PREFIXO>: <descricao>' "
        f"com um dos prefixos: {prefixes} (ver docs/adr/0002-git-flow.md).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
