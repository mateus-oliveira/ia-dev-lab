"""Testes para scripts/check_branch.py (validacao da branch atual, ADR 0002)."""

import pytest
from check_branch import get_current_branch, is_protected_branch, main


@pytest.mark.parametrize("branch", ["main", "dev"])
def test_branches_protegidas_sao_identificadas(branch: str) -> None:
    """main e dev devem ser reconhecidas como branches protegidas."""
    assert is_protected_branch(branch) is True


@pytest.mark.parametrize(
    "branch",
    ["feature/pipeline-ingestao-eventos", "fix/validacao-eventos", "chore/setup-harness"],
)
def test_branches_de_tarefa_nao_sao_protegidas(branch: str) -> None:
    """Branches de tarefa no formato <tipo>/<descricao> nao devem ser bloqueadas."""
    assert is_protected_branch(branch) is False


def test_main_bloqueia_quando_branch_atual_e_protegida(monkeypatch: pytest.MonkeyPatch) -> None:
    """O hook deve retornar codigo de saida 1 quando a branch atual for main ou dev."""
    monkeypatch.setattr("check_branch.get_current_branch", lambda: "dev")
    assert main() == 1


def test_main_permite_quando_branch_atual_e_de_tarefa(monkeypatch: pytest.MonkeyPatch) -> None:
    """O hook deve retornar codigo de saida 0 quando a branch atual for uma branch de tarefa."""
    monkeypatch.setattr("check_branch.get_current_branch", lambda: "feature/exemplo")
    assert main() == 0


def test_get_current_branch_retorna_a_branch_real_do_repositorio() -> None:
    """get_current_branch deve refletir a branch git real (nao vazia neste repositorio)."""
    assert get_current_branch() != ""
