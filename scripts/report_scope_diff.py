"""Relata os arquivos alterados em relacao a branch de origem, sinalizando dados brutos."""

import subprocess
import sys

DEFAULT_BASE_BRANCH = "dev"
FLAGGED_PATHS = ("src/data/events.csv", "src/data/sessions_features.csv")


def get_changed_files(base_branch: str = DEFAULT_BASE_BRANCH) -> list[str]:
    """Lista os arquivos alterados na branch atual em relacao a branch base.

    :param base_branch: Nome da branch de origem usada como referencia (padrao: "dev").

    :return: Lista de caminhos relativos dos arquivos alterados.
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def flag_out_of_scope(files: list[str]) -> list[str]:
    """Identifica, entre os arquivos alterados, quais sao considerados fora de escopo.

    :param files: Lista de caminhos de arquivos alterados.

    :return: Subconjunto de `files` que corresponde a dados brutos sinalizados
        (ex.: `src/data/events.csv`, `src/data/sessions_features.csv`).
    """
    return [f for f in files if f in FLAGGED_PATHS]


def main(argv: list[str]) -> int:
    """Ponto de entrada: reporta os arquivos alterados e sinaliza os fora de escopo.

    :param argv: Argumentos de linha de comando; `argv[1]`, se presente, sobrescreve a
        branch base usada como referencia (padrao: `dev`).

    :return: Sempre 0 — o comando e informativo e nao bloqueia nenhuma operacao,
        apenas sinaliza para revisao humana.
    """
    base_branch = argv[1] if len(argv) > 1 else DEFAULT_BASE_BRANCH
    files = get_changed_files(base_branch)

    if not files:
        print(f"Nenhuma alteracao em relacao a '{base_branch}'.")
        return 0

    print(f"Arquivos alterados em relacao a '{base_branch}':")
    for changed_file in files:
        print(f"  - {changed_file}")

    flagged = flag_out_of_scope(files)
    if flagged:
        print("\nAtencao: os seguintes arquivos parecem fora do escopo usual de uma tarefa:")
        for changed_file in flagged:
            print(f"  - {changed_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
