"""Bloqueia o commit de arquivos sensiveis: .env, venvs e artefatos de execucao."""

import subprocess
import sys

_SENSITIVE_DIR_NAMES = ("venv", ".venv", "__pycache__")
_ALLOWED_ENV_FILES = {".env.example"}


def is_sensitive_path(path: str) -> bool:
    """Verifica se o caminho corresponde a um arquivo ou diretorio sensivel.

    Considera sensivel: qualquer caminho dentro de um diretorio de venv ou de
    artefatos de execucao (`venv/`, `.venv/`, `__pycache__/`), arquivos `.env*`
    (exceto `.env.example`, mantido como modelo versionado) e arquivos `.pyc`.

    :param path: Caminho relativo do arquivo (staged) a verificar.

    :return: True se o caminho for considerado sensivel, False caso contrario.
    """
    parts = path.split("/")
    filename = parts[-1]

    if any(part in _SENSITIVE_DIR_NAMES for part in parts[:-1]):
        return True
    if filename.endswith(".pyc"):
        return True
    if filename == ".env":
        return True
    if filename.startswith(".env.") and filename not in _ALLOWED_ENV_FILES:
        return True
    return False


def get_staged_files() -> list[str]:
    """Lista os arquivos atualmente staged para commit.

    :return: Lista de caminhos relativos dos arquivos staged.
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main(argv: list[str]) -> int:
    """Ponto de entrada do hook: bloqueia o commit se algum arquivo staged for sensivel.

    :param argv: Caminhos de arquivos a verificar (tipicamente fornecidos pelo pre-commit);
        quando vazio, os arquivos staged do git sao usados.

    :return: 0 se nenhum arquivo sensivel for encontrado, 1 caso contrario.
    """
    files = argv[1:] if len(argv) > 1 else get_staged_files()
    sensitive = [f for f in files if is_sensitive_path(f)]

    if sensitive:
        listed = "\n".join(f"  - {f}" for f in sensitive)
        print(
            "Commit bloqueado: os seguintes arquivos sao considerados sensiveis "
            f"(.env, venv ou artefatos de execucao):\n{listed}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
