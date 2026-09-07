"""Testes para scripts/report_scope_diff.py (relatorio de alteracoes fora do escopo)."""

from report_scope_diff import flag_out_of_scope


def test_alteracoes_dentro_do_escopo_nao_sao_sinalizadas() -> None:
    """Arquivos comuns da tarefa nao devem ser sinalizados como fora de escopo."""
    files = ["scripts/check_branch.py", "src/tests/test_check_branch.py", "README.md"]
    assert flag_out_of_scope(files) == []


def test_alteracao_em_dado_bruto_e_sinalizada() -> None:
    """Eventos e features em src/data/ devem ser sinalizados quando alterados."""
    files = ["scripts/check_branch.py", "src/data/events.csv", "src/data/sessions_features.csv"]
    assert flag_out_of_scope(files) == ["src/data/events.csv", "src/data/sessions_features.csv"]
