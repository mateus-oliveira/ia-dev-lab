"""Testes para scripts/block_raw_data_write_hook.py (protecao dos dados de origem)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from block_raw_data_write_hook import (
    PROTECTED_PATHS,
    command_writes_protected_path,
    is_blocked,
    is_protected_path,
)

HOOK_PATH = Path(__file__).resolve().parents[3] / "scripts" / "block_raw_data_write_hook.py"

_WRITING_COMMANDS = [
    "echo corrompido > src/data/events.csv",
    "cat /dev/null >> src/data/sessions_features.csv",
    "rm src/data/events.csv",
    "rm -f ./src/data/events.csv",
    "mv /tmp/outro.csv src/data/events.csv",
    "sed -i '' 's/attack/chat/g' src/data/events.csv",
    "truncate -s 0 src/data/sessions_features.csv",
    "cp /tmp/fake.csv src/data/sessions_features.csv",
    "poetry run pytest && rm src/data/events.csv",
]

_READING_COMMANDS = [
    "cat src/data/events.csv",
    "head -5 src/data/sessions_features.csv",
    "wc -l src/data/events.csv",
    "grep attack src/data/events.csv",
    "poetry run python src/player_modeling/scripts/generate_raw_events.py --players 200 --seed 42",
    "echo teste > /tmp/outro.csv",
    "rm src/tests/scratch.txt",
    "git status",
]


@pytest.mark.parametrize("command", _WRITING_COMMANDS)
def test_comandos_de_escrita_em_dados_de_origem_sao_detectados(command: str) -> None:
    """Redirecionamentos e utilitarios de escrita sobre os CSVs devem ser detectados."""
    assert command_writes_protected_path(command) is True


@pytest.mark.parametrize("command", _READING_COMMANDS)
def test_comandos_de_leitura_e_geracao_oficial_sao_permitidos(command: str) -> None:
    """Leitura dos CSVs e o script oficial de geracao nao devem ser bloqueados."""
    assert command_writes_protected_path(command) is False


@pytest.mark.parametrize("protected", PROTECTED_PATHS)
def test_caminhos_protegidos_sao_reconhecidos(protected: str) -> None:
    """Cada caminho da lista protegida deve ser reconhecido como tal."""
    assert is_protected_path(protected) is True


def test_caminho_equivalente_nao_escapa_do_bloqueio() -> None:
    """Prefixo './', segmentos redundantes e caminho absoluto apontam para o mesmo arquivo."""
    repo_root = Path(__file__).resolve().parents[3]
    assert is_protected_path("./src/data/events.csv") is True
    assert is_protected_path("src/data/../data/events.csv") is True
    assert is_protected_path(str(repo_root / "src" / "data" / "events.csv")) is True


def test_caminho_fora_do_repositorio_nao_e_protegido() -> None:
    """Um arquivo de mesmo nome fora do repositorio nao deve ser confundido com o dataset."""
    assert is_protected_path("/tmp/src/data/events.csv") is False


def test_ferramenta_de_edicao_em_arquivo_protegido_e_bloqueada() -> None:
    """Write/Edit/NotebookEdit sobre um CSV de origem devem ser bloqueados pelo file_path."""
    for tool in ("Write", "Edit", "NotebookEdit"):
        assert is_blocked(tool, {"file_path": "src/data/events.csv"}) is True


def test_ferramenta_de_edicao_em_arquivo_comum_e_permitida() -> None:
    """Edicoes em codigo do projeto nao devem ser afetadas pelo hook."""
    assert is_blocked("Write", {"file_path": "src/player_modeling/ml/knn.py"}) is False


def test_ferramenta_nao_coberta_e_permitida() -> None:
    """Ferramentas fora do escopo do hook (ex.: Read) nunca sao bloqueadas."""
    assert is_blocked("Read", {"file_path": "src/data/events.csv"}) is False


def _run_hook(payload: str) -> subprocess.CompletedProcess[str]:
    """Executa o hook como processo, alimentando o payload por stdin.

    :param payload: Texto enviado ao hook via stdin.

    :return: Resultado da execucao, com codigo de saida e stderr.
    """
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
    )


def test_hook_bloqueia_com_codigo_2_e_mensagem_explicativa() -> None:
    """O protocolo de hooks exige codigo 2 e motivo em stderr para bloquear."""
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "src/data/events.csv"}})
    result = _run_hook(payload)
    assert result.returncode == 2
    assert "generate_raw_events.py" in result.stderr


def test_hook_permite_chamada_legitima_com_codigo_0() -> None:
    """Uma leitura do dataset deve passar pelo hook sem bloqueio."""
    payload = json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": "head -3 src/data/events.csv"}}
    )
    result = _run_hook(payload)
    assert result.returncode == 0


def test_hook_permite_quando_payload_e_malformado() -> None:
    """Falha do proprio controle nao deve interromper a sessao do agente."""
    assert _run_hook("nao e json").returncode == 0
    assert _run_hook(json.dumps(["lista", "inesperada"])).returncode == 0
    assert _run_hook(json.dumps({"tool_name": "Write"})).returncode == 0
