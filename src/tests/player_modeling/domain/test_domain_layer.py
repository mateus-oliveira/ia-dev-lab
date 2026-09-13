"""Testes da camada de domínio e da regra que a mantém independente.

A camada de domínio só cumpre seu papel enquanto não depender de mais nada:
é isso que permite usar `ml/` sem FastAPI e `worker/` sem o simulador. Esta
regra é verificada mecanicamente, não apenas documentada.
"""

import ast
from pathlib import Path

import pytest

from player_modeling.domain.events import EVENT_TYPES
from player_modeling.domain.features import FEATURE_COLUMNS, LABEL_COLUMN
from player_modeling.domain.personas import PERSONAS, BartlePersona

DOMAIN_DIR = Path(__file__).resolve().parents[3] / "player_modeling" / "domain"

DOMAIN_MODULES = sorted(DOMAIN_DIR.glob("*.py"))


def _imported_modules(source: str) -> list[str]:
    """Extrai os módulos importados por um arquivo Python.

    :param source: Código-fonte completo do módulo.

    :return: Nomes dos módulos importados, incluindo os de `from ... import`.
    """
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def test_domain_directory_is_not_empty() -> None:
    """Falha ruidosamente se a camada de domínio for esvaziada por engano."""
    assert DOMAIN_MODULES


@pytest.mark.parametrize("module_path", DOMAIN_MODULES, ids=lambda p: str(p.name))
def test_domain_modules_do_not_import_the_rest_of_the_project(module_path: Path) -> None:
    """Nenhum módulo de domínio importa outro módulo de `player_modeling`.

    É esta regra que impede a camada de virar depósito e que quebra as
    dependências invertidas que motivaram sua criação.

    :param module_path: Arquivo do pacote `domain/` sob teste.
    """
    imported = _imported_modules(module_path.read_text(encoding="utf-8"))
    internal = [name for name in imported if name.startswith("player_modeling")]

    assert internal == [], f"{module_path.name} importa {internal}"


def test_personas_match_the_bartle_taxonomy() -> None:
    """A lista de personas é exatamente a Taxonomia de Bartle, sem duplicação."""
    assert PERSONAS == [persona.value for persona in BartlePersona]
    assert set(PERSONAS) == {"Achiever", "Explorer", "Socializer", "Killer"}


def test_persona_order_is_preserved_for_seeded_generation() -> None:
    """A ordem das personas é a usada na geração semeada do dataset sintético.

    Reordenar mudaria o dataset produzido por uma mesma semente, e
    `src/data/` não pode ser sobrescrito (ver CLAUDE.md).
    """
    assert PERSONAS == ["Achiever", "Explorer", "Socializer", "Killer"]


def test_event_types_cover_the_features_the_worker_aggregates() -> None:
    """Todo tipo de evento usado na agregação de features existe no vocabulário."""
    aggregated = {"attack", "explore_area", "chat", "trade", "quest_complete", "retry"}

    assert aggregated <= set(EVENT_TYPES)


def test_feature_contract_is_ordered_and_excludes_the_label() -> None:
    """As colunas de feature são uma tupla ordenada e não incluem o rótulo."""
    assert isinstance(FEATURE_COLUMNS, tuple)
    assert LABEL_COLUMN not in FEATURE_COLUMNS
    assert len(set(FEATURE_COLUMNS)) == len(FEATURE_COLUMNS)
