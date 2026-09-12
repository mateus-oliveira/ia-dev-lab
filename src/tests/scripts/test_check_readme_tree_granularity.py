"""Testes para scripts/check_readme_tree_granularity.py (granularidade da arvore do README)."""

from check_readme_tree_granularity import check_readme_tree_granularity, main
from conftest import REPO_ROOT

VALID_TREE_README = """\
## Estrutura do projeto

```text
player-modeling-lab/
│
├── CLAUDE.md
├── README.md
├── docker-compose.yml
├── Makefile
│
├── docs/
│   └── adr/
│
├── scripts/
│
└── src/
    ├── player_modeling/
    │   ├── simulator/
    │   ├── worker/
    │   ├── ml/
    │   ├── api/
    │   └── scripts/
    ├── alembic/
    │   └── versions/
    ├── data/
    └── tests/
        ├── player_modeling/
        │   ├── simulator/
        │   └── worker/
        └── scripts/
```
"""

INVALID_TREE_README = """\
## Estrutura do projeto

```text
player-modeling-lab/
│
├── CLAUDE.md
│
├── scripts/
│   ├── check_branch.py
│   └── check_sensitive_paths.py
│
└── src/
    └── player_modeling/
        └── worker/
            ├── features.py
            └── subscriber.py
```
"""

README_WITHOUT_TREE = """\
## Objetivo

Este projeto nao tem nenhum bloco de arvore de diretorios, apenas texto.

```text
Simulador (cronjob)
      │
      ▼
   RabbitMQ
```
"""


def test_arvore_com_apenas_diretorios_e_arquivos_de_raiz_e_valida() -> None:
    """Uma arvore que so lista diretorios e arquivos de raiz nao deve ter violacoes."""
    assert check_readme_tree_granularity(VALID_TREE_README) == []


def test_arvore_com_arquivo_em_subdiretorio_e_invalida() -> None:
    """Arquivos listados dentro de subdiretorios (scripts/, src/**) devem ser reportados."""
    violations = check_readme_tree_granularity(INVALID_TREE_README)
    assert len(violations) == 4
    assert any("check_branch.py" in line for line in violations)
    assert any("check_sensitive_paths.py" in line for line in violations)
    assert any("features.py" in line for line in violations)
    assert any("subscriber.py" in line for line in violations)


def test_readme_sem_bloco_de_arvore_e_considerado_valido() -> None:
    """Quando nao ha bloco de arvore de diretorios no README, nao ha o que violar."""
    assert check_readme_tree_granularity(README_WITHOUT_TREE) == []


def test_arvore_atual_do_readme_do_projeto_e_valida() -> None:
    """Regressao: a arvore real do README.md do projeto deve respeitar a granularidade."""
    readme_content = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert check_readme_tree_granularity(readme_content) == []


def test_main_bloqueia_quando_readme_viola_granularidade(tmp_path) -> None:
    """O hook deve retornar codigo de saida 1 quando o README tiver arquivos fora da raiz."""
    readme_path = tmp_path / "README.md"
    readme_path.write_text(INVALID_TREE_README, encoding="utf-8")
    assert main(["check_readme_tree_granularity.py", str(readme_path)]) == 1


def test_main_permite_quando_readme_respeita_granularidade(tmp_path) -> None:
    """O hook deve retornar codigo de saida 0 quando a arvore do README for valida."""
    readme_path = tmp_path / "README.md"
    readme_path.write_text(VALID_TREE_README, encoding="utf-8")
    assert main(["check_readme_tree_granularity.py", str(readme_path)]) == 0


def test_main_permite_quando_readme_nao_existe(tmp_path) -> None:
    """O hook nao deve falhar quando o caminho informado nao existir."""
    missing_path = tmp_path / "does-not-exist.md"
    assert main(["check_readme_tree_granularity.py", str(missing_path)]) == 0
