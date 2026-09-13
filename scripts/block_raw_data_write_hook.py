"""Hook PreToolUse do Claude Code: bloqueia escrita do agente nos dados de origem.

`src/data/events.csv` e `src/data/sessions_features.csv` sao o dataset
sintetico rotulado que pre-treina o classificador de personas: a regra
"Nao modificar dados brutos" do CLAUDE.md diz que eles nunca devem ser
editados manualmente nem sobrescritos pelo pipeline, e que a unica forma
sancionada de regenera-los e
`src/player_modeling/scripts/generate_raw_events.py`.

Este hook impoe essa regra tecnicamente: leitura e analise continuam
livres, assim como a execucao do script oficial de geracao.
"""

import json
import os
import shlex
import sys
from pathlib import Path

PROTECTED_PATHS: tuple[str, ...] = (
    "src/data/events.csv",
    "src/data/sessions_features.csv",
)

EDIT_TOOLS: tuple[str, ...] = ("Write", "Edit", "NotebookEdit")

WRITE_COMMANDS: frozenset[str] = frozenset(
    {"rm", "mv", "cp", "tee", "truncate", "dd", "sed", "install", "shred"}
)

_REDIRECTION_TOKENS = {">", ">>"}

_OPERATOR_TOKENS = {";", "&&", "||", "|"}

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


def normalize_path(raw_path: str) -> str:
    """Normaliza um caminho para comparacao com a lista de caminhos protegidos.

    Caminhos absolutos dentro do repositorio sao convertidos para caminhos
    relativos a raiz; caminhos absolutos fora do repositorio sao devolvidos
    normalizados, e nunca correspondem a um arquivo protegido.

    :param raw_path: Caminho como aparece no payload do hook ou no comando.

    :return: Caminho normalizado, relativo a raiz do repositorio quando possivel.
    """
    expanded = os.path.expanduser(raw_path)
    if os.path.isabs(expanded):
        try:
            return os.path.relpath(os.path.normpath(expanded), REPOSITORY_ROOT)
        except ValueError:
            return os.path.normpath(expanded)
    return os.path.normpath(expanded)


def is_protected_path(raw_path: str) -> bool:
    """Verifica se um caminho aponta para um arquivo de dataset de origem protegido.

    :param raw_path: Caminho como aparece no payload do hook ou no comando.

    :return: True se o caminho corresponder a um arquivo protegido, False caso contrario.
    """
    normalized = normalize_path(raw_path)
    return any(normalized == normalize_path(protected) for protected in PROTECTED_PATHS)


def _split_into_simple_commands(command: str) -> list[list[str]]:
    """Tokeniza um comando de shell e o divide em sub-comandos simples.

    Respeita aspas e usa `;`, `&&`, `||` e `|` como separadores quando
    aparecem como tokens isolados, igual ao hook de bloqueio de `git push`.

    :param command: Texto bruto do comando de shell.

    :return: Lista de sub-comandos, cada um como lista de tokens.
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


def command_writes_protected_path(command: str) -> bool:
    """Verifica se um comando de shell escreve em algum arquivo de dataset protegido.

    Bloqueia duas formas de escrita: redirecionamento (`>`/`>>`) para um
    caminho protegido e utilitario de escrita/remocao (`WRITE_COMMANDS`)
    aplicado a um caminho protegido. Comandos de leitura (`cat`, `head`,
    `grep`, `wc`) e a execucao do script oficial de geracao do dataset nao
    sao bloqueados.

    :param command: Texto do comando que a ferramenta Bash tentaria executar.

    :return: True se o comando escrever em um arquivo protegido, False caso contrario.
    """
    for tokens in _split_into_simple_commands(command):
        for index, token in enumerate(tokens):
            if not is_protected_path(token):
                continue
            if index > 0 and tokens[index - 1] in _REDIRECTION_TOKENS:
                return True
            if os.path.basename(tokens[0]) in WRITE_COMMANDS:
                return True
    return False


def is_blocked(tool_name: str, tool_input: dict[str, object]) -> bool:
    """Decide se a chamada de ferramenta deve ser bloqueada pelo hook.

    :param tool_name: Nome da ferramenta que o agente tentaria executar.
    :param tool_input: Conteudo de `tool_input` do payload do hook.

    :return: True se a chamada escrever em um arquivo protegido, False caso contrario.
    """
    if tool_name in EDIT_TOOLS:
        file_path = tool_input.get("file_path", "")
        return isinstance(file_path, str) and is_protected_path(file_path)

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        return isinstance(command, str) and command_writes_protected_path(command)

    return False


def main() -> int:
    """Le o payload do hook PreToolUse via stdin e bloqueia escritas nos dados de origem.

    Segue o protocolo de hooks do Claude Code: o codigo de saida 2 bloqueia
    a execucao da ferramenta e devolve a mensagem de stderr como motivo ao
    agente. Um payload que nao possa ser interpretado devolve 0 (permite),
    para que uma falha do proprio controle nao interrompa a sessao.

    :return: 0 se a chamada for permitida; 2 se escrever em arquivo protegido.
    """
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0

    if not isinstance(payload, dict):
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        return 0

    if is_blocked(tool_name, tool_input):
        protected = ", ".join(PROTECTED_PATHS)
        print(
            "Bloqueado pelo harness: escrita em dados de origem do projeto "
            f"({protected}) nao e permitida ao agente de IA. Esses arquivos sao o "
            "dataset sintetico que pre-treina o modelo e devem ser regenerados "
            "apenas por 'src/player_modeling/scripts/generate_raw_events.py' "
            "(ver secao 'Nao modificar dados brutos' do CLAUDE.md e "
            "docs/adr/0003-harness-desenvolvimento.md).",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
