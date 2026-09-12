"""Bloqueia commits cuja arvore de diretorios do README.md liste arquivos fora da raiz do projeto.

Ver docs/adr/0009-granularidade-arvore-readme.md: a arvore ASCII da secao
"Estrutura do projeto" do README.md pode listar diretorios em qualquer
profundidade, mas arquivos individuais somente quando estao na raiz do
projeto (profundidade 1). Arquivos dentro de qualquer subdiretorio (ex.:
`docs/adr/*.md`, `scripts/*.py`, qualquer caminho sob `src/`) nao devem
aparecer na arvore, para que o README nao precise ser atualizado a cada
arquivo novo criado no projeto.
"""

import re
import sys
from pathlib import Path

DEFAULT_README_PATH = "README.md"

_TREE_ENTRY_RE = re.compile(r"^(?P<indent>(?:[│ ]{4})*)(?P<connector>├── |└── )(?P<name>.+?)\s*$")


def extract_fenced_code_blocks(content: str) -> list[list[str]]:
    """Extrai o conteudo de todos os blocos de codigo delimitados por ``` em um texto Markdown.

    :param content: Conteudo Markdown completo a ser analisado.

    :return: Lista de blocos, cada um representado como lista de linhas (sem as cercas ```).
    """
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in content.splitlines():
        if line.strip().startswith("```"):
            if current is None:
                current = []
            else:
                blocks.append(current)
                current = None
        elif current is not None:
            current.append(line)
    return blocks


def find_directory_tree_block(content: str) -> list[str] | None:
    """Localiza, entre os blocos de codigo do README, o que representa a arvore de diretorios.

    O bloco da arvore e identificado pela primeira linha nao vazia terminar em "/"
    e nao ter indentacao (nome do diretorio raiz do projeto), distinguindo-o de
    outros blocos ```text``` do documento (ex.: o diagrama do pipeline).

    :param content: Conteudo completo do README.md.

    :return: Linhas do bloco da arvore de diretorios, ou None se nenhum for encontrado.
    """
    for block in extract_fenced_code_blocks(content):
        non_empty = [line for line in block if line.strip()]
        if not non_empty:
            continue
        first = non_empty[0]
        if first.rstrip().endswith("/") and first == first.lstrip():
            return block
    return None


def find_granularity_violations(tree_block: list[str]) -> list[str]:
    """Encontra entradas de arquivo em profundidade maior que a raiz do projeto na arvore.

    Cada entrada de diretorio (nome terminado em "/") e sempre permitida, em
    qualquer profundidade. Uma entrada de arquivo so e permitida quando esta
    imediatamente abaixo da raiz do projeto (profundidade 1); entradas de
    arquivo mais profundas violam a granularidade permitida.

    :param tree_block: Linhas do bloco da arvore de diretorios (ver `find_directory_tree_block`).

    :return: Lista das linhas originais que violam a granularidade permitida.
    """
    violations: list[str] = []
    for line in tree_block:
        match = _TREE_ENTRY_RE.match(line)
        if match is None:
            continue
        depth = len(match.group("indent")) // 4 + 1
        name = match.group("name")
        is_directory = name.rstrip().endswith("/")
        if not is_directory and depth > 1:
            violations.append(line)
    return violations


def check_readme_tree_granularity(readme_content: str) -> list[str]:
    """Verifica a granularidade da arvore de diretorios do conteudo de um README.

    :param readme_content: Conteudo completo do README.md a verificar.

    :return: Lista de linhas que violam a granularidade permitida (vazia se
        a arvore for valida ou se nenhum bloco de arvore for encontrado).
    """
    tree_block = find_directory_tree_block(readme_content)
    if tree_block is None:
        return []
    return find_granularity_violations(tree_block)


def main(argv: list[str]) -> int:
    """Ponto de entrada do hook: bloqueia o commit se a arvore do README violar a granularidade.

    :param argv: Argumentos de linha de comando; `argv[1]`, se presente, sobrescreve
        o caminho do README.md a verificar (usado nos testes).

    :return: 0 se a arvore do README for valida (ou inexistente), 1 caso contrario.
    """
    readme_path = Path(argv[1]) if len(argv) > 1 else Path(DEFAULT_README_PATH)
    if not readme_path.exists():
        return 0

    violations = check_readme_tree_granularity(readme_path.read_text(encoding="utf-8"))
    if violations:
        listed = "\n".join(f"  - {line.strip()}" for line in violations)
        print(
            "Commit bloqueado: a arvore de diretorios em "
            f"{readme_path} lista arquivo(s) fora da raiz do projeto "
            f"(ver docs/adr/0009-granularidade-arvore-readme.md):\n{listed}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
